<?php

namespace App\Http\Middleware;

use App\Models\ShopSettings;
use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class ShopBrevementeMiddleware
{
    public function handle(Request $request, Closure $next): Response
    {
        if ($request->attributes->get('subdomain') !== 'shop') {
            return $next($request);
        }

        $shopSettings = ShopSettings::first();

        if (!$shopSettings?->is_shop_brevemente) {
            return $next($request);
        }

        if ($request->is('_health', '_health/*', 'payment/callback', 'payment/callback/*')) {
            return $next($request);
        }

        return response()->view('brevemente');
    }
}
