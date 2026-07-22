<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('products', function (Blueprint $table) {
            // Drop the composite index that includes stock before dropping the column
            // (SQLite cannot drop indexed columns)
            $table->dropIndex('products_is_active_stock_index');

            if (Schema::hasColumn('products', 'price')) {
                $table->dropColumn('price');
            }
            if (Schema::hasColumn('products', 'stock')) {
                $table->dropColumn('stock');
            }
            if (Schema::hasColumn('products', 'is_preview')) {
                $table->dropColumn('is_preview');
            }
            if (Schema::hasColumn('products', 'allow_shipping')) {
                $table->dropColumn('allow_shipping');
            }
            if (Schema::hasColumn('products', 'allow_pickup')) {
                $table->dropColumn('allow_pickup');
            }
        });
    }

    public function down(): void
    {
        Schema::table('products', function (Blueprint $table) {
            if (! Schema::hasColumn('products', 'price')) {
                $table->decimal('price', 10, 2)->default(0);
            }
            if (! Schema::hasColumn('products', 'stock')) {
                $table->integer('stock')->default(0);
            }
            if (! Schema::hasColumn('products', 'is_preview')) {
                $table->boolean('is_preview')->default(false);
            }
            if (! Schema::hasColumn('products', 'allow_shipping')) {
                $table->boolean('allow_shipping')->default(true);
            }
            if (! Schema::hasColumn('products', 'allow_pickup')) {
                $table->boolean('allow_pickup')->default(true);
            }
        });
    }
};
