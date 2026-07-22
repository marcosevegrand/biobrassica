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
        ];
    }

    public static function current(): self
    {
        return self::firstOrCreate(['id' => 1], self::defaults());
    }

    protected $fillable = [
        'is_shop_active',
        'is_shop_brevemente',
    ];

    protected function casts(): array
    {
        return [
            'is_shop_active' => 'boolean',
            'is_shop_brevemente' => 'boolean',
        ];
    }

    public function getModeLabelAttribute(): string
    {
        if ($this->is_shop_brevemente) {
            return 'Brevemente';
        }
        if (! $this->is_shop_active) {
            return 'Inativa';
        }

        return 'Ativada';
    }
}
