<?php

namespace App\Services;

use App\Models\Cart;
use App\Models\CartItem;
use App\Models\Product;
use App\Models\User;
use Illuminate\Validation\ValidationException;

class CartService
{
    private const MAX_PURCHASE_QUANTITY = 99;

    public function getOrCreateCart(User $user): Cart
    {
        $cart = Cart::firstOrCreate(
            ['user_id' => $user->id],
            ['reserved_until' => null]
        );

        return $cart->load('items.product');
    }

    public function addItem(Cart $cart, Product $product, int $quantity): CartItem
    {
        if (!$product->is_active) {
            throw ValidationException::withMessages([
                'product' => 'Este produto não está disponível.',
            ]);
        }

        $item = $cart->items()->where('product_id', $product->id)->first();
        $desiredQuantity = ($item?->quantity ?? 0) + $quantity;

        $this->ensureQuantityIsAvailable($product, $desiredQuantity);

        if ($item) {
            $item->quantity = min($desiredQuantity, self::MAX_PURCHASE_QUANTITY);
            $item->save();
        } else {
            $item = $cart->items()->create([
                'product_id' => $product->id,
                'quantity' => min($quantity, self::MAX_PURCHASE_QUANTITY),
                'reserved_quantity' => 0,
            ]);
        }

        return $item->load('product');
    }

    public function updateItem(CartItem $item, int $quantity): CartItem
    {
        if ($quantity <= 0) {
            $item->delete();

            return $item;
        }

        $this->ensureQuantityIsAvailable($item->product, $quantity);

        $item->quantity = min($quantity, self::MAX_PURCHASE_QUANTITY);
        $item->save();

        return $item->load('product');
    }

    public function removeItem(CartItem $item): void
    {
        $item->delete();
    }

    public function getTotal(Cart $cart): float
    {
        $cart->loadMissing('items.product');

        return (float) $cart->items->sum(function ($item) {
            return $item->quantity * (float) ($item->product->price ?? 0);
        });
    }

    public function getCount(Cart $cart): int
    {
        return (int) $cart->items()->sum('quantity');
    }

    public function reserveStock(Cart $cart): void
    {
        $cart->loadMissing('items.product');

        foreach ($cart->items as $item) {
            if ($item->product) {
                $this->ensureQuantityIsAvailable($item->product, $item->quantity);

                $item->reserved_quantity = $item->quantity;
                $item->save();

                $item->product->stock = max(0, ((int) $item->product->stock) - $item->quantity);
                $item->product->save();
            }
        }

        $cart->reserved_until = now()->addMinutes(30);
        $cart->save();
    }

    public function releaseStock(Cart $cart): void
    {
        $cart->loadMissing('items.product');

        foreach ($cart->items as $item) {
            if ($item->product) {
                $item->product->stock += $item->reserved_quantity;
                $item->product->save();

                $item->reserved_quantity = 0;
                $item->save();
            }
        }

        $cart->reserved_until = null;
        $cart->save();
    }

    public function clearCart(Cart $cart): void
    {
        $cart->items()->delete();
        $cart->reserved_until = null;
        $cart->save();
    }

    private function ensureQuantityIsAvailable(?Product $product, int $quantity): void
    {
        if (!$product) {
            throw ValidationException::withMessages([
                'product' => 'Este produto já não está disponível.',
            ]);
        }

        if ($quantity > self::MAX_PURCHASE_QUANTITY) {
            throw ValidationException::withMessages([
                'quantity' => 'A quantidade máxima por produto é ' . self::MAX_PURCHASE_QUANTITY . '.',
            ]);
        }

        if ((int) $product->stock < $quantity) {
            throw ValidationException::withMessages([
                'quantity' => "Só existem {$product->stock} unidades disponíveis de {$product->name}.",
            ]);
        }
    }
}
