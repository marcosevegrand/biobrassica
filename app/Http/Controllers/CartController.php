<?php

namespace App\Http\Controllers;

use App\Models\CartItem;
use App\Models\Product;
use App\Services\CartService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class CartController extends Controller
{
    protected CartService $cartService;

    public function __construct(CartService $cartService)
    {
        $this->cartService = $cartService;
    }

    public function count()
    {
        $cart = $this->getCart();
        $count = $this->cartService->getCount($cart);

        return view('cart.partials.cart-count', compact('count'));
    }

    public function popup()
    {
        $cart = $this->getCart();
        $total = $this->cartService->getTotal($cart);
        $count = $this->cartService->getCount($cart);

        return view('cart.partials.cart-popup', compact('cart', 'total', 'count'));
    }

    public function detail()
    {
        $cart = $this->getCart();
        $total = $this->cartService->getTotal($cart);
        $count = $this->cartService->getCount($cart);

        return view('cart.detail', compact('cart', 'total', 'count'));
    }

    public function add(Request $request, $productId)
    {
        $product = Product::where('id', $productId)
            ->where('is_active', true)
            ->firstOrFail();

        $quantity = max(1, (int) $request->input('quantity', 1));

        $cart = $this->getCart();
        $this->cartService->addItem($cart, $product, $quantity);

        $cart->load('items.product');
        $total = $this->cartService->getTotal($cart);
        $count = $this->cartService->getCount($cart);

        if ($request->hasHeader('HX-Request')) {
            return response()
                ->view('cart.partials.cart-popup', compact('cart', 'total', 'count'))
                ->withHeaders([
                    'HX-Trigger-After-Swap' => json_encode([
                        'cartUpdated' => ['count' => $count, 'total' => number_format($total, 2)],
                    ]),
                ]);
        }

        return redirect()->back()->with('success', 'Produto adicionado ao carrinho.');
    }

    public function update(Request $request, $itemId)
    {
        $item = CartItem::whereHas('cart', fn ($query) => $query->where('user_id', Auth::id()))->findOrFail($itemId);
        $quantity = max(0, (int) $request->input('quantity', 1));

        $this->cartService->updateItem($item, $quantity);

        $cart = $item->cart()->with('items.product')->first();
        $total = $this->cartService->getTotal($cart);
        $count = $this->cartService->getCount($cart);

        if ($request->hasHeader('HX-Request')) {
            if ($quantity <= 0) {
                return response()
                    ->view('cart.partials.cart-popup', compact('cart', 'total', 'count'))
                    ->withHeaders([
                        'HX-Trigger-After-Swap' => json_encode([
                            'cartUpdated' => ['count' => $count, 'total' => number_format($total, 2)],
                        ]),
                    ]);
            }

            return response()
                ->view('cart.partials.cart-summary', compact('cart', 'total', 'count'))
                ->withHeaders([
                    'HX-Trigger-After-Swap' => json_encode([
                        'cartUpdated' => ['count' => $count, 'total' => number_format($total, 2)],
                    ]),
                ]);
        }

        return redirect()->back();
    }

    public function remove($itemId)
    {
        $item = CartItem::whereHas('cart', fn ($query) => $query->where('user_id', Auth::id()))->findOrFail($itemId);
        $cart = $item->cart;
        $this->cartService->removeItem($item);

        $cart->load('items.product');
        $total = $this->cartService->getTotal($cart);
        $count = $this->cartService->getCount($cart);

        if (request()->hasHeader('HX-Request')) {
            return response()
                ->view('cart.partials.cart-popup', compact('cart', 'total', 'count'))
                ->withHeaders([
                    'HX-Trigger-After-Swap' => json_encode([
                        'cartUpdated' => ['count' => $count, 'total' => number_format($total, 2)],
                    ]),
                ]);
        }

        return redirect()->back()->with('success', 'Produto removido do carrinho.');
    }

    protected function getCart()
    {
        $user = Auth::user();

        return $this->cartService->getOrCreateCart($user);
    }
}
