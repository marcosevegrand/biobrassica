<?php

namespace App\Filament\Resources\ShopSettingsResource\Pages;

use App\Filament\Resources\ShopSettingsResource;
use App\Models\ShopSettings;
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
        $settings = ShopSettings::current();

        return $settings->toArray();
    }

    public function getRecord(): ShopSettings
    {
        return ShopSettings::current();
    }

    public function getTitle(): string
    {
        return 'Definições da loja';
    }
}
