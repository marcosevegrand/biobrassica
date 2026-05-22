<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class LocationPosition extends Model
{
    protected $fillable = [
        'location_id',
        'position',
    ];

    public function location()
    {
        return $this->belongsTo(Location::class);
    }
}
