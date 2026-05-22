<?php

namespace App\Filament\Resources\WebsiteContentResource\Pages;

use App\Filament\Resources\WebsiteContentResource;
use App\Models\WebsiteContent;
use Filament\Resources\Pages\EditRecord;

class ManageWebsiteContent extends EditRecord
{
    protected static string $resource = WebsiteContentResource::class;

    protected function getHeaderActions(): array
    {
        return [];
    }

    public function getRecord(): WebsiteContent
    {
        return WebsiteContent::firstOrCreate(['id' => 1]);
    }

    public function getTitle(): string
    {
        return 'Website Content';
    }
}
