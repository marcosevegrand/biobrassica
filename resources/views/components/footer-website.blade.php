<footer class="bg-forest text-white">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-16">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10">
            <div class="lg:col-span-1">
                <img src="{{ asset('images/brand/logo-white-no-bg.png') }}"
                     alt="BioBrassica"
                     class="h-10 w-auto mb-6">
                @if(isset($websiteDefaults) && $websiteDefaults->footer_about)
                    <p class="text-sm text-white/70 leading-relaxed">
                        {{ \Illuminate\Support\Str::limit($websiteDefaults->footer_about, 200) }}
                    </p>
                @endif
            </div>

            <div>
                <h4 class="font-serif text-lg font-semibold mb-4">Contactos</h4>
                <div class="space-y-3 text-sm text-white/70">
                    @if(isset($websiteDefaults))
                        @if($websiteDefaults->footer_address)
                            <div class="flex items-start gap-2">
                                <svg class="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                          d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                          d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                                </svg>
                                <span>{{ $websiteDefaults->footer_address }}</span>
                            </div>
                        @endif
                        @if($websiteDefaults->footer_email)
                            <div class="flex items-center gap-2">
                                <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                          d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                                </svg>
                                <a href="mailto:{{ $websiteDefaults->footer_email }}" class="hover:text-white transition-colors">
                                    {{ $websiteDefaults->footer_email }}
                                </a>
                            </div>
                        @endif
                        @if($websiteDefaults->footer_phone)
                            <div class="flex items-center gap-2">
                                <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                          d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>
                                </svg>
                                <a href="tel:{{ $websiteDefaults->footer_phone }}" class="hover:text-white transition-colors">
                                    {{ $websiteDefaults->footer_phone }}
                                </a>
                            </div>
                        @endif
                    @endif
                </div>
            </div>

            <div>
                <h4 class="font-serif text-lg font-semibold mb-4">Links Rápidos</h4>
                <div class="space-y-2 text-sm text-white/70">
                    <a href="{{ route('website.home') }}" class="block hover:text-white transition-colors">Início</a>
                    <a href="{{ route('website.about') }}" class="block hover:text-white transition-colors">Quem Somos</a>
                    <a href="{{ route('website.agriculture') }}" class="block hover:text-white transition-colors">Agricultura Biológica</a>
                    <a href="{{ route('website.contacts') }}" class="block hover:text-white transition-colors">Contactos</a>
                    <a href="https://loja.biobrassica.pt" class="block hover:text-white transition-colors">Loja Online</a>
                </div>
            </div>

            <div>
                <h4 class="font-serif text-lg font-semibold mb-4">Certificações</h4>
                <div class="flex flex-wrap gap-3">
                    <img src="{{ asset('images/certs/eu-bio-logo.jpg') }}"
                         alt="Agricultura Biológica UE"
                         class="h-12 w-auto bg-white rounded p-1">
                    <img src="{{ asset('images/certs/certiplanet-logo.png') }}"
                         alt="Certiplanet"
                         class="h-12 w-auto bg-white rounded p-1">
                </div>

                <h4 class="font-serif text-lg font-semibold mb-4 mt-6">Siga-nos</h4>
                <div class="flex items-center space-x-4">
                    @if(isset($websiteDefaults) && $websiteDefaults->instagram_url)
                        <a href="{{ $websiteDefaults->instagram_url }}" target="_blank" rel="noopener noreferrer"
                           class="text-white/70 hover:text-white transition-colors">
                            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/>
                            </svg>
                        </a>
                    @endif
                    @if(isset($websiteDefaults) && $websiteDefaults->facebook_url)
                        <a href="{{ $websiteDefaults->facebook_url }}" target="_blank" rel="noopener noreferrer"
                           class="text-white/70 hover:text-white transition-colors">
                            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                            </svg>
                        </a>
                    @endif
                    @if(isset($websiteDefaults) && $websiteDefaults->youtube_url)
                        <a href="{{ $websiteDefaults->youtube_url }}" target="_blank" rel="noopener noreferrer"
                           class="text-white/70 hover:text-white transition-colors">
                            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M23.498 6.186a3.016 3.016 0 00-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 00.502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 002.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 002.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                            </svg>
                        </a>
                    @endif
                    @if(isset($websiteDefaults) && $websiteDefaults->linkedin_url)
                        <a href="{{ $websiteDefaults->linkedin_url }}" target="_blank" rel="noopener noreferrer"
                           class="text-white/70 hover:text-white transition-colors">
                            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                            </svg>
                        </a>
                    @endif
                </div>
            </div>
        </div>

        <div class="mt-12 pt-8 border-t border-white/20">
            <div class="flex flex-col md:flex-row items-center justify-between gap-4">
                <p class="text-sm text-white/50">
                    &copy; {{ date('Y') }} BioBrassica. Todos os direitos reservados.
                </p>
                <div class="flex items-center space-x-6 text-sm text-white/50">
                    <a href="{{ route('website.privacy') }}" class="hover:text-white transition-colors">
                        Política de Privacidade
                    </a>
                    <a href="{{ route('website.terms') }}" class="hover:text-white transition-colors">
                        Termos e Condições
                    </a>
                </div>
            </div>
        </div>
    </div>
</footer>
