<header id="site-header" class="fixed top-0 left-0 right-0 z-50 bg-forest text-paper transition-all duration-300">
  <nav class="max-w-384 mx-auto px-6 xl:px-8 2xl:px-10 py-3 flex items-center gap-6 xl:gap-8">
    <a href="{{ route('website.home') }}" class="block shrink-0" aria-label="Biobrassica">
      <img id="logo-white" src="{{ asset('images/brand/logo-white-no-bg.png') }}" alt="Biobrassica" class="hidden-logo-state h-[68px] max-h-[68px] w-auto max-w-[280px] object-contain block">
      <img id="logo-green" src="{{ asset('images/brand/logo-green-no-bg.png') }}" alt="Biobrassica" class="hidden hidden-logo-state h-[68px] max-h-[68px] w-auto max-w-[280px] object-contain">
    </a>

    <ul class="hidden lg:flex flex-1 items-center justify-center gap-5 xl:gap-7 2xl:gap-8 min-w-0">
      <li><a href="{{ route('website.about') }}" class="whitespace-nowrap text-sm uppercase tracking-[0.22em] text-current opacity-80 hover:opacity-100 transition-colors">Quem Somos</a></li>
      <li><a href="{{ route('website.agriculture') }}" class="whitespace-nowrap text-sm uppercase tracking-[0.22em] text-current opacity-80 hover:opacity-100 transition-colors">Agricultura Bio</a></li>
      <li><a href="{{ route('content.blog') }}" class="whitespace-nowrap text-sm uppercase tracking-[0.22em] text-current opacity-80 hover:opacity-100 transition-colors">Blog</a></li>
      <li><a href="{{ route('content.recipes') }}" class="whitespace-nowrap text-sm uppercase tracking-[0.22em] text-current opacity-80 hover:opacity-100 transition-colors">Receitas</a></li>
      <li><a href="{{ route('website.contacts') }}" class="whitespace-nowrap text-sm uppercase tracking-[0.22em] text-current opacity-80 hover:opacity-100 transition-colors">Contactos</a></li>
    </ul>

    <div class="hidden lg:flex items-center gap-3 xl:gap-4 ml-auto shrink-0">
      <a id="loja-cta" href="{{ route('shop.home') }}" class="whitespace-nowrap px-5 py-2 bg-paper text-forest text-xs font-medium uppercase tracking-[0.22em] rounded-sm hover:bg-paper/90 transition-colors">Loja Online</a>
    </div>

    <div class="flex lg:hidden items-center gap-4 ml-auto">
      <button id="mobile-menu-btn" class="flex flex-col gap-1.5 p-1" aria-label="Alternar menu">
        <span class="block w-6 h-0.5 bg-current transition-transform" id="hamburger-top"></span>
        <span class="block w-6 h-0.5 bg-current transition-opacity" id="hamburger-mid"></span>
        <span class="block w-6 h-0.5 bg-current transition-transform" id="hamburger-bot"></span>
      </button>
    </div>
  </nav>

  <div id="mobile-menu" class="lg:hidden hidden bg-forest text-paper border-t border-paper/20">
    <ul class="flex flex-col items-center gap-6 py-8">
      <li><a href="{{ route('website.about') }}" class="text-sm uppercase tracking-widest hover:opacity-80 transition-colors">Quem Somos</a></li>
      <li><a href="{{ route('website.agriculture') }}" class="text-sm uppercase tracking-widest hover:opacity-80 transition-colors">Agricultura Bio</a></li>
      <li><a href="{{ route('content.blog') }}" class="text-sm uppercase tracking-widest hover:opacity-80 transition-colors">Blog</a></li>
      <li><a href="{{ route('content.recipes') }}" class="text-sm uppercase tracking-widest hover:opacity-80 transition-colors">Receitas</a></li>
      <li><a href="{{ route('website.contacts') }}" class="text-sm uppercase tracking-widest hover:opacity-80 transition-colors">Contactos</a></li>
      <li><a href="{{ route('shop.home') }}" class="px-5 py-2 bg-paper text-forest text-xs font-medium uppercase tracking-widest rounded-sm">Loja Online</a></li>
    </ul>
  </div>
</header>
