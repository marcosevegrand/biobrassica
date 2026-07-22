<?php

use App\Http\Kernel;
use App\Http\Middleware\LocaleMiddleware;
use App\Http\Middleware\SubdomainMiddleware;
use Illuminate\Contracts\Console\Kernel as ConsoleKernel;
use Illuminate\Contracts\Http\Kernel as HttpKernel;
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| Bootstrap The Application
|--------------------------------------------------------------------------
|
| This is the normal Laravel 11 builder flow. The only cPanel-specific piece
| is loading .env manually and using tiny kernels that skip Laravel's Dotenv
| file reader, which is blocked on this host.
|
*/

require __DIR__.'/env.php';

$app = Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        using: function (): void {
            require base_path('routes/health.php');

            $shopPath = trim((string) config('biobrassica.paths.shop', 'loja'), '/');

            Route::middleware('web')
                ->prefix($shopPath)
                ->group(base_path('routes/web.php'));

            Route::middleware('web')
                ->prefix($shopPath)
                ->group(base_path('routes/shop.php'));

            Route::middleware('web')
                ->group(base_path('routes/website.php'));
        },
        commands: __DIR__.'/../routes/console.php',
    )
    ->withMiddleware(function (Middleware $middleware): void {
        $middleware->web(append: [
            SubdomainMiddleware::class,
            LocaleMiddleware::class,
        ]);
    })
    ->withExceptions(function (Exceptions $exceptions): void {
        // Keep Laravel's default exception handling.
    })
    ->create();

$app->singleton(HttpKernel::class, Kernel::class);
$app->singleton(ConsoleKernel::class, App\Console\Kernel::class);

return $app;
