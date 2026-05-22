@extends('layouts.shop')

@section('title', 'Recuperar Palavra-passe - BioBrassica')

@section('content')
<div class="mx-auto max-w-md px-4 py-16 sm:px-6 lg:px-8">
    <h1 class="font-serif text-3xl font-bold text-forest text-center">Recuperar Palavra-passe</h1>
    <p class="mt-2 text-center text-muted">Introduza o seu email para receber o link de recuperação.</p>

    @if (session('status'))
        <div class="mt-4 rounded-md bg-green-50 border border-green-200 p-4">
            <p class="text-sm text-green-700">{{ session('status') }}</p>
        </div>
    @endif

    <form action="{{ route('password.email') }}" method="POST" class="mt-8 space-y-6">
        @csrf

        <div>
            <label for="email" class="block text-sm font-medium text-forest">Email</label>
            <input
                type="email"
                name="email"
                id="email"
                value="{{ old('email') }}"
                required
                autocomplete="email"
                autofocus
                class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest"
            >
            @error('email')
                <p class="mt-1 text-sm text-red-600">{{ $message }}</p>
            @enderror
        </div>

        <div>
            <button
                type="submit"
                class="w-full rounded-md bg-forest px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-forest/90 focus:outline-none focus:ring-2 focus:ring-forest focus:ring-offset-2 transition"
            >
                Enviar Link de Recuperação
            </button>
        </div>

        <p class="text-center text-sm text-muted">
            <a href="{{ route('login') }}" class="text-terracotta hover:underline">Voltar ao Login</a>
        </p>
    </form>
</div>
@endsection
