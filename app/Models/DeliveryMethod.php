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

    protected static function booted(): void
    {
        static::created(function (DeliveryMethod $deliveryMethod): void {
            DeliveryMethodPosition::firstOrCreate(
                ['delivery_method_id' => $deliveryMethod->id],
                ['position' => ((int) DeliveryMethodPosition::max('position')) + 1],
            );
        });
    }

    public function position()
    {
        return $this->hasOne(DeliveryMethodPosition::class);
    }
}
