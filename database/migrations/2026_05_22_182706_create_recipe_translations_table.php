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
        Schema::create('recipe_translations', function (Blueprint $table) {
            $table->id();
            $table->foreignId('recipe_id')->constrained()->cascadeOnDelete();
            $table->string('language', 2);
            $table->string('title');
            $table->text('description')->nullable();
            $table->text('content')->nullable();
            $table->json('ingredients');
            $table->json('instructions');
            $table->text('meta_description')->nullable();
            $table->timestamps();

            $table->unique(['recipe_id', 'language']);
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('recipe_translations');
    }
};
