<?php

namespace App\Console\Commands;

use App\Models\Payment;
use App\Services\PaymentService;
use Illuminate\Console\Command;

class ExpirePayments extends Command
{
    protected $signature = 'payments:expire';

    protected $description = 'Cancel pending IfThenPay payments whose timeout has elapsed.';

    public function handle(PaymentService $paymentService): int
    {
        $count = 0;

        Payment::query()
            ->where('status', Payment::STATUS_PENDING)
            ->whereNotNull('expires_at')
            ->where('expires_at', '<=', now())
            ->chunkById(100, function ($payments) use ($paymentService, &$count): void {
                foreach ($payments as $payment) {
                    $paymentService->expireIfTimedOut($payment);
                    $count++;
                }
            });

        $this->info("Processed {$count} expired payment(s).");

        return self::SUCCESS;
    }
}
