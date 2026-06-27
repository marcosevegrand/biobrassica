<?php

use Illuminate\Http\Request;

define('LARAVEL_START', microtime(true));

/*
|--------------------------------------------------------------------------
| cPanel public_html front controller
|--------------------------------------------------------------------------
|
| This file is intentionally safe for shared hosting. It does not force
| debug mode or print logs. The Laravel application should live outside the
| web root, normally at /home/<cpanel-user>/biobrassica.
|
*/

$candidateRoots = array_filter([
    getenv('LARAVEL_APP_ROOT') ?: null,
    __DIR__.'/../biobrassica',
    __DIR__.'/..',
]);

$appRoot = null;

foreach ($candidateRoots as $candidateRoot) {
    $candidateRoot = rtrim($candidateRoot, DIRECTORY_SEPARATOR);

    if (
        is_file($candidateRoot.'/bootstrap/app.php')
        && is_file($candidateRoot.'/vendor/autoload.php')
    ) {
        $appRoot = $candidateRoot;
        break;
    }
}

if (! $appRoot) {
    http_response_code(503);
    header('Content-Type: text/plain; charset=UTF-8');
    exit('Application is not fully installed. Check that the Laravel files and vendor directory exist outside public_html.');
}

$maintenance = $appRoot.'/storage/framework/maintenance.php';

if (is_file($maintenance)) {
    require $maintenance;
}

require $appRoot.'/vendor/autoload.php';

$app = require_once $appRoot.'/bootstrap/app.php';

if (method_exists($app, 'usePublicPath')) {
    $app->usePublicPath(__DIR__);
}

$app->handleRequest(Request::capture());
