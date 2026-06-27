<?php

namespace App\Console\Commands;

use App\Services\PaymentService;
use Illuminate\Console\Command;

class RegisterIfthenpayWebhooks extends Command
{
    protected $signature = 'ifthenpay:register-webhooks {--url= : Public callback URL. Defaults to the payment.callback route.}';

    protected $description = 'Register configured IfThenPay MB WAY and Multibanco callbacks.';

    public function handle(PaymentService $paymentService): int
    {
        $url = $this->option('url') ?: route('payment.callback');

        $registered = $paymentService->registerConfiguredWebhooks($url);

        if ($registered === []) {
            $this->warn('No IfThenPay payment methods are configured.');

            return self::SUCCESS;
        }

        foreach ($registered as $method => $registeredUrl) {
            $this->info("{$method}: {$registeredUrl}");
        }

        return self::SUCCESS;
    }
}
