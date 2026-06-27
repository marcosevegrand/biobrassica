<?php

namespace App\Http\Controllers;

use App\Models\Product;
use App\Services\CartService;
use Illuminate\Http\Request;
use Illuminate\Validation\ValidationException;

class CartController extends Controller
{
    protected CartService $cartService;

    public function __construct(CartService $cartService)
    {
        $this->cartService = $cartService;
    }

    public function count(Request $request)
    {
        $cart = $this->getCart($request);
        $count = $this->cartService->getCount($cart);

        return view('cart.partials.cart-count', compact('count'));
    }

    public function popup(Request $request)
    {
        $cart = $this->getCart($request);
        $total = $this->cartService->getTotal($cart);
        $count = $this->cartService->getCount($cart);

        return view('cart.partials.cart-popup', compact('cart', 'total', 'count'));
    }

    public function detail(Request $request)
    {
        $cart = $this->getCart($request);
        $total = $this->cartService->getTotal($cart);
        $count = $this->cartService->getCount($cart);

        return view('cart.detail', compact('cart', 'total', 'count'));
    }

    public function add(Request $request, $productId)
    {
        $product = Product::where('id', $productId)
            ->where('is_active', true)
            ->where('is_preview', false)
            ->firstOrFail();

        $quantity = max(1, (int) $request->input('quantity', 1));

        $cart = $this->getCart($request);

        try {
            $this->cartService->addItem($cart, $product, $quantity);
        } catch (ValidationException $exception) {
            return $this->cartValidationResponse($request, $exception);
        }

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
        $cart = $this->getCart($request);
        $item = $cart->items()->whereKey($itemId)->firstOrFail();
        $quantity = max(0, (int) $request->input('quantity', 1));

        try {
            $this->cartService->updateItem($item, $quantity);
        } catch (ValidationException $exception) {
            return $this->cartValidationResponse($request, $exception);
        }

        $cart = $cart->refresh()->load('items.product');
        $total = $this->cartService->getTotal($cart);
        $count = $this->cartService->getCount($cart);

        if ($request->hasHeader('HX-Request')) {
            return response()
                ->view('cart.partials.cart-content', compact('cart', 'total', 'count'))
                ->withHeaders([
                    'HX-Trigger-After-Swap' => json_encode([
                        'cartUpdated' => ['count' => $count, 'total' => number_format($total, 2)],
                    ]),
                ]);
        }

        return redirect()->back();
    }

    public function remove(Request $request, $itemId)
    {
        $cart = $this->getCart($request);
        $item = $cart->items()->whereKey($itemId)->firstOrFail();
        $this->cartService->removeItem($item);

        $cart = $cart->refresh()->load('items.product');
        $total = $this->cartService->getTotal($cart);
        $count = $this->cartService->getCount($cart);

        if ($request->hasHeader('HX-Request')) {
            return response()
                ->view('cart.partials.cart-content', compact('cart', 'total', 'count'))
                ->withHeaders([
                    'HX-Trigger-After-Swap' => json_encode([
                        'cartUpdated' => ['count' => $count, 'total' => number_format($total, 2)],
                    ]),
                ]);
        }

        return redirect()->back()->with('success', 'Produto removido do carrinho.');
    }

    protected function getCart(Request $request)
    {
        return $this->cartService->getOrCreateCartForRequest($request);
    }

    private function cartValidationResponse(Request $request, ValidationException $exception)
    {
        $message = collect($exception->errors())->flatten()->first() ?: 'Não foi possível atualizar o carrinho.';

        if ($request->hasHeader('HX-Request')) {
            return response($message, 422)->withHeaders([
                'HX-Trigger' => json_encode([
                    'cartError' => ['message' => $message],
                ]),
            ]);
        }

        return redirect()->back()->with('error', $message);
    }
}
