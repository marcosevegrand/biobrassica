<?php

namespace App\Filament\Resources\ProductResource\Pages;

use App\Filament\Resources\ProductResource;
use Filament\Resources\Pages\CreateRecord;

class CreateProduct extends CreateRecord
{
    protected static string $resource = ProductResource::class;

    protected function mutateFormDataBeforeCreate(array $data): array
    {
        $data = static::getResource()::mapVisibilityToBooleans($data);
        $data = static::getResource()::mapDeliveryToBooleans($data);

        unset($data['visibility'], $data['delivery']);

        return $data;
    }
}
