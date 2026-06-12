<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('shop_settings', function (Blueprint $table) {
            $table->string('mbway_number', 20)->nullable()->after('mbway_enabled');
            $table->string('bank_beneficiary', 120)->nullable()->after('bank_transfer_enabled');
            $table->string('bank_iban', 34)->nullable()->after('bank_beneficiary');
            $table->string('bank_bic', 11)->nullable()->after('bank_iban');
        });
    }

    public function down(): void
    {
        Schema::table('shop_settings', function (Blueprint $table) {
            $table->dropColumn(['mbway_number', 'bank_beneficiary', 'bank_iban', 'bank_bic']);
        });
    }
};
