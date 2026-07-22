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
        $this->assertFalse($data['is_highlight']);
    }

    public function test_map_visibility_normal(): void
    {
        $data = ProductResource::mapVisibilityToBooleans(['visibility' => 'normal']);

        $this->assertTrue($data['is_active']);
        $this->assertFalse($data['is_highlight']);
    }

    public function test_map_visibility_highlighted(): void
    {
        $data = ProductResource::mapVisibilityToBooleans(['visibility' => 'highlighted']);

        $this->assertTrue($data['is_active']);
        $this->assertTrue($data['is_highlight']);
    }

    // -----------------------------------------------------------------
    // Virtual fields are never written to DB (removed by page hooks)
    // -----------------------------------------------------------------

    public function test_virtual_fields_are_removed_before_save(): void
    {
        $data = [
            'visibility' => 'normal',
            'is_active' => false, // stale, will be overwritten
            'is_highlight' => false,
        ];

        $data = ProductResource::mapVisibilityToBooleans($data);
        unset($data['visibility']);

        $this->assertArrayNotHasKey('visibility', $data);
        $this->assertArrayHasKey('is_active', $data);
        $this->assertArrayHasKey('is_highlight', $data);
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
