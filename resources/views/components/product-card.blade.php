<div class="bg-white rounded-lg border border-stone/40 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
    <a href="{{ route('catalog.product', $product->slug) }}" class="block">
        <div class="aspect-square overflow-hidden bg-paper">
            @if($product->image)
                <img src="{{ asset('storage/' . $product->image) }}"
                     alt="{{ $product->name }}"
                     class="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                     loading="lazy">
            @else
                <div class="w-full h-full flex items-center justify-center bg-paper">
                    <svg class="w-16 h-16 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                    </svg>
                </div>
            @endif
        </div>
    </a>

    <div class="p-4">
        @if($product->brand)
            <p class="text-xs text-muted uppercase tracking-wide mb-1">{{ $product->brand }}</p>
        @endif

        <a href="{{ route('catalog.product', $product->slug) }}" class="block group">
            <h3 class="font-serif text-forest font-semibold text-lg leading-tight group-hover:text-terracotta transition-colors">
                {{ $product->name }}
            </h3>
        </a>

        @if($product->category)
            <p class="text-xs text-muted mt-1">{{ $product->category->name }}</p>
        @endif

        <div class="mt-3 flex items-center justify-between">
            <span class="text-forest font-bold text-lg">
                &euro;{{ number_format($product->price, 2) }}
            </span>

            @if($product->quantity)
                <span class="text-xs text-muted">{{ $product->quantity }}</span>
            @endif
        </div>

        @if($product->stock !== null && $product->stock <= 0)
            <p class="mt-2 text-sm text-terracotta font-medium">Esgotado</p>
        @else
            <button class="mt-3 w-full bg-forest text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-forest/90 transition-colors"
                    hx-post="{{ route('cart.add', $product->id) }}"
                    hx-target="#cart-popup-container"
                    hx-swap="innerHTML"
                    hx-headers='{"X-CSRF-TOKEN": "{{ csrf_token() }}"}'
                    hx-vals='{"quantity": 1}'>
                Adicionar
            </button>
        @endif
    </div>
</div>
