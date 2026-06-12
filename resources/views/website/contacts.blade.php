@extends('layouts.website')

@section('title', 'Contactos - BioBrassica')
@section('meta_description', 'Entre em contacto com a BioBrassica. Encontre os nossos locais de venda, horários, contactos telefónicos e localização.')

@section('content')
<section class="relative h-[50vh] flex items-center justify-center overflow-hidden bg-gradient-to-br from-forest via-forest/90 to-forest/70">
    <div class="relative z-10 text-center px-4">
        <h1 class="font-serif text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4 drop-shadow-lg">
            {{ $websiteContent->contacts_title ?? 'Encontre-nos' }}
        </h1>
        <p class="text-lg md:text-xl text-white/80 font-light max-w-2xl mx-auto">
            {{ $websiteContent->contacts_content ?? 'Visite-nos nas nossas lojas ou entre em contacto por telefone e email.' }}
        </p>
    </div>
</section>

<section class="py-20 bg-paper">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        @if(isset($locations) && $locations->isNotEmpty())
            <div class="space-y-16">
                @foreach($locations as $location)
                    <div class="flex flex-col lg:flex-row gap-10 bg-white rounded-xl shadow-sm border border-stone-400/40 overflow-hidden">
                        @if($location->image)
                            <div class="lg:w-1/3">
                                @php($locationImage = str_starts_with($location->image, 'images/') ? asset($location->image) : asset('storage/' . $location->image))
                                <img src="{{ $locationImage }}"
                                     alt="{{ $location->name }}"
                                     class="w-full h-64 lg:h-full object-cover">
                            </div>
                        @endif

                        <div class="flex-1 p-8 lg:p-10">
                            <h3 class="font-serif text-2xl font-bold text-forest mb-2">
                                {{ $location->name }}
                            </h3>

                            <div class="w-12 h-0.5 bg-terracotta mb-6"></div>

                            <div class="space-y-4 text-muted">
                                @if($location->address)
                                    <div class="flex items-start gap-3">
                                        <div class="w-8 h-8 bg-forest/10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                                            <svg class="w-4 h-4 text-forest" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                      d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                                            </svg>
                                        </div>
                                        <div>
                                            <p class="text-sm font-medium text-forest mb-0.5">Morada</p>
                                            <p class="text-sm">{{ $location->address }}</p>
                                        </div>
                                    </div>
                                @endif

                                @if($location->phone)
                                    <div class="flex items-start gap-3">
                                        <div class="w-8 h-8 bg-forest/10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                                            <svg class="w-4 h-4 text-forest" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                      d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>
                                            </svg>
                                        </div>
                                        <div>
                                            <p class="text-sm font-medium text-forest mb-0.5">Telefone</p>
                                            <a href="tel:{{ $location->phone }}" class="text-sm hover:text-terracotta transition-colors">
                                                {{ $location->phone }}
                                            </a>
                                        </div>
                                    </div>
                                @endif

                                @if($location->email)
                                    <div class="flex items-start gap-3">
                                        <div class="w-8 h-8 bg-forest/10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                                            <svg class="w-4 h-4 text-forest" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                      d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                                            </svg>
                                        </div>
                                        <div>
                                            <p class="text-sm font-medium text-forest mb-0.5">Email</p>
                                            <a href="mailto:{{ $location->email }}" class="text-sm hover:text-terracotta transition-colors">
                                                {{ $location->email }}
                                            </a>
                                        </div>
                                    </div>
                                @endif

                                @if($location->opening_hours)
                                    <div class="flex items-start gap-3">
                                        <div class="w-8 h-8 bg-forest/10 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                                            <svg class="w-4 h-4 text-forest" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                            </svg>
                                        </div>
                                        <div>
                                            <p class="text-sm font-medium text-forest mb-0.5">Horário</p>
                                            <p class="text-sm whitespace-pre-line">{{ $location->opening_hours }}</p>
                                        </div>
                                    </div>
                                @endif
                            </div>

                            @if($location->map_embed_url)
                                <div class="mt-6 rounded-lg overflow-hidden border border-stone-400/40">
                                    @php
                                        $mapUrl = $location->map_embed_url;
                                        if (!str_contains($mapUrl, 'src=') && !str_contains($mapUrl, 'output=embed')) {
                                            $mapUrl = 'https://www.google.com/maps?q=' . urlencode($location->address ?? $location->name);
                                        }
                                    @endphp
                                    <iframe src="{{ $mapUrl }}"
                                            width="100%"
                                            height="250"
                                            style="border:0;"
                                            allowfullscreen=""
                                            loading="lazy"
                                            referrerpolicy="no-referrer-when-downgrade">
                                    </iframe>
                                </div>
                            @endif
                        </div>
                    </div>
                @endforeach
            </div>
        @else
            <div class="text-center py-16">
                <div class="w-20 h-20 bg-forest/10 rounded-full flex items-center justify-center mx-auto mb-6">
                    <svg class="w-10 h-10 text-forest" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                              d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                              d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                    </svg>
                </div>
                <h3 class="font-serif text-xl font-semibold text-forest mb-2">Em breve</h3>
                <p class="text-muted">Estamos a preparar a informação de contactos.</p>
            </div>
        @endif
    </div>
</section>

<section class="py-16 bg-forest">
    <div class="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="font-serif text-3xl font-bold text-white mb-4">
            Prefere falar connosco pelo WhatsApp?
        </h2>
        <p class="text-white/70 font-light mb-8">
            Envie-nos uma mensagem. Respondemos rapidamente em horário laboral.
        </p>

        @if(isset($websiteDefaults) && $websiteDefaults->whatsapp_number)
            <a href="https://wa.me/{{ preg_replace('/[^0-9+]/', '', $websiteDefaults->whatsapp_number) }}"
               target="_blank"
               rel="noopener noreferrer"
               class="inline-flex items-center gap-3 bg-[#25D366] text-white px-8 py-4 rounded-full text-lg font-medium hover:bg-[#22c35e] transition-colors shadow-lg">
                <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                </svg>
                Falar pelo WhatsApp
            </a>
        @else
            <a href="https://wa.me/"
               target="_blank"
               rel="noopener noreferrer"
               class="inline-flex items-center gap-3 bg-[#25D366] text-white px-8 py-4 rounded-full text-lg font-medium hover:bg-[#22c35e] transition-colors shadow-lg">
                <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                </svg>
                Falar pelo WhatsApp
            </a>
        @endif
    </div>
</section>
@endsection
