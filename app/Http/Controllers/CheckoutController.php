<?php

namespace App\Http\Controllers;

use App\Http\Requests\CheckoutRequest;
use App\Models\Cart;
use App\Models\Location;
use App\Models\Order;
use App\Models\OrderItem;
use App\Models\Payment;
use App\Models\Product;
use App\Models\ShopSettings;
use App\Services\CartService;
use App\Services\PaymentService;
use App\Services\ShippingService;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\ValidationException;

class CheckoutController extends Controller
{
    public function __construct(
        private readonly CartService $cartService,
        private readonly PaymentService $paymentService,
        private readonly ShippingService $shippingService,
    ) {}

    public function show()
    {
        $user = Auth::user();
        $settings = $this->settings();

        // Block checkout in Inativa mode (is_shop_active=false, is_shop_brevemente=false).
        // Brevemente mode is already handled by ShopBrevementeMiddleware which blocks all pages.
        if (! $settings->is_shop_active && ! $settings->is_shop_brevemente) {
            return redirect()->route('cart.detail')
                ->with('error', 'A loja está temporariamente indisponível para novas encomendas. Pode continuar a navegar e a adicionar produtos ao carrinho.');
        }

        // Block checkout if user already has a pending order with pending payment.
        $pendingOrder = Order::where('user_id', $user->id)
            ->where('status', Order::STATUS_PENDING)
            ->where('payment_state', Order::PAYMENT_PENDING)
            ->first();

        if ($pendingOrder) {
            return redirect()->route('payment.show', ['order' => $pendingOrder->id])
                ->with('error', 'Já tem uma encomenda pendente por pagar. Conclua ou cancele essa encomenda antes de iniciar uma nova.');
        }

        $cart = $this->cartService->getOrCreateCart($user);

        // Release expired reservation and reload cart if needed
        $reservationWarning = $this->releaseExpiredReservationAndCheckAvailability($cart);

        $subtotal = $this->cartService->getTotal($cart);
        $cart->loadMissing('items.product');
        $pickupShippingCost = $this->shippingService->calculate($subtotal, 'pickup', $settings);
        $shippingCost = $this->shippingService->calculate($subtotal, 'shipping', $settings);
        $canPickup = $this->cartSupportsFulfillment($cart, 'pickup');
        $canShipping = $this->cartSupportsFulfillment($cart, 'shipping');
        $defaultFulfillmentMethod = $canPickup ? 'pickup' : ($canShipping ? 'shipping' : 'pickup');
        $selectedFulfillmentMethod = old('fulfillment_method', $defaultFulfillmentMethod);
        $total = $subtotal + ($selectedFulfillmentMethod === 'shipping' ? $shippingCost : $pickupShippingCost);
        $count = $this->cartService->getCount($cart);

        $minOrderTotal = $settings->min_order_total ?? 0;

        $locations = Location::where('is_active', true)
            ->orderBy('name')
            ->get();

        $addresses = $user->addresses()->orderBy('is_default', 'desc')->get();
        $paymentMethods = $this->availablePaymentMethods($settings);

        return view('checkout.checkout', compact(
            'cart', 'subtotal', 'pickupShippingCost', 'shippingCost', 'total', 'count', 'user', 'locations', 'addresses',
            'settings', 'minOrderTotal', 'paymentMethods', 'canPickup', 'canShipping', 'selectedFulfillmentMethod'
        ))->with('warning', $reservationWarning);
    }

