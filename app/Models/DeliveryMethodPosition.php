<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class DeliveryMethodPosition extends Model
{
    protected $fillable = [
        'delivery_method_id',
        'position',
    ];

    public function deliveryMethod()
    {
        return $this->belongsTo(DeliveryMethod::class);
    }
}
