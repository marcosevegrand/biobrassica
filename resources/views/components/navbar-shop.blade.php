<header id="site-header" class="fixed top-0 left-0 right-0 z-50 bg-forest text-paper transition-all duration-300">
  <nav class="max-w-7xl mx-auto px-6 py-3 flex items-center gap-8">
    <a href="{{ route('shop.home') }}" class="block shrink-0" aria-label="Biobrassica">
      <img id="logo-white" src="{{ asset('images/brand/logo-white-no-bg.png') }}" alt="Biobrassica" class="hidden-logo-state h-[68px] max-h-[68px] w-auto max-w-[280px] object-contain block">
      <img id="logo-green" src="{{ asset('images/brand/logo-green-no-bg.png') }}" alt="Biobrassica" class="hidden hidden-logo-state h-[68px] max-h-[68px] w-auto max-w-[280px] object-contain">
    </a>

    <ul class="hidden lg:flex flex-1 items-center justify-center gap-8">
      <li><a href="{{ route('shop.home') }}" class="text-sm uppercase tracking-widest text-current opacity-80 hover:opacity-100 transition-colors">Início</a></li>
      <li><a href="{{ route('catalog.products') }}" class="text-sm uppercase tracking-widest text-current opacity-80 hover:opacity-100 transition-colors">Produtos</a></li>
    </ul>

    <div class="hidden lg:flex items-center gap-4 ml-auto">
      <div class="relative">
        <a href="{{ auth()->check() ? route('cart.detail') : route('login') }}" @auth id="cart-trigger" @endauth class="inline-flex items-center justify-center text-current opacity-90 hover:opacity-100 transition-colors relative" aria-label="Carrinho">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 3h1.386a1.125 1.125 0 011.09.852l.383 1.53m0 0L6.75 12h10.5l1.643-6.618a.75.75 0 00-.727-.93H5.109zm0 0L4.5 15.75A1.5 1.5 0 006 17.25h12m-10.5 3a1.125 1.125 0 100-2.25 1.125 1.125 0 000 2.25zm9 0a1.125 1.125 0 100-2.25 1.125 1.125 0 000 2.25z" /></svg>
          @auth
            @php($headerCart = \App\Models\Cart::where('user_id', auth()->id())->first())
            <span id="cart-count-badge" hx-get="{{ route('cart.count') }}" hx-trigger="cartUpdated from:body" hx-swap="innerHTML">@include('cart.partials.cart-count', ['count' => $headerCart ? $headerCart->items()->sum('quantity') : 0])</span>
          @endauth
        </a>
        @auth
          @php($popupCart = $headerCart?->load('items.product'))
          <div id="cart-popup" class="hidden absolute right-0 top-full mt-3 w-80 bg-paper border border-stone/30 rounded-sm shadow-sm z-50 p-4 text-forest">
            @if($popupCart && $popupCart->items->isNotEmpty())
              <div class="flex items-center justify-between mb-3"><span class="text-sm font-semibold">Carrinho</span><a href="{{ route('cart.detail') }}" class="text-xs text-terracotta hover:underline">Ver carrinho</a></div>
              <div class="space-y-2 max-h-64 overflow-y-auto">@foreach($popupCart->items as $item)<div class="flex items-center justify-between text-xs gap-2"><span class="truncate">{{ $item->product->name }}</span><span class="text-muted">x{{ $item->quantity }}</span></div>@endforeach</div>
            @else
              <p class="text-sm text-muted">O carrinho está vazio.</p>
            @endif
          </div>
        @endauth
      </div>

      <div class="relative">
        <button id="user-menu-trigger" type="button" class="inline-flex items-center justify-center text-current opacity-90 hover:opacity-100 transition-colors" aria-label="Menu de conta e idioma">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5" /></svg>
        </button>
        <div id="user-menu" class="hidden absolute right-0 top-full mt-3 w-56 bg-paper border border-stone/30 rounded-sm shadow-sm z-50 p-3">
          <div class="space-y-1 mb-3">
            @auth
              <a href="{{ route('shop.profile') }}" class="block px-3 py-2 text-sm hover:bg-forest/5 rounded-sm text-forest">Perfil</a>
              <a href="{{ route('shop.orders') }}" class="block px-3 py-2 text-sm hover:bg-forest/5 rounded-sm text-forest">Encomendas</a>
              <form method="POST" action="{{ route('shop.logout') }}">@csrf<button type="submit" class="block w-full text-left px-3 py-2 text-sm hover:bg-forest/5 rounded-sm text-forest">Sair</button></form>
            @else
              <a href="{{ route('login') }}" class="block px-3 py-2 text-sm hover:bg-forest/5 rounded-sm font-medium text-forest">Entrar</a>
            @endauth
          </div>
        </div>
      </div>
    </div>

    <div class="flex lg:hidden items-center gap-4 ml-auto">
      <button id="mobile-menu-btn" class="flex flex-col gap-1.5 p-1" aria-label="Alternar menu"><span class="block w-6 h-0.5 bg-current transition-transform" id="hamburger-top"></span><span class="block w-6 h-0.5 bg-current transition-opacity" id="hamburger-mid"></span><span class="block w-6 h-0.5 bg-current transition-transform" id="hamburger-bot"></span></button>
    </div>
  </nav>

  <div id="mobile-menu" class="lg:hidden hidden bg-paper text-forest border-t border-stone/20">
    <ul class="flex flex-col items-center gap-6 py-8">
      <li><a href="{{ route('shop.home') }}" class="text-sm uppercase tracking-widest hover:text-terracotta transition-colors">Início</a></li>
      <li><a href="{{ route('catalog.products') }}" class="text-sm uppercase tracking-widest hover:text-terracotta transition-colors">Produtos</a></li>
      <li><a href="{{ auth()->check() ? route('cart.detail') : route('login') }}" class="text-sm uppercase tracking-widest hover:text-terracotta transition-colors">Carrinho</a></li>
      @auth<li><a href="{{ route('shop.profile') }}" class="text-sm uppercase tracking-widest hover:text-terracotta transition-colors">Conta</a></li>@else<li><a href="{{ route('login') }}" class="text-sm uppercase tracking-widest hover:text-terracotta transition-colors font-semibold text-forest">Entrar</a></li>@endauth
    </ul>
  </div>
</header>
