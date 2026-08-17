<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        $tables = [
            'product_pickup_location',
            'recipe_product',
            'product_translations',
            'products',
            'category_translations',
            'category_positions',
            'categories',
            'cart_items',
            'carts',
            'order_items',
            'orders',
            'payments',
            'addresses',
            'location_positions',
            'locations',
            'delivery_method_positions',
            'delivery_methods',
            'shop_settings',
        ];

        foreach ($tables as $table) {
            Schema::dropIfExists($table);
        }
    }

    public function down(): void
    {
        // Shop tables were removed intentionally and cannot be restored here.
    }
};
