<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class RecipeTranslation extends Model
{
    protected $fillable = [
        'recipe_id',
        'language',
        'title',
        'description',
        'content',
        'ingredients',
        'instructions',
        'meta_description',
    ];

    protected function casts(): array
    {
        return [
            'ingredients' => 'array',
            'instructions' => 'array',
        ];
    }

    public function recipe()
    {
        return $this->belongsTo(Recipe::class);
    }
}
