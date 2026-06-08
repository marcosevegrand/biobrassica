<?php

use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;
use Illuminate\Support\Facades\Route;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        commands: __DIR__.'/../routes/console.php',
        then: function () {
            require base_path('routes/health.php');

            Route::middleware('web')->group(base_path('routes/web.php'));

            $domains = config('biobrassica.domains');

            Route::middleware('web')
                ->domain($domains['shop'])
                ->group(base_path('routes/shop.php'));

            Route::middleware('web')
                ->domain($domains['admin'])
                ->group(base_path('routes/admin.php'));

            Route::middleware('web')
                ->domain($domains['website'])
                ->group(base_path('routes/website.php'));

            if (app()->environment(['local', 'testing'])) {
                Route::middleware('web')->group(base_path('routes/website.php'));
            }
        },
    )
    ->withMiddleware(function (Middleware $middleware) {
        $middleware->web(append: [
            \App\Http\Middleware\SubdomainMiddleware::class,
            \App\Http\Middleware\ShopBrevementeMiddleware::class,
        ]);
    })
    ->withExceptions(function (Exceptions $exceptions) {
        //
    })->create();
