<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        $this->deduplicateProviderPaymentIds();

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

    private function deduplicateProviderPaymentIds(): void
    {
        if (! Schema::hasColumn('payments', 'provider_payment_id')) {
            return;
        }

        DB::table('payments')
            ->where('provider_payment_id', '')
            ->update(['provider_payment_id' => null]);

        $duplicates = DB::table('payments')
            ->select('provider_payment_id')
            ->whereNotNull('provider_payment_id')
            ->groupBy('provider_payment_id')
            ->havingRaw('COUNT(*) > 1')
            ->pluck('provider_payment_id');

        foreach ($duplicates as $providerPaymentId) {
            $payments = DB::table('payments')
                ->where('provider_payment_id', $providerPaymentId)
                ->orderBy('id')
                ->get(['id', 'provider_payment_id']);

            foreach ($payments->slice(1) as $payment) {
                DB::table('payments')
                    ->where('id', $payment->id)
                    ->update([
                        'provider_payment_id' => mb_substr($payment->provider_payment_id.'-duplicate-'.$payment->id, 0, 255),
                    ]);
            }
        }
    }
};
