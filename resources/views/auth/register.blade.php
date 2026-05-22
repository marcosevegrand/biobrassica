@extends('layouts.shop')

@section('title', 'Registar - BioBrassica')

@section('content')
<div class="mx-auto max-w-md px-4 py-16 sm:px-6 lg:px-8">
    <h1 class="font-serif text-3xl font-bold text-forest text-center">Criar Conta</h1>
    <p class="mt-2 text-center text-muted">Já tem conta? <a href="{{ route('login') }}" class="text-terracotta hover:underline">Entrar</a></p>

    <form action="{{ route('shop.register') }}" method="POST" class="mt-8 space-y-6">
        @csrf

        <div>
            <label for="name" class="block text-sm font-medium text-forest">Nome</label>
            <input
                type="text"
                name="name"
                id="name"
                value="{{ old('name') }}"
                required
                autocomplete="name"
                class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest"
            >
            @error('name')
                <p class="mt-1 text-sm text-red-600">{{ $message }}</p>
            @enderror
        </div>

        <div>
            <label for="email" class="block text-sm font-medium text-forest">Email</label>
            <input
                type="email"
                name="email"
                id="email"
                value="{{ old('email') }}"
                required
                autocomplete="email"
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
                autocomplete="new-password"
                class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest"
            >
            @error('password')
                <p class="mt-1 text-sm text-red-600">{{ $message }}</p>
            @enderror
        </div>

        <div>
            <label for="password_confirmation" class="block text-sm font-medium text-forest">Confirmar Palavra-passe</label>
            <input
                type="password"
                name="password_confirmation"
                id="password_confirmation"
                required
                autocomplete="new-password"
                class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest"
            >
        </div>

        <div>
            <button
                type="submit"
                class="w-full rounded-md bg-forest px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-forest/90 focus:outline-none focus:ring-2 focus:ring-forest focus:ring-offset-2 transition"
            >
                Registar
            </button>
        </div>
    </form>
</div>
@endsection
