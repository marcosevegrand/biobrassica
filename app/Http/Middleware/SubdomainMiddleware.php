<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class SubdomainMiddleware
{
    public function handle(Request $request, Closure $next): Response
    {
        $host = $request->getHost();

        if (str_starts_with($host, 'loja.')) {
            $role = 'shop';
        } elseif (str_starts_with($host, 'admin.')) {
            $role = 'admin';
        } else {
            $role = 'website';
        }

        $request->attributes->set('subdomain', $role);

        return $next($request);
    }
}
