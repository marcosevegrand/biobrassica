<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('website_contents', function (Blueprint $table) {
            if (! Schema::hasColumn('website_contents', 'shop_coming_soon')) {
                $table->boolean('shop_coming_soon')->default(true)->after('terms_conditions_text');
            }

            foreach (['hero_cta_text', 'hero_cta_url'] as $column) {
                if (Schema::hasColumn('website_contents', $column)) {
                    $table->dropColumn($column);
                }
            }
        });
    }

    public function down(): void
    {
        Schema::table('website_contents', function (Blueprint $table) {
            if (Schema::hasColumn('website_contents', 'shop_coming_soon')) {
                $table->dropColumn('shop_coming_soon');
            }

            if (! Schema::hasColumn('website_contents', 'hero_cta_text')) {
                $table->text('hero_cta_text')->nullable();
            }

            if (! Schema::hasColumn('website_contents', 'hero_cta_url')) {
                $table->text('hero_cta_url')->nullable();
            }
        });
    }
};
