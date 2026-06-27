<?php

namespace App\Services;

use App\Models\Order;
use App\Models\Payment;
use App\Models\ShopSettings;
use App\Models\User;
use App\Notifications\OrderPaymentConfirmed;
use App\Notifications\OrderPaymentRejected;
use Carbon\Carbon;
use DateTimeInterface;
use Ifthenpay\PaymentGateway\Enums\Status as IfthenpayStatus;
use Ifthenpay\PaymentGateway\Exception\EndpointResponseException;
use Ifthenpay\PaymentGateway\Exception\WebhookValidationException;
use Ifthenpay\PaymentGateway\IfthenpayGateway;
use Ifthenpay\PaymentGateway\Model\Mbway;
use Ifthenpay\PaymentGateway\Model\MultibancoDynamic;
use Ifthenpay\PaymentGateway\RequestObj\WebhookRequest;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Notification;
use RuntimeException;

class PaymentService
{
    public function createPayment(Order $order, string $method): Payment
    {
        $this->ensureConfigured($method);

        if ($this->fakePaymentsEnabled()) {
            return $this->createFakePayment($order, $method);
        }

        $payment = Payment::create([
            'order_id' => $order->id,
            'method' => $method,
            'status' => Payment::STATUS_PENDING,
            'amount' => $order->total,
            'expires_at' => Carbon::now()->addMinutes($this->paymentTimeoutMinutes()),
        ]);

        try {
            $providerPayment = match ($method) {
                'mbway' => $this->initMbwayPayment($order),
                'multibanco' => $this->initMultibancoPayment($order),
                default => throw new RuntimeException('Método de pagamento inválido.'),
            };
        } catch (RuntimeException $exception) {
            $this->rejectPayment($payment->refresh(), $exception->getMessage());

            throw $exception;
        }

        try {
            $payment->update([
                'provider_reference' => $providerPayment->getReference(),
                'provider_payment_id' => $providerPayment->getTransactionId(),
                'provider_data' => $providerPayment->toArray(),
                'expires_at' => $this->carbonFromDate($providerPayment->getExpireDate())
                    ?? Carbon::now()->addMinutes($this->paymentTimeoutMinutes()),
            ]);
        } catch (\Throwable $exception) {
            $this->rejectPayment($payment->refresh(), 'Não foi possível guardar os dados devolvidos pela IfThenPay.');

            throw new RuntimeException('Não foi possível guardar os dados devolvidos pela IfThenPay.', previous: $exception);
        }

        return $payment->refresh();
    }

    public function providerConfigurationErrors(?string $method = null): array
    {
        $errors = [];

        if (! filled(config('payments.ifthenpay.backoffice_key'))) {
            $errors[] = 'A chave de backoffice da IfThenPay não está configurada.';
        }

        if (! filled(config('payments.ifthenpay.anti_phishing_key'))) {
            $errors[] = 'A chave anti-phishing da IfThenPay não está configurada.';
        }

        if (($method === null || $method === 'mbway') && ! filled(config('payments.ifthenpay.mbway_key'))) {
            $errors[] = 'A chave MB WAY da IfThenPay não está configurada.';
        }

        if (($method === null || $method === 'multibanco') && ! filled(config('payments.ifthenpay.multibanco_key'))) {
            $errors[] = 'A chave Multibanco da IfThenPay não está configurada.';
        }

        return array_values(array_unique($errors));
    }

    public function getPaymentDetails(Payment $payment): array
    {
        $data = $payment->provider_data ?? [];

        return match ($payment->method) {
            'mbway' => [
                'label' => 'MB WAY',
                'transaction_id' => $payment->provider_payment_id,
                'mobile_number' => $data['mobileNumber'] ?? $data['mobile_number'] ?? null,
                'status' => $payment->status,
            ],
            'multibanco' => [
                'label' => 'Multibanco',
                'entity' => $data['entity'] ?? null,
                'reference' => $payment->provider_reference,
                'transaction_id' => $payment->provider_payment_id,
                'amount' => $payment->amount,
            ],
            default => [],
        };
    }

