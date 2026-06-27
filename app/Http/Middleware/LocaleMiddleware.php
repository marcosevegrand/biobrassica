<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class LocaleMiddleware
{
    public function handle(Request $request, Closure $next): Response
    {
        $locale = $request->session()->get('locale')
            ?: $request->user()?->preferred_language
            ?: config('app.locale', 'pt');

        if (! in_array($locale, ['pt', 'en', 'fr'], true)) {
            $locale = 'pt';
        }

        app()->setLocale($locale);

        return $next($request);
    }
}
