<?php

namespace App\Http\Controllers;

use App\Http\Requests\CheckoutRequest;
use App\Models\Location;
use App\Models\Order;
use App\Models\OrderItem;
use App\Models\Product;
use App\Models\ShopSettings;
use App\Services\CartService;
use App\Services\PaymentService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

class CheckoutController extends Controller
{
    public function __construct(
        private readonly CartService $cartService,
        private readonly PaymentService $paymentService,
    ) {}

    public function show()
    {
        $user = Auth::user();
        $cart = $this->cartService->getOrCreateCart($user);
        $total = $this->cartService->getTotal($cart);
        $count = $this->cartService->getCount($cart);

        $settings = $this->settings();
        $minOrderTotal = $settings->min_order_total ?? 0;

        $locations = Location::where('is_active', true)
            ->orderBy('name')
            ->get();

        $addresses = $user->addresses()->orderBy('is_default', 'desc')->get();

        return view('checkout.checkout', compact(
            'cart', 'total', 'count', 'user', 'locations', 'addresses',
            'settings', 'minOrderTotal'
        ));
    }

    public function store(CheckoutRequest $request)
    {
        $user = Auth::user();
        $cart = $this->cartService->getOrCreateCart($user);
        $total = $this->cartService->getTotal($cart);

        $settings = $this->settings();
        $minOrderTotal = $settings->min_order_total ?? 0;

        if (!$settings->is_shop_active) {
            return redirect()->route('cart.detail')
                ->with('error', 'A loja está temporariamente indisponível para encomendas.');
        }

        if ($cart->items->isEmpty()) {
            return redirect()->route('cart.detail')
                ->with('error', 'O carrinho está vazio.');
        }

        if (!$this->paymentMethodIsEnabled($settings, $request->payment_method)) {
            return redirect()->back()
                ->with('error', 'O método de pagamento selecionado não está disponível.')
                ->withInput();
        }

        if ($message = $this->cartFulfillmentError($cart, $request->fulfillment_method, $request->pickup_location)) {
            return redirect()->back()->with('error', $message)->withInput();
        }

        if ($total < $minOrderTotal) {
            return redirect()->back()
                ->with('error', "O valor mínimo de encomenda é &euro;{$minOrderTotal}.")
                ->withInput();
        }

        $order = DB::transaction(function () use ($request, $user, $cart, $total) {
            $cart->load('items.product');

            foreach ($cart->items as $cartItem) {
                $lockedProduct = Product::whereKey($cartItem->product_id)->lockForUpdate()->first();
                if ($lockedProduct) {
                    $cartItem->setRelation('product', $lockedProduct);
                }
            }

            $this->cartService->reserveStock($cart);

            $order = Order::create([
                'user_id' => $user->id,
                'access_token' => Str::random(32),
                'name' => $request->name,
                'email' => $request->email,
                'phone' => $request->phone,
                'nif' => $request->nif,
                'status' => 'pending',
                'payment_state' => 'pending',
                'fulfillment_method' => $request->fulfillment_method,
                'pickup_location' => $request->fulfillment_method === 'pickup'
                    ? $request->pickup_location
                    : null,
                'shipping_address_line1' => $request->fulfillment_method === 'shipping'
                    ? $request->shipping_address_line1
                    : null,
                'shipping_address_line2' => $request->fulfillment_method === 'shipping'
                    ? $request->shipping_address_line2
                    : null,
                'shipping_city' => $request->fulfillment_method === 'shipping'
                    ? $request->shipping_city
                    : null,
                'shipping_postal_code' => $request->fulfillment_method === 'shipping'
                    ? $request->shipping_postal_code
                    : null,
                'language' => app()->getLocale(),
                'subtotal' => $total,
                'total' => $total,
                'notes' => $request->notes,
            ]);

            foreach ($cart->items as $cartItem) {
                $product = $cartItem->product;
                OrderItem::create([
                    'order_id' => $order->id,
                    'product_id' => $product->id,
                    'product_name' => $product->name,
                    'price' => $product->price,
                    'quantity' => $cartItem->quantity,
                ]);
            }

            $this->paymentService->createPayment($order, $request->payment_method);
            $this->cartService->clearCart($cart);

            return $order;
        });

        return redirect()->route('payment.show', ['order' => $order->id]);
    }

    public function paymentSelect($orderId)
    {
        $order = Order::where('user_id', Auth::id())->findOrFail($orderId);

        return view('orders.payment-select', compact('order'));
    }

    public function confirm($orderId)
    {
        $order = Order::where('user_id', Auth::id())->findOrFail($orderId);

        return view('orders.complete', compact('order'));
    }

    public function discard($orderId)
    {
        $order = Order::where('user_id', Auth::id())
            ->with(['payment', 'items.product'])
            ->findOrFail($orderId);

        if (!in_array($order->status, ['pending'])) {
            return redirect()->back()
                ->with('error', 'Esta encomenda já não pode ser cancelada.');
        }

        foreach ($order->items as $orderItem) {
            $product = $orderItem->product;
            if ($product) {
                $product->stock = (int) $product->stock + $orderItem->quantity;
                $product->save();
            }
        }

        $order->status = 'cancelled';
        $order->save();

        if ($order->payment) {
            $order->payment->status = 'cancelled';
            $order->payment->save();
        }

        return redirect()->route('checkout')->with('error', 'Encomenda cancelada.');
    }

    private function settings(): ShopSettings
    {
        return ShopSettings::firstOrCreate(
            ['id' => 1],
            [
                'is_shop_active' => true,
                'is_shop_brevemente' => false,
                'min_order_total' => 0,
                'mbway_enabled' => true,
                'bank_transfer_enabled' => true,
                'payment_timeout_minutes' => 30,
                'checkout_reservation_minutes' => 30,
            ]
        );
    }

    private function paymentMethodIsEnabled(ShopSettings $settings, string $method): bool
    {
        return match ($method) {
            'mbway' => (bool) $settings->mbway_enabled,
            'bank_transfer' => (bool) $settings->bank_transfer_enabled,
            default => false,
        };
    }

    private function cartFulfillmentError($cart, string $method, ?int $pickupLocationId): ?string
    {
        $cart->loadMissing('items.product.pickupLocations');

        foreach ($cart->items as $item) {
            $product = $item->product;

            if (!$product || !$product->is_active) {
                return 'Um dos produtos do carrinho já não está disponível.';
            }

            if ((int) $product->stock < (int) $item->quantity) {
                return "Só existem {$product->stock} unidades disponíveis de {$product->name}.";
            }

            if ($method === 'shipping' && !$product->allow_shipping) {
                return "{$product->name} apenas está disponível para levantamento.";
            }

            if ($method === 'pickup' && !$product->allow_pickup) {
                return "{$product->name} apenas está disponível para envio.";
            }

            if ($method === 'pickup' && $product->pickupLocations->isNotEmpty() && !$product->pickupLocations->contains('id', (int) $pickupLocationId)) {
                return "{$product->name} não está disponível no local de levantamento selecionado.";
            }
        }

        return null;
    }
}
