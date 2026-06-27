<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('website_contents', function (Blueprint $table) {
            foreach (['custom_css', 'custom_js'] as $column) {
                if (Schema::hasColumn('website_contents', $column)) {
                    $table->dropColumn($column);
                }
            }
        });
    }

    public function down(): void
    {
        Schema::table('website_contents', function (Blueprint $table) {
            if (! Schema::hasColumn('website_contents', 'custom_css')) {
                $table->text('custom_css')->nullable();
            }

            if (! Schema::hasColumn('website_contents', 'custom_js')) {
                $table->text('custom_js')->nullable();
            }
        });
    }
};
