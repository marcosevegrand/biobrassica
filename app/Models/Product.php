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

    public function hasFulfillmentMethod(): bool
    {
        return (bool) $this->allow_shipping || (bool) $this->allow_pickup;
    }

    public function canBePurchasedOnline(): bool
    {
        return $this->is_active
            && ! $this->is_preview
            && (int) $this->stock > 0
            && $this->hasFulfillmentMethod();
    }

    public function getVisibilityLabelAttribute(): string
    {
        if (! $this->is_active) {
            return 'Escondido';
        }
        if ($this->is_preview) {
            return 'Pré-visualização';
        }
        if ($this->is_highlight) {
            return 'Destacado';
        }

        return 'Normal';
    }

    public function getDeliveryLabelAttribute(): string
    {
        if (! $this->allow_shipping && $this->allow_pickup) {
            return 'Apenas Levantamento';
        }
        if ($this->allow_shipping && ! $this->allow_pickup) {
            return 'Apenas Envio';
        }

        return 'Ambos';
    }
}
