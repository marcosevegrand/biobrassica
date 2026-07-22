<?php

namespace App\Filament\Resources\ProductResource\Pages;

use App\Filament\Resources\ProductResource;
use Filament\Actions;
use Filament\Resources\Pages\EditRecord;

class EditProduct extends EditRecord
{
    protected static string $resource = ProductResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\DeleteAction::make(),
        ];
    }

    protected function mutateFormDataBeforeSave(array $data): array
    {
        $data = static::getResource()::mapVisibilityToBooleans($data);
        $data = static::getResource()::mapDeliveryToBooleans($data);

        unset($data['visibility'], $data['delivery']);

        return $data;
    }
}
