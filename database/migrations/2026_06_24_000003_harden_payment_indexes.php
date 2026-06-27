<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('payments', function (Blueprint $table) {
            if (! $this->indexExists('payments', 'payments_status_expires_at_index')) {
                $table->index(['status', 'expires_at'], 'payments_status_expires_at_index');
            }

            if (! $this->indexExists('payments', 'payments_provider_payment_id_unique')) {
                $table->unique('provider_payment_id', 'payments_provider_payment_id_unique');
            }

            if (! $this->indexExists('payments', 'payments_provider_reference_index')) {
                $table->index('provider_reference', 'payments_provider_reference_index');
            }
        });
    }

    public function down(): void
    {
        Schema::table('payments', function (Blueprint $table) {
            if ($this->indexExists('payments', 'payments_provider_reference_index')) {
                $table->dropIndex('payments_provider_reference_index');
            }

            if ($this->indexExists('payments', 'payments_provider_payment_id_unique')) {
                $table->dropUnique('payments_provider_payment_id_unique');
            }

            if ($this->indexExists('payments', 'payments_status_expires_at_index')) {
                $table->dropIndex('payments_status_expires_at_index');
            }
        });
    }

    private function indexExists(string $table, string $index): bool
    {
        return collect(Schema::getIndexes($table))->contains(fn (array $existingIndex): bool => ($existingIndex['name'] ?? null) === $index);
    }
};
