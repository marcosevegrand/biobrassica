<?php

namespace App\Services;

use App\Models\Order;
use App\Models\Payment;
use App\Models\ShopSettings;
use Carbon\Carbon;
use RuntimeException;

class PaymentService
{
    public function __construct(
        private readonly OrderStateMachine $stateMachine,
    ) {}

    public function createPayment(Order $order, string $method): Payment
    {
        $settings = ShopSettings::first();
        $timeout = $settings?->payment_timeout_minutes ?: config('payments.timeout_minutes', 30);

        return Payment::create([
            'order_id' => $order->id,
            'method' => $method,
            'status' => 'pending',
            'amount' => $order->total,
            'expires_at' => Carbon::now()->addMinutes($timeout),
        ]);
    }

    public function getManualMbwayDetails(): array
    {
        $settings = ShopSettings::first();

        return [
            'phone' => $settings?->mbway_number ?: config('payments.mbway_phone'),
            'label' => 'MB WAY',
        ];
    }

    public function getManualBankTransferDetails(): array
    {
        $settings = ShopSettings::first();

        return [
            'iban' => $settings?->bank_iban ?: config('payments.bank_transfer_iban'),
            'bic' => $settings?->bank_bic ?: config('payments.bank_transfer_bic'),
            'beneficiary' => $settings?->bank_beneficiary ?: config('payments.bank_transfer_beneficiary'),
            'label' => 'Transferência Bancária',
        ];
    }

    public function confirmPayment(Payment $payment): void
    {
        if ($payment->status === 'paid') {
            return;
        }

        $payment->status = 'paid';
        $payment->paid_at = Carbon::now();
        $payment->save();

        $order = $payment->order;
        $order->payment_state = 'paid';
        $order->save();

        $this->stateMachine->transition($order, 'confirmed');
    }

    public function rejectPayment(Payment $payment, string $reason): void
    {
        if ($payment->status !== 'pending') {
            throw new RuntimeException('Apenas pagamentos pendentes podem ser rejeitados.');
        }

        $payment->status = 'rejected';
        $payment->last_error = $reason;
        $payment->save();

        $order = $payment->order;
        $order->payment_state = 'rejected';
        $order->save();

        $this->stateMachine->transition($order, 'cancelled');
    }

    public function expireIfTimedOut(Payment $payment): void
    {
        if ($payment->status !== 'pending' || !$payment->expires_at || $payment->expires_at->isFuture()) {
            return;
        }

        $order = $payment->order()->with('items.product')->first();

        $payment->status = 'expired';
        $payment->last_error = 'Tempo de pagamento expirado.';
        $payment->save();

        if (!$order || $order->payment_state !== 'pending') {
            return;
        }

        foreach ($order->items as $item) {
            if ($item->product) {
                $item->product->stock = (int) $item->product->stock + (int) $item->quantity;
                $item->product->save();
            }
        }

        $order->payment_state = 'expired';
        $order->save();
    }
}
