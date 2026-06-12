@extends('layouts.website')

@section('title', isset($websiteContent) && $websiteContent->seo_title ? $websiteContent->seo_title : 'BioBrassica')

@section('content')
@php
    $heroImage = isset($websiteContent) && $websiteContent->hero_image
        ? asset('storage/' . $websiteContent->hero_image)
        : null;
@endphp

<section class="relative h-screen flex items-center justify-center overflow-hidden">
    @if($heroImage)
        <img src="{{ $heroImage }}" alt="BioBrassica" class="absolute inset-0 w-full h-full object-cover">
    @else
        <div class="absolute inset-0 bg-gradient-to-br from-forest via-forest/90 to-forest/70"></div>
    @endif
    <div class="absolute inset-0 bg-forest/40"></div>

    <div class="relative z-10 text-center px-4 max-w-4xl mx-auto">
        <img src="{{ asset('images/brand/logo-white-no-bg.png') }}"
             alt="BioBrassica"
             class="h-24 md:h-32 w-auto mx-auto mb-8 drop-shadow-lg">

        @if(isset($websiteContent) && $websiteContent->hero_title)
            <h1 class="font-serif text-4xl md:text-5xl lg:text-6xl font-bold text-white leading-tight mb-6 drop-shadow-lg">
                {!! nl2br(e($websiteContent->hero_title)) !!}
            </h1>
        @else
            <h1 class="font-serif text-4xl md:text-5xl lg:text-6xl font-bold text-white leading-tight mb-6 drop-shadow-lg">
                Da Nossa Terra<br>Para a Sua Mesa
            </h1>
        @endif

        @if(isset($websiteContent) && $websiteContent->hero_subtitle)
            <p class="text-lg md:text-xl text-white/90 font-light mb-10 max-w-2xl mx-auto">
                {{ $websiteContent->hero_subtitle }}
            </p>
        @else
            <p class="text-lg md:text-xl text-white/90 font-light mb-10 max-w-2xl mx-auto">
                Produtos biológicos certificados, cultivados com respeito pela natureza e paixão pela qualidade.
            </p>
        @endif

        <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a href="{{ route('website.about') }}"
               class="inline-flex items-center gap-2 bg-white text-forest px-8 py-3 rounded-full font-medium hover:bg-white/90 transition-colors shadow-lg">
                Saber Mais
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                </svg>
            </a>
            <a href="#shop-cta"
               class="inline-flex items-center gap-2 border-2 border-white text-white px-8 py-3 rounded-full font-medium hover:bg-white/20 transition-colors">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"/>
                </svg>
                Loja Online
            </a>
        </div>
    </div>

    <div class="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
        <svg class="w-6 h-6 text-white/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"/>
        </svg>
    </div>
</section>

<section class="py-20 bg-white">
    <div class="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <div class="flex flex-col md:flex-row items-center gap-10">
            <div class="flex-shrink-0">
                <div class="w-48 h-48 md:w-56 md:h-56 rounded-full overflow-hidden border-4 border-terracotta/30 shadow-lg">
                    @php($quoteMember = $teamMembers->where('photo', '!=', null)->first())
                    @php($quotePhoto = $quoteMember?->photo ? (str_starts_with($quoteMember->photo, 'images/') ? asset($quoteMember->photo) : asset('storage/' . $quoteMember->photo)) : asset('images/people/006.jpg'))
                    <img src="{{ $quotePhoto }}"
                         alt="Engª Ângela Pereira"
                         class="w-full h-full object-cover">
                </div>
            </div>
            <div class="flex-1 text-center md:text-left">
                <svg class="w-10 h-10 text-terracotta/30 mb-4 mx-auto md:mx-0" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M4.583 17.321C3.553 16.227 3 15 3 13.011c0-3.5 2.457-6.637 6.03-8.188l.893 1.378c-3.335 1.804-3.987 4.145-4.247 5.621.537-.278 1.24-.375 1.929-.311C9.591 11.69 11 13.166 11 15c0 1.933-1.567 3.5-3.5 3.5-1.267 0-2.417-.667-2.917-1.179zm10 0C13.553 16.227 13 15 13 13.011c0-3.5 2.457-6.637 6.03-8.188l.893 1.378c-3.335 1.804-3.987 4.145-4.247 5.621.537-.278 1.24-.375 1.929-.311C19.591 11.69 21 13.166 21 15c0 1.933-1.567 3.5-3.5 3.5-1.267 0-2.417-.667-2.917-1.179z"/>
                </svg>
                <blockquote class="font-serif text-xl md:text-2xl text-forest italic leading-relaxed mb-4">
                    "Temos conseguido ao longo destes anos oferecer cada vez mais produtos frescos, colhidos no próprio dia, vindos das mãos de produtores que se levantam às 5h da manhã num esforço último de transmitir a vitalidade e qualidade das suas terras aos consumidores que já se haviam esquecido do sabor e do cheiro dos legumes acabados de colher!"
                </blockquote>
                <p class="text-terracotta font-semibold text-lg">{{ $quoteMember->name ?? 'Engª Ângela Pereira' }}</p>
                <p class="text-muted text-sm">{{ $quoteMember->role ?? 'Fundadora' }}</p>
            </div>
        </div>
    </div>
