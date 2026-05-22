@extends('layouts.website')

@section('title', 'Quem Somos - BioBrassica')
@section('meta_description', 'Conheça a história da BioBrassica, a nossa equipa e o nosso compromisso com a agricultura biológica certificada.')

@section('content')
@php
    $teamImage = isset($websiteContent) && $websiteContent->about_image
        ? asset('storage/' . $websiteContent->about_image)
        : null;
@endphp

<section class="relative h-[70vh] flex items-center justify-center overflow-hidden">
    @if($teamImage)
        <img src="{{ $teamImage }}" alt="Equipa BioBrassica" class="absolute inset-0 w-full h-full object-cover">
    @else
        <div class="absolute inset-0 bg-gradient-to-br from-forest via-forest/90 to-forest/70"></div>
    @endif
    <div class="absolute inset-0 bg-forest/50"></div>

    <div class="relative z-10 text-center px-4">
        <h1 class="font-serif text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-4 drop-shadow-lg">
            Quem Somos
        </h1>
        <p class="text-lg md:text-xl text-white/80 font-light max-w-2xl mx-auto">
            Uma história de paixão pela terra e compromisso com a agricultura biológica
        </p>
    </div>
</section>

<section class="py-20 bg-paper">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="flex flex-col lg:flex-row items-center gap-12 mb-20">
            <div class="lg:w-1/2">
                <img src="{{ asset('images/people/001.jpg') }}"
                     alt="O significado de BioBrassica"
                     class="w-full rounded-lg shadow-lg object-cover aspect-[4/3]">
            </div>
            <div class="lg:w-1/2">
                <h2 class="font-serif text-3xl md:text-4xl font-bold text-forest mb-4">
                    O significado de BioBrassica
                </h2>
                <div class="w-20 h-1 bg-terracotta mb-6"></div>
                <p class="text-muted leading-relaxed mb-4">
                    O nome BioBrassica nasce da união entre "Bio" — de biológico — e "Brassica", o género botânico que inclui
                    culturas como os brócolos, couves e nabos, tão presentes na agricultura portuguesa.
                </p>
                <p class="text-muted leading-relaxed mb-4">
                    Representa o nosso compromisso com uma agricultura que respeita os ciclos da natureza, preserva a
                    biodiversidade e oferece alimentos saudáveis, saborosos e certificados.
                </p>
                <p class="text-muted leading-relaxed">
                    Cada produto que sai da nossa horta carrega consigo o saber de gerações, adaptado às exigências
                    e padrões de qualidade da agricultura biológica moderna.
                </p>
            </div>
        </div>

        <div class="flex flex-col lg:flex-row-reverse items-center gap-12 mb-20">
            <div class="lg:w-1/2">
                <img src="{{ asset('images/people/002.jpg') }}"
                     alt="Seleção rigorosa"
                     class="w-full rounded-lg shadow-lg object-cover aspect-[4/3]">
            </div>
            <div class="lg:w-1/2">
                <h2 class="font-serif text-3xl md:text-4xl font-bold text-forest mb-4">
                    Seleção Rigorosa
                </h2>
                <div class="w-20 h-1 bg-terracotta mb-6"></div>
                <p class="text-muted leading-relaxed mb-4">
                    Na BioBrassica, cada produto é cuidadosamente selecionado. Trabalhamos apenas com
                    produtores que partilham os nossos valores e que são certificados para o modo de produção biológico.
                </p>
                <p class="text-muted leading-relaxed mb-4">
                    A qualidade começa na semente e termina no prato. Por isso, acompanhamos de perto
                    todo o processo — desde a seleção das variedades mais adaptadas ao nosso clima, até ao
                    momento da colheita e distribuição.
                </p>
                <p class="text-muted leading-relaxed">
                    Acreditamos que comer bem é um direito de todos, e que a agricultura biológica
                    é o caminho para uma alimentação mais consciente e sustentável.
                </p>
            </div>
        </div>

        <div class="flex flex-col lg:flex-row items-center gap-12">
            <div class="lg:w-1/2">
                <img src="{{ asset('images/people/003.jpg') }}"
                     alt="A nossa exploração"
                     class="w-full rounded-lg shadow-lg object-cover aspect-[4/3]">
            </div>
            <div class="lg:w-1/2">
                <h2 class="font-serif text-3xl md:text-4xl font-bold text-forest mb-4">
                    A Nossa Exploração
                </h2>
                <div class="w-20 h-1 bg-terracotta mb-6"></div>
                <p class="text-muted leading-relaxed mb-4">
                    A nossa exploração agrícola está localizada em Guimarães, no coração do Minho,
                    uma região de tradição agrícola rica e solos férteis.
                </p>
                <p class="text-muted leading-relaxed mb-4">
                    Cultivamos uma grande variedade de hortícolas, frutas e ervas aromáticas,
                    sempre respeitando os princípios da agricultura biológica: rotação de culturas,
                    compostagem natural, controlo biológico de pragas e proteção da biodiversidade.
                </p>
                <p class="text-muted leading-relaxed">
                    Acreditamos que a transparência é fundamental. Por isso, convidamo-lo a conhecer
                    a nossa exploração e a ver de perto como cultivamos os alimentos que chegam à sua mesa.
                </p>
            </div>
        </div>
    </div>
</section>

@if($teamMembers->isNotEmpty())
<section class="py-20 bg-white">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-14">
            <h2 class="font-serif text-3xl md:text-4xl font-bold text-forest mb-4">
                A Nossa Equipa
            </h2>
            <div class="w-20 h-1 bg-terracotta mb-6 mx-auto"></div>
            <p class="text-muted font-light max-w-2xl mx-auto">
                Pessoas apaixonadas que tornam a BioBrassica possível, todos os dias.
            </p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8">
            @foreach($teamMembers as $member)
                <div class="text-center group">
                    <div class="w-40 h-40 mx-auto rounded-full overflow-hidden bg-paper mb-4 border-2 border-terracotta/20 group-hover:border-terracotta/50 transition-colors shadow-md">
                        <img src="{{ $member->photo ? asset('storage/' . $member->photo) : asset('images/people/001.jpg') }}"
                             alt="{{ $member->name }}"
                             class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                             loading="lazy">
                    </div>
                    <h3 class="font-serif text-lg font-semibold text-forest">{{ $member->name }}</h3>
                    <p class="text-terracotta text-sm font-medium">{{ $member->role }}</p>
                </div>
            @endforeach
        </div>
    </div>
</section>
@endif

<section class="py-20 bg-forest">
    <div class="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="font-serif text-3xl md:text-4xl font-bold text-white mb-6">
            Venha Conhecer-nos
        </h2>
        <p class="text-white/70 font-light max-w-2xl mx-auto mb-10">
            Visite a nossa exploração, conheça a nossa equipa e descubra o sabor autêntico
            dos produtos biológicos da BioBrassica.
        </p>
        <a href="{{ route('website.contacts') }}"
           class="inline-flex items-center gap-2 bg-terracotta text-white px-8 py-3 rounded-full font-medium hover:bg-terracotta/90 transition-colors shadow-lg">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
            </svg>
            Contacte-nos
        </a>
    </div>
</section>
@endsection
