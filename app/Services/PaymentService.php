<?php

namespace App\Services;

use App\Models\Order;
use App\Models\Payment;
use Carbon\Carbon;
use RuntimeException;

class PaymentService
{
    public function __construct(
        private readonly OrderStateMachine $stateMachine,
    ) {}

    public function createPayment(Order $order, string $method): Payment
    {
        $timeout = config('payments.timeout_minutes', 30);

        return Payment::create([
            'order_id' => $order->id,
            'method' => $method,
            'status' => 'pending',
            'amount' => $order->total,
            'expires_at' => Carbon::now()->addMinutes($timeout),
        ]);
    }

    public function getManualMbwayDetails(): array
    {
        return [
            'phone' => config('payments.mbway_phone'),
            'label' => 'MB WAY',
        ];
    }

    public function getManualBankTransferDetails(): array
    {
        return [
            'iban' => config('payments.bank_transfer_iban'),
            'bic' => config('payments.bank_transfer_bic'),
            'beneficiary' => config('payments.bank_transfer_beneficiary'),
            'label' => 'Transferência Bancária',
        ];
    }

    public function confirmPayment(Payment $payment): void
    {
        if ($payment->status === 'paid') {
            return;
        }

        $payment->status = 'paid';
        $payment->paid_at = Carbon::now();
        $payment->save();

        $order = $payment->order;
        $this->stateMachine->transition($order, 'confirmed');
    }

    public function rejectPayment(Payment $payment, string $reason): void
    {
        if ($payment->status !== 'pending') {
            throw new RuntimeException('Apenas pagamentos pendentes podem ser rejeitados.');
        }

        $payment->status = 'failed';
        $payment->last_error = $reason;
        $payment->save();

        $order = $payment->order;
        $this->stateMachine->transition($order, 'cancelled');
    }
}
