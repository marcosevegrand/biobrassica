<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('shop_settings', function (Blueprint $table) {
            foreach (['mbway_number', 'bank_beneficiary', 'bank_iban', 'bank_bic'] as $column) {
                if (Schema::hasColumn('shop_settings', $column)) {
                    $table->dropColumn($column);
                }
            }
        });
    }

    public function down(): void
    {
        Schema::table('shop_settings', function (Blueprint $table) {
            if (! Schema::hasColumn('shop_settings', 'mbway_number')) {
                $table->string('mbway_number', 20)->nullable()->after('mbway_enabled');
            }
            if (! Schema::hasColumn('shop_settings', 'bank_beneficiary')) {
                $table->string('bank_beneficiary', 120)->nullable()->after('bank_transfer_enabled');
            }
            if (! Schema::hasColumn('shop_settings', 'bank_iban')) {
                $table->string('bank_iban', 34)->nullable()->after('bank_beneficiary');
            }
            if (! Schema::hasColumn('shop_settings', 'bank_bic')) {
                $table->string('bank_bic', 11)->nullable()->after('bank_iban');
            }
        });
    }
};
