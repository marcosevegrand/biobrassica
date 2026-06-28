<?php

namespace App\Filament\Resources\WebsiteContentResource\Pages;

use App\Filament\Resources\WebsiteContentResource;
use App\Models\WebsiteContent;
use Filament\Resources\Pages\EditRecord;

class ManageWebsiteContent extends EditRecord
{
    protected static string $resource = WebsiteContentResource::class;

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

    public function getRecord(): WebsiteContent
    {
        return WebsiteContent::current();
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
        return 'Conteúdo do website';
    }
}