    public function refreshProviderStatus(Payment $payment): void
    {
        if ($this->fakePaymentsEnabled()) {
            if ($payment->status === Payment::STATUS_PENDING && $this->fakePaymentsAutoConfirm()) {
                $this->confirmPayment($payment);
            }

            return;
        }

        if ($payment->status !== Payment::STATUS_PENDING || $payment->method !== 'mbway' || ! $payment->provider_payment_id) {
            return;
        }

        $cacheKey = "payments:provider-refresh:{$payment->id}";

        if (Cache::has($cacheKey)) {
            return;
        }

        Cache::put($cacheKey, true, now()->addSeconds(30));

        try {
            $status = $this->gateway()->mbway()->getPaymentStatus($payment->provider_payment_id);
        } catch (\Throwable) {
            return;
        }

        if ($status === IfthenpayStatus::PAID) {
            $this->confirmPayment($payment->refresh());

            return;
        }

        if (in_array($status, [IfthenpayStatus::REJECTED_BY_USER, IfthenpayStatus::DECLINED, IfthenpayStatus::EXPIRED, IfthenpayStatus::CANCELED], true)) {
            $this->rejectPayment($payment->refresh(), match ($status) {
                IfthenpayStatus::REJECTED_BY_USER => 'Pagamento MB WAY rejeitado pelo utilizador.',
                IfthenpayStatus::DECLINED => 'Pagamento MB WAY recusado.',
                IfthenpayStatus::EXPIRED => 'Pagamento MB WAY expirado.',
                default => 'Pagamento MB WAY cancelado.',
            });
        }
    }

    public function confirmFromWebhook(array $payload): Payment
    {
        $extracted = $this->extractWebhookPayload($payload);

        $this->validateWebhookKey($extracted);

        $payment = $this->findWebhookPayment($extracted);

        if (! $payment) {
            throw new RuntimeException('Pagamento não encontrado.');
        }

        $this->validateWebhookPayload($payment, $extracted);

        if ($payment->status === Payment::STATUS_CANCELLED) {
            $this->recordLateConfirmedPayment($payment);

            return $payment->refresh();
        }

        $this->confirmPayment($payment);

        return $payment->refresh();
    }

    public function registerConfiguredWebhooks(string $webhookUrl): array
    {
        $registered = [];

        if (filled(config('payments.ifthenpay.mbway_key'))) {
            $this->ensureConfigured('mbway');
            $registered['mbway'] = $this->gateway()->mbway()->registerWebhook($webhookUrl);
        }

        if (filled(config('payments.ifthenpay.multibanco_key'))) {
            $this->ensureConfigured('multibanco');
            $registered['multibanco'] = $this->gateway()->multibancoDynamic()->registerWebhook($webhookUrl);
        }

        return $registered;
    }

    public function confirmPayment(Payment $payment): void
    {
        if ($payment->status === Payment::STATUS_CONFIRMED) {
            return;
        }

        if ($payment->status !== Payment::STATUS_PENDING) {
            throw new RuntimeException('Apenas pagamentos pendentes podem ser confirmados.');
        }

        [$order, $changed] = DB::transaction(function () use ($payment) {
            $lockedPayment = Payment::whereKey($payment->id)->lockForUpdate()->firstOrFail();

            if ($lockedPayment->status === Payment::STATUS_CONFIRMED) {
                return [$lockedPayment->order()->with('items')->firstOrFail(), false];
            }

            if ($lockedPayment->status !== Payment::STATUS_PENDING) {
                throw new RuntimeException('Apenas pagamentos pendentes podem ser confirmados.');
            }

            $lockedPayment->status = Payment::STATUS_CONFIRMED;
            $lockedPayment->paid_at = Carbon::now();
            $lockedPayment->last_error = null;
            $lockedPayment->save();

            $order = $lockedPayment->order()->lockForUpdate()->firstOrFail();
            $order->payment_state = Order::PAYMENT_CONFIRMED;
            $order->save();

            return [$order->load('items'), true];
        });

        if ($changed) {
            $this->notifyPaymentConfirmed($order->loadMissing('payment'));
        }
    }

