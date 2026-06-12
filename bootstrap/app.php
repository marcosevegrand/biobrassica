<?php

use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| Bootstrap the application
|--------------------------------------------------------------------------
|
| On some shared hosting environments, the Application builder's create()
| method completes without binding 'config', which prevents
| registerConfiguredProviders() from running. This file detects that
| condition and manually finishes booting the application.
|
*/

$app = Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        commands: __DIR__ . '/../routes/console.php',
        then: function () {
            require base_path('routes/health.php');
            $shopPath = trim((string) env('SHOP_PATH', 'loja'), '/');
            Route::middleware('web')
                ->prefix($shopPath)
                ->group(base_path('routes/web.php'));
            Route::middleware('web')
                ->prefix($shopPath)
                ->group(base_path('routes/shop.php'));
            Route::middleware('web')->group(base_path('routes/website.php'));
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

/*
|--------------------------------------------------------------------------
| Fix: ensure the application is fully booted
|--------------------------------------------------------------------------
|
| If create() returned an un-bootstrapped Application (config not bound),
| manually finish what create() was supposed to do.
|
*/
if (! $app->bound('config')) {
    // Bind env first — it's normally set by bootstrappers that haven't run
    $app->instance('env', env('APP_ENV', 'production'));

    // Bind config manually
    $app->instance(
        'config',
        tap(new \Illuminate\Config\Repository, function ($config) use ($app) {
            foreach (glob($app->configPath('*.php')) as $file) {
                $config->set(basename($file, '.php'), require $file);
            }
        })
    );
    $app->alias('config', \Illuminate\Contracts\Config\Repository::class);
    $app->alias('config', \Illuminate\Config\Repository::class);

    // Now register all providers and boot
    $app->registerConfiguredProviders();

    foreach (require $app->basePath('bootstrap/providers.php') as $provider) {
        $app->register($provider);
    }

    $app->boot();
}

return $app;
