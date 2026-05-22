@if($count > 0)
    <div class="m-4 p-4 bg-white border border-stone/40 rounded-lg shadow-lg max-w-xs">
        <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-semibold text-forest">Carrinho</span>
            <a href="{{ route('cart.detail') }}" class="text-xs text-terracotta hover:underline">Ver carrinho</a>
        </div>
        <div class="space-y-2 max-h-48 overflow-y-auto">
            @foreach($cart->items as $item)
                <div class="flex items-center justify-between text-xs">
                    <span class="text-forest truncate max-w-[140px]">{{ $item->product->name }}</span>
                    <span class="text-muted">x{{ $item->quantity }}</span>
                    <span class="text-forest font-medium">&euro;{{ number_format($item->quantity * $item->product->price, 2) }}</span>
                </div>
            @endforeach
        </div>
        <div class="mt-3 pt-3 border-t border-stone/40 flex items-center justify-between">
            <span class="text-sm font-bold text-forest">Total</span>
            <span class="text-sm font-bold text-forest">&euro;{{ number_format($total, 2) }}</span>
        </div>
    </div>
@endif
