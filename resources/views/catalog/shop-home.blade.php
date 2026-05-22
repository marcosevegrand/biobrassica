@extends('layouts.shop')

@section('title', 'Loja')

@section('content')
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

    @if($featuredCategories->isNotEmpty())
        <section class="py-12">
            <h2 class="font-serif text-3xl font-bold text-forest text-center mb-8">Categorias</h2>

            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                @foreach($featuredCategories as $category)
                    <a href="{{ route('catalog.category', $category->slug) }}"
                       class="group relative bg-white rounded-lg border border-stone/40 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
                        <div class="aspect-square overflow-hidden bg-paper">
                            @if($category->image)
                                <img src="{{ asset('storage/' . $category->image) }}"
                                     alt="{{ $category->name }}"
                                     class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                                     loading="lazy">
                            @else
                                <div class="w-full h-full flex items-center justify-center bg-paper">
                                    <svg class="w-12 h-12 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                                              d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"/>
                                    </svg>
                                </div>
                            @endif
                        </div>
                        <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent flex items-end p-4">
                            <h3 class="font-serif text-white font-semibold text-lg">{{ $category->name }}</h3>
                        </div>
                    </a>
                @endforeach
            </div>
        </section>
    @endif

    @if($highlightedProducts->isNotEmpty())
        <section class="py-12">
            <h2 class="font-serif text-3xl font-bold text-forest text-center mb-2">Produtos em Destaque</h2>
            <p class="text-center text-muted mb-8">Os nossos produtos mais especiais</p>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                @foreach($highlightedProducts as $product)
                    <x-product-card :product="$product" />
                @endforeach
            </div>

            <div class="text-center mt-8">
                <a href="{{ route('catalog.products') }}"
                   class="inline-flex items-center px-6 py-3 border border-forest text-forest rounded-md hover:bg-forest hover:text-white transition-colors font-medium">
                    Ver todos os produtos
                    <svg class="ml-2 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
                    </svg>
                </a>
            </div>
        </section>
    @endif

    @if(isset($contactLocations) && $contactLocations->isNotEmpty())
        <section class="py-12 border-t border-stone/40">
            <h2 class="font-serif text-3xl font-bold text-forest text-center mb-8">Onde nos Encontrar</h2>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                @foreach($contactLocations as $location)
                    <div class="bg-white rounded-lg border border-stone/40 p-6 shadow-sm">
                        <h3 class="font-serif text-lg font-bold text-forest mb-2">{{ $location->name }}</h3>
                        @if($location->address)
                            <p class="text-sm text-muted mb-1">{{ $location->address }}</p>
                        @endif
                        @if($location->phone)
                            <p class="text-sm text-muted mb-1">
                                <a href="tel:{{ $location->phone }}" class="hover:text-terracotta transition-colors">{{ $location->phone }}</a>
                            </p>
                        @endif
                        @if($location->email)
                            <p class="text-sm text-muted mb-1">
                                <a href="mailto:{{ $location->email }}" class="hover:text-terracotta transition-colors">{{ $location->email }}</a>
                            </p>
                        @endif
                        @if($location->opening_hours)
                            <p class="text-xs text-muted mt-3">{{ $location->opening_hours }}</p>
                        @endif
                    </div>
                @endforeach
            </div>
        </section>
    @endif

</div>
@endsection
