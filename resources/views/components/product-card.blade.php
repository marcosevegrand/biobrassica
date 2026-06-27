@php($canBuyProduct = $product->canBePurchasedOnline())
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
    <a href="{{ route('catalog.product', $product->slug) }}" class="block"><h3 class="font-serif text-lg italic mb-2 group-hover:text-terracotta transition-colors">{{ $product->name }}</h3></a>
    <div class="mb-4 bg-terracotta/6 px-3 py-3"><p class="font-serif text-2xl italic leading-none text-forest">€{{ number_format((float) $product->price, 2, ',', ' ') }}</p><p class="mt-1 text-xs uppercase tracking-[0.14em] text-terracotta">{{ $product->quantity }}</p></div>

    <div class="flex flex-wrap gap-1 mb-3">
      @if($product->allow_pickup && $product->relationLoaded('pickupLocations') && $product->pickupLocations->isNotEmpty())
        @foreach($product->pickupLocations as $loc)<span class="text-[10px] uppercase tracking-widest text-muted border border-stone/30 px-2 py-0.5 rounded-sm">{{ $loc->name }}</span>@endforeach
      @endif
      <span class="text-[10px] uppercase tracking-widest border px-2 py-0.5 rounded-sm {{ $product->allow_shipping ? 'text-forest border-forest/30' : 'text-muted border-stone/30' }}">{{ $product->allow_shipping && $product->allow_pickup ? 'Envio e recolha' : ($product->allow_shipping ? 'Apenas envio' : ($product->allow_pickup ? 'Apenas recolha' : 'Sem modo disponível')) }}</span>
    </div>

    @if($product->is_preview)<p class="mb-3 text-[10px] uppercase tracking-widest text-terracotta">Pré-visualização</p>@endif

    <form method="post" action="{{ route('cart.add', $product->id) }}" hx-post="{{ route('cart.add', $product->id) }}" hx-swap="none">
      @csrf
      <div class="flex items-center gap-2 mb-3"><div class="flex items-center border border-stone/40 rounded-sm"><button type="button" data-cart-quantity-action="decrement" aria-label="Diminuir quantidade" class="px-2 py-1 text-muted hover:text-forest transition-colors">−</button><input type="number" name="quantity" value="1" min="1" max="{{ min(99, max(1, (int) $product->stock)) }}" class="w-12 text-center border-x border-stone/40 py-1 text-xs focus:outline-none no-spinner"><button type="button" data-cart-quantity-action="increment" aria-label="Aumentar quantidade" class="px-2 py-1 text-muted hover:text-forest transition-colors">+</button></div><button type="button" data-cart-quantity-action="set" data-cart-quantity-value="3" class="text-[10px] uppercase tracking-widest border border-stone/40 px-2 py-1 rounded-sm hover:border-forest hover:text-forest transition-colors">3x</button><button type="button" data-cart-quantity-action="set" data-cart-quantity-value="6" class="text-[10px] uppercase tracking-widest border border-stone/40 px-2 py-1 rounded-sm hover:border-forest hover:text-forest transition-colors">6x</button></div>
      <button type="submit" class="w-full text-xs uppercase tracking-widest border border-forest px-4 py-2.5 rounded-sm hover:bg-forest hover:text-paper transition-colors cursor-pointer {{ ! $canBuyProduct ? 'opacity-50 cursor-not-allowed' : '' }}" {{ ! $canBuyProduct ? 'disabled' : '' }}>{{ $product->is_preview ? 'Pré-visualização' : (! $product->hasFulfillmentMethod() ? 'Indisponível' : ((int) $product->stock > 0 ? 'Adicionar ao carrinho' : 'Esgotado')) }}</button>
    </form>
  </div>
</div>
