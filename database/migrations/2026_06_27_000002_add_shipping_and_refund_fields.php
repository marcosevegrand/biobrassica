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
            if (! Schema::hasColumn('shop_settings', 'shipping_flat_rate')) {
                $table->decimal('shipping_flat_rate', 10, 2)->default(0)->after('min_order_total');
            }

            if (! Schema::hasColumn('shop_settings', 'free_shipping_min_subtotal')) {
                $table->decimal('free_shipping_min_subtotal', 10, 2)->nullable()->after('shipping_flat_rate');
            }
        });

        Schema::table('orders', function (Blueprint $table) {
            if (! Schema::hasColumn('orders', 'shipping_cost')) {
                $table->decimal('shipping_cost', 10, 2)->default(0)->after('subtotal');
            }
        });

        Schema::table('payments', function (Blueprint $table) {
            if (! Schema::hasColumn('payments', 'refund_state')) {
                $table->string('refund_state')->nullable()->after('paid_at');
            }

            if (! Schema::hasColumn('payments', 'refund_amount')) {
                $table->decimal('refund_amount', 10, 2)->nullable()->after('refund_state');
            }

            if (! Schema::hasColumn('payments', 'refund_reason')) {
                $table->text('refund_reason')->nullable()->after('refund_amount');
            }

            if (! Schema::hasColumn('payments', 'refund_reference')) {
                $table->string('refund_reference')->nullable()->after('refund_reason');
            }

            if (! Schema::hasColumn('payments', 'refund_notes')) {
                $table->text('refund_notes')->nullable()->after('refund_reference');
            }

            if (! Schema::hasColumn('payments', 'refund_requested_at')) {
                $table->dateTime('refund_requested_at')->nullable()->after('refund_notes');
            }

            if (! Schema::hasColumn('payments', 'refunded_at')) {
                $table->dateTime('refunded_at')->nullable()->after('refund_requested_at');
            }

            if (! Schema::hasColumn('payments', 'refund_requested_by')) {
                $table->foreignId('refund_requested_by')->nullable()->after('refunded_at')->constrained('users')->nullOnDelete();
            }

            if (! Schema::hasColumn('payments', 'refunded_by')) {
                $table->foreignId('refunded_by')->nullable()->after('refund_requested_by')->constrained('users')->nullOnDelete();
            }
        });

        DB::table('orders')->whereNull('shipping_cost')->update(['shipping_cost' => 0]);

        DB::table('payments')
            ->where('status', 'refunded')
            ->whereNull('refund_state')
            ->update([
                'refund_state' => 'completed',
                'refund_amount' => DB::raw('amount'),
                'refunded_at' => DB::raw('updated_at'),
            ]);
    }

    public function down(): void
    {
        Schema::table('payments', function (Blueprint $table) {
            foreach (['refunded_by', 'refund_requested_by'] as $column) {
                if (Schema::hasColumn('payments', $column)) {
                    $table->dropConstrainedForeignId($column);
                }
            }

            foreach (['refunded_at', 'refund_requested_at', 'refund_notes', 'refund_reference', 'refund_reason', 'refund_amount', 'refund_state'] as $column) {
                if (Schema::hasColumn('payments', $column)) {
                    $table->dropColumn($column);
                }
            }
        });

        Schema::table('orders', function (Blueprint $table) {
            if (Schema::hasColumn('orders', 'shipping_cost')) {
                $table->dropColumn('shipping_cost');
            }
        });

        Schema::table('shop_settings', function (Blueprint $table) {
            foreach (['free_shipping_min_subtotal', 'shipping_flat_rate'] as $column) {
                if (Schema::hasColumn('shop_settings', $column)) {
                    $table->dropColumn($column);
                }
            }
        });
    }
};
