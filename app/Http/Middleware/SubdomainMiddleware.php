<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class SubdomainMiddleware
{
    public function handle(Request $request, Closure $next): Response
    {
        $shopPath = trim((string) config('biobrassica.paths.shop', 'loja'), '/');
        $adminPath = trim((string) config('biobrassica.paths.admin', 'admin'), '/');

        if ($request->is($shopPath, $shopPath.'/*')) {
            $role = 'shop';
        } elseif ($request->is($adminPath, $adminPath.'/*')) {
            $role = 'admin';
        } else {
            $role = 'website';
        }

        $request->attributes->set('subdomain', $role);

        return $next($request);
    }
}
