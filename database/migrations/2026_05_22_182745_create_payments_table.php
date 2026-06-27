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
        Schema::create('payments', function (Blueprint $table) {
            $table->id();
            $table->foreignId('order_id')->unique()->constrained()->cascadeOnDelete();
            $table->string('method');
            $table->string('status')->default('pending');
            $table->decimal('amount', 10, 2);
            $table->string('provider_reference')->nullable();
            $table->string('provider_payment_id')->nullable();
            $table->json('provider_data')->nullable();
            $table->text('checkout_url')->nullable();
            $table->text('last_error')->nullable();
            $table->dateTime('expires_at')->nullable();
            $table->dateTime('paid_at')->nullable();
            $table->string('refund_state')->nullable();
            $table->decimal('refund_amount', 10, 2)->nullable();
            $table->text('refund_reason')->nullable();
            $table->string('refund_reference')->nullable();
            $table->text('refund_notes')->nullable();
            $table->dateTime('refund_requested_at')->nullable();
            $table->dateTime('refunded_at')->nullable();
            $table->foreignId('refund_requested_by')->nullable()->constrained('users')->nullOnDelete();
            $table->foreignId('refunded_by')->nullable()->constrained('users')->nullOnDelete();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('payments');
    }
};
