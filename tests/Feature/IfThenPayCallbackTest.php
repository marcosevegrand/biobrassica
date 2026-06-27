<?php

namespace Tests\Feature;

use App\Models\Order;
use App\Models\Payment;
use App\Models\User;
use App\Notifications\OrderPaymentConfirmed;
use App\Services\PaymentService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Notification;
use Tests\TestCase;

class IfThenPayCallbackTest extends TestCase
{
    use RefreshDatabase;

    public function test_valid_ifthenpay_mbway_callback_confirms_payment_and_order(): void
    {
        Notification::fake();

        $user = User::factory()->create();

        $order = Order::create([
            'user_id' => $user->id,
            'email' => 'cliente@example.com',
            'phone' => '912345678',
            'name' => 'Cliente Teste',
            'status' => Order::STATUS_PENDING,
            'payment_state' => Order::PAYMENT_PENDING,
            'fulfillment_method' => 'pickup',
            'pickup_location' => '1',
            'language' => 'pt',
            'subtotal' => 12.34,
            'total' => 12.34,
        ]);

        Payment::create([
            'order_id' => $order->id,
            'method' => 'mbway',
            'status' => Payment::STATUS_PENDING,
            'amount' => 12.34,
            'provider_payment_id' => 'REQ123456',
            'provider_data' => [
                'amount' => '12.34',
                'orderId' => (string) $order->id,
                'transactionId' => 'REQ123456',
                'mobileNumber' => '912345678',
                'status' => 'pending',
            ],
            'expires_at' => now()->addMinutes(4),
        ]);

        $response = $this->getJson(route('payment.callback', [
            'key' => 'test-anti-phishing',
            'orderId' => $order->id,
            'amount' => '12.34',
            'requestId' => 'REQ123456',
        ]));

        $response->assertOk()->assertJson(['status' => 'ok']);

        $order->refresh();
        $this->assertSame(Order::PAYMENT_CONFIRMED, $order->payment_state);
        $this->assertSame(Order::STATUS_PENDING, $order->status);
        $this->assertSame(Payment::STATUS_CONFIRMED, $order->payment->status);
        $this->assertNotNull($order->payment->paid_at);
    }

    public function test_invalid_ifthenpay_callback_is_rejected(): void
    {
        $response = $this->getJson(route('payment.callback', [
            'key' => 'wrong',
            'orderId' => '999',
            'amount' => '10.00',
            'requestId' => 'missing',
        ]));

        $response->assertStatus(400)->assertJson(['status' => 'invalid']);
    }

    public function test_ifthenpay_callback_missing_required_fields_is_rejected(): void
    {
        $payment = $this->createPendingPayment();

        $response = $this->getJson(route('payment.callback', [
            'key' => 'test-anti-phishing',
            'orderId' => $payment->order_id,
            'requestId' => $payment->provider_payment_id,
        ]));

        $response->assertStatus(400)->assertJson(['status' => 'invalid']);
        $this->assertSame(Payment::STATUS_PENDING, $payment->refresh()->status);
    }

    public function test_ifthenpay_callback_with_wrong_method_is_rejected(): void
    {
        $payment = $this->createPendingPayment();

        $response = $this->getJson(route('payment.callback', [
            'key' => 'test-anti-phishing',
            'orderId' => $payment->order_id,
            'amount' => '12.34',
            'requestId' => $payment->provider_payment_id,
            'pm' => 'multibanco',
        ]));

        $response->assertStatus(400)->assertJson(['status' => 'invalid']);
        $this->assertSame(Payment::STATUS_PENDING, $payment->refresh()->status);
    }

    public function test_ifthenpay_multibanco_callback_with_wrong_reference_is_rejected(): void
    {
        $payment = $this->createPendingPayment(method: 'multibanco', providerPaymentId: 'MB123456', reference: '123456789');

        $response = $this->getJson(route('payment.callback', [
            'key' => 'test-anti-phishing',
            'orderId' => $payment->order_id,
            'amount' => '12.34',
            'requestId' => 'MB123456',
            'reference' => '999999999',
            'pm' => 'multibanco',
        ]));

        $response->assertStatus(400)->assertJson(['status' => 'invalid']);
        $this->assertSame(Payment::STATUS_PENDING, $payment->refresh()->status);
    }

    public function test_valid_ifthenpay_multibanco_callback_confirms_payment_and_order(): void
    {
        Notification::fake();
        $payment = $this->createPendingPayment(method: 'multibanco', providerPaymentId: 'MB123456', reference: '123456789');

        $response = $this->getJson(route('payment.callback', [
            'key' => 'test-anti-phishing',
            'orderId' => $payment->order_id,
            'amount' => '12.34',
            'requestId' => 'MB123456',
            'reference' => '123456789',
            'pm' => 'multibanco',
        ]));

        $response->assertOk()->assertJson(['status' => 'ok']);

        $payment->refresh();
        $payment->order->refresh();
        $this->assertSame(Payment::STATUS_CONFIRMED, $payment->status);
        $this->assertSame(Order::PAYMENT_CONFIRMED, $payment->order->payment_state);
    }

