<?php

namespace Tests\Feature;

use App\Models\Cart;
use App\Models\Category;
use App\Models\Location;
use App\Models\Order;
use App\Models\Payment;
use App\Models\Product;
use App\Models\User;
use App\Models\WebsiteContent;
use App\Services\PaymentService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Log;
use Tests\TestCase;

class SecurityAndCartFlowTest extends TestCase
{
    use RefreshDatabase;

    public function test_login_next_parameter_does_not_redirect_to_external_urls(): void
    {
        $user = User::factory()->create([
            'email' => 'cliente@example.com',
            'password' => 'password',
        ]);

        $this->get(route('login', ['next' => 'https://evil.example/phishing']));

        $response = $this->post(route('login'), [
            'email' => $user->email,
            'password' => 'password',
        ]);

        $response->assertRedirect(route('shop.home'));
    }

    public function test_public_registration_rejects_configured_admin_email(): void
    {
        config(['biobrassica.admin.emails' => ['admin@example.com']]);

        $response = $this->post(route('shop.register'), [
            'name' => 'Impostor',
            'email' => 'admin@example.com',
            'password' => 'password123',
            'password_confirmation' => 'password123',
        ]);

        $response->assertSessionHasErrors('email');
        $this->assertDatabaseMissing('users', ['email' => 'admin@example.com']);
    }

    public function test_registration_regenerates_session_after_login(): void
    {
        $this->startSession();
        $previousSessionId = session()->getId();

        $response = $this->post(route('shop.register'), [
            'name' => 'Cliente',
            'email' => 'cliente@example.com',
            'password' => 'password123',
            'password_confirmation' => 'password123',
        ]);

        $response->assertRedirect(route('shop.home'));
        $this->assertAuthenticated();
        $this->assertNotSame($previousSessionId, session()->getId());
    }

    public function test_legal_page_markdown_strips_unsafe_html_and_links(): void
    {
        WebsiteContent::create([
            'id' => 1,
            'company_legal_name' => 'BioBrassica',
            'support_email' => 'support@example.com',
            'privacy_policy_text' => "# Privacidade\n\n<img src=x onerror=alert(1)>\n\n[clique](javascript:alert(1))",
            'terms_conditions_text' => "# Termos\n\n<script>alert(1)</script>\n\n[clique](javascript:alert(1))",
        ]);

        $this->get(route('website.privacy'))
            ->assertOk()
            ->assertDontSee('onerror', false)
            ->assertDontSee('javascript:alert', false);

        $this->get(route('website.terms'))
            ->assertOk()
            ->assertDontSee('<script>alert(1)</script>', false)
            ->assertDontSee('javascript:alert', false);
    }

    public function test_invalid_payment_callback_logs_only_redacted_allowlisted_payload_fields(): void
    {
        Log::shouldReceive('warning')
            ->once()
            ->withArgs(function (string $message, array $context): bool {
                return $message === 'IfThenPay callback rejected'
                    && ($context['payload']['key'] ?? null) === '[redacted]'
                    && ($context['payload']['orderId'] ?? null) === '999'
                    && ! array_key_exists('password', $context['payload'])
                    && ! array_key_exists('token', $context['payload']);
            });

        $this->getJson(route('payment.callback', [
            'key' => 'wrong-secret',
            'orderId' => '999',
            'amount' => '10.00',
            'requestId' => 'missing',
            'password' => 'must-not-be-logged',
            'token' => 'must-not-be-logged',
        ]))->assertStatus(400);
    }

