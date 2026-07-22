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

    @if($product->quantity)
      <p class="text-xs mb-1">{{ $product->quantity }}</p>
    @endif
    @if($product->brand)
      <p class="text-xs text-muted">{{ $product->brand }}</p>
    @endif

    <a href="{{ route('catalog.product', $product->slug) }}" class="mt-3 inline-flex items-center gap-1 text-xs text-muted hover:text-forest transition-colors">
      <span class="text-[10px] leading-none">↗</span>
      <span class="underline underline-offset-2">Ver detalhes</span>
    </a>
  </div>
</div>
