<?php

namespace App\Filament\Resources\ShopSettingsResource\Pages;

use App\Filament\Resources\ShopSettingsResource;
use App\Models\ShopSettings;
use Filament\Actions;
use Filament\Resources\Pages\EditRecord;

class ManageShopSettings extends EditRecord
{
    protected static string $resource = ShopSettingsResource::class;

    protected function getHeaderActions(): array
    {
        return [];
    }

    protected function mutateFormDataBeforeFill(array $data): array
    {
        $settings = ShopSettings::firstOrCreate([
            'id' => 1,
        ], [
            'is_shop_active' => true,
            'is_shop_brevemente' => false,
            'min_order_total' => 0,
            'mbway_enabled' => true,
            'bank_transfer_enabled' => true,
            'payment_timeout_minutes' => 30,
            'checkout_reservation_minutes' => 15,
        ]);

        return $settings->toArray();
    }

    public function getRecord(): ShopSettings
    {
        return ShopSettings::firstOrCreate([
            'id' => 1,
        ], [
            'is_shop_active' => true,
            'is_shop_brevemente' => false,
            'min_order_total' => 0,
            'mbway_enabled' => true,
            'bank_transfer_enabled' => true,
            'payment_timeout_minutes' => 30,
            'checkout_reservation_minutes' => 15,
        ]);
    }

    public function getTitle(): string
    {
        return 'Shop Settings';
    }
}
