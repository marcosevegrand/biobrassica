<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class ShopSettings extends Model
{
    public static function defaults(): array
    {
        return [
            'is_shop_active' => true,
            'is_shop_brevemente' => false,
            'min_order_total' => 0,
            'shipping_flat_rate' => 0,
            'free_shipping_min_subtotal' => null,
            'mbway_enabled' => true,
            'bank_transfer_enabled' => true,
            'payment_timeout_minutes' => 30,
            'payment_expiry_grace_minutes' => 10,
            'mbway_minutes_to_expire' => 4,
            'multibanco_days_to_expire' => 3,
            'staff_notification_emails' => null,
            'checkout_reservation_minutes' => 30,
        ];
    }

    public static function current(): self
    {
        return self::firstOrCreate(['id' => 1], self::defaults());
    }

    protected $fillable = [
        'is_shop_active',
        'is_shop_brevemente',
        'min_order_total',
        'shipping_flat_rate',
        'free_shipping_min_subtotal',
        'mbway_enabled',
        'payment_timeout_minutes',
        'payment_expiry_grace_minutes',
        'mbway_minutes_to_expire',
        'multibanco_days_to_expire',
        'staff_notification_emails',
        'checkout_reservation_minutes',
        'bank_transfer_enabled',
    ];

    protected function casts(): array
    {
        return [
            'is_shop_active' => 'boolean',
            'is_shop_brevemente' => 'boolean',
            'min_order_total' => 'decimal:2',
            'shipping_flat_rate' => 'decimal:2',
            'free_shipping_min_subtotal' => 'decimal:2',
            'mbway_enabled' => 'boolean',
            'bank_transfer_enabled' => 'boolean',
            'payment_timeout_minutes' => 'integer',
            'payment_expiry_grace_minutes' => 'integer',
            'mbway_minutes_to_expire' => 'integer',
            'multibanco_days_to_expire' => 'integer',
            'checkout_reservation_minutes' => 'integer',
        ];
    }
}
