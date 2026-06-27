<?php

namespace App\Http\Controllers;

use App\Models\Order;
use App\Services\PaymentService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;

class PaymentController extends Controller
{
    public function __construct(
        private readonly PaymentService $paymentService,
    ) {}

    public function show($orderId)
    {
        $order = Order::where('user_id', Auth::id())
            ->with('payment')
            ->findOrFail($orderId);

        if (! $order->payment) {
            return redirect()->route('checkout')
                ->with('error', 'Pagamento não encontrado.');
        }

        $this->paymentService->refreshProviderStatus($order->payment);
        $this->paymentService->expireIfTimedOut($order->payment->refresh());
        $order->refresh()->load('payment');

        $paymentDetails = $this->paymentService->getPaymentDetails($order->payment);

        return view('payments.show', compact('order', 'paymentDetails'));
    }

    public function callback(Request $request)
    {
        try {
            $payment = $this->paymentService->confirmFromWebhook($request->query());
        } catch (\Throwable $exception) {
            Log::warning('IfThenPay callback rejected', [
                'error' => $exception->getMessage(),
                'payload' => $this->redactedCallbackPayload($request->query()),
            ]);

            return response()->json(['status' => 'invalid'], 400);
        }

        return response()->json([
            'status' => 'ok',
            'payment_id' => $payment->id,
        ]);
    }

    private function redactedCallbackPayload(array $payload): array
    {
        $allowedFields = [
            'key',
            'apk',
            'anti_phishing_key',
            'orderId',
            'oid',
            'id',
            'order_id',
            'amount',
            'val',
            'requestId',
            'tid',
            'transaction_id',
            'reference',
            'ref',
            'pm',
            'payment_method',
            'method',
        ];

        $redacted = [];

        foreach ($allowedFields as $field) {
            if (! array_key_exists($field, $payload)) {
                continue;
            }

            if (in_array($field, ['key', 'apk', 'anti_phishing_key'], true)) {
                $redacted[$field] = '[redacted]';

                continue;
            }

            $value = $payload[$field];
            $redacted[$field] = is_scalar($value)
                ? mb_substr((string) $value, 0, 120)
                : '[non-scalar]';
        }

        return $redacted;
    }
}
