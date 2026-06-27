@extends('layouts.website')

@section('title', $translation?->title ?? 'Receita')

@php
    $difficultyColors = [
        'Fácil' => 'bg-green-100 text-green-800 border-green-200',
        'Médio' => 'bg-yellow-100 text-yellow-800 border-yellow-200',
        'Difícil' => 'bg-red-100 text-red-800 border-red-200',
    ];
    $difficultyColor = $difficultyColors[$recipe->difficulty] ?? 'bg-paper text-forest border-stone/40';
@endphp

@section('content')
<article>
    <div class="relative h-64 md:h-80 bg-forest/10">
        @if($recipe->cover_image)
            @php($recipeImage = str_starts_with($recipe->cover_image, 'images/') ? asset($recipe->cover_image) : asset('storage/' . $recipe->cover_image))
            <img src="{{ $recipeImage }}"
                 alt="{{ $translation?->title }}"
                 class="w-full h-full object-cover">
        @else
            <div class="w-full h-full flex items-center justify-center bg-paper">
                <svg class="w-16 h-16 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                </svg>
            </div>
        @endif
    </div>

    <div class="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 py-10">
        <nav class="flex items-center space-x-2 text-sm text-muted mb-8">
            <a href="{{ route('website.home') }}" class="hover:text-forest transition-colors">Início</a>
            <span>/</span>
            <a href="{{ route('content.recipes') }}" class="hover:text-forest transition-colors">Receitas</a>
            <span>/</span>
            <span class="text-forest font-medium truncate max-w-[200px]">{{ $translation?->title }}</span>
        </nav>

        <h1 class="font-serif text-3xl md:text-4xl font-bold text-forest mb-6">
            {{ $translation?->title }}
        </h1>

        <div class="flex flex-wrap items-center gap-3 mb-6">
            @if($recipe->difficulty)
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border {{ $difficultyColor }}">
                    {{ $recipe->difficulty }}
                </span>
            @endif
            @if($recipe->prep_time)
                <span class="inline-flex items-center gap-1 text-sm text-muted">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    Prep: {{ $recipe->prep_time }}
                </span>
            @endif
            @if($recipe->cook_time)
                <span class="inline-flex items-center gap-1 text-sm text-muted">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                              d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z"/>
                    </svg>
                    Cozinhar: {{ $recipe->cook_time }}
                </span>
            @endif
            @if($recipe->servings)
                <span class="inline-flex items-center gap-1 text-sm text-muted">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/>
                    </svg>
                    {{ $recipe->servings }} porções
                </span>
            @endif
        </div>

        @if($recipe->tags && count($recipe->tags))
            <div class="flex flex-wrap gap-2 mb-8">
                @foreach($recipe->tags as $tag)
                    <a href="{{ route('content.recipes', ['tag' => $tag]) }}"
                       class="inline-block px-3 py-1 bg-paper border border-stone/40 rounded-full text-xs text-forest hover:bg-terracotta/10 hover:border-terracotta/30 transition-colors">
                        {{ $tag }}
                    </a>
                @endforeach
            </div>
        @endif

        @if($translation?->description)
            <p class="text-lg text-muted leading-relaxed mb-10">
                {{ $translation->description }}
            </p>
        @endif

        @if($translation?->ingredients && count($translation->ingredients))
            <section class="mb-10">
                <h2 class="font-serif text-2xl font-bold text-forest mb-4">Ingredientes</h2>
                <ul class="bg-white rounded-lg border border-stone/40 divide-y divide-stone/40">
                    @foreach($translation->ingredients as $ingredient)
                        <li class="px-5 py-3 flex items-center gap-3">
                            <span class="w-2 h-2 rounded-full bg-terracotta flex-shrink-0"></span>
                            <span class="text-forest">{{ $ingredient }}</span>
                        </li>
                    @endforeach
                </ul>
            </section>
        @endif

        @if($translation?->instructions && count($translation->instructions))
            <section class="mb-10">
                <h2 class="font-serif text-2xl font-bold text-forest mb-6">Instruções</h2>
                <ol class="space-y-6">
                    @foreach($translation->instructions as $index => $step)
                        <li class="flex gap-4">
                            <span class="flex-shrink-0 w-8 h-8 rounded-full bg-forest text-white flex items-center justify-center text-sm font-bold">
                                {{ $index + 1 }}
                            </span>
                            <p class="text-forest leading-relaxed pt-1">{{ $step }}</p>
                        </li>
                    @endforeach
                </ol>
            </section>
        @endif

        @if($translation?->content)
            <div class="prose prose-forest max-w-none text-forest leading-relaxed space-y-4 mb-10">
                {!! nl2br(e($translation->content)) !!}
            </div>
        @endif

        @if($recipe->products && $recipe->products->isNotEmpty())
            <section class="mt-12 pt-8 border-t border-stone/40">
                <h2 class="font-serif text-2xl font-bold text-forest mb-6">Produtos Relacionados</h2>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    @foreach($recipe->products as $product)
                        <x-product-card :product="$product" />
                    @endforeach
                </div>
            </section>
        @endif

        <div class="mt-12 pt-8 border-t border-stone/40">
            <a href="{{ route('content.recipes') }}" class="inline-flex items-center gap-2 text-terracotta hover:underline font-medium">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
                </svg>
                Voltar para as receitas
            </a>
        </div>
    </div>
</article>
@endsection
