<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class CategoryPosition extends Model
{
    protected $fillable = [
        'category_id',
        'position',
    ];

    public function category()
    {
        return $this->belongsTo(Category::class);
    }
}
