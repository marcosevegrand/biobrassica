<?php

namespace Tests\Feature;

use App\Filament\Resources\ProductResource;
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

}
