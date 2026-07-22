<?php

namespace App\Filament\Pages;

use Filament\Pages\Page;
use Illuminate\Support\Facades\Artisan;

class SeedCatalog extends Page
{
    protected static ?string $navigationIcon = 'heroicon-o-rocket-launch';

    protected static ?string $navigationGroup = 'Configuração';

    protected static ?string $navigationLabel = 'Sear dados do catálogo';

    protected static ?string $title = 'Sear dados do catálogo';

    protected static ?string $slug = 'seed-catalog';

    protected static string $view = 'filament.pages.seed-catalog';

    public function seed(): void
    {
        Artisan::call('db:seed', ['--class' => 'BiobrassicaContentSeeder', '--force' => true]);

        $this->dispatch('seed-completed');
    }
}
