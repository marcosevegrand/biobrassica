<div class="group border border-stone/40 rounded-sm overflow-hidden bg-paper">
  <a href="{{ route('catalog.product', $product->slug) }}">
    <div class="overflow-hidden">
      @if($product->image)
        @php($productImage = str_starts_with($product->image, 'images/') ? asset($product->image) : asset('storage/' . $product->image))
        <img src="{{ $productImage }}" alt="{{ $product->name }}" class="aspect-square w-full object-cover transition-transform duration-500 group-hover:scale-105" loading="lazy">
      @else
        <div class="aspect-square w-full bg-stone/20 flex items-center justify-center"><span class="text-muted text-sm">Sem imagem</span></div>
      @endif
    </div>
  </a>

  <div class="p-4">
    <p class="text-[10px] uppercase tracking-widest text-muted mb-1">{{ $product->category?->name }}</p>
    <a href="{{ route('catalog.product', $product->slug) }}" class="block"><h3 class="font-serif text-lg italic mb-3 group-hover:text-terracotta transition-colors">{{ $product->name }}</h3></a>

    @if($product->brand || $product->quantity)
    <div class="mb-3 space-y-1">
      @if($product->quantity)<p class="text-xs uppercase tracking-[0.14em] text-terracotta">{{ $product->quantity }}</p>@endif
      @if($product->brand)<p class="text-[10px] uppercase tracking-widest text-muted">{{ $product->brand }}</p>@endif
    </div>
    @endif
  </div>
</div>