    public function store(CheckoutRequest $request)
    {
        $user = Auth::user();
        $settings = $this->settings();

        // Block checkout in Inativa mode (is_shop_active=false, is_shop_brevemente=false).
        if (! $settings->is_shop_active && ! $settings->is_shop_brevemente) {
            return redirect()->route('cart.detail')
                ->with('error', 'A loja está temporariamente indisponível para novas encomendas. Pode continuar a navegar e a adicionar produtos ao carrinho.');
        }

        // Block checkout if user already has a pending order with pending payment.
        $pendingOrder = Order::where('user_id', $user->id)
            ->where('status', Order::STATUS_PENDING)
            ->where('payment_state', Order::PAYMENT_PENDING)
            ->first();

        if ($pendingOrder) {
            return redirect()->route('payment.show', ['order' => $pendingOrder->id])
                ->with('error', 'Já tem uma encomenda pendente por pagar. Conclua ou cancele essa encomenda antes de iniciar uma nova.');
        }

        $cart = $this->cartService->getOrCreateCart($user);
        $minOrderTotal = $settings->min_order_total ?? 0;

        if (! $this->paymentMethodIsEnabled($settings, $request->payment_method)) {
            return redirect()->back()
                ->with('error', 'O método de pagamento selecionado não está disponível ou não está configurado.')
                ->withInput();
        }

        $order = DB::transaction(function () use ($request, $user, $cart, $settings, $minOrderTotal) {
            $cart = Cart::query()
                ->where('user_id', $user->id)
                ->whereKey($cart->id)
                ->lockForUpdate()
                ->firstOrFail();

            $cart->load(['items' => fn ($query) => $query->lockForUpdate()]);

            if ($cart->items->isEmpty()) {
                throw ValidationException::withMessages([
                    'cart' => 'O carrinho está vazio.',
                ]);
            }

            foreach ($cart->items as $cartItem) {
                $lockedProduct = Product::with('pickupLocations')
                    ->whereKey($cartItem->product_id)
                    ->lockForUpdate()
                    ->first();

                if ($lockedProduct) {
                    $cartItem->setRelation('product', $lockedProduct);
                }
            }

            if (! $this->paymentMethodIsEnabled($settings, $request->payment_method)) {
                throw ValidationException::withMessages([
                    'payment_method' => 'O método de pagamento selecionado não está disponível ou não está configurado.',
                ]);
            }

            if ($message = $this->cartFulfillmentError($cart, $request->fulfillment_method, $request->pickup_location)) {
                throw ValidationException::withMessages([
                    'cart' => $message,
                ]);
            }

            $subtotal = $this->cartService->getTotal($cart);

            if ($subtotal < $minOrderTotal) {
                throw ValidationException::withMessages([
                    'cart' => "O valor mínimo de encomenda é &euro;{$minOrderTotal}.",
                ]);
            }

            $shippingCost = $this->shippingService->calculate((float) $subtotal, $request->fulfillment_method, $settings);
            $total = round((float) $subtotal + $shippingCost, 2);

            $this->cartService->reserveStock($cart);

            $order = Order::create([
                'user_id' => $user->id,
                'name' => $request->name,
                'email' => $request->email,
                'phone' => $request->phone,
                'nif' => $request->nif,
                'status' => Order::STATUS_PENDING,
                'payment_state' => Order::PAYMENT_PENDING,
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
                'subtotal' => $subtotal,
                'shipping_cost' => $shippingCost,
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

            $this->cartService->clearCart($cart);

            return $order;
        });

        try {
            $this->paymentService->createPayment($order, $request->payment_method);
        } catch (\Throwable $exception) {
            $message = 'Não foi possível preparar o pagamento. A sua encomenda foi cancelada e o carrinho foi reposto para tentar novamente.';

            $this->cancelOrderAfterPaymentFailure($order, $message);
            $this->restoreCartFromOrder($order, $user->id);

            report($exception);

            return redirect()->route('checkout')
                ->with('error', $message);
        }

        return redirect()->route('payment.show', ['order' => $order->id]);
    }

    public function confirm($orderId)
    {
        $order = Order::where('user_id', Auth::id())->findOrFail($orderId);

        return $order->isPaid()
            ? view('orders.complete', compact('order'))
            : redirect()->route('payment.show', ['order' => $order->id]);
    }

    public function discard($orderId)
    {
        $order = Order::where('user_id', Auth::id())
            ->with(['payment', 'items.product'])
            ->findOrFail($orderId);

        if (! in_array($order->status, [Order::STATUS_PENDING], true)) {
            return redirect()->back()
                ->with('error', 'Esta encomenda já não pode ser cancelada.');
        }

        if ($order->payment_state === Order::PAYMENT_CONFIRMED || $order->payment?->status === Payment::STATUS_CONFIRMED) {
            return redirect()->back()
                ->with('error', 'Esta encomenda já foi paga e não pode ser cancelada automaticamente. Contacte a equipa Biobrassica.');
        }

        if ($order->payment && $order->payment->status === Payment::STATUS_PENDING) {
            $this->paymentService->rejectPayment($order->payment, 'Encomenda cancelada pelo cliente.');
        } else {
            $order->status = Order::STATUS_CANCELLED;
            $order->payment_state = Order::PAYMENT_CANCELLED;
            $order->save();
        }

        return redirect()->route('checkout')->with('error', 'Encomenda cancelada.');
    }

    private function settings(): ShopSettings
    {
        return ShopSettings::current();
    }

    private function paymentMethodIsEnabled(ShopSettings $settings, string $method): bool
    {
        return match ($method) {
            'mbway' => (bool) $settings->mbway_enabled && $this->paymentService->methodIsConfigured('mbway'),
            'multibanco' => (bool) $settings->bank_transfer_enabled && $this->paymentService->methodIsConfigured('multibanco'),
            default => false,
        };
    }

    private function availablePaymentMethods(ShopSettings $settings): array
    {
        return [
            'mbway' => [
                'enabled' => $this->paymentMethodIsEnabled($settings, 'mbway'),
                'label' => 'MB WAY',
                'description' => 'Receba uma notificação na app MB WAY e confirme o pagamento em poucos minutos.',
            ],
            'multibanco' => [
                'enabled' => $this->paymentMethodIsEnabled($settings, 'multibanco'),
                'label' => 'Multibanco',
                'description' => 'Pague por entidade e referência numa caixa Multibanco, homebanking ou app bancária.',
            ],
        ];
    }

    private function cartFulfillmentError($cart, string $method, ?int $pickupLocationId): ?string
    {
        $cart->loadMissing('items.product.pickupLocations');

        foreach ($cart->items as $item) {
            $product = $item->product;

            if (! $product || ! $product->is_active || $product->is_preview) {
                return 'Um dos produtos do carrinho já não está disponível.';
            }

            if ((int) $product->stock < (int) $item->quantity) {
                return "Só existem {$product->stock} unidades disponíveis de {$product->name}.";
            }

            if (! $product->allow_shipping && ! $product->allow_pickup) {
                return "{$product->name} ainda não tem um método de entrega disponível.";
            }

            if ($method === 'shipping' && ! $product->allow_shipping) {
                return "{$product->name} apenas está disponível para levantamento.";
            }

            if ($method === 'pickup' && ! $product->allow_pickup) {
                return "{$product->name} apenas está disponível para envio.";
            }

            if ($method === 'pickup' && $product->pickupLocations->isNotEmpty() && ! $product->pickupLocations->contains('id', (int) $pickupLocationId)) {
                return "{$product->name} não está disponível no local de levantamento selecionado.";
            }
        }

        return null;
    }

    private function cancelOrderAfterPaymentFailure(Order $order, string $reason): void
    {
        $order->loadMissing('payment');

        if ($order->payment?->status === Payment::STATUS_PENDING) {
            try {
                $this->paymentService->rejectPayment($order->payment, $reason);
            } catch (\RuntimeException) {
                // The payment may already have been reconciled by a callback.
            }

            return;
        }

        DB::transaction(function () use ($order, $reason): void {
            $lockedOrder = Order::with('items.product')
                ->whereKey($order->id)
                ->lockForUpdate()
                ->first();

            if (! $lockedOrder || $lockedOrder->payment_state !== Order::PAYMENT_PENDING) {
                return;
            }

            foreach ($lockedOrder->items as $item) {
                $product = $item->product()->lockForUpdate()->first();

                if ($product) {
                    $product->stock = (int) $product->stock + (int) $item->quantity;
                    $product->save();
                }
            }

            $lockedOrder->payment_state = Order::PAYMENT_CANCELLED;
            $lockedOrder->status = Order::STATUS_CANCELLED;
            $lockedOrder->notes = trim(implode("\n", array_filter([$lockedOrder->notes, $reason])));
            $lockedOrder->save();
        });
    }

    private function cartSupportsFulfillment(Cart $cart, string $method): bool
    {
        if ($cart->items->isEmpty()) {
            return false;
        }

        return $cart->items->every(function ($item) use ($method): bool {
            $product = $item->product;

            if (! $product || ! $product->is_active || $product->is_preview || (int) $product->stock < (int) $item->quantity) {
                return false;
            }

            return $method === 'shipping'
                ? (bool) $product->allow_shipping
                : (bool) $product->allow_pickup;
        });
    }

    /**
     * Release expired reservation stock and check current product availability.
     * Returns a warning message if items became unavailable, or null.
     */
    private function releaseExpiredReservationAndCheckAvailability(Cart $cart): ?string
    {
        if ($cart->reserved_until && $cart->reserved_until->isPast()) {
            $this->cartService->releaseStock($cart);

            // Reload cart from DB after stock release.
            $cart->refresh();
            $cart->load('items.product');
        }

        // Check each item's current availability; collect warnings.
        $warnings = [];

        foreach ($cart->items as $item) {
            $product = $item->product;

            if (! $product || ! $product->is_active || $product->is_preview) {
                $productName = $product?->name ?? 'Um produto';
                $warnings[] = "{$productName} já não está disponível para compra.";
            } elseif (! $product->allow_shipping && ! $product->allow_pickup) {
                $warnings[] = "{$product->name} ainda não tem um método de entrega disponível.";
            } elseif ((int) $product->stock < (int) $item->quantity) {
                $warnings[] = "Apenas {$product->stock} unidade(s) disponíveis de {$product->name}. O stock atual é insuficiente para a quantidade no carrinho. Por favor, atualize as quantidades antes de continuar.";
            }
        }

        return $warnings !== [] ? implode(' ', $warnings) : null;
    }

    private function restoreCartFromOrder(Order $order, int $userId): void
    {
        DB::transaction(function () use ($order, $userId): void {
            $cart = Cart::firstOrCreate(['user_id' => $userId], ['guest_token' => null, 'reserved_until' => null]);
            $cart = Cart::whereKey($cart->id)->lockForUpdate()->firstOrFail();

            $order->loadMissing('items.product');

            foreach ($order->items as $orderItem) {
                if (! $orderItem->product_id) {
                    continue;
                }

                $product = Product::whereKey($orderItem->product_id)->lockForUpdate()->first();

                if (! $product || ! $product->is_active || $product->is_preview || (! $product->allow_shipping && ! $product->allow_pickup)) {
                    continue;
                }

                $cartItem = $cart->items()->where('product_id', $product->id)->lockForUpdate()->first();
                $quantity = min(99, (int) $orderItem->quantity + (int) ($cartItem?->quantity ?? 0), max(0, (int) $product->stock));

                if ($quantity <= 0) {
                    continue;
                }

                if ($cartItem) {
                    $cartItem->quantity = $quantity;
                    $cartItem->reserved_quantity = 0;
                    $cartItem->save();
                } else {
                    $cart->items()->create([
                        'product_id' => $product->id,
                        'quantity' => $quantity,
                        'reserved_quantity' => 0,
                    ]);
                }
            }

            $cart->reserved_until = null;
            $cart->save();
        });
    }
}
