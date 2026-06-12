<?php

/*
|--------------------------------------------------------------------------
| Create & Boot The Application
|--------------------------------------------------------------------------
|
| Uses a proven manual boot sequence that works on this cPanel host.
| The standard builder pattern fails because open_basedir prevents
| Dotenv from discovering .env, which blocks the normal boot chain.
|
| This file replaces Application::configure()->create() with the
| exact step-by-step sequence confirmed working via diagnostics.
|
*/

// .env is already loaded by bootstrap/env.php (required below)
require __DIR__ . '/env.php';

$basePath = dirname(__DIR__);

// 1. Create Application
$app = new \Illuminate\Foundation\Application($basePath);

// 2. LoadConfiguration bootstrapper — binds 'config'
(new \Illuminate\Foundation\Bootstrap\LoadConfiguration)->bootstrap($app);

// 3. RegisterProviders bootstrapper — loads core + package providers
(new \Illuminate\Foundation\Bootstrap\RegisterProviders)->bootstrap($app);

// 4. Enable facades
\Illuminate\Support\Facades\Facade::setFacadeApplication($app);

// 5. Bind HTTP/Console kernels
$app->singleton(
    \Illuminate\Contracts\Http\Kernel::class,
    \Illuminate\Foundation\Http\Kernel::class
);
$app->singleton(
    \Illuminate\Contracts\Console\Kernel::class,
    \Illuminate\Foundation\Console\Kernel::class
);

// 6. Set up routes
require $app->basePath('routes/health.php');

use Illuminate\Support\Facades\Route;
$shopPath = trim((string) env('SHOP_PATH', 'loja'), '/');

Route::middleware('web')
    ->prefix($shopPath)
    ->group($app->basePath('routes/web.php'));

Route::middleware('web')
    ->prefix($shopPath)
    ->group($app->basePath('routes/shop.php'));

Route::middleware('web')
    ->group($app->basePath('routes/website.php'));

// 7. Register custom middleware
$app->make('router')->pushMiddlewareToGroup('web', [
    \App\Http\Middleware\SubdomainMiddleware::class,
    \App\Http\Middleware\ShopBrevementeMiddleware::class,
]);

// 8. Boot all service providers
$app->boot();

return $app;
