@extends('layouts.website')

@section('title', $currentTag ? 'Receitas — ' . $currentTag : 'Receitas')

@section('content')
<div class="bg-terracotta/5 border-b border-stone/40">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-16">
        <h1 class="font-serif text-4xl font-bold text-forest">Receitas</h1>
        @if($currentTag)
            <p class="mt-3 text-muted">
                Receitas com a tag <span class="font-medium text-terracotta">{{ $currentTag }}</span>
                &mdash; <a href="{{ route('content.recipes') }}" class="text-forest hover:underline">Ver todas</a>
            </p>
        @else
            <p class="mt-3 text-muted max-w-2xl">Explore as nossas receitas saudáveis e saborosas com produtos biológicos.</p>
        @endif
    </div>
</div>

<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
    @if($recipes->isEmpty())
        <div class="bg-white rounded-lg border border-stone/40 p-12 text-center">
            <svg class="w-16 h-16 text-muted mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                      d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
            <h3 class="font-serif text-lg font-semibold text-forest mb-2">Nenhuma receita encontrada</h3>
            <p class="text-muted text-sm">Ainda não há receitas publicadas. Volte em breve.</p>
        </div>
    @else
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
            @foreach($recipes as $recipe)
                @include('content.partials.recipe-card', ['recipe' => $recipe, 'locale' => $locale])
            @endforeach
        </div>

        <div class="mt-12">
            {{ $recipes->appends(request()->query())->links() }}
        </div>
    @endif
</div>
@endsection
