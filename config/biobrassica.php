<?php

$primaryDomain = env('PRIMARY_DOMAIN', 'biobrassica.pt');
$adminEmail = env('ADMIN_EMAIL');

return [
    'primary_domain' => $primaryDomain,

    'domains' => [
        'website' => env('WEBSITE_DOMAIN', $primaryDomain),
        'shop' => env('SHOP_DOMAIN', 'loja.'.$primaryDomain),
        'admin' => env('ADMIN_DOMAIN', 'admin.'.$primaryDomain),
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
