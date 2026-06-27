@extends('layouts.website')

@section('title', 'Biobrassica')

@section('content')
@php
  $homeHeroTitle = $websiteContent?->hero_title ?: 'Tudo que precisa para uma alimentação saudável';
  $homeHeroSubtitle = $websiteContent?->hero_subtitle ?: 'Produtos biológicos, saudáveis para si, bons para o ambiente.';
  $homeHeroCtaText = $websiteContent?->hero_cta_text ?: 'Ir para a Loja';
  $homeHeroCtaUrl = $websiteContent?->hero_cta_url ?: route('shop.home');
@endphp
<section class="relative h-screen flex items-center justify-center overflow-hidden">
  <img src="{{ asset('images/products/003.jpg') }}" alt="Biobrassica" class="absolute inset-0 w-full h-full object-cover" loading="eager">
  <div class="relative z-10 text-center text-paper px-6 sm:px-8 w-full max-w-6xl xl:max-w-7xl mx-auto">
    <img src="{{ asset('images/brand/logo-white-no-bg.png') }}" alt="Biobrassica" class="h-16 md:h-20 mx-auto mb-8">
    <h1 class="font-serif text-3xl sm:text-4xl md:text-6xl lg:text-7xl leading-tight mb-6">
      @foreach(preg_split('/\r\n|\r|\n/', wordwrap($homeHeroTitle, 28)) as $line)
        <span class="block">{{ $line }}</span>
      @endforeach
    </h1>
    <p class="text-sm md:text-base uppercase tracking-widest text-paper/80">{{ $homeHeroSubtitle }}</p>
  </div>
</section>

<section class="bg-paper py-24">
  <div class="max-w-5xl mx-auto px-6">
    <div class="flex flex-col md:flex-row gap-12 items-center">
      <div class="w-56 md:w-64 shrink-0 rounded-sm overflow-hidden shadow-md self-start">
        <img src="{{ asset('images/people/006.jpg') }}" alt="Engª Ângela Pereira" class="w-full h-80 object-cover object-top" loading="lazy">
      </div>
      <div class="border-l-2 border-terracotta/40 pl-8">
        <blockquote class="font-serif text-xl md:text-2xl italic text-forest leading-relaxed mb-8">
          Temos conseguido ao longo destes anos oferecer cada vez mais produtos frescos, colhidos no próprio dia, vindos das mãos de produtores que se levantam às 5h da manhã num esforço último de transmitir a vitalidade e qualidade das suas terras aos consumidores que já se haviam esquecido do sabor e do cheiro dos legumes acabados de colher!
        </blockquote>
        <p class="text-sm font-medium text-forest tracking-wide">Engª Ângela Pereira</p>
        <p class="text-xs text-muted mt-0.5 uppercase tracking-widest">Fundadora</p>
      </div>
    </div>
  </div>
</section>

@if(isset($featuredRecipes) && $featuredRecipes->isNotEmpty())
<section class="bg-paper py-24">
  <div class="max-w-7xl mx-auto px-6">
    <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-10">
      <div>
        <p class="text-xs uppercase tracking-[0.3em] text-terracotta mb-3">Receitas</p>
        <h2 class="font-serif text-3xl md:text-4xl italic text-forest">Inspiração para cozinhar bio</h2>
      </div>
      <a href="{{ route('content.recipes') }}" class="text-xs uppercase tracking-widest text-forest hover:text-terracotta transition-colors">Ver todas</a>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
      @foreach($featuredRecipes as $recipe)
        @include('content.partials.recipe-card', ['recipe' => $recipe, 'locale' => $locale ?? app()->getLocale()])
      @endforeach
    </div>
  </div>
</section>
@endif

<section class="relative bg-forest text-paper py-24 overflow-hidden">
  <div class="absolute inset-0 pointer-events-none" aria-hidden="true">
    <img src="{{ asset('images/arts/broccoli.svg') }}" alt="" class="absolute w-14 md:w-16 opacity-[0.22] rotate-8 svg-filter-hero top-[6%] left-[9%]">
    <img src="{{ asset('images/arts/avocado.svg') }}" alt="" class="absolute w-14 md:w-16 opacity-[0.19] -rotate-5 svg-filter-hero top-[27%] left-[15%]">
    <img src="{{ asset('images/arts/onion.svg') }}" alt="" class="absolute w-14 md:w-16 opacity-[0.21] rotate-12 svg-filter-hero top-[53%] left-[10%]">
    <img src="{{ asset('images/arts/cabbage.svg') }}" alt="" class="absolute w-14 md:w-16 opacity-[0.20] -rotate-9 svg-filter-hero top-[78%] left-[14%]">
    <img src="{{ asset('images/arts/tomato.svg') }}" alt="" class="absolute w-14 md:w-16 opacity-[0.19] -rotate-7 svg-filter-hero top-[11%] left-[82%]">
    <img src="{{ asset('images/arts/carrot.svg') }}" alt="" class="absolute w-14 md:w-16 opacity-[0.22] rotate-5 svg-filter-hero top-[36%] left-[87%]">
    <img src="{{ asset('images/arts/grapes.svg') }}" alt="" class="absolute w-14 md:w-16 opacity-[0.20] -rotate-11 svg-filter-hero top-[60%] left-[81%]">
    <img src="{{ asset('images/arts/strawberry.svg') }}" alt="" class="absolute w-14 md:w-16 opacity-[0.21] rotate-8 svg-filter-hero top-[82%] left-[85%]">
  </div>
  <div class="relative z-10 max-w-3xl mx-auto px-6 text-center">
    <p class="text-xs uppercase tracking-[0.3em] text-paper/60 mb-4">Loja Online</p>
    <h2 class="text-3xl md:text-4xl font-serif italic mb-6">Descubra os nossos produtos</h2>
    <p class="text-paper/70 mb-10 max-w-xl mx-auto">Entrega em todo o Portugal continental ou levantamento nas nossas lojas em Braga e Guimarães.</p>
    <a href="{{ $homeHeroCtaUrl }}" class="inline-block px-10 py-4 bg-paper text-forest text-sm uppercase tracking-widest font-medium rounded-sm hover:bg-paper/90 transition-colors">{{ $homeHeroCtaText }}</a>
  </div>
</section>

<section class="max-w-7xl mx-auto px-6 py-24">
  <div class="flex items-center justify-between mb-8">
    <h2 class="font-serif text-3xl md:text-4xl italic">Instagram</h2>
    <a href="https://www.instagram.com/biobrassica/" target="_blank" rel="noopener noreferrer" class="text-xs uppercase tracking-widest text-forest hover:text-terracotta transition-colors">@biobrassica</a>
  </div>
  @if(isset($instagramPosts) && $instagramPosts->isNotEmpty())
    <div class="instagram-grid grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      @foreach($instagramPosts as $post)
        <blockquote class="instagram-media" data-instgrm-permalink="{{ $post->permalink }}" data-instgrm-captioned data-instgrm-version="14" style="margin:0;max-width:540px;min-width:280px;width:100%;"></blockquote>
      @endforeach
    </div>
    <script async src="//www.instagram.com/embed.js"></script>
  @else
    <div class="text-center py-12"><p class="text-sm text-muted">O feed do Instagram está temporariamente indisponível. Veja as novidades diretamente no nosso perfil.</p><a href="https://www.instagram.com/biobrassica/" target="_blank" rel="noopener noreferrer" class="inline-block mt-4 px-6 py-2 bg-forest text-paper text-xs uppercase tracking-widest rounded-sm hover:bg-forest/90 transition-colors">@biobrassica</a></div>
  @endif
</section>
@endsection
