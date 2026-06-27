<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('shop_settings', function (Blueprint $table) {
            if (! Schema::hasColumn('shop_settings', 'payment_expiry_grace_minutes')) {
                $table->unsignedInteger('payment_expiry_grace_minutes')->default(10)->after('payment_timeout_minutes');
            }

            if (! Schema::hasColumn('shop_settings', 'mbway_minutes_to_expire')) {
                $table->unsignedInteger('mbway_minutes_to_expire')->default(4)->after('payment_expiry_grace_minutes');
            }

            if (! Schema::hasColumn('shop_settings', 'multibanco_days_to_expire')) {
                $table->unsignedInteger('multibanco_days_to_expire')->default(3)->after('mbway_minutes_to_expire');
            }

            if (! Schema::hasColumn('shop_settings', 'staff_notification_emails')) {
                $table->text('staff_notification_emails')->nullable()->after('multibanco_days_to_expire');
            }
        });

        DB::table('shop_settings')->whereNull('payment_timeout_minutes')->update([
            'payment_timeout_minutes' => 30,
        ]);
    }

    public function down(): void
    {
        Schema::table('shop_settings', function (Blueprint $table) {
            foreach (['staff_notification_emails', 'multibanco_days_to_expire', 'mbway_minutes_to_expire', 'payment_expiry_grace_minutes'] as $column) {
                if (Schema::hasColumn('shop_settings', $column)) {
                    $table->dropColumn($column);
                }
            }
        });
    }
};
