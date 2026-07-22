<?php

$adminEmail = env('ADMIN_EMAIL');

return [
    'primary_domain' => env('PRIMARY_DOMAIN', 'biobrassica.pt'),

    'paths' => [
        'shop' => 'catalogo',
        'admin' => 'admin',
    ],

    'public_path' => env('APP_PUBLIC_PATH'),

    'admin' => [
        'name' => env('ADMIN_NAME', 'Biobrassica Admin'),
        'email' => $adminEmail,
        'password' => env('ADMIN_PASSWORD'),
    ],
];
