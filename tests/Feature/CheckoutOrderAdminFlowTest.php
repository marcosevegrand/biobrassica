<?php

namespace Tests\Feature;

use App\Models\Cart;
use App\Models\Category;
use App\Models\Location;
use App\Models\Order;
use App\Models\Payment;
use App\Models\Product;
use App\Models\ShopSettings;
use App\Models\User;
use App\Services\OrderStateMachine;
use App\Services\PaymentService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use RuntimeException;
use Tests\TestCase;

class CheckoutOrderAdminFlowTest extends TestCase
{
    use RefreshDatabase;

    public function test_guest_can_add_view_and_merge_cart_on_login(): void
    {
        $product = $this->createProduct(stock: 10);
        $user = User::factory()->create(['email' => 'cliente@example.com']);

        $this->post(route('cart.add', ['product' => $product->id]), ['quantity' => 3])
            ->assertRedirect();

        $guestCart = Cart::whereNull('user_id')->firstOrFail();
        $this->assertNotNull($guestCart->guest_token);
        $this->assertSame(3, (int) $guestCart->items()->firstOrFail()->quantity);

        $this->get(route('cart.detail'))
            ->assertOk()
            ->assertSee($product->name);

        $this->post(route('login'), [
            'email' => $user->email,
            'password' => 'password',
        ])->assertRedirect(route('shop.home'));

        $this->assertDatabaseMissing('carts', ['id' => $guestCart->id]);
        $this->assertDatabaseHas('carts', ['user_id' => $user->id]);
        $this->assertDatabaseHas('cart_items', [
            'product_id' => $product->id,
            'quantity' => 3,
        ]);
    }

    public function test_guest_cannot_update_another_cart_item(): void
    {
        $product = $this->createProduct(stock: 10);
        $otherCart = Cart::create(['guest_token' => 'other-token']);
        $otherItem = $otherCart->items()->create([
            'product_id' => $product->id,
            'quantity' => 2,
            'reserved_quantity' => 0,
        ]);

        $this->post(route('cart.add', ['product' => $product->id]), ['quantity' => 1]);

        $this->post(route('cart.update', ['item' => $otherItem->id]), ['quantity' => 9])
            ->assertNotFound();

        $this->assertSame(2, (int) $otherItem->refresh()->quantity);
    }

    public function test_checkout_requires_authentication_but_preserves_guest_cart_after_login(): void
    {
        $product = $this->createProduct(stock: 10);
        $user = User::factory()->create(['email' => 'cliente@example.com']);

        $this->post(route('cart.add', ['product' => $product->id]), ['quantity' => 2]);

        $this->get(route('checkout'))->assertRedirect(route('login'));

        $this->post(route('login'), [
            'email' => $user->email,
            'password' => 'password',
        ]);

        $this->actingAs($user)
            ->get(route('checkout'))
            ->assertOk()
            ->assertSee($product->name);
    }

    public function test_shipping_checkout_adds_flat_rate_and_payment_uses_grand_total(): void
    {
        $this->fakePaymentCreation();
        $user = User::factory()->create();
        $product = $this->createProduct(price: 10, stock: 10);
        $this->createLocation();
        $this->createCart($user, $product, 2);
        $this->settings(['shipping_flat_rate' => 4.50]);

        $this->actingAs($user)
            ->post(route('checkout.store'), $this->checkoutPayload([
                'fulfillment_method' => 'shipping',
            ]))
            ->assertRedirect();

        $order = Order::firstOrFail();
        $this->assertSame('20.00', $order->subtotal);
        $this->assertSame('4.50', $order->shipping_cost);
        $this->assertSame('24.50', $order->total);
        $this->assertSame('24.50', $order->payment->amount);
    }

    public function test_fake_payments_allow_non_production_checkout_without_ifthenpay_keys(): void
    {
        config([
            'payments.ifthenpay.backoffice_key' => '',
            'payments.ifthenpay.anti_phishing_key' => '',
            'payments.ifthenpay.mbway_key' => '',
            'payments.ifthenpay.multibanco_key' => '',
            'payments.fake.enabled' => true,
            'payments.fake.auto_confirm' => true,
        ]);

        $user = User::factory()->create();
        $product = $this->createProduct(price: 10, stock: 10);
        $this->createLocation();
        $this->createCart($user, $product, 1);
        $this->settings();

        $this->actingAs($user)
            ->post(route('checkout.store'), $this->checkoutPayload())
            ->assertRedirect();

        $order = Order::firstOrFail();

        $this->assertSame(Order::PAYMENT_CONFIRMED, $order->payment_state);
        $this->assertSame(Payment::STATUS_CONFIRMED, $order->payment->status);
        $this->assertStringStartsWith('FAKE-mbway-', $order->payment->provider_payment_id);
    }

