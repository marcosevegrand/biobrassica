@extends('layouts.shop')

@section('title', 'Entrar - BioBrassica')

@section('content')
<div class="mx-auto max-w-md px-4 py-16 sm:px-6 lg:px-8">
    <h1 class="font-serif text-3xl font-bold text-forest text-center">Entrar</h1>
    <p class="mt-2 text-center text-muted">Ainda não tem conta? <a href="{{ route('shop.register') }}" class="text-terracotta hover:underline">Registar</a></p>

    <form action="{{ route('login') }}" method="POST" class="mt-8 space-y-6">
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
            <label for="password" class="block text-sm font-medium text-forest">Palavra-passe</label>
            <input
                type="password"
                name="password"
                id="password"
                required
                autocomplete="current-password"
                class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest"
            >
            @error('password')
                <p class="mt-1 text-sm text-red-600">{{ $message }}</p>
            @enderror
        </div>

        <div class="flex items-center justify-between">
            <label for="remember" class="flex items-center gap-2 text-sm text-muted">
                <input
                    type="checkbox"
                    name="remember"
                    id="remember"
                    class="rounded border-stone/40 text-forest focus:ring-forest"
                >
                Lembrar-me
            </label>

            <a href="{{ route('password.request') }}" class="text-sm text-terracotta hover:underline">Esqueceu a palavra-passe?</a>
        </div>

        <div>
            <button
                type="submit"
                class="w-full rounded-md bg-forest px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-forest/90 focus:outline-none focus:ring-2 focus:ring-forest focus:ring-offset-2 transition"
            >
                Entrar
            </button>
        </div>
    </form>
</div>
@endsection
