<?php

namespace App\Services;

use App\Models\ShopSettings;

class ShippingService
{
    public function calculate(float $subtotal, string $fulfillmentMethod, ShopSettings $settings): float
    {
        if ($fulfillmentMethod !== 'shipping') {
            return 0.0;
        }

        $freeShippingThreshold = $settings->free_shipping_min_subtotal;

        if ($freeShippingThreshold !== null && (float) $freeShippingThreshold > 0 && $subtotal >= (float) $freeShippingThreshold) {
            return 0.0;
        }

        return round(max(0, (float) $settings->shipping_flat_rate), 2);
    }
}