    public function test_free_shipping_threshold_and_malicious_shipping_input_are_ignored(): void
    {
        $this->fakePaymentCreation();
        $user = User::factory()->create();
        $product = $this->createProduct(price: 30, stock: 10);
        $this->createLocation();
        $this->createCart($user, $product, 2);
        $this->settings([
            'shipping_flat_rate' => 9.99,
            'free_shipping_min_subtotal' => 50,
        ]);

        $payload = $this->checkoutPayload([
            'fulfillment_method' => 'shipping',
            'shipping_cost' => 999,
            'total' => 1,
        ]);

        $this->actingAs($user)->post(route('checkout.store'), $payload)->assertRedirect();

        $order = Order::firstOrFail();
        $this->assertSame('60.00', $order->subtotal);
        $this->assertSame('0.00', $order->shipping_cost);
        $this->assertSame('60.00', $order->total);
    }

    public function test_checkout_disables_unavailable_fulfilment_method(): void
    {
        $user = User::factory()->create();
        $product = $this->createProduct(stock: 10);
        $product->update(['allow_shipping' => false, 'allow_pickup' => true]);
        $this->createLocation();
        $this->createCart($user, $product, 1);

        $this->actingAs($user)
            ->get(route('checkout'))
            ->assertOk()
            ->assertSee('value="shipping"', false)
            ->assertSee('disabled', false);
    }

    public function test_users_cannot_access_other_users_orders_or_payments(): void
    {
        [$owner, $order] = $this->createOrderWithPayment();
        $other = User::factory()->create();

        $this->actingAs($other)->get(route('order.show', ['order' => $order->id]))->assertNotFound();
        $this->actingAs($other)->get(route('payment.show', ['order' => $order->id]))->assertNotFound();
        $this->actingAs($other)->post(route('checkout.discard', ['order' => $order->id]))->assertNotFound();

        $this->actingAs($owner)->get(route('order.show', ['order' => $order->id]))->assertOk();
    }

    public function test_admin_panel_access_requires_verified_admin_user(): void
    {
        $regular = User::factory()->create(['is_admin' => false, 'email_verified_at' => now()]);
        $unverifiedAdmin = User::factory()->create(['is_admin' => true, 'email_verified_at' => null]);
        $admin = User::factory()->create(['is_admin' => true, 'email_verified_at' => now()]);

        $this->actingAs($regular)->get('/admin')->assertForbidden();
        $this->actingAs($unverifiedAdmin)->get('/admin')->assertForbidden();
        $this->actingAs($admin)->get('/admin')->assertOk();
    }

    public function test_admin_singleton_settings_pages_render_in_admin_panel(): void
    {
        $admin = User::factory()->create(['is_admin' => true, 'email_verified_at' => now()]);

        $this->actingAs($admin)->get('/admin/shop-settings')->assertOk();
        $this->actingAs($admin)->get('/admin/website-content')->assertOk();
    }

    public function test_refund_workflow_tracks_request_completion_and_restock(): void
    {
        [$admin, $order, $payment, $product] = $this->createOrderWithPayment(paymentStatus: Payment::STATUS_CONFIRMED, paymentState: Order::PAYMENT_CONFIRMED, withProduct: true);
        $service = app(PaymentService::class);

        $service->requestRefund($payment, 'Cliente pediu devolução.', $admin);
        $payment->refresh();

        $this->assertSame(Payment::REFUND_REQUESTED, $payment->refund_state);
        $this->assertSame($admin->id, $payment->refund_requested_by);

        $service->completeRefund($payment, 'RF-123', $admin, 'Transferência manual.', restock: true);
        $payment->refresh();
        $order->refresh();

        $this->assertSame(Payment::STATUS_REFUNDED, $payment->status);
        $this->assertSame(Payment::REFUND_COMPLETED, $payment->refund_state);
        $this->assertSame(Order::PAYMENT_REFUNDED, $order->payment_state);
        $this->assertSame(Order::STATUS_CANCELLED, $order->status);
        $this->assertSame(7, $product->refresh()->stock);
    }

    public function test_refund_requested_order_cannot_progress_to_fulfilment(): void
    {
        [$admin, $order, $payment] = $this->createOrderWithPayment(paymentStatus: Payment::STATUS_CONFIRMED, paymentState: Order::PAYMENT_CONFIRMED);
        $service = app(PaymentService::class);

        $service->requestRefund($payment, 'Cliente pediu devolução.', $admin);

        $this->expectException(RuntimeException::class);
        app(OrderStateMachine::class)->transition($order->refresh(), Order::STATUS_PREPARING);
    }

