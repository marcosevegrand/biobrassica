<?php

namespace App\Http\Controllers;

use App\Models\Order;
use App\Services\PaymentService;
use Illuminate\Support\Facades\Auth;

class OrderController extends Controller
{
    public function __construct(
        private readonly PaymentService $paymentService,
    ) {}

    public function show($orderId)
    {
        $order = Order::where('user_id', Auth::id())
            ->with(['items.product', 'payment'])
            ->findOrFail($orderId);

        if ($order->payment) {
            $this->paymentService->refreshProviderStatus($order->payment);
            $this->paymentService->expireIfTimedOut($order->payment->refresh());
            $order->refresh()->load(['items.product', 'payment']);
        }

        return view('orders.show', compact('order'));
    }

    public function paymentStatus($orderId)
    {
        $order = Order::where('user_id', Auth::id())
            ->with('payment')
            ->findOrFail($orderId);

        if ($order->payment) {
            $this->paymentService->refreshProviderStatus($order->payment);
            $this->paymentService->expireIfTimedOut($order->payment->refresh());
            $order->refresh()->load('payment');
        }

        return view('orders.partials.payment-status', compact('order'));
    }
}
