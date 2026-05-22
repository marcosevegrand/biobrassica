<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class DeliveryMethod extends Model
{
    protected $fillable = [
        'name',
        'estimated_delivery_time',
        'is_active',
    ];

    protected function casts(): array
    {
        return [
            'is_active' => 'boolean',
        ];
    }

    public function position()
    {
        return $this->hasOne(DeliveryMethodPosition::class);
    }
}