    public function test_blank_anti_phishing_key_never_confirms_payment(): void
    {
        config(['payments.ifthenpay.anti_phishing_key' => '']);
        $payment = $this->createPendingPayment();

        $response = $this->getJson(route('payment.callback', [
            'key' => '',
            'orderId' => $payment->order_id,
            'amount' => '12.34',
            'requestId' => $payment->provider_payment_id,
        ]));

        $response->assertStatus(400)->assertJson(['status' => 'invalid']);
        $this->assertSame(Payment::STATUS_PENDING, $payment->refresh()->status);
    }

    public function test_replayed_valid_callback_is_idempotent_and_does_not_duplicate_notifications(): void
    {
        Notification::fake();
        $payment = $this->createPendingPayment();
        $payload = [
            'key' => 'test-anti-phishing',
            'orderId' => $payment->order_id,
            'amount' => '12.34',
            'requestId' => $payment->provider_payment_id,
        ];

        $this->getJson(route('payment.callback', $payload))->assertOk();
        $this->getJson(route('payment.callback', $payload))->assertOk();

        $this->assertSame(Payment::STATUS_CONFIRMED, $payment->refresh()->status);
        Notification::assertSentOnDemand(OrderPaymentConfirmed::class, 1);
    }

    public function test_late_valid_callback_for_locally_cancelled_payment_is_recorded_for_manual_review(): void
    {
        $payment = $this->createPendingPayment();
        $payment->update([
            'status' => Payment::STATUS_CANCELLED,
            'last_error' => 'Tempo de pagamento expirado.',
        ]);
        $payment->order->update([
            'payment_state' => Order::PAYMENT_CANCELLED,
            'status' => Order::STATUS_CANCELLED,
        ]);

        $this->getJson(route('payment.callback', [
            'key' => 'test-anti-phishing',
            'orderId' => $payment->order_id,
            'amount' => '12.34',
            'requestId' => $payment->provider_payment_id,
        ]))->assertOk();

        $payment->refresh();
        $payment->order->refresh();

        $this->assertSame(Payment::STATUS_CONFIRMED, $payment->status);
        $this->assertSame(Payment::REFUND_REQUESTED, $payment->refund_state);
        $this->assertSame(Order::PAYMENT_CONFIRMED, $payment->order->payment_state);
        $this->assertSame(Order::STATUS_CANCELLED, $payment->order->status);
    }

    public function test_customer_cannot_cancel_already_confirmed_payment(): void
    {
        $payment = $this->createPendingPayment();
        $payment->update([
            'status' => Payment::STATUS_CONFIRMED,
            'paid_at' => now(),
        ]);
        $payment->order->update([
            'payment_state' => Order::PAYMENT_CONFIRMED,
            'status' => Order::STATUS_PENDING,
        ]);

        $this->actingAs($payment->order->user)
            ->post(route('checkout.discard', ['order' => $payment->order_id]))
            ->assertRedirect();

        $payment->refresh();
        $payment->order->refresh();
        $this->assertSame(Payment::STATUS_CONFIRMED, $payment->status);
        $this->assertSame(Order::PAYMENT_CONFIRMED, $payment->order->payment_state);
        $this->assertSame(Order::STATUS_PENDING, $payment->order->status);
    }

    public function test_ifthenpay_methods_require_global_credentials_before_checkout_enables_them(): void
    {
        config([
            'payments.ifthenpay.backoffice_key' => '',
            'payments.ifthenpay.anti_phishing_key' => 'test-anti-phishing',
            'payments.ifthenpay.mbway_key' => 'ITP-TEST',
            'payments.ifthenpay.multibanco_key' => 'ITP-TEST-MB',
        ]);

        $service = app(PaymentService::class);

        $this->assertFalse($service->methodIsConfigured('mbway'));
        $this->assertFalse($service->methodIsConfigured('multibanco'));
    }

    private function createPendingPayment(string $method = 'mbway', string $providerPaymentId = 'REQ123456', ?string $reference = null): Payment
    {
        $user = User::factory()->create();

        $order = Order::create([
            'user_id' => $user->id,
            'email' => 'cliente@example.com',
            'phone' => '912345678',
            'name' => 'Cliente Teste',
            'status' => Order::STATUS_PENDING,
            'payment_state' => Order::PAYMENT_PENDING,
            'fulfillment_method' => 'pickup',
            'pickup_location' => '1',
            'language' => 'pt',
            'subtotal' => 12.34,
            'total' => 12.34,
        ]);

        return Payment::create([
            'order_id' => $order->id,
            'method' => $method,
            'status' => Payment::STATUS_PENDING,
            'amount' => 12.34,
            'provider_payment_id' => $providerPaymentId,
            'provider_reference' => $reference,
            'provider_data' => [
                'amount' => '12.34',
                'orderId' => (string) $order->id,
                'transactionId' => $providerPaymentId,
                'mobileNumber' => '912345678',
                'entity' => $method === 'multibanco' ? '12345' : null,
                'reference' => $reference,
                'status' => 'pending',
            ],
            'expires_at' => now()->addMinutes(4),
        ]);
    }
}