    public function confirmPaymentIfPaidAtProvider(Payment $payment): void
    {
        $providerPaid = $this->paymentIsPaidAtProvider($payment);

        if ($providerPaid !== true) {
            throw new RuntimeException('A IfThenPay ainda não confirma este pagamento. Aguarde o callback automático ou valide manualmente no backoffice IfThenPay.');
        }

        $this->confirmPayment($payment->refresh());
    }

    public function rejectPayment(Payment $payment, string $reason): void
    {
        $order = DB::transaction(function () use ($payment, $reason) {
            $lockedPayment = Payment::whereKey($payment->id)->lockForUpdate()->firstOrFail();

            if ($lockedPayment->status !== Payment::STATUS_PENDING) {
                throw new RuntimeException('Apenas pagamentos pendentes podem ser rejeitados.');
            }

            $lockedPayment->status = Payment::STATUS_CANCELLED;
            $lockedPayment->last_error = $reason;
            $lockedPayment->save();

            $order = $lockedPayment->order()->with('items.product')->lockForUpdate()->firstOrFail();
            $this->restoreOrderStock($order);
            $order->payment_state = Order::PAYMENT_CANCELLED;
            $order->status = Order::STATUS_CANCELLED;
            $order->save();

            return $order;
        });

        $this->notifyPaymentRejected($order->loadMissing('payment'), $reason);
    }

    public function requestRefund(Payment $payment, string $reason, ?User $actor = null): void
    {
        DB::transaction(function () use ($payment, $reason, $actor): void {
            $lockedPayment = Payment::whereKey($payment->id)->lockForUpdate()->firstOrFail();

            if ($lockedPayment->status !== Payment::STATUS_CONFIRMED) {
                throw new RuntimeException('Apenas pagamentos confirmados podem ter reembolso pedido.');
            }

            if ($lockedPayment->refund_state === Payment::REFUND_COMPLETED) {
                throw new RuntimeException('Este pagamento já foi reembolsado.');
            }

            $lockedPayment->refund_state = Payment::REFUND_REQUESTED;
            $lockedPayment->refund_amount = $lockedPayment->amount;
            $lockedPayment->refund_reason = $reason;
            $lockedPayment->refund_requested_at = Carbon::now();
            $lockedPayment->refund_requested_by = $actor?->id;
            $lockedPayment->refund_notes = null;
            $lockedPayment->save();

            $order = $lockedPayment->order()->lockForUpdate()->first();

            if ($order && $order->status !== Order::STATUS_DELIVERED) {
                $order->status = Order::STATUS_CANCELLED;
                $order->save();
            }
        });
    }

    public function completeRefund(Payment $payment, ?string $reference = null, ?User $actor = null, ?string $notes = null, bool $restock = false): void
    {
        DB::transaction(function () use ($payment, $reference, $actor, $notes, $restock): void {
            $lockedPayment = Payment::whereKey($payment->id)->lockForUpdate()->firstOrFail();

            if ($lockedPayment->status !== Payment::STATUS_CONFIRMED || $lockedPayment->refund_state !== Payment::REFUND_REQUESTED) {
                throw new RuntimeException('Apenas pedidos de reembolso pendentes podem ser concluídos.');
            }

            $order = $lockedPayment->order()->with('items.product')->lockForUpdate()->firstOrFail();

            if ($restock && $order->status !== Order::STATUS_DELIVERED) {
                $this->restockOrderItems($order);
            }

            $lockedPayment->status = Payment::STATUS_REFUNDED;
            $lockedPayment->refund_state = Payment::REFUND_COMPLETED;
            $lockedPayment->refund_reference = $reference;
            $lockedPayment->refund_notes = $notes;
            $lockedPayment->refunded_at = Carbon::now();
            $lockedPayment->refunded_by = $actor?->id;
            $lockedPayment->save();

            $order->payment_state = Order::PAYMENT_REFUNDED;
            if ($order->status !== Order::STATUS_DELIVERED) {
                $order->status = Order::STATUS_CANCELLED;
            }
            $order->save();
        });
    }

