@extends('layouts.shop')

@section('title', $category->name)

@section('content')
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <nav class="flex items-center space-x-2 text-sm text-muted mb-8">
        <a href="{{ route('shop.home') }}" class="hover:text-forest transition-colors">Início</a>
        <span>/</span>
        <a href="{{ route('catalog.products') }}" class="hover:text-forest transition-colors">Produtos</a>
        <span>/</span>
        <span class="text-forest font-medium">{{ $category->name }}</span>
    </nav>

    <div class="bg-white rounded-lg border border-stone/40 overflow-hidden mb-8">
        <div class="relative">
            @if($category->image)
                <div class="h-48 md:h-64 overflow-hidden">
                    @php($categoryImage = str_starts_with($category->image, 'images/') ? asset($category->image) : asset('storage/' . $category->image))
                    <img src="{{ $categoryImage }}"
                         alt="{{ $category->name }}"
                         class="w-full h-full object-cover">
                </div>
                <div class="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent"></div>
            @else
                <div class="h-48 md:h-64 bg-forest/10"></div>
            @endif

            <div class="{{ $category->image ? 'absolute bottom-0 left-0 right-0' : '' }} p-6 md:p-8">
                <h1 class="font-serif text-3xl font-bold {{ $category->image ? 'text-white' : 'text-forest' }}">
                    {{ $category->name }}
                </h1>
                @if($category->featured_message)
                    <p class="mt-2 {{ $category->image ? 'text-white/80' : 'text-muted' }} max-w-2xl">
                        {{ $category->featured_message }}
                    </p>
                @endif
            </div>
        </div>
    </div>

    <div class="flex items-center justify-between mb-6">
        <h2 class="font-serif text-xl font-bold text-forest">
            Produtos nesta categoria
        </h2>
        <span class="text-sm text-muted">{{ $products->total() }} produto(s)</span>
    </div>

    @if($products->isEmpty())
        <div class="bg-white rounded-lg border border-stone/40 p-12 text-center">
            <svg class="w-16 h-16 text-muted mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                      d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/>
            </svg>
            <h3 class="font-serif text-lg font-semibold text-forest mb-2">Sem produtos ainda</h3>
            <p class="text-muted text-sm">Ainda não existem produtos nesta categoria. Volte em breve!</p>
        </div>
    @else
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            @foreach($products as $product)
                <x-product-card :product="$product" />
            @endforeach
        </div>

        <div class="mt-8">
            {{ $products->links() }}
        </div>
    @endif

    <div class="mt-8 text-center">
        <a href="{{ route('catalog.products') }}"
           class="inline-flex items-center px-6 py-3 border border-forest text-forest rounded-md hover:bg-forest hover:text-white transition-colors font-medium">
            <svg class="mr-2 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
            Ver todos os produtos
        </a>
    </div>
</div>
@endsection
