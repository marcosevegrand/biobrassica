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
        Schema::create('instagram_posts', function (Blueprint $table) {
            $table->id();
            $table->string('instagram_id')->unique();
            $table->string('permalink');
            $table->string('image_url')->nullable();
            $table->text('caption')->nullable();
            $table->dateTime('posted_at')->nullable();
            $table->integer('sort_order')->default(0);
            $table->boolean('is_active')->default(true);
            $table->dateTime('fetched_at')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('instagram_posts');
    }
};
