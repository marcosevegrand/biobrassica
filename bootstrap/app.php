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

            $host = request()->getHost();

            if (str_starts_with($host, 'loja.')) {
                $routeFile = base_path('routes/shop.php');
            } elseif (str_starts_with($host, 'admin.')) {
                $routeFile = base_path('routes/admin.php');
            } else {
                $routeFile = base_path('routes/website.php');
            }

            Route::middleware('web')->group($routeFile);
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
