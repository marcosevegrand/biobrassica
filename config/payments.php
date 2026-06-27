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

];
