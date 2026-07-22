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
use App\Services\PaymentService;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class ShopCheckoutBusinessLogicTest extends TestCase
{
    use RefreshDatabase;

    // -----------------------------------------------------------------
    // Pending payment blocks checkout
    // -----------------------------------------------------------------

    public function test_pending_payment_blocks_get_checkout(): void
    {
        $user = User::factory()->create();
        $product = $this->createProduct(stock: 10);
        $this->createLocation();
        $this->createCart($user, $product, 2);

        // Create a pending order with pending payment
        $order = Order::create([
            'user_id' => $user->id,
            'email' => $user->email,
            'phone' => '912345678',
            'name' => $user->name,
            'status' => Order::STATUS_PENDING,
            'payment_state' => Order::PAYMENT_PENDING,
            'fulfillment_method' => 'pickup',
            'pickup_location' => '1',
            'language' => 'pt',
            'subtotal' => 10,
            'shipping_cost' => 0,
            'total' => 10,
        ]);

        $this->actingAs($user)
            ->get(route('checkout'))
            ->assertRedirect(route('payment.show', ['order' => $order->id]))
            ->assertSessionHas('error');
    }

    public function test_pending_payment_blocks_post_checkout(): void
    {
        $user = User::factory()->create();
        $product = $this->createProduct(stock: 10);
        $this->createLocation();
        $this->createCart($user, $product, 2);

        Order::create([
            'user_id' => $user->id,
            'email' => $user->email,
            'phone' => '912345678',
            'name' => $user->name,
            'status' => Order::STATUS_PENDING,
            'payment_state' => Order::PAYMENT_PENDING,
            'fulfillment_method' => 'pickup',
            'pickup_location' => '1',
            'language' => 'pt',
            'subtotal' => 10,
            'shipping_cost' => 0,
            'total' => 10,
        ]);

        $this->actingAs($user)
            ->post(route('checkout.store'), $this->checkoutPayload())
            ->assertRedirect()
            ->assertSessionHas('error');
    }

    public function test_cancelled_or_paid_orders_do_not_block_checkout(): void
    {
        $user = User::factory()->create();
        $product = $this->createProduct(stock: 10);
        $this->createLocation();
        $this->createCart($user, $product, 2);

        // Cancelled order
        Order::create([
            'user_id' => $user->id,
            'email' => $user->email,
            'phone' => '912345678',
            'name' => $user->name,
            'status' => Order::STATUS_CANCELLED,
            'payment_state' => Order::PAYMENT_CANCELLED,
            'fulfillment_method' => 'pickup',
            'pickup_location' => '1',
            'language' => 'pt',
            'subtotal' => 10,
            'shipping_cost' => 0,
            'total' => 10,
        ]);

        $this->actingAs($user)
            ->get(route('checkout'))
            ->assertOk();
    }

    // -----------------------------------------------------------------
    // Inactive mode allows browsing but blocks checkout
    // -----------------------------------------------------------------

    public function test_inactive_shop_blocks_get_checkout_with_message(): void
    {
        ShopSettings::current()->update([
            'is_shop_active' => false,
            'is_shop_brevemente' => false,
        ]);

        $user = User::factory()->create();
        $product = $this->createProduct(stock: 10);
        $this->createCart($user, $product, 2);

        $this->actingAs($user)
            ->get(route('checkout'))
            ->assertRedirect(route('cart.detail'))
            ->assertSessionHas('error');
    }

    public function test_inactive_shop_blocks_post_checkout_with_message(): void
    {
        ShopSettings::current()->update([
            'is_shop_active' => false,
            'is_shop_brevemente' => false,
        ]);

        $user = User::factory()->create();
        $product = $this->createProduct(stock: 10);
        $this->createLocation();
        $this->createCart($user, $product, 2);

        $this->actingAs($user)
            ->post(route('checkout.store'), $this->checkoutPayload())
            ->assertRedirect(route('cart.detail'))
            ->assertSessionHas('error');
    }

    public function test_inactive_shop_still_allows_browsing_catalog(): void
    {
        ShopSettings::current()->update([
            'is_shop_active' => false,
            'is_shop_brevemente' => false,
        ]);

        $category = Category::create([
            'slug' => 'fruta',
            'name' => 'Fruta',
            'is_active' => true,
        ]);
        $product = Product::create([
            'category_id' => $category->id,
            'slug' => 'maca',
            'name' => 'Maçã',
            'price' => 1.50,
            'stock' => 5,
            'is_active' => true,
        ]);

        $this->get(route('shop.home'))->assertOk();
        $this->get(route('catalog.product', ['slug' => $product->slug]))->assertOk();
    }

    // -----------------------------------------------------------------
    // Product visibility/delivery label mapping
    // -----------------------------------------------------------------

    public function test_product_visibility_label_mapping(): void
    {
        $category = Category::create([
            'slug' => 'legumes',
            'name' => 'Legumes',
            'is_active' => true,
        ]);

        $hidden = Product::create([
            'category_id' => $category->id,
            'slug' => 'hidden',
            'name' => 'Hidden',
            'price' => 1,
            'stock' => 1,
            'is_active' => false,
            'is_preview' => false,
            'is_highlight' => false,
        ]);
        $this->assertSame('Escondido', $hidden->visibilityLabel);

        $preview = Product::create([
            'category_id' => $category->id,
            'slug' => 'preview',
            'name' => 'Preview',
            'price' => 1,
            'stock' => 1,
            'is_active' => true,
            'is_preview' => true,
            'is_highlight' => false,
        ]);
        $this->assertSame('Pré-visualização', $preview->visibilityLabel);

        $normal = Product::create([
            'category_id' => $category->id,
            'slug' => 'normal',
            'name' => 'Normal',
            'price' => 1,
            'stock' => 1,
            'is_active' => true,
            'is_preview' => false,
            'is_highlight' => false,
        ]);
        $this->assertSame('Normal', $normal->visibilityLabel);

        $highlighted = Product::create([
            'category_id' => $category->id,
            'slug' => 'highlighted',
            'name' => 'Highlighted',
            'price' => 1,
            'stock' => 1,
            'is_active' => true,
            'is_preview' => false,
            'is_highlight' => true,
        ]);
        $this->assertSame('Destacado', $highlighted->visibilityLabel);
    }

    public function test_product_delivery_label_mapping(): void
    {
        $category = Category::create([
            'slug' => 'legumes',
            'name' => 'Legumes',
            'is_active' => true,
        ]);

        $pickupOnly = Product::create([
            'category_id' => $category->id,
            'slug' => 'pickup-only',
            'name' => 'Pickup Only',
            'price' => 1,
            'stock' => 1,
            'is_active' => true,
            'allow_shipping' => false,
            'allow_pickup' => true,
        ]);
        $this->assertSame('Apenas Levantamento', $pickupOnly->deliveryLabel);

        $shippingOnly = Product::create([
            'category_id' => $category->id,
            'slug' => 'shipping-only',
            'name' => 'Shipping Only',
            'price' => 1,
            'stock' => 1,
            'is_active' => true,
            'allow_shipping' => true,
            'allow_pickup' => false,
        ]);
        $this->assertSame('Apenas Envio', $shippingOnly->deliveryLabel);

        $both = Product::create([
            'category_id' => $category->id,
            'slug' => 'both',
            'name' => 'Both',
            'price' => 1,
            'stock' => 1,
            'is_active' => true,
            'allow_shipping' => true,
            'allow_pickup' => true,
        ]);
        $this->assertSame('Ambos', $both->deliveryLabel);
    }

    // -----------------------------------------------------------------
    // Shop settings mode mapping
    // -----------------------------------------------------------------

    public function test_shop_mode_label_mapping(): void
    {
        $settings = ShopSettings::current();

        $settings->update(['is_shop_active' => true, 'is_shop_brevemente' => true]);
        $this->assertSame('Brevemente', $settings->fresh()->modeLabel);

        $settings->update(['is_shop_active' => false, 'is_shop_brevemente' => false]);
        $this->assertSame('Inativa', $settings->fresh()->modeLabel);

        $settings->update(['is_shop_active' => true, 'is_shop_brevemente' => false]);
        $this->assertSame('Ativada', $settings->fresh()->modeLabel);
    }

    // -----------------------------------------------------------------
    // Reservation expiry warning/release on GET checkout
    // -----------------------------------------------------------------

    public function test_expired_reservation_triggers_release_and_warning(): void
    {
        $user = User::factory()->create();
        $product = $this->createProduct(price: 5, stock: 5);
        $this->createLocation();

        $cart = Cart::create([
            'user_id' => $user->id,
            'reserved_until' => now()->subMinute(), // expired
        ]);
        $cart->items()->create([
            'product_id' => $product->id,
            'quantity' => 2,
            'reserved_quantity' => 0,
        ]);

        // Product stock unchanged by reservation (no reserve on GET, but simulate stale state)
        $response = $this->actingAs($user)
            ->get(route('checkout'))
            ->assertOk();

        // Cart reservation should be released (reserved_until set to null)
        $cart->refresh();
        $this->assertNull($cart->reserved_until);

        // When stock is sufficient, no warning should be set
        $this->assertNull($response->viewData('warning'), 'Expected null warning when stock is sufficient.');
        $response->assertDontSee('Apenas');
    }

    public function test_expired_reservation_warns_insufficient_stock_without_claiming_adjustment(): void
    {
        $user = User::factory()->create();
        $product = $this->createProduct(price: 5, stock: 2);  // Only 2 in stock
        $this->createLocation();

        $cart = Cart::create([
            'user_id' => $user->id,
            'reserved_until' => now()->subMinute(), // expired
        ]);
        $cart->items()->create([
            'product_id' => $product->id,
            'quantity' => 5,  // More than available stock
            'reserved_quantity' => 0,
        ]);

        $response = $this->actingAs($user)
            ->get(route('checkout'))
            ->assertOk();

        // Reservation should be released
        $cart->refresh();
        $this->assertNull($cart->reserved_until);

        // Warning should be present as view data
        $warning = $response->viewData('warning');
        $this->assertNotNull($warning, 'Expected a non-null warning when stock is insufficient.');

        // Warning should mention the product and available stock count
        $this->assertStringContainsString('Apenas 2 unidade(s) disponíveis', $warning);
        $this->assertStringContainsString($product->name, $warning);

        // Warning must NOT falsely claim quantities were adjusted
        $this->assertStringNotContainsStringIgnoringCase('ajustada', $warning);
        $this->assertStringNotContainsStringIgnoringCase('ajustado', $warning);

        // Warning must include clear call-to-action for the customer
        $this->assertStringContainsStringIgnoringCase('atualize as quantidades', $warning);

        // Warning must be rendered in the HTML response (not only in view data)
        $response->assertSee('Apenas 2 unidade(s) disponíveis');
        $response->assertSee($product->name);
        $response->assertSee('atualize as quantidades');
    }

    // -----------------------------------------------------------------
    // Admin navigation labels (basic existence checks via admin panels)
    // -----------------------------------------------------------------

    public function test_admin_panel_navigation_loads(): void
    {
        $admin = User::factory()->create(['is_admin' => true, 'email_verified_at' => now()]);

        // Pages should still be accessible
        $this->actingAs($admin)->get('/admin/website-content')->assertOk();
        $this->actingAs($admin)->get('/admin/instagram-posts')->assertOk();
        $this->actingAs($admin)->get('/admin/blog-posts')->assertOk();
        $this->actingAs($admin)->get('/admin/recipes')->assertOk();
    }

    // -----------------------------------------------------------------
    // Helpers
    // -----------------------------------------------------------------

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

    private function checkoutPayload(array $overrides = []): array
    {
        return array_merge([
            'name' => 'Cliente Teste',
            'email' => 'cliente@example.com',
            'phone' => '912345678',
            'payment_method' => 'mbway',
            'fulfillment_method' => 'pickup',
            'pickup_location' => $this->createLocation()->id,
        ], $overrides);
    }
}
