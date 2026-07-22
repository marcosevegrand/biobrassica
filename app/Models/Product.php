<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Product extends Model
{
    protected $fillable = [
        'category_id',
        'slug',
        'name',
        'brand',
        'bio_code',
        'description',
        'allergens',
        'quantity',
        'is_active',
        'is_highlight',
        'image',
    ];

    protected function casts(): array
    {
        return [
            'is_active' => 'boolean',
            'is_highlight' => 'boolean',
        ];
    }

    public function category()
    {
        return $this->belongsTo(Category::class);
    }

    public function translations()
    {
        return $this->hasMany(ProductTranslation::class);
    }

    public function recipes()
    {
        return $this->belongsToMany(Recipe::class, 'recipe_product');
    }

    public function getVisibilityLabelAttribute(): string
    {
        if (! $this->is_active) {
            return 'Escondido';
        }
        if ($this->is_highlight) {
            return 'Destacado';
        }

        return 'Normal';
    }
}
