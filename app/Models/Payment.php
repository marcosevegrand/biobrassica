<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Payment extends Model
{
    protected $fillable = [
        'order_id',
        'method',
        'status',
        'amount',
        'provider_reference',
        'provider_payment_id',
        'provider_data',
        'checkout_url',
        'last_error',
        'expires_at',
        'paid_at',
    ];

    protected function casts(): array
    {
        return [
            'amount' => 'decimal:2',
            'provider_data' => 'array',
            'expires_at' => 'datetime',
            'paid_at' => 'datetime',
        ];
    }

    public function order()
    {
        return $this->belongsTo(Order::class);
    }
}
