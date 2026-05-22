<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class BlogPostTranslation extends Model
{
    protected $fillable = [
        'blog_post_id',
        'language',
        'title',
        'excerpt',
        'content',
        'meta_description',
    ];

    public function blogPost()
    {
        return $this->belongsTo(BlogPost::class);
    }
}