    public function test_preview_products_cannot_be_added_to_cart_by_direct_post(): void
    {
        $user = User::factory()->create();
        $category = Category::create([
            'slug' => 'legumes',
            'name' => 'Legumes',
            'is_active' => true,
        ]);
        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'produto-preview',
            'name' => 'Produto Preview',
            'price' => 3.50,
            'stock' => 10,
            'is_active' => true,
            'is_preview' => true,
        ]);

        $this->actingAs($user)
            ->post(route('cart.add', ['product' => $product->id]), ['quantity' => 1])
            ->assertNotFound();

        $this->assertDatabaseMissing('cart_items', [
            'product_id' => $product->id,
        ]);
    }

    public function test_products_without_fulfilment_method_cannot_be_added_to_cart(): void
    {
        $category = Category::create([
            'slug' => 'sem-entrega',
            'name' => 'Sem entrega',
            'is_active' => true,
        ]);
        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'produto-sem-entrega',
            'name' => 'Produto Sem Entrega',
            'price' => 3.50,
            'stock' => 10,
            'is_active' => true,
            'allow_shipping' => false,
            'allow_pickup' => false,
        ]);

        $this->post(route('cart.add', ['product' => $product->id]), ['quantity' => 1])
            ->assertRedirect()
            ->assertSessionHas('error');

        $this->assertDatabaseMissing('cart_items', [
            'product_id' => $product->id,
        ]);
    }

    public function test_register_after_checkout_redirects_back_to_checkout(): void
    {
        $this->get(route('shop.register', ['next' => parse_url(route('checkout'), PHP_URL_PATH)]));

        $this->post(route('shop.register'), [
            'name' => 'Cliente',
            'email' => 'cliente-checkout@example.com',
            'password' => 'password123',
            'password_confirmation' => 'password123',
        ])->assertRedirect(parse_url(route('checkout'), PHP_URL_PATH));
    }

    public function test_cart_page_exposes_checkout_call_to_action(): void
    {
        $user = User::factory()->create();
        $category = Category::create([
            'slug' => 'fruta',
            'name' => 'Fruta',
            'is_active' => true,
        ]);
        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'maca',
            'name' => 'Maçã',
            'price' => 1.25,
            'stock' => 5,
            'is_active' => true,
        ]);
        $cart = Cart::create(['user_id' => $user->id]);
        $cart->items()->create([
            'product_id' => $product->id,
            'quantity' => 2,
            'reserved_quantity' => 0,
        ]);

        $this->actingAs($user)
            ->get(route('cart.detail'))
            ->assertOk()
            ->assertSee('Finalizar compra')
            ->assertSee(route('checkout'), false);
    }

    public function test_checkout_payment_bootstrap_failure_cancels_order_and_restores_stock(): void
    {
        $this->app->instance(PaymentService::class, new class extends PaymentService
        {
            public function methodIsConfigured(string $method): bool
            {
                return true;
            }

            public function createPayment(Order $order, string $method): Payment
            {
                throw new \Error('payment database failure');
            }
        });

        $user = User::factory()->create();
        $category = Category::create([
            'slug' => 'legumes',
            'name' => 'Legumes',
            'is_active' => true,
        ]);
        $location = Location::create([
            'name' => 'Quinta',
            'is_active' => true,
        ]);
        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'couve',
            'name' => 'Couve',
            'price' => 2.50,
            'stock' => 5,
            'is_active' => true,
        ]);
        $cart = Cart::create(['user_id' => $user->id]);
        $cart->items()->create([
            'product_id' => $product->id,
            'quantity' => 2,
            'reserved_quantity' => 0,
        ]);

        $this->actingAs($user)
            ->post(route('checkout.store'), [
                'name' => 'Cliente Teste',
                'email' => 'cliente@example.com',
                'phone' => '912345678',
                'payment_method' => 'mbway',
                'fulfillment_method' => 'pickup',
                'pickup_location' => $location->id,
            ])
            ->assertRedirect();

        $order = Order::firstOrFail();

        $this->assertSame(Order::STATUS_CANCELLED, $order->status);
        $this->assertSame(Order::PAYMENT_CANCELLED, $order->payment_state);
        $this->assertSame(5, $product->refresh()->stock);
        $this->assertDatabaseHas('cart_items', [
            'product_id' => $product->id,
            'quantity' => 2,
            'reserved_quantity' => 0,
        ]);
    }
}
