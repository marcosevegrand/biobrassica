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
        Schema::create('orders', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->uuid('access_token');
            $table->string('email');
            $table->string('phone')->nullable();
            $table->string('nif')->nullable();
            $table->string('name');
            $table->string('status')->default('pending');
            $table->string('payment_state')->default('pending');
            $table->string('fulfillment_method');
            $table->string('pickup_location')->nullable();
            $table->string('shipping_address_line1')->nullable();
            $table->string('shipping_address_line2')->nullable();
            $table->string('shipping_city')->nullable();
            $table->string('shipping_postal_code')->nullable();
            $table->string('language')->default('pt');
            $table->decimal('subtotal', 10, 2);
            $table->decimal('total', 10, 2);
            $table->text('notes')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('orders');
    }
};