    public function test_order_state_machine_blocks_unpaid_order_progression(): void
    {
        [, $order] = $this->createOrderWithPayment();
        $service = app(OrderStateMachine::class);

        $this->expectException(RuntimeException::class);
        $service->transition($order, Order::STATUS_PREPARING);
    }

    private function fakePaymentCreation(): void
    {
        $this->app->instance(PaymentService::class, new class extends PaymentService
        {
            public function methodIsConfigured(string $method): bool
            {
                return true;
            }

            public function createPayment(Order $order, string $method): Payment
            {
                return Payment::create([
                    'order_id' => $order->id,
                    'method' => $method,
                    'status' => Payment::STATUS_PENDING,
                    'amount' => $order->total,
                    'provider_payment_id' => 'TEST-'.$order->id,
                    'provider_data' => [
                        'amount' => (string) $order->total,
                        'orderId' => (string) $order->id,
                        'transactionId' => 'TEST-'.$order->id,
                    ],
                    'expires_at' => now()->addMinutes(10),
                ]);
            }
        });
    }

    private function createProduct(float $price = 2.50, int $stock = 5): Product
    {
        $category = Category::firstOrCreate([
            'slug' => 'legumes',
        ], [
            'name' => 'Legumes',
            'is_active' => true,
        ]);

        return Product::create([
            'category_id' => $category->id,
            'slug' => 'produto-'.uniqid(),
            'name' => 'Produto Teste',
            'price' => $price,
            'stock' => $stock,
            'is_active' => true,
        ]);
    }

    private function createLocation(): Location
    {
        return Location::create([
            'name' => 'Quinta',
            'address' => 'Rua da Quinta',
            'is_active' => true,
        ]);
    }

    private function createCart(User $user, Product $product, int $quantity): Cart
    {
        $cart = Cart::create(['user_id' => $user->id]);
        $cart->items()->create([
            'product_id' => $product->id,
            'quantity' => $quantity,
            'reserved_quantity' => 0,
        ]);

        return $cart;
    }

    private function settings(array $overrides = []): ShopSettings
    {
        return ShopSettings::updateOrCreate(['id' => 1], array_merge([
            'is_shop_active' => true,
            'is_shop_brevemente' => false,
            'min_order_total' => 0,
            'shipping_flat_rate' => 0,
            'free_shipping_min_subtotal' => null,
            'mbway_enabled' => true,
            'bank_transfer_enabled' => true,
            'payment_timeout_minutes' => 30,
            'payment_expiry_grace_minutes' => 10,
            'mbway_minutes_to_expire' => 4,
            'multibanco_days_to_expire' => 3,
            'checkout_reservation_minutes' => 30,
        ], $overrides));
    }

    private function checkoutPayload(array $overrides = []): array
    {
        return array_merge([
            'name' => 'Cliente Teste',
            'email' => 'cliente@example.com',
            'phone' => '912345678',
            'payment_method' => 'mbway',
            'fulfillment_method' => 'pickup',
            'pickup_location' => $this->createLocation()->id,
            'shipping_address_line1' => 'Rua Teste',
            'shipping_city' => 'Braga',
            'shipping_postal_code' => '4700-000',
        ], $overrides);
    }

    private function createOrderWithPayment(string $paymentStatus = Payment::STATUS_PENDING, string $paymentState = Order::PAYMENT_PENDING, bool $withProduct = false): array
    {
        $user = User::factory()->create();
        $order = Order::create([
            'user_id' => $user->id,
            'email' => 'cliente@example.com',
            'phone' => '912345678',
            'name' => 'Cliente Teste',
            'status' => Order::STATUS_PENDING,
            'payment_state' => $paymentState,
            'fulfillment_method' => 'pickup',
            'pickup_location' => '1',
            'language' => 'pt',
            'subtotal' => 12.34,
            'shipping_cost' => 0,
            'total' => 12.34,
        ]);

        $product = null;

        if ($withProduct) {
            $product = $this->createProduct(price: 12.34, stock: 5);
            $order->items()->create([
                'product_id' => $product->id,
                'product_name' => $product->name,
                'price' => 12.34,
                'quantity' => 2,
            ]);
        }

        $payment = Payment::create([
            'order_id' => $order->id,
            'method' => 'mbway',
            'status' => $paymentStatus,
            'amount' => $order->total,
            'provider_payment_id' => 'REQ'.$order->id,
            'provider_data' => [
                'amount' => '12.34',
                'orderId' => (string) $order->id,
                'transactionId' => 'REQ'.$order->id,
            ],
            'paid_at' => $paymentStatus === Payment::STATUS_CONFIRMED ? now() : null,
        ]);

        return [$user, $order, $payment, $product];
    }
}
