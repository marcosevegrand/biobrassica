<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class ShopSettings extends Model
{
    protected $fillable = [
        'is_shop_active',
        'is_shop_brevemente',
        'min_order_total',
        'mbway_enabled',
        'payment_timeout_minutes',
        'checkout_reservation_minutes',
        'bank_transfer_enabled',
    ];

    protected function casts(): array
    {
        return [
            'is_shop_active' => 'boolean',
            'is_shop_brevemente' => 'boolean',
            'min_order_total' => 'decimal:2',
            'mbway_enabled' => 'boolean',
            'bank_transfer_enabled' => 'boolean',
        ];
    }
}
