<?php

namespace App\Services;

use App\Models\Cart;
use App\Models\CartItem;
use App\Models\Product;
use App\Models\ShopSettings;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;
use Illuminate\Validation\ValidationException;

class CartService
{
    private const MAX_PURCHASE_QUANTITY = 99;

    private const GUEST_TOKEN_SESSION_KEY = 'cart.guest_token';

    public function getOrCreateCart(?User $user, ?string $guestToken = null): Cart
    {
        if ($user) {
            $cart = Cart::firstOrCreate(
                ['user_id' => $user->id],
                ['guest_token' => null, 'reserved_until' => null]
            );

            return $cart->load('items.product');
        }

        if (! $guestToken) {
            throw new \InvalidArgumentException('Guest cart token is required when no user is authenticated.');
        }

        $cart = Cart::firstOrCreate(
            ['guest_token' => $guestToken],
            ['user_id' => null, 'reserved_until' => null]
        );

        return $cart->load('items.product');
    }

    public function getOrCreateCartForRequest(Request $request): Cart
    {
        /** @var User|null $user */
        $user = $request->user();

        if ($user) {
            return $this->getOrCreateCart($user);
        }

        return $this->getOrCreateCart(null, $this->guestToken($request));
    }

    public function findCartForRequest(Request $request): ?Cart
    {
        /** @var User|null $user */
        $user = $request->user();

        if ($user) {
            return Cart::where('user_id', $user->id)->with('items.product')->first();
        }

        $guestToken = $request->session()->get(self::GUEST_TOKEN_SESSION_KEY);

        if (! is_string($guestToken) || $guestToken === '') {
            return null;
        }

        return Cart::where('guest_token', $guestToken)->with('items.product')->first();
    }

    public function mergeGuestCartIntoUserCart(Request $request, User $user): array
    {
        $guestToken = $request->session()->get(self::GUEST_TOKEN_SESSION_KEY);

        if (! is_string($guestToken) || $guestToken === '') {
            return [];
        }

        $warnings = DB::transaction(function () use ($guestToken, $user): array {
            $guestCart = Cart::where('guest_token', $guestToken)
                ->whereNull('user_id')
                ->with('items.product')
                ->lockForUpdate()
                ->first();

            if (! $guestCart) {
                return [];
            }

            $userCart = Cart::firstOrCreate(
                ['user_id' => $user->id],
                ['guest_token' => null, 'reserved_until' => null]
            );

            $warnings = [];

            foreach ($guestCart->items as $guestItem) {
                $product = Product::whereKey($guestItem->product_id)->lockForUpdate()->first();

                if (! $product || ! $product->is_active || $product->is_preview || ! $this->productHasFulfillment($product) || (int) $product->stock <= 0) {
                    $warnings[] = 'Um produto do carrinho de convidado já não está disponível.';

                    continue;
                }

                $userItem = $userCart->items()
                    ->where('product_id', $product->id)
                    ->lockForUpdate()
                    ->first();

                $requestedQuantity = (int) ($userItem?->quantity ?? 0) + (int) $guestItem->quantity;
                $quantity = min($requestedQuantity, self::MAX_PURCHASE_QUANTITY, (int) $product->stock);

                if ($quantity < $requestedQuantity) {
                    $warnings[] = "A quantidade de {$product->name} foi ajustada ao stock disponível.";
                }

                if ($quantity <= 0) {
                    continue;
                }

                if ($userItem) {
                    $userItem->quantity = $quantity;
                    $userItem->reserved_quantity = 0;
                    $userItem->save();
                } else {
                    $userCart->items()->create([
                        'product_id' => $product->id,
                        'quantity' => $quantity,
                        'reserved_quantity' => 0,
                    ]);
                }
            }

            $guestCart->items()->delete();
            $guestCart->delete();

            return array_values(array_unique($warnings));
        });

        $request->session()->forget(self::GUEST_TOKEN_SESSION_KEY);

        return $warnings;
    }

