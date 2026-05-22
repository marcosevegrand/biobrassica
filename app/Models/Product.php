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
        'price',
        'quantity',
        'stock',
        'is_active',
        'is_highlight',
        'is_preview',
        'allow_shipping',
        'allow_pickup',
        'image',
    ];

    protected function casts(): array
    {
        return [
            'price' => 'decimal:2',
            'quantity' => 'decimal:2',
            'is_active' => 'boolean',
            'is_highlight' => 'boolean',
            'is_preview' => 'boolean',
            'allow_shipping' => 'boolean',
            'allow_pickup' => 'boolean',
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

    public function pickupLocations()
    {
        return $this->belongsToMany(Location::class, 'product_pickup_location');
    }

    public function recipes()
    {
        return $this->belongsToMany(Recipe::class, 'recipe_product');
    }

    public function cartItems()
    {
        return $this->hasMany(CartItem::class);
    }
}
