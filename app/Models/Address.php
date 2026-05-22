<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Address extends Model
{
    protected $fillable = [
        'user_id',
        'name',
        'line1',
        'line2',
        'city',
        'postal_code',
        'country',
        'is_default',
    ];

    public function user()
    {
        return $this->belongsTo(User::class);
    }
}