    public function failRefund(Payment $payment, string $notes, ?User $actor = null): void
    {
        DB::transaction(function () use ($payment, $notes, $actor): void {
            $lockedPayment = Payment::whereKey($payment->id)->lockForUpdate()->firstOrFail();

            if ($lockedPayment->status !== Payment::STATUS_CONFIRMED || $lockedPayment->refund_state !== Payment::REFUND_REQUESTED) {
                throw new RuntimeException('Apenas pedidos de reembolso pendentes podem ser marcados como falhados.');
            }

            $lockedPayment->refund_state = Payment::REFUND_FAILED;
            $lockedPayment->refund_notes = $notes;
            $lockedPayment->refunded_by = $actor?->id;
            $lockedPayment->save();
        });
    }

    public function expireIfTimedOut(Payment $payment): void
    {
        if ($payment->status !== Payment::STATUS_PENDING || ! $payment->expires_at || $payment->expires_at->isFuture()) {
            return;
        }

        $this->refreshProviderStatus($payment);
        $payment->refresh();

        if ($payment->status !== Payment::STATUS_PENDING || $payment->expires_at?->copy()->addMinutes($this->paymentExpiryGraceMinutes())->isFuture()) {
            return;
        }

        $providerPaid = $this->paymentIsPaidAtProvider($payment);

        if ($providerPaid === true) {
            $this->confirmPayment($payment->refresh());

            return;
        }

        if ($providerPaid === null) {
            return;
        }

        DB::transaction(function () use ($payment) {
            $lockedPayment = Payment::whereKey($payment->id)->lockForUpdate()->first();
            if (! $lockedPayment || $lockedPayment->status !== Payment::STATUS_PENDING || ! $lockedPayment->expires_at || $lockedPayment->expires_at->copy()->addMinutes($this->paymentExpiryGraceMinutes())->isFuture()) {
                return;
            }

            $order = $lockedPayment->order()->with('items.product')->lockForUpdate()->first();

            $lockedPayment->status = Payment::STATUS_CANCELLED;
            $lockedPayment->last_error = 'Tempo de pagamento expirado.';
            $lockedPayment->save();

            if (! $order || $order->payment_state !== Order::PAYMENT_PENDING) {
                return;
            }

            $this->restoreOrderStock($order);
            $order->payment_state = Order::PAYMENT_CANCELLED;
            $order->status = Order::STATUS_CANCELLED;
            $order->save();
        });
    }

    private function restoreOrderStock(Order $order): void
    {
        if ($order->payment_state !== Order::PAYMENT_PENDING) {
            return;
        }

        foreach ($order->items as $item) {
            if ($item->product) {
                $product = $item->product()->lockForUpdate()->first();
                if ($product) {
                    $product->stock = (int) $product->stock + (int) $item->quantity;
                    $product->save();
                }
            }
        }
    }

    private function restockOrderItems(Order $order): void
    {
        foreach ($order->items as $item) {
            $product = $item->product()->lockForUpdate()->first();

            if ($product) {
                $product->stock = (int) $product->stock + (int) $item->quantity;
                $product->save();
            }
        }
    }

    private function notifyPaymentConfirmed(Order $order): void
    {
        try {
            Notification::route('mail', $order->email)->notify(new OrderPaymentConfirmed($order));

            foreach ($this->staffNotificationEmails() as $email) {
                Notification::route('mail', $email)->notify(new OrderPaymentConfirmed($order, true));
            }
        } catch (\Throwable) {
            // Payment confirmation must not be rolled back because SMTP is unavailable.
        }
    }

    private function notifyPaymentRejected(Order $order, string $reason): void
    {
        try {
            Notification::route('mail', $order->email)->notify(new OrderPaymentRejected($order, $reason));
        } catch (\Throwable) {
            // Payment rejection must not fail because SMTP is unavailable.
        }
    }

    private function staffNotificationEmails(): array
    {
        return array_values(array_filter(array_map(
            static fn (string $email): string => trim($email),
            explode(',', (string) $this->settings()->staff_notification_emails),
        )));
    }

