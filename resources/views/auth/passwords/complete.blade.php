@extends('layouts.shop')

@section('title', 'Palavra-passe Atualizada - BioBrassica')

@section('content')
<div class="mx-auto max-w-md px-4 py-16 sm:px-6 lg:px-8 text-center">
    <div class="rounded-lg border border-stone/40 bg-white p-8 shadow-sm">
        <h1 class="font-serif text-3xl font-bold text-forest">Palavra-passe atualizada</h1>
        <p class="mt-4 text-muted">A sua palavra-passe foi redefinida com sucesso. Já pode iniciar sessão.</p>
        @if (session('status'))
            <p class="mt-4 rounded-md bg-green-50 border border-green-200 p-3 text-sm text-green-700">{{ session('status') }}</p>
        @endif
        <a href="{{ route('login') }}" class="mt-6 inline-flex rounded-md bg-forest px-5 py-2.5 text-sm font-semibold text-white hover:bg-forest/90 transition">
            Entrar
        </a>
    </div>
</div>
@endsection
