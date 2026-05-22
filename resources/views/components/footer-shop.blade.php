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
                    <a href="{{ route('website.home') }}" class="block hover:text-white transition-colors">Site Principal</a>
                </div>

                <h4 class="font-serif text-lg font-semibold mb-4 mt-6">Certificações</h4>
                <div class="flex flex-wrap gap-2">
                    <img src="{{ asset('images/certs/eu-bio-logo.jpg') }}"
                         alt="Agricultura Biológica UE"
                         class="h-10 w-auto bg-white rounded p-0.5">
                    <img src="{{ asset('images/certs/certiplanet-logo.png') }}"
                         alt="Certiplanet"
                         class="h-10 w-auto bg-white rounded p-0.5">
                </div>
            </div>
        </div>

        <div class="mt-8 pt-8 border-t border-white/20">
            <div class="flex flex-col md:flex-row items-center justify-between gap-4">
                <p class="text-center text-sm text-white/60">
                    &copy; {{ date('Y') }} BioBrassica. Todos os direitos reservados.
                </p>
                <div class="flex items-center space-x-4 text-sm text-white/60">
                    <a href="{{ route('website.privacy') }}" class="hover:text-white transition-colors">
                        Privacidade
                    </a>
                    <a href="{{ route('website.terms') }}" class="hover:text-white transition-colors">
                        Termos
                    </a>
                </div>
            </div>
        </div>
    </div>
</footer>