    private function initMbwayPayment(Order $order): Mbway
    {
        try {
            return $this->gateway()->mbway()->initPayment(
                $this->providerOrderId($order),
                $this->formatAmount($order->total),
                $this->normalizeMobileNumber($order->phone),
                "Encomenda #{$order->id}",
                $order->email,
            );
        } catch (EndpointResponseException|\Throwable $exception) {
            report($exception);

            throw new RuntimeException('Não foi possível iniciar o pagamento MB WAY. Tente novamente.', previous: $exception);
        }
    }

    private function initMultibancoPayment(Order $order): MultibancoDynamic
    {
        try {
            return $this->gateway()->multibancoDynamic()->initPayment(
                $this->providerOrderId($order),
                $this->formatAmount($order->total),
                "Encomenda #{$order->id}",
            );
        } catch (EndpointResponseException|\Throwable $exception) {
            report($exception);

            throw new RuntimeException('Não foi possível gerar a referência Multibanco. Tente novamente.', previous: $exception);
        }
    }

    private function gateway(): IfthenpayGateway
    {
        $credentials = config('payments.ifthenpay');
        $settings = $this->settings();

        return new IfthenpayGateway([
            'backofficeKey' => (string) ($credentials['backoffice_key'] ?? ''),
            'antiPhishingKey' => (string) ($credentials['anti_phishing_key'] ?? ''),
            'language' => app()->getLocale() ?: 'pt',
            'mbway' => [
                'key' => (string) ($credentials['mbway_key'] ?? ''),
                'minutesToExpire' => (int) $settings->mbway_minutes_to_expire,
            ],
            'multibancoDynamic' => [
                'key' => (string) ($credentials['multibanco_key'] ?? ''),
                'daysToExpire' => (int) $settings->multibanco_days_to_expire,
            ],
        ]);
    }

    public function methodIsConfigured(string $method): bool
    {
        if ($this->fakePaymentsEnabled()) {
            return in_array($method, ['mbway', 'multibanco'], true);
        }

        if (! filled(config('payments.ifthenpay.backoffice_key')) || ! filled(config('payments.ifthenpay.anti_phishing_key'))) {
            return false;
        }

        return match ($method) {
            'mbway' => filled(config('payments.ifthenpay.mbway_key')),
            'multibanco' => filled(config('payments.ifthenpay.multibanco_key')),
            default => false,
        };
    }

    private function ensureConfigured(string $method): void
    {
        if (! $this->methodIsConfigured($method)) {
            throw new RuntimeException($this->providerConfigurationErrors($method)[0] ?? 'O método de pagamento selecionado não está configurado.');
        }
    }

    private function paymentExpiryGraceMinutes(): int
    {
        return max(0, (int) $this->settings()->payment_expiry_grace_minutes);
    }

    private function paymentTimeoutMinutes(): int
    {
        return max(1, (int) $this->settings()->payment_timeout_minutes);
    }

    private function settings(): ShopSettings
    {
        return ShopSettings::current();
    }

    private function providerOrderId(Order $order): string
    {
        return (string) $order->id;
    }

    private function formatAmount(mixed $amount): string
    {
        return number_format((float) $amount, 2, '.', '');
    }

    private function normalizeMobileNumber(?string $phone): string
    {
        $digits = preg_replace('/\D+/', '', (string) $phone) ?: '';

        if (str_starts_with($digits, '351') && strlen($digits) === 12) {
            $digits = substr($digits, 3);
        }

        if (! preg_match('/^9\d{8}$/', $digits)) {
            throw new RuntimeException('Para pagar por MB WAY indique um telemóvel português válido.');
        }

        return $digits;
    }

    private function carbonFromDate(?DateTimeInterface $date): ?Carbon
    {
        return $date ? Carbon::instance($date) : null;
    }

    private function extractWebhookPayload(array $payload): array
    {
        return [
            'anti_phishing_key' => (string) ($payload['key'] ?? $payload['apk'] ?? $payload['anti_phishing_key'] ?? ''),
            'order_id' => (string) ($payload['orderId'] ?? $payload['oid'] ?? $payload['id'] ?? $payload['order_id'] ?? ''),
            'amount' => (string) ($payload['amount'] ?? $payload['val'] ?? ''),
            'transaction_id' => (string) ($payload['requestId'] ?? $payload['tid'] ?? $payload['transaction_id'] ?? ''),
            'reference' => (string) ($payload['reference'] ?? $payload['ref'] ?? ''),
            'method' => (string) ($payload['pm'] ?? $payload['payment_method'] ?? $payload['method'] ?? ''),
            'raw' => $payload,
        ];
    }

