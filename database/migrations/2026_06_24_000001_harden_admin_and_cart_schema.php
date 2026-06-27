<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('users', function (Blueprint $table) {
            if (! Schema::hasColumn('users', 'is_admin')) {
                $table->boolean('is_admin')->default(false)->after('nif');
            }
        });

        foreach (config('biobrassica.admin.emails', []) as $email) {
            DB::table('users')
                ->whereRaw('LOWER(email) = ?', [strtolower($email)])
                ->update([
                    'is_admin' => true,
                    'email_verified_at' => DB::raw('COALESCE(email_verified_at, CURRENT_TIMESTAMP)'),
                ]);
        }

        $duplicateCartItems = DB::table('cart_items')
            ->select('cart_id', 'product_id', DB::raw('MIN(id) as keep_id'), DB::raw('SUM(quantity) as quantity'), DB::raw('SUM(reserved_quantity) as reserved_quantity'))
            ->groupBy('cart_id', 'product_id')
            ->havingRaw('COUNT(*) > 1')
            ->get();

        foreach ($duplicateCartItems as $duplicate) {
            DB::table('cart_items')
                ->where('id', $duplicate->keep_id)
                ->update([
                    'quantity' => min((int) $duplicate->quantity, 99),
                    'reserved_quantity' => min((int) $duplicate->reserved_quantity, 99),
                ]);

            DB::table('cart_items')
                ->where('cart_id', $duplicate->cart_id)
                ->where('product_id', $duplicate->product_id)
                ->where('id', '!=', $duplicate->keep_id)
                ->delete();
        }

        if (! $this->indexExists('cart_items', 'cart_items_cart_id_product_id_unique')) {
            Schema::table('cart_items', function (Blueprint $table) {
                $table->unique(['cart_id', 'product_id'], 'cart_items_cart_id_product_id_unique');
            });
        }

        Schema::table('orders', function (Blueprint $table) {
            if (Schema::hasColumn('orders', 'access_token')) {
                $table->dropColumn('access_token');
            }
        });
    }

    public function down(): void
    {
        Schema::table('orders', function (Blueprint $table) {
            if (! Schema::hasColumn('orders', 'access_token')) {
                $table->uuid('access_token')->nullable()->after('user_id');
            }
        });

        if ($this->indexExists('cart_items', 'cart_items_cart_id_product_id_unique')) {
            Schema::table('cart_items', function (Blueprint $table) {
                $table->dropUnique('cart_items_cart_id_product_id_unique');
            });
        }

        Schema::table('users', function (Blueprint $table) {
            if (Schema::hasColumn('users', 'is_admin')) {
                $table->dropColumn('is_admin');
            }
        });
    }

    private function indexExists(string $table, string $index): bool
    {
        return collect(Schema::getIndexes($table))->contains(fn (array $existingIndex): bool => ($existingIndex['name'] ?? null) === $index);
    }
};
