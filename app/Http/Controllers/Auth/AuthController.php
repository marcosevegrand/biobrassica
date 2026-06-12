<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Http\Requests\LoginRequest;
use App\Http\Requests\ProfileRequest;
use App\Http\Requests\RegisterRequest;
use App\Models\Order;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;

class AuthController extends Controller
{
    public function showRegister()
    {
        return view('auth.register');
    }

    public function register(RegisterRequest $request)
    {
        $user = \App\Models\User::create([
            'name' => $request->name,
            'email' => $request->email,
            'password' => $request->password,
        ]);

        Auth::login($user);

        return redirect()->route('shop.home');
    }

    public function showLogin(Request $request)
    {
        if ($request->filled('next')) {
            $request->session()->put('url.intended', $request->input('next'));
        }

        return view('auth.login');
    }

    public function login(LoginRequest $request)
    {
        $credentials = $request->only('email', 'password');

        if (Auth::attempt($credentials, $request->filled('remember'))) {
            $request->session()->regenerate();

            return redirect()->intended(route('shop.home'));
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
            ->with(['items', 'payment'])
            ->latest()
            ->paginate(10);

        return view('auth.order-history', compact('orders'));
    }
}
