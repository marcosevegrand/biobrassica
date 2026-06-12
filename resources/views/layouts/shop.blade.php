<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    @if(isset($websiteDefaults) && $websiteDefaults->seo_title)
        <title>{{ $websiteDefaults->seo_title }}</title>
    @else
        <title>@yield('title', 'Loja') - BioBrassica</title>
    @endif

    @if(isset($websiteDefaults) && $websiteDefaults->seo_description)
        <meta name="description" content="{{ $websiteDefaults->seo_description }}">
    @endif

    @if(isset($websiteDefaults) && $websiteDefaults->seo_keywords)
        <meta name="keywords" content="{{ $websiteDefaults->seo_keywords }}">
    @endif

    <link rel="preconnect" href="https://fonts.bunny.net">
    <link href="https://fonts.bunny.net/css?family=figtree:400,500,600,700&display=swap" rel="stylesheet" />

    <link rel="stylesheet" href="{{ asset('css/output.css') }}">

    <script src="https://unpkg.com/htmx.org@2.0.4"></script>

    <style>
        {!! $websiteDefaults->custom_css ?? '' !!}
    </style>
</head>
<body class="bg-paper text-forest font-sans antialiased min-h-screen flex flex-col">

    <header class="bg-white border-b border-stone/40 sticky top-0 z-50">
        <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex items-center space-x-8">
                    <a href="{{ route('shop.home') }}" class="font-serif text-2xl font-bold text-forest">
                        BioBrassica
                    </a>

                    <div class="hidden md:flex items-center space-x-6">
                        <a href="{{ route('catalog.products') }}" class="text-forest hover:text-terracotta transition-colors text-sm font-medium">
                            Produtos
                        </a>
                        @php
                            $navCategories = \App\Models\Category::query()
                                ->select('categories.*')
                                ->join('category_positions', 'categories.id', '=', 'category_positions.category_id')
                                ->where('categories.is_active', true)
                                ->orderBy('category_positions.position')
                                ->take(5)
                                ->get();
                        @endphp
                        @foreach($navCategories as $navCat)
                            <a href="{{ route('catalog.category', $navCat->slug) }}"
                               class="text-forest hover:text-terracotta transition-colors text-sm font-medium">
                                {{ $navCat->name }}
                            </a>
                        @endforeach
                    </div>
                </div>

                <div class="flex items-center space-x-4">
                    <div id="cart-count-badge" class="relative"
                         hx-get="{{ route('cart.count') }}"
                         hx-trigger="cartUpdated from:body"
                         hx-target="this"
                         hx-swap="innerHTML">
                        @php
                            $badgeCart = \App\Models\Cart::where('user_id', auth()->id())->first();
                            $badgeCount = $badgeCart ? $badgeCart->items()->sum('quantity') : 0;
                        @endphp
                        <a href="{{ route('cart.detail') }}" class="relative p-2 block text-forest hover:text-terracotta transition-colors">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                      d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z"/>
                            </svg>
                            @if($badgeCount > 0)
                                <span class="absolute -top-1 -right-1 bg-terracotta text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
                                    {{ $badgeCount }}
                                </span>
                            @endif
                        </a>
                    </div>

                    @auth
                        <a href="{{ url('/dashboard') }}" class="text-sm font-medium text-forest hover:text-terracotta transition-colors">
                            {{ auth()->user()->name }}
                        </a>
                        <form method="POST" action="{{ route('logout') }}" class="inline">
                            @csrf
                            <button type="submit" class="text-sm text-muted hover:text-terracotta transition-colors">
                                Sair
                            </button>
                        </form>
                    @endauth
                </div>
            </div>
        </nav>
    </header>

    @if(session('success'))
        <div class="bg-green-50 border-b border-green-200">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
                <p class="text-sm text-green-800">{{ session('success') }}</p>
            </div>
        </div>
    @endif

    @if(session('error'))
        <div class="bg-red-50 border-b border-red-200">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
                <p class="text-sm text-red-800">{{ session('error') }}</p>
            </div>
        </div>
    @endif

    <main class="flex-1">
        @yield('content')
    </main>

    <footer class="bg-forest text-white mt-16">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div>
                    <h3 class="font-serif text-xl font-bold mb-4">BioBrassica</h3>
                    @if(isset($websiteDefaults) && $websiteDefaults->footer_about)
                        <p class="text-sm text-white/80 leading-relaxed">{{ $websiteDefaults->footer_about }}</p>
                    @endif
                </div>

                <div>
                    <h4 class="font-serif text-lg font-semibold mb-4">Contactos</h4>
                    <div class="space-y-2 text-sm text-white/80">
                        @if(isset($websiteDefaults))
                            @if($websiteDefaults->footer_address)
                                <p>{{ $websiteDefaults->footer_address }}</p>
                            @endif
                            @if($websiteDefaults->footer_email)
                                <p><a href="mailto:{{ $websiteDefaults->footer_email }}" class="hover:text-white transition-colors">{{ $websiteDefaults->footer_email }}</a></p>
                            @endif
                            @if($websiteDefaults->footer_phone)
                                <p><a href="tel:{{ $websiteDefaults->footer_phone }}" class="hover:text-white transition-colors">{{ $websiteDefaults->footer_phone }}</a></p>
                            @endif
                        @endif
                    </div>
                </div>

                <div>
                    <h4 class="font-serif text-lg font-semibold mb-4">Links</h4>
                    <div class="space-y-2 text-sm text-white/80">
                        <a href="{{ route('catalog.products') }}" class="block hover:text-white transition-colors">Produtos</a>
                        <a href="{{ route('cart.detail') }}" class="block hover:text-white transition-colors">Carrinho</a>
                    </div>
                </div>
            </div>

            <div class="mt-8 pt-8 border-t border-white/20 text-center text-sm text-white/60">
                <p>&copy; {{ date('Y') }} BioBrassica. Todos os direitos reservados.</p>
            </div>
        </div>
    </footer>

    <div id="cart-popup-container"
         class="fixed bottom-0 right-0 z-40"
         hx-get="{{ route('cart.popup') }}"
         hx-trigger="cartUpdated from:body"
         hx-target="this"
         hx-swap="innerHTML">
        @php
            $popupCart = \App\Models\Cart::where('user_id', auth()->id())->first();
            $popupCount = $popupCart ? $popupCart->items()->sum('quantity') : 0;
        @endphp
        @if($popupCount > 0)
            <div class="m-4 p-4 bg-white border border-stone/40 rounded-lg shadow-lg max-w-xs">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-semibold text-forest">Carrinho</span>
                    <a href="{{ route('cart.detail') }}" class="text-xs text-terracotta hover:underline">Ver carrinho</a>
                </div>
                <p class="text-xs text-muted">{{ $popupCount }} item(ns) no carrinho</p>
            </div>
        @endif
    </div>

    @if(isset($websiteDefaults) && $websiteDefaults->custom_js)
        <script>{!! $websiteDefaults->custom_js !!}</script>
    @endif

</body>
</html>
