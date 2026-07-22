<header id="site-header" class="fixed top-0 left-0 right-0 z-50 bg-forest text-paper transition-all duration-300">
  <nav class="max-w-7xl mx-auto px-6 py-3 flex items-center gap-8">
    <a href="{{ route('website.home') }}" class="block shrink-0" aria-label="Biobrassica">
      <img id="logo-white" src="{{ asset('images/brand/logo-white-no-bg.png') }}" alt="Biobrassica" class="hidden-logo-state h-[68px] max-h-[68px] w-auto max-w-[280px] object-contain block">
      <img id="logo-green" src="{{ asset('images/brand/logo-green-no-bg.png') }}" alt="Biobrassica" class="hidden hidden-logo-state h-[68px] max-h-[68px] w-auto max-w-[280px] object-contain">
    </a>

    <ul class="hidden lg:flex flex-1 items-center justify-center gap-8">
      <li><a href="{{ route('shop.home') }}" class="text-sm uppercase tracking-widest text-current opacity-80 hover:opacity-100 transition-colors">Início</a></li>
      <li><a href="{{ route('catalog.products') }}" class="text-sm uppercase tracking-widest text-current opacity-80 hover:opacity-100 transition-colors">Produtos</a></li>
    </ul>

    <div class="hidden lg:flex items-center gap-4 ml-auto">
    </div>

    <div class="flex lg:hidden items-center gap-4 ml-auto">
      <button id="mobile-menu-btn" class="flex flex-col gap-1.5 p-1" aria-label="Alternar menu"><span class="block w-6 h-0.5 bg-current transition-transform" id="hamburger-top"></span><span class="block w-6 h-0.5 bg-current transition-opacity" id="hamburger-mid"></span><span class="block w-6 h-0.5 bg-current transition-transform" id="hamburger-bot"></span></button>
    </div>
  </nav>

  <div id="mobile-menu" class="lg:hidden hidden bg-paper text-forest border-t border-stone/20">
    <ul class="flex flex-col items-center gap-6 py-8">
      <li><a href="{{ route('shop.home') }}" class="text-sm uppercase tracking-widest hover:text-terracotta transition-colors">Início</a></li>
      <li><a href="{{ route('catalog.products') }}" class="text-sm uppercase tracking-widest hover:text-terracotta transition-colors">Produtos</a></li>
      <li><a href="{{ route('website.home') }}" class="text-sm uppercase tracking-widest hover:text-terracotta transition-colors">Website</a></li>
    </ul>
  </div>
</header>
