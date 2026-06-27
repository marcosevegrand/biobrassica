<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Password;

class ForgotPasswordController extends Controller
{
    public function showLinkRequestForm()
    {
        return view('auth.passwords.email');
    }

    public function showLinkSentPage()
    {
        return view('auth.passwords.done');
    }

    public function sendResetLinkEmail(Request $request)
    {
        $request->validate(['email' => 'required|email']);

        Password::sendResetLink(
            $request->only('email')
        );

        return redirect()->route('password.sent')
            ->with(['status' => 'Se o email existir, enviaremos instruções para recuperar a palavra-passe.']);
    }
}
