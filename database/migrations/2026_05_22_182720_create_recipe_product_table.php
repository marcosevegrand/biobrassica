<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('recipe_product', function (Blueprint $table) {
            $table->id();
            $table->foreignId('recipe_id')->constrained()->cascadeOnDelete();
            $table->foreignId('product_id')->constrained()->cascadeOnDelete();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('recipe_product');
    }
};
