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
        Schema::create('products', function (Blueprint $table) {
            $table->id();
            $table->foreignId('category_id')->constrained()->cascadeOnDelete();
            $table->string('slug');
            $table->string('name');
            $table->string('brand')->nullable();
            $table->string('bio_code')->nullable();
            $table->text('description')->nullable();
            $table->text('allergens')->nullable();
            $table->decimal('price', 10, 2);
            $table->decimal('quantity', 10, 2)->nullable();
            $table->integer('stock')->default(0);
            $table->boolean('is_active')->default(true);
            $table->boolean('is_highlight')->default(false);
            $table->boolean('is_preview')->default(false);
            $table->boolean('allow_shipping')->default(true);
            $table->boolean('allow_pickup')->default(true);
            $table->string('image')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('products');
    }
};
