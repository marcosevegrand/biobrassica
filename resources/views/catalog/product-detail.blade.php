@extends('layouts.shop')

@section('title', $product->name . ' | Biobrassica')

@section('content')
<section class="max-w-7xl mx-auto px-6 py-12">
  <nav class="text-xs uppercase tracking-widest text-muted mb-8"><a href="{{ route('catalog.products') }}" class="hover:text-forest transition-colors">Produtos</a><span class="mx-2">/</span><span class="text-forest">{{ $product->name }}</span></nav>
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
    <div>@if($product->image)@php($productImage = str_starts_with($product->image, 'images/') ? asset($product->image) : asset('storage/' . $product->image))<img src="{{ $productImage }}" alt="{{ $product->name }}" class="w-full aspect-square object-cover rounded-sm" loading="eager">@else<div class="w-full aspect-square bg-stone/20 rounded-sm flex items-center justify-center"><span class="text-muted">Sem imagem</span></div>@endif</div>
    <div>
      <p class="text-[10px] uppercase tracking-widest text-muted mb-2">{{ $product->category?->name }}</p>
      <h1 class="font-serif text-3xl md:text-4xl italic mb-4">{{ $product->name }}</h1>
      @if($product->brand)<p class="text-sm uppercase tracking-[0.2em] text-muted mb-3">{{ $product->brand }}</p>@endif

      @if($product->quantity)
      <div class="mb-8 inline-flex flex-col bg-terracotta/6 px-4 py-4">
        <span class="text-[10px] uppercase tracking-[0.18em] text-terracotta">Formato</span>
        <span class="mt-2 text-sm uppercase tracking-[0.14em] text-muted">{{ $product->quantity }}</span>
        @if($product->bio_code)<span class="mt-2 text-xs text-muted">Código BIO: {{ $product->bio_code }}</span>@endif
      </div>
      @endif

      <div class="flex items-center gap-3 mb-6">
        @if($product->bio_code)
        <div class="flex items-center gap-2">
          <img src="{{ asset('images/certs/eu-bio-logo.jpg') }}" alt="EU Bio Logo" class="h-12 w-12 object-contain">
        </div>
        @endif
      </div>
    </div>

    @if($product->description)
    <div class="lg:col-span-2 text-sm text-muted leading-relaxed">
      <h2 class="font-serif text-lg italic mb-4 text-forest">Descrição</h2>
      {!! \App\Services\HtmlSanitizer::sanitize($product->description) !!}
    </div>
    @endif

    <dl class="space-y-6 lg:col-span-2">
      @if($product->brand)<div><dt class="text-[10px] uppercase tracking-widest text-muted mb-2">Marca</dt><dd class="text-sm text-forest">{{ $product->brand }}</dd></div>@endif
      @if($product->allergens)<div><dt class="text-[10px] uppercase tracking-widest text-muted mb-2">Alergénicos</dt><dd class="text-sm text-forest">{{ $product->allergens }}</dd></div>@endif
      @if($product->quantity)<div><dt class="text-[10px] uppercase tracking-widest text-muted mb-2">Quantidade</dt><dd class="text-sm text-forest">{{ $product->quantity }}</dd></div>@endif
      @if($product->bio_code)<div><dt class="text-[10px] uppercase tracking-widest text-muted mb-2">Código Bio</dt><dd class="text-sm text-forest">{{ $product->bio_code }}</dd><img src="{{ asset('images/certs/eu-bio-logo.jpg') }}" alt="EU Bio Logo" class="h-12 w-12 object-contain"></div>@endif
    </dl>
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