    public function addItem(Cart $cart, Product $product, int $quantity): CartItem
    {
        return DB::transaction(function () use ($cart, $product, $quantity): CartItem {
            $lockedCart = Cart::whereKey($cart->id)->lockForUpdate()->firstOrFail();
            $lockedProduct = Product::whereKey($product->id)->lockForUpdate()->firstOrFail();

            $this->ensureProductCanBePurchased($lockedProduct);

            $item = $lockedCart->items()
                ->where('product_id', $lockedProduct->id)
                ->lockForUpdate()
                ->first();

            $desiredQuantity = ($item?->quantity ?? 0) + $quantity;

            $this->ensureQuantityIsAvailable($lockedProduct, $desiredQuantity);

            if ($item) {
                $item->quantity = min($desiredQuantity, self::MAX_PURCHASE_QUANTITY);
                $item->save();
            } else {
                $item = $lockedCart->items()->create([
                    'product_id' => $lockedProduct->id,
                    'quantity' => min($quantity, self::MAX_PURCHASE_QUANTITY),
                    'reserved_quantity' => 0,
                ]);
            }

            return $item->load('product');
        });
    }

    public function updateItem(CartItem $item, int $quantity): CartItem
    {
        return DB::transaction(function () use ($item, $quantity): CartItem {
            $lockedItem = CartItem::whereKey($item->id)->lockForUpdate()->firstOrFail();

            if ($quantity <= 0) {
                $lockedItem->delete();

                return $lockedItem;
            }

            $product = Product::whereKey($lockedItem->product_id)->lockForUpdate()->first();

            $this->ensureProductCanBePurchased($product);
            $this->ensureQuantityIsAvailable($product, $quantity);

            $lockedItem->quantity = min($quantity, self::MAX_PURCHASE_QUANTITY);
            $lockedItem->save();

            return $lockedItem->load('product');
        });
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
                $this->ensureProductCanBePurchased($item->product);
                $this->ensureQuantityIsAvailable($item->product, $item->quantity);

                $item->reserved_quantity = $item->quantity;
                $item->save();

                $item->product->stock = max(0, ((int) $item->product->stock) - $item->quantity);
                $item->product->save();
            }
        }

        $minutes = ShopSettings::current()->checkout_reservation_minutes ?: 30;
        $cart->reserved_until = now()->addMinutes((int) $minutes);
        $cart->save();
    }

    public function releaseStock(Cart $cart): void
    {
        DB::transaction(function () use ($cart): void {
            $lockedCart = Cart::whereKey($cart->id)->lockForUpdate()->first();

            if (! $lockedCart || $lockedCart->reserved_until === null) {
                return;
            }

            $lockedCart->load(['items' => fn ($query) => $query->lockForUpdate()]);

            foreach ($lockedCart->items as $item) {
                if ((int) $item->reserved_quantity <= 0) {
                    continue;
                }

                $product = Product::whereKey($item->product_id)->lockForUpdate()->first();

                if ($product) {
                    $product->stock = (int) $product->stock + (int) $item->reserved_quantity;
                    $product->save();
                }

                $item->reserved_quantity = 0;
                $item->save();
            }

            $lockedCart->reserved_until = null;
            $lockedCart->save();
        });
    }

    public function clearCart(Cart $cart): void
    {
        $cart->items()->delete();
        $cart->reserved_until = null;
        $cart->save();
    }

    private function ensureQuantityIsAvailable(?Product $product, int $quantity): void
    {
        if (! $product) {
            throw ValidationException::withMessages([
                'product' => 'Este produto já não está disponível.',
            ]);
        }

        if ($quantity > self::MAX_PURCHASE_QUANTITY) {
            throw ValidationException::withMessages([
                'quantity' => 'A quantidade máxima por produto é '.self::MAX_PURCHASE_QUANTITY.'.',
            ]);
        }

        if ((int) $product->stock < $quantity) {
            throw ValidationException::withMessages([
                'quantity' => "Só existem {$product->stock} unidades disponíveis de {$product->name}.",
            ]);
        }
    }

    private function ensureProductCanBePurchased(?Product $product): void
    {
        if (! $product || ! $product->is_active || $product->is_preview) {
            throw ValidationException::withMessages([
                'product' => 'Este produto não está disponível para compra.',
            ]);
        }

        if (! $this->productHasFulfillment($product)) {
            throw ValidationException::withMessages([
                'product' => 'Este produto ainda não tem um método de entrega disponível.',
            ]);
        }
    }

    private function productHasFulfillment(Product $product): bool
    {
        return (bool) $product->allow_shipping || (bool) $product->allow_pickup;
    }

    private function guestToken(Request $request): string
    {
        $token = $request->session()->get(self::GUEST_TOKEN_SESSION_KEY);

        if (! is_string($token) || $token === '') {
            $token = (string) Str::uuid();
            $request->session()->put(self::GUEST_TOKEN_SESSION_KEY, $token);
        }

        return $token;
    }
}
