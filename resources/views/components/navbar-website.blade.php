<header id="site-header" class="fixed top-0 left-0 right-0 z-50 bg-forest text-paper transition-colors duration-300">
    <nav class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="flex h-20 items-center justify-between">
            <a href="{{ route('website.home') }}" class="flex-shrink-0">
                <img src="{{ asset('images/brand/logo-white-no-bg.png') }}"
                     alt="BioBrassica"
                     class="h-12 w-auto"
                     id="logo-white">
                <img src="{{ asset('images/brand/logo-green-no-bg.png') }}"
                     alt="BioBrassica"
                     class="h-12 w-auto"
                     id="logo-green"
                     style="display:none;">
            </a>

            <div class="hidden md:flex items-center space-x-8">
                <a href="{{ route('website.home') }}" class="text-sm font-medium tracking-wide hover:text-terracotta transition-colors">
                    Início
                </a>
                <a href="{{ route('website.about') }}" class="text-sm font-medium tracking-wide hover:text-terracotta transition-colors">
                    Quem Somos
                </a>
                <a href="{{ route('website.agriculture') }}" class="text-sm font-medium tracking-wide hover:text-terracotta transition-colors">
                    Agricultura Biológica
                </a>
                <a href="{{ route('website.contacts') }}" class="text-sm font-medium tracking-wide hover:text-terracotta transition-colors">
                    Contactos
                </a>
                <a href="https://loja.biobrassica.pt"
                   id="loja-cta"
                   class="inline-flex items-center gap-2 bg-paper text-forest px-4 py-2 rounded-full text-sm font-medium hover:bg-paper/90 transition-all">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"/>
                    </svg>
                    Loja Online
                </a>
            </div>

            <button id="mobile-menu-btn" class="md:hidden p-2" aria-label="Menu">
                <svg id="hamburger-top" class="w-6 h-6 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                     style="transform-origin: center;">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16"/>
                </svg>
                <svg id="hamburger-mid" class="w-6 h-6 -mt-4 transition-opacity duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 12h16"/>
                </svg>
                <svg id="hamburger-bot" class="w-6 h-6 -mt-4 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                     style="transform-origin: center;">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 18h16"/>
                </svg>
            </button>
        </div>

        <div id="mobile-menu" class="md:hidden hidden pb-6">
            <div class="flex flex-col space-y-4">
                <a href="{{ route('website.home') }}" class="text-sm font-medium tracking-wide hover:text-terracotta transition-colors">
                    Início
                </a>
                <a href="{{ route('website.about') }}" class="text-sm font-medium tracking-wide hover:text-terracotta transition-colors">
                    Quem Somos
                </a>
                <a href="{{ route('website.agriculture') }}" class="text-sm font-medium tracking-wide hover:text-terracotta transition-colors">
                    Agricultura Biológica
                </a>
                <a href="{{ route('website.contacts') }}" class="text-sm font-medium tracking-wide hover:text-terracotta transition-colors">
                    Contactos
                </a>
                <a href="https://loja.biobrassica.pt"
                   class="inline-flex items-center justify-center gap-2 bg-forest text-paper px-4 py-2 rounded-full text-sm font-medium hover:bg-forest/90 transition-colors w-full">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"/>
                    </svg>
                    Loja Online
                </a>
            </div>
        </div>
    </nav>
</header>
