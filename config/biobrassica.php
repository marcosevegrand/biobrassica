<?php

$adminEmail = env('ADMIN_EMAIL');

return [
    'primary_domain' => env('PRIMARY_DOMAIN', 'biobrassica.pt'),

    // URL the "Loja" button points to (external shop). Placeholder for now.
    'shop_url' => env('SHOP_URL', '#'),

    'paths' => [
        'admin' => 'admin',
    ],

    'public_path' => env('APP_PUBLIC_PATH'),

    'admin' => [
        'name' => env('ADMIN_NAME', 'Biobrassica Admin'),
        'email' => $adminEmail,
        'password' => env('ADMIN_PASSWORD'),
    ],
];
