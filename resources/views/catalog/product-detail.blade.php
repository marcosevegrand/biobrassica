@extends('layouts.shop')

@section('title', $product->name)

@section('content')
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <nav class="flex items-center space-x-2 text-sm text-muted mb-8">
        <a href="{{ route('shop.home') }}" class="hover:text-forest transition-colors">Início</a>
        <span>/</span>
        <a href="{{ route('catalog.products') }}" class="hover:text-forest transition-colors">Produtos</a>
        @if($product->category)
            <span>/</span>
            <a href="{{ route('catalog.category', $product->category->slug) }}" class="hover:text-forest transition-colors">
                {{ $product->category->name }}
            </a>
        @endif
        <span>/</span>
        <span class="text-forest font-medium">{{ $product->name }}</span>
    </nav>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">
        <div class="bg-white rounded-lg border border-stone/40 overflow-hidden">
            <div class="aspect-square">
                @if($product->image)
                    <img src="{{ asset('storage/' . $product->image) }}"
                         alt="{{ $product->name }}"
                         class="w-full h-full object-cover">
                @else
                    <div class="w-full h-full flex items-center justify-center bg-paper">
                        <svg class="w-24 h-24 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                        </svg>
                    </div>
                @endif
            </div>
        </div>

        <div class="flex flex-col">
            <div>
                @if($product->brand)
                    <p class="text-xs text-muted uppercase tracking-wide mb-2">{{ $product->brand }}</p>
                @endif

                <h1 class="font-serif text-3xl font-bold text-forest mb-2">{{ $product->name }}</h1>

                @if($product->bio_code)
                    <p class="text-sm text-muted mb-4">Código: {{ $product->bio_code }}</p>
                @endif

                <div class="text-2xl font-bold text-forest mb-6">
                    &euro;{{ number_format($product->price, 2) }}
                </div>

                @if($product->quantity)
                    <p class="text-sm text-muted mb-4">{{ $product->quantity }}</p>
                @endif
            </div>

            <div class="border-t border-stone/40 pt-6">
                @if($product->stock !== null && $product->stock <= 0)
                    <p class="text-terracotta font-medium mb-4">Produto esgotado</p>
                @else
                    <form class="flex items-center gap-4"
                          hx-post="{{ route('cart.add', $product->id) }}"
                          hx-target="#cart-popup-container"
                          hx-swap="innerHTML"
                          hx-headers='{"X-CSRF-TOKEN": "{{ csrf_token() }}"}'>
                        <label class="flex items-center gap-2">
                            <span class="text-sm font-medium text-forest">Qtd:</span>
                            <input type="number" name="quantity" value="1" min="1"
                                   class="w-20 px-3 py-2 border border-stone/40 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-forest/30">
                        </label>
                        <button type="submit"
                                class="flex-1 bg-forest text-white py-3 px-6 rounded-md font-medium hover:bg-forest/90 transition-colors">
                            Adicionar ao Carrinho
                        </button>
                    </form>
                @endif

                @if($product->allow_pickup && $product->pickupLocations->isNotEmpty())
                    <div class="mt-4 p-4 bg-paper rounded-md border border-stone/40">
                        <p class="text-sm font-medium text-forest mb-2">Disponível para levantamento em:</p>
                        @foreach($product->pickupLocations as $loc)
                            <p class="text-xs text-muted">{{ $loc->name }}</p>
                        @endforeach
                    </div>
                @endif
            </div>

            @if($product->description)
                <div class="mt-8">
                    <h2 class="font-serif text-lg font-bold text-forest mb-3">Descrição</h2>
                    <div class="prose prose-sm text-muted max-w-none">
                        {!! nl2br(e($product->description)) !!}
                    </div>
                </div>
            @endif

            @if($product->allergens)
                <div class="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
                    <h3 class="text-sm font-semibold text-yellow-800 mb-1">Alergénios</h3>
                    <p class="text-sm text-yellow-700">{{ $product->allergens }}</p>
                </div>
            @endif
        </div>
    </div>

    @if($relatedProducts->isNotEmpty())
        <section class="mt-16 border-t border-stone/40 pt-12">
            <h2 class="font-serif text-2xl font-bold text-forest text-center mb-8">Produtos Relacionados</h2>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                @foreach($relatedProducts as $related)
                    <x-product-card :product="$related" />
                @endforeach
            </div>
        </section>
    @endif
</div>
@endsection
