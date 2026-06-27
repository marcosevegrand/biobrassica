<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('carts', function (Blueprint $table) {
            if (! Schema::hasColumn('carts', 'guest_token')) {
                $table->string('guest_token')->nullable()->unique()->after('user_id');
            }

            $table->foreignId('user_id')->nullable()->change();
        });
    }

    public function down(): void
    {
        Schema::table('carts', function (Blueprint $table) {
            if (Schema::hasColumn('carts', 'guest_token')) {
                $table->dropUnique(['guest_token']);
                $table->dropColumn('guest_token');
            }

            $table->foreignId('user_id')->nullable(false)->change();
        });
    }
};
