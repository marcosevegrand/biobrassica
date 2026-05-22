<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class BlogPost extends Model
{
    protected $fillable = [
        'slug',
        'author_id',
        'cover_image',
        'is_published',
        'published_at',
        'tags',
    ];

    protected function casts(): array
    {
        return [
            'is_published' => 'boolean',
            'published_at' => 'datetime',
            'tags' => 'array',
        ];
    }

    public function author()
    {
        return $this->belongsTo(User::class, 'author_id');
    }

    public function translations()
    {
        return $this->hasMany(BlogPostTranslation::class);
    }
}