</section>

@php
    $decorativeIcons = ['tomato', 'broccoli', 'carrot', 'garlic', 'onion', 'cabbage', 'grapes', 'strawberry', 'avocado'];
@endphp

<section id="shop-cta" class="relative py-32 bg-forest overflow-hidden">
    <div class="absolute inset-0 opacity-10">
        <div class="grid grid-cols-6 gap-4 p-8">
            @foreach($decorativeIcons as $icon)
                <img src="{{ asset('images/arts/' . $icon . '.svg') }}"
                     alt=""
                     class="w-16 h-16 md:w-24 md:h-24 opacity-60
                            @if($loop->index % 3 === 0) translate-y-4 @endif
                            @if($loop->index % 2 === 0) rotate-12 @else -rotate-12 @endif">
            @endforeach
        </div>
    </div>

    <div class="relative z-10 text-center px-4">
        <img src="{{ asset('images/brand/logo-white-no-bg.png') }}"
             alt="BioBrassica"
             class="h-16 w-auto mx-auto mb-8">

        <h2 class="font-serif text-4xl md:text-5xl font-bold text-white mb-6">
            {{ $websiteContent->hero_cta_text ?? 'Descubra os nossos produtos' }}
        </h2>
        <p class="text-lg text-white/80 font-light max-w-2xl mx-auto mb-10">
            Entrega em todo o Portugal continental ou levantamento nas nossas lojas em Braga e Guimarães.
        </p>

        <a href="https://loja.biobrassica.pt"
           class="inline-flex items-center gap-3 bg-terracotta text-white px-10 py-4 rounded-full text-lg font-medium hover:bg-terracotta/90 transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"/>
            </svg>
            Visitar Loja Online
        </a>

        <p class="text-white/50 text-sm mt-6">
            Entregamos em Guimarães, Braga e arredores
        </p>
    </div>
</section>

@if($instagramPosts->isNotEmpty())
<section class="py-20 bg-paper">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-14">
            <h2 class="font-serif text-3xl md:text-4xl font-bold text-forest mb-4">
                Siga-nos no Instagram
            </h2>
            <p class="text-muted font-light max-w-xl mx-auto">
                Acompanhe o nosso dia-a-dia, os bastidores da produção biológica e as novidades da BioBrassica.
            </p>
            @if(isset($websiteDefaults) && $websiteDefaults->instagram_url)
                <a href="{{ $websiteDefaults->instagram_url }}" target="_blank" rel="noopener noreferrer"
                   class="inline-flex items-center gap-2 text-terracotta hover:text-terracotta/80 font-medium mt-4 transition-colors">
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/>
                    </svg>
                    @biobrassica
                </a>
            @endif
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-3 lg:grid-cols-5 gap-4">
            @foreach($instagramPosts as $post)
                <a href="{{ $post->permalink ?? '#' }}"
                   target="_blank"
                   rel="noopener noreferrer"
                   class="group block relative aspect-square rounded-lg overflow-hidden bg-gray-100 shadow-sm hover:shadow-md transition-all">
                    <img src="{{ $post->image_url }}"
                         alt="{{ \Illuminate\Support\Str::limit($post->caption, 80) }}"
                         class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                         loading="lazy">
                    <div class="absolute inset-0 bg-gradient-to-t from-forest/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                        <div class="absolute bottom-0 left-0 right-0 p-4">
                            @if($post->caption)
                                <p class="text-white text-xs leading-relaxed line-clamp-3">
                                    {{ $post->caption }}
                                </p>
                            @endif
                        </div>
                    </div>
                    <div class="absolute top-3 right-3">
                        <svg class="w-5 h-5 text-white drop-shadow opacity-0 group-hover:opacity-100 transition-opacity" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/>
                        </svg>
                    </div>
                </a>
            @endforeach
        </div>
    </div>
</section>
@endif
@endsection
