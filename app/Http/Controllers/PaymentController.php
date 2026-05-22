<?php

namespace App\Http\Controllers;

use App\Models\Order;
use App\Services\PaymentService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

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

        if (!$order->payment) {
            return redirect()->route('checkout')
                ->with('error', 'Pagamento não encontrado.');
        }

        $paymentDetails = null;

        if ($order->payment->method === 'mbway') {
            $paymentDetails = $this->paymentService->getManualMbwayDetails();
        } elseif ($order->payment->method === 'bank_transfer') {
            $paymentDetails = $this->paymentService->getManualBankTransferDetails();
        }

        return view('payments.show', compact('order', 'paymentDetails'));
    }

    public function callback(Request $request)
    {
        return response()->json(['status' => 'received']);
    }
}
