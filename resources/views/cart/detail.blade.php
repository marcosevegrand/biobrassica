@extends('layouts.shop')

@section('title', 'Carrinho')

@section('content')
<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <h1 class="font-serif text-3xl font-bold text-forest mb-8">Carrinho</h1>

    @if($cart->items->isEmpty())
        <div class="bg-white rounded-lg border border-stone/40 p-12 text-center">
            <svg class="w-16 h-16 text-muted mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                      d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z"/>
            </svg>
            <h3 class="font-serif text-lg font-semibold text-forest mb-2">Carrinho vazio</h3>
            <p class="text-muted text-sm mb-6">Adicione produtos para começar as suas compras.</p>
            <a href="{{ route('catalog.products') }}"
               class="inline-flex items-center px-6 py-3 bg-forest text-white rounded-md font-medium hover:bg-forest/90 transition-colors">
                Ver Produtos
            </a>
        </div>
    @else
        <div id="cart-items-container">
            @include('cart.partials.cart-content', ['cart' => $cart, 'total' => $total, 'count' => $count])
        </div>
    @endif
</div>
@endsection
