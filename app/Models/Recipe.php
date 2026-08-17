<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Recipe extends Model
{
    protected $fillable = [
        'slug',
        'cover_image',
        'prep_time',
        'cook_time',
        'servings',
        'difficulty',
        'tags',
        'is_published',
    ];

    protected function casts(): array
    {
        return [
            'tags' => 'array',
            'is_published' => 'boolean',
        ];
    }

    public function translations()
    {
        return $this->hasMany(RecipeTranslation::class);
    }
}
