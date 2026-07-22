@extends('layouts.website')

@section('title', 'Agricultura Biológica | Biobrassica')
@section('meta_description', 'Saiba como praticamos agricultura biológica certificada no Minho, com respeito pela biodiversidade e pelos ciclos naturais.')

@section('content')
@php
  $agricultureTitle = $websiteContent?->agriculture_title ?: 'Agricultura Biológica';
  $agricultureIntro = 'A agricultura biológica respeita os ciclos naturais, promove a biodiversidade e dispensa pesticidas químicos. Conheça os nossos princípios e certificações.';
  $agricultureImage = $websiteContent?->agriculture_image
    ? (str_starts_with($websiteContent->agriculture_image, 'images/') ? asset($websiteContent->agriculture_image) : asset('storage/'.$websiteContent->agriculture_image))
    : asset('images/products/006.jpg');
@endphp
<section class="relative h-screen flex items-center justify-center overflow-hidden">
  <img src="{{ $agricultureImage }}" alt="Campo de agricultura biológica" class="absolute inset-0 w-full h-full object-cover" loading="eager">
  <div class="relative z-10 text-center text-forest px-8 sm:px-10 md:px-12 py-10 max-w-4xl xl:max-w-5xl rounded-sm bg-paper/80 backdrop-blur-sm">
    <h1 class="font-serif text-4xl md:text-6xl italic mb-6">{{ $agricultureTitle }}</h1>
    <p class="text-base md:text-lg leading-relaxed text-forest/75 max-w-2xl mx-auto">{{ $agricultureIntro }}</p>
  </div>
</section>

<section class="bg-paper pb-20 pt-24">
  <div class="max-w-4xl mx-auto px-6">
    <div class="text-center mb-14"><h2 class="text-3xl font-serif text-forest mb-4 italic">Os Princípios da Agricultura Bio</h2></div>
    <div class="grid md:grid-cols-2 gap-8 mb-16">
      @foreach([
        ['Sem pesticidas sintéticos','Utilizamos apenas métodos naturais de controlo de pragas: insetos auxiliares, rotação de culturas e preparados biológicos.'],
        ['Solo vivo','Alimentamos o solo, não apenas a planta. Compostagem, adubos verdes e coberturas vegetais mantêm a vida microbiana do solo.'],
        ['Sem OGM','Não utilizamos organismos geneticamente modificados em nenhuma fase da produção.'],
        ['Biodiversidade','Promovemos a diversidade de espécies nas nossas hortas, criando ecossistemas resilientes e equilibrados.'],
      ] as $i => $principle)
      <div class="flex gap-4"><div class="shrink-0 w-12 h-12 bg-forest/10 rounded-full flex items-center justify-center"><span class="text-forest font-serif text-lg">{{ $i + 1 }}</span></div><div><h3 class="font-serif text-lg text-forest mb-2">{{ $principle[0] }}</h3><p class="text-muted text-sm leading-relaxed">{{ $principle[1] }}</p></div></div>
      @endforeach
    </div>
  </div>
</section>

<section class="bg-forest/5 py-24">
  <div class="max-w-7xl mx-auto px-6">
    <h2 class="font-serif text-3xl md:text-4xl text-center italic mb-16">As Nossas Certificações</h2>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
      <div class="bg-paper border border-stone/40 rounded-sm p-8 text-center"><img src="{{ asset('images/certs/eu-bio-logo.jpg') }}" alt="Euro Leaf" class="h-20 w-auto mx-auto mb-6" loading="lazy"><h3 class="font-serif text-xl italic mb-4">Euro Leaf</h3><p class="text-muted text-sm leading-relaxed">O logótipo europeu de agricultura biológica garante que pelo menos 95% dos ingredientes agrícolas são de produção biológica certificada, seguindo regulamentos rigorosos da UE.</p></div>
      <div class="bg-paper border border-stone/40 rounded-sm p-8 text-center"><img src="{{ asset('images/certs/certiplanet-logo.png') }}" alt="Certiplanet" class="h-20 w-auto mx-auto mb-6" loading="lazy"><h3 class="font-serif text-xl italic mb-4">Certiplanet</h3><p class="text-muted text-sm leading-relaxed">Organismo de controlo e certificação reconhecido em Portugal, a Certiplanet verifica e atesta que os nossos métodos de produção cumprem todas as normas de agricultura biológica.</p></div>
    </div>
  </div>
