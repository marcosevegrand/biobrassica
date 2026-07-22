@extends('layouts.shop')

@section('title', $product->name . ' | Biobrassica')

@section('content')
<section class="max-w-7xl mx-auto px-6 py-12">
  <nav class="text-xs uppercase tracking-widest text-muted mb-8"><a href="{{ route('catalog.products') }}" class="hover:text-forest transition-colors">Produtos</a><span class="mx-2">/</span><span class="text-forest">{{ $product->name }}</span></nav>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-start">
    {{-- Left: sticky image --}}
    <div class="lg:sticky lg:top-24">
      @if($product->image)
        @php($productImage = str_starts_with($product->image, 'images/') ? asset($product->image) : asset('storage/' . $product->image))
        <img src="{{ $productImage }}" alt="{{ $product->name }}" class="w-full aspect-square object-cover rounded-sm" loading="eager">
      @else
        <div class="w-full aspect-square bg-stone/20 rounded-sm flex items-center justify-center"><span class="text-muted">Sem imagem</span></div>
      @endif
    </div>

    {{-- Right: all content --}}
    <div class="space-y-6">
      <p class="text-[10px] uppercase tracking-widest text-muted">{{ $product->category?->name }}</p>
      <h1 class="font-serif text-3xl md:text-4xl italic">{{ $product->name }}</h1>

      @if($product->brand)
        <p class="text-sm uppercase tracking-[0.2em] text-muted">{{ $product->brand }}</p>
      @endif

      @if($product->quantity)
      <div class="inline-flex flex-col bg-terracotta/6 px-4 py-4">
        <span class="text-[10px] uppercase tracking-[0.18em] text-terracotta">Formato</span>
        <span class="text-sm uppercase tracking-[0.14em] text-muted mt-1">{{ $product->quantity }}</span>
      </div>
      @endif

      @if($product->bio_code)
      <div class="flex items-center gap-2">
        <img src="{{ asset('images/certs/eu-bio-logo.jpg') }}" alt="EU Bio Logo" class="h-10 w-10 object-contain">
        <span class="text-xs text-muted">Código BIO: {{ $product->bio_code }}</span>
      </div>
      @endif

      @if($product->description)
      <div class="text-sm text-muted leading-relaxed">
        <h2 class="font-serif text-lg italic mb-3 text-forest">Descrição</h2>
        {!! \App\Services\HtmlSanitizer::sanitize($product->description) !!}
      </div>
      @endif

      @if($product->allergens)
      <div>
        <h3 class="text-[10px] uppercase tracking-widest text-muted mb-1">Alergénicos</h3>
        <p class="text-sm text-forest">{{ $product->allergens }}</p>
      </div>
      @endif
    </div>
  </div>

  @if($relatedProducts->isNotEmpty())
  <div class="mt-24">
    <h2 class="font-serif text-2xl italic mb-8">Produtos relacionados</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      @foreach($relatedProducts as $related)
        <x-product-card :product="$related" />
      @endforeach
    </div>
  </div>
  @endif
</section>
@endsection
