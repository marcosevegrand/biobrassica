<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Order extends Model
{
    protected $fillable = [
        'user_id',
        'access_token',
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
        'total',
        'notes',
    ];

    protected function casts(): array
    {
        return [
            'subtotal' => 'decimal:2',
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
}
