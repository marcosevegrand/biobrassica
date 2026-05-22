<?php

namespace App\Http\Controllers;

use App\Models\Order;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class OrderController extends Controller
{
    public function show($orderId)
    {
        $order = Order::where('user_id', Auth::id())
            ->with(['items.product', 'payment'])
            ->findOrFail($orderId);

        return view('orders.show', compact('order'));
    }

    public function paymentStatus($orderId)
    {
        $order = Order::where('user_id', Auth::id())
            ->with('payment')
            ->findOrFail($orderId);

        return view('orders.partials.payment-status', compact('order'));
    }
}
