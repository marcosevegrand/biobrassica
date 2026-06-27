<?php

return [

    /*
    |--------------------------------------------------------------------------
    | IfThenPay Gateway
    |--------------------------------------------------------------------------
    |
    | Payments are initiated and validated through the official IfThenPay PHP
    | SDK. Keep credentials in the environment, never in the database.
    |
    */

    'ifthenpay' => [
        'backoffice_key' => env('IFTHENPAY_BACKOFFICE_KEY', ''),
        'anti_phishing_key' => env('IFTHENPAY_ANTI_PHISHING_KEY', ''),
        'mbway_key' => env('IFTHENPAY_MBWAY_KEY', ''),
        'multibanco_key' => env('IFTHENPAY_MULTIBANCO_KEY', ''),
    ],

    /*
    |--------------------------------------------------------------------------
    | Fake Payments
    |--------------------------------------------------------------------------
    |
    | For local/staging tests without IfThenPay credentials. PaymentService
    | ignores this switch in production, so real checkouts cannot accidentally
    | use fake payments on APP_ENV=production.
    |
    */

    'fake' => [
        'enabled' => env('PAYMENTS_FAKE_ENABLED', false),
        'auto_confirm' => env('PAYMENTS_FAKE_AUTO_CONFIRM', true),
    ],

];
