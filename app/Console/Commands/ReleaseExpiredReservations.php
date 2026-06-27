<?php

namespace App\Console\Commands;

use App\Models\Cart;
use App\Services\CartService;
use Illuminate\Console\Command;

class ReleaseExpiredReservations extends Command
{
    protected $signature = 'cart:release-expired-reservations';

    protected $description = 'Release product stock reserved by abandoned checkout sessions.';

    public function handle(CartService $cartService): int
    {
        $count = 0;

        Cart::query()
            ->whereNotNull('reserved_until')
            ->where('reserved_until', '<=', now())
            ->with('items.product')
            ->chunkById(100, function ($carts) use ($cartService, &$count): void {
                foreach ($carts as $cart) {
                    $cartService->releaseStock($cart);
                    $count++;
                }
            });

        $this->info("Released {$count} expired cart reservation(s).");

        return self::SUCCESS;
    }
}
