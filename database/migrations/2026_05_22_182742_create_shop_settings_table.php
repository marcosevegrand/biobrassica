<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('shop_settings', function (Blueprint $table) {
            $table->id();
            $table->boolean('is_shop_active')->default(true);
            $table->boolean('is_shop_brevemente')->default(false);
            $table->decimal('min_order_total', 10, 2)->nullable();
            $table->boolean('mbway_enabled')->default(true);
            $table->integer('payment_timeout_minutes')->default(30);
            $table->integer('checkout_reservation_minutes')->default(15);
            $table->boolean('bank_transfer_enabled')->default(true);
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('shop_settings');
    }
};
