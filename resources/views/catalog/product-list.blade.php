@extends('layouts.shop')

@section('title', 'Produtos | Biobrassica')

@section('content')
<section class="max-w-7xl mx-auto px-6 sm:px-8 py-12">
  <h1 class="font-serif text-4xl md:text-5xl italic text-center mb-4">Produtos</h1>
  <p class="text-muted text-center mb-12">Conheça a nossa seleção de produtos biológicos.</p>

  <div class="flex flex-col md:flex-row gap-4 mb-10">
    <form method="get" action="{{ route('catalog.products') }}" class="flex-1">
      @if($current_category)<input type="hidden" name="categoria" value="{{ $current_category }}">@endif
      <div class="relative"><input type="text" name="q" value="{{ $search_query }}" placeholder="Pesquisar produtos..." class="w-full px-4 py-3 border border-stone/40 rounded-sm focus:outline-none focus:border-forest text-sm"><button type="submit" class="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-forest"><svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" /></svg></button></div>
    </form>
  </div>

  @if($categories->isNotEmpty())
  <div class="flex flex-wrap gap-2 mb-12" id="category-filters">
    @foreach($categories as $category)
      @php($active = $current_category === $category->slug)
      <a href="{{ $active ? route('catalog.products', $search_query ? ['q' => $search_query] : []) : route('catalog.products', array_filter(['categoria' => $category->slug, 'q' => $search_query])) }}" class="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm transition-all duration-200 {{ $active ? 'bg-forest text-paper' : 'bg-stone/15 text-forest hover:bg-forest/10' }}" data-category-tag><span>{{ $category->name }}</span>@if($active)<svg class="w-3.5 h-3.5 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>@endif</a>
    @endforeach
  </div>
  @endif

  <div id="product-grid">
    @if($products->count())
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">@foreach($products as $product)<x-product-card :product="$product" />@endforeach</div>
      <div class="mt-10">{{ $products->links() }}</div>
    @else
      <div class="text-center py-24"><p class="text-muted text-lg">Nenhum produto encontrado.</p></div>
    @endif
  </div>
</section>
@endsection
