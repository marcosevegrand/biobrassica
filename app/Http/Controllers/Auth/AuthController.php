<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Http\Requests\LoginRequest;
use App\Http\Requests\ProfileRequest;
use App\Http\Requests\RegisterRequest;
use App\Models\Order;
use App\Models\User;
use App\Services\CartService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

class AuthController extends Controller
{
    public function __construct(
        private readonly CartService $cartService,
    ) {}

    public function showRegister(Request $request)
    {
        if ($request->filled('next')) {
            if ($intended = $this->normalizeIntendedUrl($request, (string) $request->input('next'))) {
                $request->session()->put('url.intended', $intended);
            } else {
                $request->session()->forget('url.intended');
            }
        }

        return view('auth.register');
    }

    public function register(RegisterRequest $request)
    {
        $user = User::create([
            'name' => $request->name,
            'email' => $request->email,
            'password' => $request->password,
        ]);

        Auth::login($user);
        $request->session()->regenerate();
        $warnings = $this->cartService->mergeGuestCartIntoUserCart($request, $user);

        $intended = $request->session()->pull('url.intended');

        if (is_string($intended) && $safeUrl = $this->normalizeIntendedUrl($request, $intended)) {
            return redirect()->to($safeUrl)->with('warning', implode(' ', $warnings));
        }

        return redirect()->route('shop.home')
            ->with('warning', implode(' ', $warnings));
    }

    public function showLogin(Request $request)
    {
        if ($request->filled('next')) {
            if ($intended = $this->normalizeIntendedUrl($request, (string) $request->input('next'))) {
                $request->session()->put('url.intended', $intended);
            } else {
                $request->session()->forget('url.intended');
            }
        }

        return view('auth.login');
    }

    public function login(LoginRequest $request)
    {
        $credentials = $request->only('email', 'password');

        if (Auth::attempt($credentials, $request->filled('remember'))) {
            $request->session()->regenerate();
            $warnings = $this->cartService->mergeGuestCartIntoUserCart($request, $request->user());

            $intended = $request->session()->pull('url.intended');

            if (is_string($intended) && $safeUrl = $this->normalizeIntendedUrl($request, $intended)) {
                return redirect()->to($safeUrl)->with('warning', implode(' ', $warnings));
            }

            return redirect()->route('shop.home')
                ->with('warning', implode(' ', $warnings));
        }

        return back()->withErrors([
            'email' => 'As credenciais fornecidas não correspondem aos nossos registos.',
        ])->onlyInput('email');
    }

    public function logout(Request $request)
    {
        Auth::logout();

        $request->session()->invalidate();
        $request->session()->regenerateToken();

        return redirect()->route('website.home');
    }

    public function profile()
    {
        $user = Auth::user();

        return view('auth.profile', compact('user'));
    }

    public function updateProfile(ProfileRequest $request)
    {
        $user = Auth::user();

        $user->update($request->only([
            'name',
            'phone',
            'nif',
            'preferred_language',
        ]));

        return back()->with('success', 'Perfil atualizado com sucesso.');
    }

    public function orderHistory()
    {
        $orders = Order::where('user_id', Auth::id())
            ->with(['items', 'payment', 'pickupLocation'])
            ->latest()
            ->paginate(10);

        return view('auth.order-history', compact('orders'));
    }

    private function normalizeIntendedUrl(Request $request, string $url): ?string
    {
        $url = trim($url);

        if ($url === '' || preg_match('/[\x00-\x1F\x7F]/', $url)) {
            return null;
        }

        $parts = parse_url($url);

        if ($parts === false) {
            return null;
        }

        if (isset($parts['host'])) {
            if (! in_array($parts['scheme'] ?? '', ['http', 'https'], true) || ! hash_equals($request->getHost(), $parts['host'])) {
                return null;
            }
        } elseif (isset($parts['scheme']) || str_starts_with($url, '//')) {
            return null;
        }

        $path = '/'.ltrim($parts['path'] ?? '/', '/');
        $shopPrefix = '/'.trim((string) config('biobrassica.paths.shop', 'loja'), '/');

        if ($shopPrefix !== '/' && $path !== $shopPrefix && ! str_starts_with($path, $shopPrefix.'/')) {
            return null;
        }

        return $path.(isset($parts['query']) ? '?'.$parts['query'] : '');
    }
}
