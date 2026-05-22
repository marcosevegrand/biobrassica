<header class="bg-white border-b border-stone-400/40 sticky top-0 z-50">
    <nav class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
            <div class="flex items-center space-x-8">
                <a href="{{ route('shop.home') }}" class="flex-shrink-0">
                    <img src="{{ asset('images/brand/logo-green-no-bg.png') }}"
                         alt="BioBrassica"
                         class="h-10 w-auto">
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

                <button id="shop-mobile-menu-btn" class="md:hidden p-2 text-forest" aria-label="Menu">
                    <svg id="shop-hamburger-icon" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
                    </svg>
                </button>

                @auth
                    <div class="hidden md:flex items-center space-x-3">
                        <a href="{{ url('/dashboard') }}" class="text-sm font-medium text-forest hover:text-terracotta transition-colors">
                            {{ auth()->user()->name }}
                        </a>
                        <form method="POST" action="{{ route('shop.logout') }}" class="inline">
                            @csrf
                            <button type="submit" class="text-sm text-muted hover:text-terracotta transition-colors">
                                Sair
                            </button>
                        </form>
                    </div>
                @endauth
            </div>
        </div>

        <div id="shop-mobile-menu" class="md:hidden hidden pb-4">
            <div class="flex flex-col space-y-3">
                <a href="{{ route('catalog.products') }}" class="text-sm font-medium text-forest hover:text-terracotta transition-colors">
                    Produtos
                </a>
                @foreach($navCategories as $navCat)
                    <a href="{{ route('catalog.category', $navCat->slug) }}"
                       class="text-sm font-medium text-forest hover:text-terracotta transition-colors">
                        {{ $navCat->name }}
                    </a>
                @endforeach
                @auth
                    <hr class="border-stone-400/40">
                    <a href="{{ url('/dashboard') }}" class="text-sm font-medium text-forest hover:text-terracotta transition-colors">
                        {{ auth()->user()->name }}
                    </a>
                    <form method="POST" action="{{ route('shop.logout') }}" class="inline">
                        @csrf
                        <button type="submit" class="text-sm text-muted hover:text-terracotta transition-colors text-left">
                            Sair
                        </button>
                    </form>
                @endauth
            </div>
        </div>
    </nav>
</header>

<script>
    (() => {
        const btn = document.getElementById('shop-mobile-menu-btn');
        const menu = document.getElementById('shop-mobile-menu');
        const icon = document.getElementById('shop-hamburger-icon');
        if (!btn || !menu) return;
        let open = false;
        btn.addEventListener('click', () => {
            open = !open;
            menu.classList.toggle('hidden', !open);
            if (open) {
                icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>';
            } else {
                icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>';
            }
        });
    })();
</script>
