@extends('layouts.website')

@section('title', 'Agricultura Biológica - BioBrassica')
@section('meta_description', 'Saiba mais sobre a agricultura biológica certificada, os nossos métodos de cultivo e as certificações que garantem a qualidade BioBrassica.')

@section('content')
@php
    $agriImage = isset($websiteContent) && $websiteContent->agriculture_image
        ? asset('storage/' . $websiteContent->agriculture_image)
        : null;
@endphp

<section class="relative h-[60vh] flex items-center justify-center overflow-hidden">
    @if($agriImage)
        <img src="{{ $agriImage }}" alt="Agricultura Biológica" class="absolute inset-0 w-full h-full object-cover">
    @else
        <div class="absolute inset-0 bg-gradient-to-br from-forest via-forest/90 to-forest/70"></div>
    @endif
    <div class="absolute inset-0 bg-forest/50"></div>

    <div class="relative z-10 text-center px-4">
        <h1 class="font-serif text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4 drop-shadow-lg">
            Agricultura Biológica
        </h1>
        <p class="text-lg md:text-xl text-white/80 font-light max-w-2xl mx-auto">
            Cultivar com respeito, colher com qualidade
        </p>
    </div>
</section>

<section class="py-16 bg-paper">
    <div class="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <div class="flex flex-wrap justify-center items-center gap-8 mb-16">
            <div class="bg-white rounded-lg p-6 shadow-sm border border-stone-400/40 text-center w-56">
                <img src="{{ asset('images/certs/eu-bio-logo.jpg') }}"
                     alt="Agricultura Biológica - União Europeia"
                     class="h-20 w-auto mx-auto mb-3">
                <p class="text-xs text-muted">
                    Certificado pelo organismo de controlo e certificação para o modo de produção biológico
                </p>
            </div>
            <div class="bg-white rounded-lg p-6 shadow-sm border border-stone-400/40 text-center w-56">
                <img src="{{ asset('images/certs/certiplanet-logo.png') }}"
                     alt="Certiplanet"
                     class="h-16 w-auto mx-auto mb-3">
                <p class="text-xs text-muted">
                    Certiplanet - Certificação de produtos, processos e sistemas
                </p>
            </div>
        </div>

        @if(isset($websiteContent) && $websiteContent->agriculture_content)
            <div class="prose prose-lg max-w-none font-light">
                {!! Str::markdown($websiteContent->agriculture_content) !!}
            </div>
        @else
            <div class="space-y-8">
                <div>
                    <h2 class="font-serif text-2xl md:text-3xl font-bold text-forest mb-4">
                        O que é a Agricultura Biológica?
                    </h2>
                    <div class="w-20 h-1 bg-terracotta mb-6"></div>
                    <p class="text-muted leading-relaxed mb-4">
                        A agricultura biológica é um modo de produção que visa produzir alimentos de elevada qualidade,
                        respeitando os ciclos naturais da terra e promovendo a biodiversidade. Recorrendo a métodos
                        culturais, biológicos e mecânicos em detrimento da utilização de produtos químicos de síntese.
                    </p>
                    <p class="text-muted leading-relaxed">
                        Este modo de produção está regulamentado na União Europeia desde 1991 e é um dos sistemas
                        de produção mais controlados e certificados do mundo. Todos os operadores biológicos
                        são inspecionados anualmente por organismos de controlo e certificação acreditados.
                    </p>
                </div>

                <div>
                    <h3 class="font-serif text-xl font-semibold text-forest mb-3">
                        Como Reconhecer um Produto Biológico?
                    </h3>
                    <p class="text-muted leading-relaxed mb-4">
                        Um produto só pode ser comercializado como "Biológico" ou "Orgânico" se for certificado
                        e ostentar no rótulo o logótipo europeu (Eurofolha) e o código do organismo de certificação.
                        Em Portugal, o principal organismo de controlo e certificação do modo de produção biológico é a SATIVA.
                    </p>
                </div>

                <div>
                    <h3 class="font-serif text-xl font-semibold text-forest mb-3">
                        Os Nossos Métodos
                    </h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div class="bg-white rounded-lg p-6 border border-stone-400/40 shadow-sm">
                            <div class="w-10 h-10 bg-forest/10 rounded-full flex items-center justify-center mb-3">
                                <svg class="w-5 h-5 text-forest" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                                </svg>
                            </div>
                            <h4 class="font-semibold text-forest mb-2">Rotação de Culturas</h4>
                            <p class="text-sm text-muted leading-relaxed">
                                Alternamos as culturas para manter a fertilidade do solo, prevenir pragas e doenças
                                de forma natural, sem recurso a químicos.
                            </p>
                        </div>

                        <div class="bg-white rounded-lg p-6 border border-stone-400/40 shadow-sm">
                            <div class="w-10 h-10 bg-forest/10 rounded-full flex items-center justify-center mb-3">
                                <svg class="w-5 h-5 text-forest" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                          d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                </svg>
                            </div>
                            <h4 class="font-semibold text-forest mb-2">Compostagem Natural</h4>
                            <p class="text-sm text-muted leading-relaxed">
                                Produzimos o nosso próprio composto a partir de matéria orgânica, enriquecendo
                                o solo de forma sustentável e reduzindo resíduos.
                            </p>
                        </div>

                        <div class="bg-white rounded-lg p-6 border border-stone-400/40 shadow-sm">
                            <div class="w-10 h-10 bg-forest/10 rounded-full flex items-center justify-center mb-3">
                                <svg class="w-5 h-5 text-forest" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                          d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"/>
                                </svg>
                            </div>
                            <h4 class="font-semibold text-forest mb-2">Controlo Biológico</h4>
                            <p class="text-sm text-muted leading-relaxed">
                                Utilizamos insetos auxiliares e outros organismos benéficos para controlar pragas,
                                mantendo o equilíbrio natural do ecossistema.
                            </p>
                        </div>

                        <div class="bg-white rounded-lg p-6 border border-stone-400/40 shadow-sm">
                            <div class="w-10 h-10 bg-forest/10 rounded-full flex items-center justify-center mb-3">
                                <svg class="w-5 h-5 text-forest" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                          d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"/>
                                </svg>
                            </div>
                            <h4 class="font-semibold text-forest mb-2">Biodiversidade Protegida</h4>
                            <p class="text-sm text-muted leading-relaxed">
                                Mantemos sebes, faixas florais e zonas de refúgio para promover a biodiversidade
                                e os polinizadores na nossa exploração.
                            </p>
                        </div>
                    </div>
                </div>

                <div>
                    <h3 class="font-serif text-xl font-semibold text-forest mb-3">
                        Benefícios da Agricultura Biológica
                    </h3>
                    <ul class="space-y-3 text-muted leading-relaxed">
                        <li class="flex items-start gap-3">
                            <svg class="w-5 h-5 text-forest flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                            </svg>
                            <span><strong class="text-forest">Alimentos mais saudáveis:</strong> sem resíduos de pesticidas químicos, com maior teor de antioxidantes e nutrientes essenciais.</span>
                        </li>
                        <li class="flex items-start gap-3">
                            <svg class="w-5 h-5 text-forest flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                            </svg>
                            <span><strong class="text-forest">Sabor superior:</strong> os alimentos biológicos têm um sabor mais intenso e autêntico, resultado de um crescimento natural e equilibrado.</span>
                        </li>
                        <li class="flex items-start gap-3">
                            <svg class="w-5 h-5 text-forest flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                            </svg>
                            <span><strong class="text-forest">Proteção do ambiente:</strong> preservação da qualidade da água, do solo e do ar, contribuindo para o combate às alterações climáticas.</span>
                        </li>
                        <li class="flex items-start gap-3">
                            <svg class="w-5 h-5 text-forest flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/>
                            </svg>
                            <span><strong class="text-forest">Bem-estar animal:</strong> os animais são criados ao ar livre, com espaço, alimentação biológica e sem utilização preventiva de antibióticos.</span>
                        </li>
                    </ul>
                </div>
            </div>
        @endif
    </div>
</section>
@endsection
