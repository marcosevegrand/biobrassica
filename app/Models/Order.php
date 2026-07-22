<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Order extends Model
{
    public const STATUS_PENDING = 'pending';

    public const STATUS_PREPARING = 'preparing';

    public const STATUS_READY = 'ready';

    public const STATUS_IN_TRANSIT = 'in_transit';

    public const STATUS_DELIVERED = 'delivered';

    public const STATUS_CANCELLED = 'cancelled';

    public const PAYMENT_PENDING = 'pending';

    public const PAYMENT_CONFIRMED = 'confirmed';

    public const PAYMENT_CANCELLED = 'cancelled';

    public const PAYMENT_REFUNDED = 'refunded';

    protected $fillable = [
        'user_id',
        'email',
        'phone',
        'nif',
        'name',
        'status',
        'payment_state',
        'fulfillment_method',
        'pickup_location',
        'shipping_address_line1',
        'shipping_address_line2',
        'shipping_city',
        'shipping_postal_code',
        'language',
        'subtotal',
        'shipping_cost',
        'total',
        'notes',
    ];

    protected function casts(): array
    {
        return [
            'subtotal' => 'decimal:2',
            'shipping_cost' => 'decimal:2',
            'total' => 'decimal:2',
        ];
    }

    public function user()
    {
        return $this->belongsTo(User::class);
    }

    public function items()
    {
        return $this->hasMany(OrderItem::class);
    }

    public function payment()
    {
        return $this->hasOne(Payment::class);
    }

    public function pickupLocation()
    {
        return $this->belongsTo(Location::class, 'pickup_location');
    }

    public function isPaid(): bool
    {
        return $this->payment_state === self::PAYMENT_CONFIRMED;
    }

    public static function statusLabels(): array
    {
        return [
            self::STATUS_PENDING => 'Pendente',
            self::STATUS_PREPARING => 'Em preparação',
            self::STATUS_READY => 'Pronta para levantamento',
            self::STATUS_IN_TRANSIT => 'Em distribuição',
            self::STATUS_DELIVERED => 'Entregue',
            self::STATUS_CANCELLED => 'Cancelada',
        ];
    }

    public static function paymentStateLabels(): array
    {
        return [
            self::PAYMENT_PENDING => 'Pendente',
            self::PAYMENT_CONFIRMED => 'Confirmado',
            self::PAYMENT_CANCELLED => 'Cancelado',
            self::PAYMENT_REFUNDED => 'Reembolsado',
        ];
    }
}
