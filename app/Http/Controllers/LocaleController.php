<?php

namespace App\Http\Controllers;

use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

class LocaleController extends Controller
{
    public function switch(Request $request, string $locale): RedirectResponse
    {
        // Only Portuguese is supported
        abort_unless($locale === 'pt', 404);

        $request->session()->put('locale', $locale);

        if ($request->user()) {
            $request->user()->forceFill(['preferred_language' => $locale])->save();
        }

        return redirect()->back();
    }
}
