<?php

$primaryDomain = env('PRIMARY_DOMAIN', 'biobrassica.pt');
$adminEmail = env('ADMIN_EMAIL');

return [
    'primary_domain' => $primaryDomain,

    'paths' => [
        'shop' => env('SHOP_PATH', 'loja'),
        'admin' => env('ADMIN_PATH', 'admin'),
    ],

    'public_path' => env('APP_PUBLIC_PATH'),

    'admin' => [
        'name' => env('ADMIN_NAME', 'Biobrassica Admin'),
        'email' => $adminEmail,
        'password' => env('ADMIN_PASSWORD'),
        'emails' => array_values(array_unique(array_filter(array_map(
            static fn (string $email): string => strtolower(trim($email)),
            array_merge(explode(',', (string) env('ADMIN_EMAILS', '')), [$adminEmail ?: '']),
        )))),
    ],
];
