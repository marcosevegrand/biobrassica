@extends('layouts.shop')

@section('title', 'Perfil - BioBrassica')

@section('content')
<div class="mx-auto max-w-2xl px-4 py-16 sm:px-6 lg:px-8">
    <h1 class="font-serif text-3xl font-bold text-forest">O Meu Perfil</h1>

    @if (session('success'))
        <div class="mt-4 rounded-md bg-green-50 border border-green-200 p-4">
            <p class="text-sm text-green-700">{{ session('success') }}</p>
        </div>
    @endif

    <form action="{{ route('shop.profile.update') }}" method="POST" class="mt-8 space-y-6">
        @csrf

        <div>
            <label for="name" class="block text-sm font-medium text-forest">Nome</label>
            <input
                type="text"
                name="name"
                id="name"
                value="{{ old('name', $user->name) }}"
                required
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
                id="email"
                value="{{ $user->email }}"
                disabled
                class="mt-1 block w-full rounded-md border border-stone/40 bg-stone-50 px-3 py-2 text-muted shadow-sm"
            >
            <p class="mt-1 text-xs text-muted">O email não pode ser alterado.</p>
        </div>

        <div>
            <label for="phone" class="block text-sm font-medium text-forest">Telefone</label>
            <input
                type="text"
                name="phone"
                id="phone"
                value="{{ old('phone', $user->phone) }}"
                placeholder="912345678"
                class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest"
            >
            @error('phone')
                <p class="mt-1 text-sm text-red-600">{{ $message }}</p>
            @enderror
        </div>

        <div>
            <label for="nif" class="block text-sm font-medium text-forest">NIF</label>
            <input
                type="text"
                name="nif"
                id="nif"
                value="{{ old('nif', $user->nif) }}"
                placeholder="123456789"
                class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest"
            >
            @error('nif')
                <p class="mt-1 text-sm text-red-600">{{ $message }}</p>
            @enderror
        </div>

        <div>
            <label for="preferred_language" class="block text-sm font-medium text-forest">Idioma Preferido</label>
            <select
                name="preferred_language"
                id="preferred_language"
                class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest"
            >
                <option value="pt" {{ old('preferred_language', $user->preferred_language) === 'pt' ? 'selected' : '' }}>Português</option>
                <option value="en" {{ old('preferred_language', $user->preferred_language) === 'en' ? 'selected' : '' }}>English</option>
                <option value="fr" {{ old('preferred_language', $user->preferred_language) === 'fr' ? 'selected' : '' }}>Français</option>
            </select>
            @error('preferred_language')
                <p class="mt-1 text-sm text-red-600">{{ $message }}</p>
            @enderror
        </div>

        <div class="flex items-center gap-4">
            <button
                type="submit"
                class="rounded-md bg-forest px-6 py-2 text-sm font-semibold text-white shadow-sm hover:bg-forest/90 focus:outline-none focus:ring-2 focus:ring-forest focus:ring-offset-2 transition"
            >
                Guardar Alterações
            </button>
            <a href="{{ route('shop.orders') }}" class="text-sm text-terracotta hover:underline">Ver Encomendas</a>
        </div>
    </form>
</div>
@endsection
