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
        Schema::create('recipes', function (Blueprint $table) {
            $table->id();
            $table->string('slug')->unique();
            $table->string('cover_image')->nullable();
            $table->integer('prep_time')->nullable();
            $table->integer('cook_time')->nullable();
            $table->integer('servings')->nullable();
            $table->string('difficulty')->nullable();
            $table->json('tags')->nullable();
            $table->boolean('is_published')->default(false);
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('recipes');
    }
};
