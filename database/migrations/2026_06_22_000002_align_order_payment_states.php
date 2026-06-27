<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    public function up(): void
    {
        DB::table('payments')->where('status', 'paid')->update(['status' => 'confirmed']);
        DB::table('payments')->whereIn('status', ['rejected', 'expired', 'failed'])->update(['status' => 'cancelled']);
        DB::table('payments')->where('method', 'bank_transfer')->update(['method' => 'multibanco']);

        DB::table('orders')->where('payment_state', 'paid')->update(['payment_state' => 'confirmed']);
        DB::table('orders')->whereIn('payment_state', ['rejected', 'expired', 'failed'])->update(['payment_state' => 'cancelled']);
        DB::table('orders')->where('payment_state', 'cancelled')->update(['status' => 'cancelled']);

        DB::table('orders')->whereIn('status', ['confirmed', 'processing'])->where('payment_state', '!=', 'cancelled')->update(['status' => 'preparing']);
        DB::table('orders')->where('status', 'shipped')->update(['status' => 'in_transit']);
        DB::table('orders')->where('status', 'completed')->update(['status' => 'delivered']);
    }

    public function down(): void
    {
        DB::table('payments')->where('status', 'confirmed')->update(['status' => 'paid']);
        DB::table('payments')->where('status', 'cancelled')->update(['status' => 'rejected']);
        DB::table('payments')->where('method', 'multibanco')->update(['method' => 'bank_transfer']);

        DB::table('orders')->where('payment_state', 'confirmed')->update(['payment_state' => 'paid']);
        DB::table('orders')->where('payment_state', 'cancelled')->update(['payment_state' => 'rejected']);

        DB::table('orders')->where('status', 'preparing')->update(['status' => 'processing']);
        DB::table('orders')->where('status', 'in_transit')->update(['status' => 'shipped']);
        DB::table('orders')->where('status', 'delivered')->update(['status' => 'completed']);
    }
};
