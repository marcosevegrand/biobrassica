<?php

namespace App\Filament\Resources\InstagramPostResource\Pages;

use App\Filament\Resources\InstagramPostResource;
use Filament\Actions;
use Filament\Resources\Pages\ListRecords;

class ListInstagramPosts extends ListRecords
{
    protected static string $resource = InstagramPostResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\CreateAction::make(),
        ];
    }
}
