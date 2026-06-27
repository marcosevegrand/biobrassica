<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('carts', function (Blueprint $table): void {
            if (! $this->indexExists('carts', 'carts_reserved_until_index')) {
                $table->index('reserved_until', 'carts_reserved_until_index');
            }
        });

        Schema::table('orders', function (Blueprint $table): void {
            if (! $this->indexExists('orders', 'orders_status_payment_state_created_at_index')) {
                $table->index(['status', 'payment_state', 'created_at'], 'orders_status_payment_state_created_at_index');
            }
        });

        Schema::table('payments', function (Blueprint $table): void {
            if (! $this->indexExists('payments', 'payments_refund_state_index')) {
                $table->index('refund_state', 'payments_refund_state_index');
            }
        });

        Schema::table('products', function (Blueprint $table): void {
            if (! $this->indexExists('products', 'products_slug_unique')) {
                $table->unique('slug', 'products_slug_unique');
            }

            if (! $this->indexExists('products', 'products_is_active_stock_index')) {
                $table->index(['is_active', 'stock'], 'products_is_active_stock_index');
            }

            if (! $this->indexExists('products', 'products_is_active_is_highlight_index')) {
                $table->index(['is_active', 'is_highlight'], 'products_is_active_is_highlight_index');
            }
        });
    }

    public function down(): void
    {
        Schema::table('products', function (Blueprint $table): void {
            if ($this->indexExists('products', 'products_is_active_is_highlight_index')) {
                $table->dropIndex('products_is_active_is_highlight_index');
            }

            if ($this->indexExists('products', 'products_is_active_stock_index')) {
                $table->dropIndex('products_is_active_stock_index');
            }

            if ($this->indexExists('products', 'products_slug_unique')) {
                $table->dropUnique('products_slug_unique');
            }
        });

        Schema::table('payments', function (Blueprint $table): void {
            if ($this->indexExists('payments', 'payments_refund_state_index')) {
                $table->dropIndex('payments_refund_state_index');
            }
        });

        Schema::table('orders', function (Blueprint $table): void {
            if ($this->indexExists('orders', 'orders_status_payment_state_created_at_index')) {
                $table->dropIndex('orders_status_payment_state_created_at_index');
            }
        });

        Schema::table('carts', function (Blueprint $table): void {
            if ($this->indexExists('carts', 'carts_reserved_until_index')) {
                $table->dropIndex('carts_reserved_until_index');
            }
        });
    }

    private function indexExists(string $table, string $index): bool
    {
        return collect(Schema::getIndexes($table))->contains(fn (array $existingIndex): bool => ($existingIndex['name'] ?? null) === $index);
    }
};
