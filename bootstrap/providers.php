<?php

return [
    // Core providers that may not be auto-discovered on shared hosting
    Illuminate\View\ViewServiceProvider::class,

    // Application providers
    App\Providers\AppServiceProvider::class,
    App\Providers\Filament\AdminPanelProvider::class,
];
