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
        <div class="space-y-4">
            @foreach($cart->items as $item)
                <div class="bg-white rounded-lg border border-stone/40 p-4 sm:p-6 flex flex-col sm:flex-row items-start gap-4">
                    <a href="{{ route('catalog.product', $item->product->slug) }}" class="flex-shrink-0">
                        <div class="w-20 h-20 bg-paper rounded-md overflow-hidden">
                            @if($item->product->image)
                                <img src="{{ asset('storage/' . $item->product->image) }}"
                                     alt="{{ $item->product->name }}"
                                     class="w-full h-full object-cover">
                            @else
                                <div class="w-full h-full flex items-center justify-center">
                                    <svg class="w-8 h-8 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                                              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                                    </svg>
                                </div>
                            @endif
                        </div>
                    </a>

                    <div class="flex-1 min-w-0">
                        <a href="{{ route('catalog.product', $item->product->slug) }}"
                           class="font-serif text-forest font-semibold hover:text-terracotta transition-colors">
                            {{ $item->product->name }}
                        </a>
                        @if($item->product->brand)
                            <p class="text-xs text-muted mt-0.5">{{ $item->product->brand }}</p>
                        @endif

                        <div class="mt-2 flex items-center gap-4">
                            <div class="flex items-center gap-2">
                                <button class="w-8 h-8 rounded border border-stone/40 flex items-center justify-center text-forest hover:bg-paper transition-colors"
                                        hx-post="{{ route('cart.update', $item->id) }}"
                                        hx-target="#cart-items-container"
                                        hx-swap="innerHTML"
                                        hx-headers='{"X-CSRF-TOKEN": "{{ csrf_token() }}"}'
                                        hx-vals='{"quantity": {{ $item->quantity - 1 }}}'
                                        {{ $item->quantity <= 1 ? 'disabled' : '' }}>
                                    -
                                </button>
                                <span class="w-10 text-center text-sm font-medium">{{ $item->quantity }}</span>
                                <button class="w-8 h-8 rounded border border-stone/40 flex items-center justify-center text-forest hover:bg-paper transition-colors"
                                        hx-post="{{ route('cart.update', $item->id) }}"
                                        hx-target="#cart-items-container"
                                        hx-swap="innerHTML"
                                        hx-headers='{"X-CSRF-TOKEN": "{{ csrf_token() }}"}'
                                        hx-vals='{"quantity": {{ $item->quantity + 1 }}}'>
                                    +
                                </button>
                            </div>

                            <button class="text-sm text-terracotta hover:underline"
                                    hx-post="{{ route('cart.remove', $item->id) }}"
                                    hx-target="#cart-items-container"
                                    hx-swap="innerHTML"
                                    hx-headers='{"X-CSRF-TOKEN": "{{ csrf_token() }}"}'>
                                Remover
                            </button>
                        </div>
                    </div>

                    <div class="text-right flex-shrink-0">
                        <p class="font-bold text-forest">
                            &euro;{{ number_format($item->quantity * $item->product->price, 2) }}
                        </p>
                        <p class="text-xs text-muted">
                            &euro;{{ number_format($item->product->price, 2) }} / un
                        </p>
                    </div>
                </div>
            @endforeach
        </div>

        <div id="cart-items-container">
            @include('cart.partials.cart-summary', ['cart' => $cart, 'total' => $total, 'count' => $count])
        </div>
    @endif
</div>
@endsection
