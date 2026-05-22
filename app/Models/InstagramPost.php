<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class InstagramPost extends Model
{
    protected $fillable = [
        'instagram_id',
        'permalink',
        'image_url',
        'caption',
        'posted_at',
        'sort_order',
        'is_active',
        'fetched_at',
    ];

    protected function casts(): array
    {
        return [
            'posted_at' => 'datetime',
            'fetched_at' => 'datetime',
            'is_active' => 'boolean',
        ];
    }
}
