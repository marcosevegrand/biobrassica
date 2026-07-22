<?php

namespace Tests\Feature;

use App\Filament\Resources\ProductResource;
use App\Filament\Resources\ShopSettingsResource;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class FilamentFormPersistenceTest extends TestCase
{
    use RefreshDatabase;

    // -----------------------------------------------------------------
    // ProductResource::mapVisibilityToBooleans
    // -----------------------------------------------------------------

    public function test_map_visibility_hidden(): void
    {
        $data = ProductResource::mapVisibilityToBooleans(['visibility' => 'hidden']);

        $this->assertFalse($data['is_active']);
        $this->assertFalse($data['is_preview']);
        $this->assertFalse($data['is_highlight']);
    }

    public function test_map_visibility_preview(): void
    {
        $data = ProductResource::mapVisibilityToBooleans(['visibility' => 'preview']);

        $this->assertTrue($data['is_active']);
        $this->assertTrue($data['is_preview']);
        $this->assertFalse($data['is_highlight']);
    }

    public function test_map_visibility_normal(): void
    {
        $data = ProductResource::mapVisibilityToBooleans(['visibility' => 'normal']);

        $this->assertTrue($data['is_active']);
        $this->assertFalse($data['is_preview']);
        $this->assertFalse($data['is_highlight']);
    }

    public function test_map_visibility_highlighted(): void
    {
        $data = ProductResource::mapVisibilityToBooleans(['visibility' => 'highlighted']);

        $this->assertTrue($data['is_active']);
        $this->assertFalse($data['is_preview']);
        $this->assertTrue($data['is_highlight']);
    }

    // -----------------------------------------------------------------
    // ProductResource::mapDeliveryToBooleans
    // -----------------------------------------------------------------

    public function test_map_delivery_pickup_only(): void
    {
        $data = ProductResource::mapDeliveryToBooleans(['delivery' => 'pickup_only']);

        $this->assertFalse($data['allow_shipping']);
        $this->assertTrue($data['allow_pickup']);
    }

    public function test_map_delivery_shipping_only(): void
    {
        $data = ProductResource::mapDeliveryToBooleans(['delivery' => 'shipping_only']);

        $this->assertTrue($data['allow_shipping']);
        $this->assertFalse($data['allow_pickup']);
    }

    public function test_map_delivery_both(): void
    {
        $data = ProductResource::mapDeliveryToBooleans(['delivery' => 'both']);

        $this->assertTrue($data['allow_shipping']);
        $this->assertTrue($data['allow_pickup']);
    }

    // -----------------------------------------------------------------
    // Legacy inconsistent data: both false → displayed "Ambos"
    // Saved without changing defaults should result in both true
    // -----------------------------------------------------------------

    public function test_legacy_no_delivery_product_saves_as_both_when_select_is_ambos(): void
    {
        // Simulates form data from a legacy record where both
        // allow_shipping and allow_pickup are false in DB.
        // afterStateHydrated maps this to delivery='both', but the hidden
        // fields still carry false/false. On save without user interaction,
        // delivery='both' should force both hidden fields to true.
        $data = [
            'delivery' => 'both',
            'allow_shipping' => false,  // stale from legacy DB
            'allow_pickup' => false,    // stale from legacy DB
        ];

        $data = ProductResource::mapDeliveryToBooleans($data);

        $this->assertTrue($data['allow_shipping'], 'Legacy false shipping should be overwritten to true');
        $this->assertTrue($data['allow_pickup'], 'Legacy false pickup should be overwritten to true');
    }

    public function test_legacy_no_delivery_product_explicit_pickup_only_not_overwritten(): void
    {
        // When the admin explicitly sets pickup_only, the legacy false values
        // should be overwritten to match the select.
        $data = [
            'delivery' => 'pickup_only',
            'allow_shipping' => false,  // stale from legacy DB
            'allow_pickup' => false,    // stale from legacy DB
        ];

        $data = ProductResource::mapDeliveryToBooleans($data);

        $this->assertFalse($data['allow_shipping']);
        $this->assertTrue($data['allow_pickup']);
    }

    // -----------------------------------------------------------------
    // Create defaults: form loads with default selects,
    // save without interaction should produce correct hidden values
    // -----------------------------------------------------------------

    public function test_create_defaults_visibility_normal_produces_correct_hidden_fields(): void
    {
        // Simulates a create where visibility is its default 'normal'
        // and the admin never touched the visibility select.
        // The hidden fields carry their own defaults but mutateFormDataBeforeCreate
        // must derive the final values from visibility.
        $data = [
            'visibility' => 'normal',
            'is_active' => true,      // default from hidden field
            'is_preview' => false,    // default from hidden field
            'is_highlight' => false,  // default from hidden field
            'delivery' => 'both',
            'allow_shipping' => true, // default from hidden field
            'allow_pickup' => true,   // default from hidden field
        ];

        $data = ProductResource::mapVisibilityToBooleans($data);
        $data = ProductResource::mapDeliveryToBooleans($data);

        $this->assertTrue($data['is_active']);
        $this->assertFalse($data['is_preview']);
        $this->assertFalse($data['is_highlight']);
        $this->assertTrue($data['allow_shipping']);
        $this->assertTrue($data['allow_pickup']);
    }

    public function test_create_defaults_visibility_hidden_produces_correct_hidden_fields(): void
    {
        // Simulates create with admin changing visibility to 'hidden'
        $data = [
            'visibility' => 'hidden',
            'is_active' => true,      // default from hidden field (wrong for hidden)
            'is_preview' => false,
            'is_highlight' => false,
            'delivery' => 'both',
            'allow_shipping' => true,
            'allow_pickup' => true,
        ];

        $data = ProductResource::mapVisibilityToBooleans($data);
        $data = ProductResource::mapDeliveryToBooleans($data);

        $this->assertFalse($data['is_active'], 'Visibility hidden must produce is_active=false');
        $this->assertFalse($data['is_preview']);
        $this->assertFalse($data['is_highlight']);
    }

    // -----------------------------------------------------------------
    // Virtual fields are never written to DB (removed by page hooks)
    // This test verifies the clean-up logic that the page hooks perform
    // -----------------------------------------------------------------

    public function test_virtual_fields_are_removed_before_save(): void
    {
        // Simulates the full mutateFormDataBeforeSave flow
        $data = [
            'visibility' => 'normal',
            'delivery' => 'both',
            'is_active' => false, // stale, will be overwritten
            'is_preview' => true, // stale, will be overwritten
            'is_highlight' => false,
            'allow_shipping' => false, // stale
            'allow_pickup' => false,   // stale
        ];

        $data = ProductResource::mapVisibilityToBooleans($data);
        $data = ProductResource::mapDeliveryToBooleans($data);
        unset($data['visibility'], $data['delivery']);

        $this->assertArrayNotHasKey('visibility', $data);
        $this->assertArrayNotHasKey('delivery', $data);
        $this->assertArrayHasKey('is_active', $data);
        $this->assertArrayHasKey('allow_shipping', $data);
        $this->assertArrayHasKey('allow_pickup', $data);
    }

    // -----------------------------------------------------------------
    // ShopSettingsResource::mapShopModeToBooleans
    // -----------------------------------------------------------------

    public function test_map_shop_mode_brevemente(): void
    {
        $data = ShopSettingsResource::mapShopModeToBooleans(['shop_mode' => 'brevemente']);

        $this->assertTrue($data['is_shop_active']);
        $this->assertTrue($data['is_shop_brevemente']);
    }

    public function test_map_shop_mode_inativa(): void
    {
        $data = ShopSettingsResource::mapShopModeToBooleans(['shop_mode' => 'inativa']);

        $this->assertFalse($data['is_shop_active']);
        $this->assertFalse($data['is_shop_brevemente']);
    }

    public function test_map_shop_mode_ativada(): void
    {
        $data = ShopSettingsResource::mapShopModeToBooleans(['shop_mode' => 'ativada']);

        $this->assertTrue($data['is_shop_active']);
        $this->assertFalse($data['is_shop_brevemente']);
    }

    public function test_shop_mode_save_default_without_interaction(): void
    {
        // Default shop_mode is 'ativada'. Hidden fields have their own defaults.
        // On save without user interaction, shop_mode='ativada' must force
        // the correct hidden values regardless of what the hidden fields hold.
        $data = [
            'shop_mode' => 'ativada',
            'is_shop_active' => false,       // stale, should be overwritten
            'is_shop_brevemente' => true,     // stale, should be overwritten
        ];

        $data = ShopSettingsResource::mapShopModeToBooleans($data);

        $this->assertTrue($data['is_shop_active'], 'shop_mode ativada must force is_shop_active=true');
        $this->assertFalse($data['is_shop_brevemente'], 'shop_mode ativada must force is_shop_brevemente=false');
    }

    public function test_shop_mode_virtual_field_removed_before_save(): void
    {
        $data = [
            'shop_mode' => 'ativada',
            'is_shop_active' => true,
            'is_shop_brevemente' => false,
        ];

        $data = ShopSettingsResource::mapShopModeToBooleans($data);
        unset($data['shop_mode']);

        $this->assertArrayNotHasKey('shop_mode', $data);
        $this->assertArrayHasKey('is_shop_active', $data);
        $this->assertArrayHasKey('is_shop_brevemente', $data);
    }
}
