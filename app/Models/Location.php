<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Location extends Model
{
    protected $fillable = [
        'name',
        'pickup_location_code',
        'address',
        'image',
        'phone',
        'email',
        'opening_hours',
        'pickup_hours',
        'map_embed_url',
        'is_active',
    ];

    protected function casts(): array
    {
        return [
            'pickup_hours' => 'array',
            'is_active' => 'boolean',
        ];
    }

    public function position()
    {
        return $this->hasOne(LocationPosition::class);
    }

    public function products()
    {
        return $this->belongsToMany(Product::class, 'product_pickup_location');
    }
}
