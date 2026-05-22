<div class="mt-8 bg-white rounded-lg border border-stone/40 p-6">
    <div class="flex items-center justify-between mb-4">
        <h3 class="font-serif text-lg font-bold text-forest">Resumo</h3>
        <span class="text-sm text-muted">{{ $count }} item(ns)</span>
    </div>

    <div class="space-y-2">
        @foreach($cart->items as $item)
            <div class="flex items-center justify-between text-sm">
                <span class="text-forest">{{ $item->product->name }} x{{ $item->quantity }}</span>
                <span class="text-forest font-medium">&euro;{{ number_format($item->quantity * $item->product->price, 2) }}</span>
            </div>
        @endforeach
    </div>

    <div class="mt-4 pt-4 border-t border-stone/40">
        <div class="flex items-center justify-between">
            <span class="font-serif text-lg font-bold text-forest">Total</span>
            <span class="text-xl font-bold text-forest">&euro;{{ number_format($total, 2) }}</span>
        </div>
    </div>

    <div class="mt-6 flex flex-col sm:flex-row gap-3">
        <a href="{{ route('catalog.products') }}"
           class="flex-1 text-center py-3 px-6 border border-forest text-forest rounded-md font-medium hover:bg-forest hover:text-white transition-colors">
            Continuar a Comprar
        </a>
    </div>
</div>
