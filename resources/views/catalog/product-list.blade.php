@extends('layouts.shop')

@section('title', 'Produtos')

@section('content')
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="flex flex-col md:flex-row gap-8">

        <aside class="w-full md:w-64 flex-shrink-0">
            <div class="bg-white rounded-lg border border-stone/40 p-6 sticky top-24">
                <h3 class="font-serif text-lg font-bold text-forest mb-4">Categorias</h3>

                <form method="GET" action="{{ route('catalog.products') }}" id="filter-form">
                    <div class="space-y-2">
                        <a href="{{ route('catalog.products') }}"
                           class="block px-3 py-2 rounded-md text-sm {{ !request('category') ? 'bg-forest text-white' : 'text-forest hover:bg-paper' }} transition-colors">
                            Todas
                        </a>

                        @foreach($categories as $cat)
                            <a href="{{ route('catalog.products', ['category' => $cat->id]) }}"
                               class="block px-3 py-2 rounded-md text-sm {{ request('category') == $cat->id ? 'bg-forest text-white' : 'text-forest hover:bg-paper' }} transition-colors">
                                {{ $cat->name }}
                            </a>
                        @endforeach
                    </div>
                </form>

                <div class="mt-6 pt-6 border-t border-stone/40">
                    <h4 class="font-serif text-sm font-bold text-forest mb-3">Procurar</h4>
                    <form method="GET" action="{{ route('catalog.products') }}">
                        @if(request('category'))
                            <input type="hidden" name="category" value="{{ request('category') }}">
                        @endif
                        <input type="text" name="q" value="{{ request('q') }}"
                               placeholder="Pesquisar produtos..."
                               class="w-full px-3 py-2 border border-stone/40 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-forest/30">
                        <button type="submit" class="mt-2 w-full bg-forest text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-forest/90 transition-colors">
                            Buscar
                        </button>
                    </form>
                </div>
            </div>
        </aside>

        <div class="flex-1">
            <div class="flex items-center justify-between mb-6">
                <h1 class="font-serif text-2xl font-bold text-forest">
                    @if(request('category'))
                        @php $activeCategory = $categories->firstWhere('id', request('category')); @endphp
                        {{ $activeCategory ? $activeCategory->name : 'Produtos' }}
                    @elseif(request('q'))
                        Resultados para "{{ request('q') }}"
                    @else
                        Todos os Produtos
                    @endif
                </h1>

                <span class="text-sm text-muted">{{ $products->total() }} produto(s)</span>
            </div>

            @if($products->isEmpty())
                <div class="bg-white rounded-lg border border-stone/40 p-12 text-center">
                    <svg class="w-16 h-16 text-muted mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"/>
                    </svg>
                    <h3 class="font-serif text-lg font-semibold text-forest mb-2">Nenhum produto encontrado</h3>
                    <p class="text-muted text-sm">Tente ajustar os filtros ou voltar mais tarde.</p>
                    <a href="{{ route('catalog.products') }}" class="inline-block mt-4 text-terracotta hover:underline text-sm font-medium">
                        Ver todos os produtos
                    </a>
                </div>
            @else
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    @foreach($products as $product)
                        <x-product-card :product="$product" />
                    @endforeach
                </div>

                <div class="mt-8">
                    {{ $products->appends(request()->query())->links() }}
                </div>
            @endif
        </div>

    </div>
</div>
@endsection