    private function findWebhookPayment(array $payload): ?Payment
    {
        return Payment::query()
            ->whereIn('status', [Payment::STATUS_PENDING, Payment::STATUS_CONFIRMED, Payment::STATUS_CANCELLED])
            ->when($payload['transaction_id'] !== '', fn ($query) => $query->where('provider_payment_id', $payload['transaction_id']))
            ->when($payload['transaction_id'] === '' && $payload['reference'] !== '', fn ($query) => $query->where('provider_reference', $payload['reference']))
            ->when($payload['transaction_id'] === '' && $payload['reference'] === '', fn ($query) => $query->whereRaw('1 = 0'))
            ->with('order')
            ->first();
    }

    private function validateWebhookPayload(Payment $payment, array $payload): void
    {
        $this->validateWebhookKey($payload);

        foreach (['anti_phishing_key', 'order_id', 'amount', 'transaction_id'] as $requiredField) {
            if ($payload[$requiredField] === '') {
                throw new RuntimeException('Callback incompleto.');
            }
        }

        if ($payment->method === 'multibanco' && $payload['reference'] === '') {
            throw new RuntimeException('Callback Multibanco sem referência.');
        }

        if ($payload['order_id'] !== $this->providerOrderId($payment->order)) {
            throw new RuntimeException('Callback com encomenda inválida.');
        }

        if ((int) round(((float) $payload['amount']) * 100) !== (int) round(((float) $payment->amount) * 100)) {
            throw new RuntimeException('Callback com valor inválido.');
        }

        if (! hash_equals((string) $payment->provider_payment_id, $payload['transaction_id'])) {
            throw new RuntimeException('Callback com transação inválida.');
        }

        if ($payment->method === 'multibanco' && ! hash_equals((string) $payment->provider_reference, $payload['reference'])) {
            throw new RuntimeException('Callback com referência inválida.');
        }

        if ($payload['method'] !== '' && $this->normalizeWebhookMethod($payload['method']) !== $payment->method) {
            throw new RuntimeException('Callback com método inválido.');
        }

        $webhookRequest = new WebhookRequest(
            $this->formatAmount($payload['amount']),
            $payload['order_id'],
            $payload['anti_phishing_key'],
            $payload['transaction_id'],
            $payload['reference'],
        );

        try {
            if ($payment->method === 'mbway') {
                $this->gateway()->mbway()->validateWebhook($webhookRequest, $this->mbwayModelFromPayment($payment));
            } elseif ($payment->method === 'multibanco') {
                $this->gateway()->multibancoDynamic()->validateWebhook($webhookRequest, $this->multibancoModelFromPayment($payment));
            }
        } catch (WebhookValidationException $exception) {
            throw new RuntimeException('Callback IfThenPay inválido.', previous: $exception);
        }
    }

    private function normalizeWebhookMethod(string $method): string
    {
        $normalized = strtolower(preg_replace('/[^a-z0-9]+/i', '', $method) ?: '');

        return match ($normalized) {
            'mbway' => 'mbway',
            'multibanco', 'multibancodynamic', 'mb' => 'multibanco',
            default => $normalized,
        };
    }

    private function validateWebhookKey(array $payload): void
    {
        if (! filled(config('payments.ifthenpay.anti_phishing_key')) || ! hash_equals((string) config('payments.ifthenpay.anti_phishing_key'), (string) ($payload['anti_phishing_key'] ?? ''))) {
            throw new RuntimeException('Callback inválido.');
        }
    }

