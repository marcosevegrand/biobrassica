<?php

namespace App\Filament\Resources\InstagramPostResource\Pages;

use App\Filament\Resources\InstagramPostResource;
use Filament\Actions;
use Filament\Resources\Pages\EditRecord;

class EditInstagramPost extends EditRecord
{
    protected static string $resource = InstagramPostResource::class;

    protected function getHeaderActions(): array
    {
        return [
            Actions\DeleteAction::make(),
        ];
    }
}
