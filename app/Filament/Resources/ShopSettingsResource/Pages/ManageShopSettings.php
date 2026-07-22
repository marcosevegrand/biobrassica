<?php

namespace App\Filament\Resources\ShopSettingsResource\Pages;

use App\Filament\Resources\ShopSettingsResource;
use App\Models\ShopSettings;
use Filament\Resources\Pages\EditRecord;

class ManageShopSettings extends EditRecord
{
    protected static string $resource = ShopSettingsResource::class;

    public function mount(int|string $record = ''): void
    {
        $this->record = $this->getRecord();

        $this->authorizeAccess();
        $this->fillForm();
    }

    protected function getHeaderActions(): array
    {
        return [];
    }

    protected function mutateFormDataBeforeFill(array $data): array
    {
        $settings = ShopSettings::current();

        return $settings->toArray();
    }

    protected function mutateFormDataBeforeSave(array $data): array
    {
        $data = static::getResource()::mapShopModeToBooleans($data);

        unset($data['shop_mode']);

        return $data;
    }

    public function getRecord(): ShopSettings
    {
        return ShopSettings::current();
    }

    protected function getRedirectUrl(): ?string
    {
        return static::getResource()::getUrl('index');
    }

    public static function shouldRegisterNavigation(array $parameters = []): bool
    {
        return true;
    }

    public function getTitle(): string
    {
        return 'Definições da loja';
    }
}