    private function paymentIsPaidAtProvider(Payment $payment): ?bool
    {
        if ($this->fakePaymentsEnabled()) {
            return true;
        }

        if (! $payment->provider_payment_id) {
            return false;
        }

        try {
            return match ($payment->method) {
                'mbway' => $this->gateway()->mbway()->isPaid($this->mbwayModelFromPayment($payment)),
                'multibanco' => $this->gateway()->multibancoDynamic()->isPaid($this->multibancoModelFromPayment($payment)),
                default => false,
            };
        } catch (\Throwable) {
            return null;
        }
    }

    private function recordLateConfirmedPayment(Payment $payment): void
    {
        DB::transaction(function () use ($payment): void {
            $lockedPayment = Payment::whereKey($payment->id)->lockForUpdate()->firstOrFail();

            if ($lockedPayment->status !== Payment::STATUS_CANCELLED) {
                return;
            }

            $order = $lockedPayment->order()->lockForUpdate()->firstOrFail();
            $reviewMessage = 'Pagamento confirmado pela IfThenPay após cancelamento/expiração local. Rever manualmente antes de preparar ou reembolsar.';

            $lockedPayment->status = Payment::STATUS_CONFIRMED;
            $lockedPayment->paid_at = Carbon::now();
            $lockedPayment->last_error = $reviewMessage;
            $lockedPayment->refund_state = Payment::REFUND_REQUESTED;
            $lockedPayment->refund_amount = $lockedPayment->amount;
            $lockedPayment->refund_reason = $reviewMessage;
            $lockedPayment->refund_requested_at = Carbon::now();
            $lockedPayment->save();

            $order->payment_state = Order::PAYMENT_CONFIRMED;
            $order->status = Order::STATUS_CANCELLED;
            $order->notes = trim(implode("\n", array_filter([$order->notes, $reviewMessage])));
            $order->save();
        });
    }

    private function createFakePayment(Order $order, string $method): Payment
    {
        if (! in_array($method, ['mbway', 'multibanco'], true)) {
            throw new RuntimeException('Método de pagamento inválido.');
        }

        $payment = Payment::create([
            'order_id' => $order->id,
            'method' => $method,
            'status' => Payment::STATUS_PENDING,
            'amount' => $order->total,
            'provider_reference' => $method === 'multibanco' ? str_pad((string) $order->id, 9, '0', STR_PAD_LEFT) : null,
            'provider_payment_id' => 'FAKE-'.$method.'-'.$order->id.'-'.now()->format('YmdHis'),
            'provider_data' => [
                'fake' => true,
                'orderId' => $this->providerOrderId($order),
                'amount' => $this->formatAmount($order->total),
                'entity' => $method === 'multibanco' ? '99999' : null,
                'mobileNumber' => $method === 'mbway' ? $order->phone : null,
            ],
            'expires_at' => Carbon::now()->addMinutes($this->paymentTimeoutMinutes()),
        ]);

        if ($this->fakePaymentsAutoConfirm()) {
            $this->confirmPayment($payment);
        }

        return $payment->refresh();
    }

    private function fakePaymentsEnabled(): bool
    {
        return (bool) config('payments.fake.enabled', false)
            && ! app()->environment('production');
    }

    private function fakePaymentsAutoConfirm(): bool
    {
        return (bool) config('payments.fake.auto_confirm', true);
    }

    private function mbwayModelFromPayment(Payment $payment): Mbway
    {
        $data = $payment->provider_data ?? [];

        return new Mbway(
            $this->formatAmount($payment->amount),
            (string) ($data['orderId'] ?? $this->providerOrderId($payment->order)),
            (string) $payment->provider_payment_id,
            (string) ($data['mobileNumber'] ?? ''),
            IfthenpayStatus::PENDING,
            $payment->expires_at?->toDateTimeImmutable(),
        );
    }

    private function multibancoModelFromPayment(Payment $payment): MultibancoDynamic
    {
        $data = $payment->provider_data ?? [];

        return new MultibancoDynamic(
            $this->formatAmount($payment->amount),
            (string) ($data['orderId'] ?? $this->providerOrderId($payment->order)),
            (string) ($data['entity'] ?? ''),
            (string) $payment->provider_reference,
            (string) $payment->provider_payment_id,
            IfthenpayStatus::PENDING,
            $payment->expires_at?->toDateTimeImmutable(),
        );
    }
}
