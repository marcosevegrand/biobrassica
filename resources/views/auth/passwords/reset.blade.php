@extends('layouts.shop')

@section('title', 'Redefinir Palavra-passe - BioBrassica')

@section('content')
<div class="mx-auto max-w-md px-4 py-16 sm:px-6 lg:px-8">
    <h1 class="font-serif text-3xl font-bold text-forest text-center">Redefinir Palavra-passe</h1>

    <form action="{{ route('password.update') }}" method="POST" class="mt-8 space-y-6">
        @csrf

        <input type="hidden" name="token" value="{{ $token }}">

        <div>
            <label for="email" class="block text-sm font-medium text-forest">Email</label>
            <input
                type="email"
                name="email"
                id="email"
                value="{{ old('email', $email) }}"
                required
                autocomplete="email"
                class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest"
            >
            @error('email')
                <p class="mt-1 text-sm text-red-600">{{ $message }}</p>
            @enderror
        </div>

        <div>
            <label for="password" class="block text-sm font-medium text-forest">Nova Palavra-passe</label>
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
                Redefinir Palavra-passe
            </button>
        </div>
    </form>
</div>
@endsection
