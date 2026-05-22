<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class ProductTranslation extends Model
{
    protected $fillable = [
        'product_id',
        'language',
        'name',
        'description',
        'allergens',
    ];

    public function product()
    {
        return $this->belongsTo(Product::class);
    }
}
