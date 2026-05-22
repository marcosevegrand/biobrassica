<?php

namespace App\Filament\Resources\DeliveryMethodResource\Pages;

use App\Filament\Resources\DeliveryMethodResource;
use Filament\Actions;
use Filament\Resources\Pages\ListRecords;

class ListDeliveryMethods extends ListRecords
{
    protected static string $resource = DeliveryMethodResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\CreateAction::make(),
        ];
    }
}
