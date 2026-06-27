<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Category extends Model
{
    protected $fillable = [
        'slug',
        'name',
        'image',
        'is_active',
        'is_special',
        'featured_message',
    ];

    protected function casts(): array
    {
        return [
            'is_active' => 'boolean',
            'is_special' => 'boolean',
        ];
    }

    protected static function booted(): void
    {
        static::created(function (Category $category): void {
            CategoryPosition::firstOrCreate(
                ['category_id' => $category->id],
                ['position' => ((int) CategoryPosition::max('position')) + 1],
            );
        });
    }

    public function position()
    {
        return $this->hasOne(CategoryPosition::class);
    }

    public function translations()
    {
        return $this->hasMany(CategoryTranslation::class);
    }

    public function products()
    {
        return $this->hasMany(Product::class);
    }
}