</section>

<section class="bg-paper py-20">
  <div class="max-w-4xl mx-auto px-6">
    <div class="text-center mb-14"><p class="text-xs uppercase tracking-[0.3em] text-muted mb-2">Da Terra</p><h2 class="text-3xl font-serif text-forest italic">Calendário Sazonal</h2><p class="text-muted mt-3 max-w-xl mx-auto">Respeitamos as estações do ano. Cada época traz os seus sabores únicos.</p></div>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
      @foreach([['🌱','Primavera','Ervilhas, favas, alfaces, morangos, ervas aromáticas'],['☀️','Verão','Tomates, pepinos, pimentos, beringelas, melancia'],['🍂','Outono','Abóboras, couves, brócolos, castanhas, cogumelos'],['❄️','Inverno','Nabiças, grelos, couves, laranjas, tangerinas']] as $season)
        <div class="text-center p-6 bg-white rounded-lg shadow-sm border border-stone/20"><span class="text-3xl mb-3 block">{{ $season[0] }}</span><h3 class="font-serif text-forest mb-1">{{ $season[1] }}</h3><p class="text-xs text-muted">{{ $season[2] }}</p></div>
      @endforeach
    </div>
  </div>
</section>

<section class="bg-forest/5 py-24">
  <div class="max-w-4xl mx-auto px-6"><div class="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center"><div><h2 class="font-serif text-3xl italic mb-6">Porquê biológico?</h2><div class="space-y-4 text-muted text-sm leading-relaxed"><p>A agricultura biológica não é apenas uma forma de produzir alimentos — é uma filosofia de vida que respeita o equilíbrio natural dos ecossistemas. Ao evitar pesticidas e fertilizantes químicos, protegemos a biodiversidade, a qualidade da água e a saúde do solo.</p><p>Para o consumidor, os alimentos biológicos significam mais sabor, mais nutrientes e a garantia de que cada mordida está livre de resíduos químicos. É uma escolha consciente para a saúde da família e do planeta.</p><p>Na região do Minho, a riqueza do solo e o clima atlântico criam condições ideais para a agricultura biológica, permitindo-nos cultivar uma enorme variedade de produtos ao longo do ano.</p></div></div><div class="overflow-hidden rounded-sm"><img src="{{ asset('images/people/006.jpg') }}" alt="Solo saudável e plantas biológicas" class="w-full aspect-3/4 object-cover" loading="lazy"></div></div></div>
</section>

<section class="relative bg-paper text-forest py-16 overflow-hidden border-t border-b border-stone/30">
  <div class="absolute inset-0 pointer-events-none" aria-hidden="true"><img src="{{ asset('images/arts/cabbage.svg') }}" alt="" class="absolute w-14 md:w-16 opacity-[0.18] -rotate-12 svg-filter-cta top-[8%] left-[9%]"><img src="{{ asset('images/arts/avocado.svg') }}" alt="" class="absolute w-14 md:w-16 opacity-[0.16] rotate-6 svg-filter-cta top-[43%] left-[14%]"><img src="{{ asset('images/arts/garlic.svg') }}" alt="" class="absolute w-14 md:w-16 opacity-[0.16] -rotate-8 svg-filter-cta top-[77%] left-[10%]"><img src="{{ asset('images/arts/strawberry.svg') }}" alt="" class="absolute w-14 md:w-16 opacity-[0.18] rotate-11 svg-filter-cta top-[13%] left-[83%]"><img src="{{ asset('images/arts/onion.svg') }}" alt="" class="absolute w-14 md:w-16 opacity-[0.18] rotate-7 svg-filter-cta top-[52%] left-[87%]"><img src="{{ asset('images/arts/broccoli.svg') }}" alt="" class="absolute w-14 md:w-16 opacity-[0.16] -rotate-9 svg-filter-cta top-[74%] left-[82%]"></div>
  <div class="relative z-10 max-w-3xl mx-auto px-6 text-center"><h2 class="text-2xl font-serif italic mb-4">Prove a diferença do biológico</h2><p class="text-forest/75 mb-8">Consulte o nosso catálogo de produtos ou visite uma das nossas lojas físicas.</p><a href="{{ route('shop.home') }}" class="inline-block px-8 py-3 bg-forest text-paper text-sm uppercase tracking-widest font-medium rounded-sm hover:bg-forest/90 transition-colors">Ver Catálogo</a></div>
</section>
@endsection
