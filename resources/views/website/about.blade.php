@extends('layouts.website')

@section('title', 'Quem Somos | Biobrassica')
@section('meta_description', 'Conheça a história da Biobrassica, uma empresa familiar dedicada à agricultura biológica no Minho.')

@section('content')
<section class="relative h-screen flex items-center justify-center overflow-hidden">
  <img src="{{ asset('images/people/003.jpg') }}" alt="A equipa Biobrassica" class="absolute inset-0 w-full h-full object-cover" loading="eager">
  <div class="relative z-10 text-center text-paper px-6 sm:px-8 max-w-5xl xl:max-w-6xl pt-20 sm:pt-24 md:pt-28">
    <h1 class="text-4xl sm:text-5xl md:text-6xl font-serif leading-tight">Do campo à sua mesa, com quem conhece a terra</h1>
    <p class="mt-6 text-lg sm:text-xl md:text-2xl text-paper/90 max-w-2xl mx-auto">Pessoas reais, produtos de confiança</p>
  </div>
</section>

<section class="max-w-7xl mx-auto px-6 sm:px-8 pt-24 pb-12">
  <div class="space-y-16">
    <article class="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12 items-center bg-forest/5 rounded-sm p-6 md:p-8"><div class="space-y-4"><h2 class="font-serif text-3xl md:text-4xl italic">O que significa "Biobrassica"</h2><p class="text-muted leading-relaxed">O nome "Biobrassica" junta duas ideias que orientam tudo o que fazemos: Bio, pela agricultura biológica e por um modo de produção responsável, e brassica, em homenagem à família de hortícolas que simboliza a origem agrícola da nossa região.</p></div><div class="border border-stone/40 rounded-sm overflow-hidden"><img src="{{ asset('images/products/002.jpg') }}" alt="Produtos biológicos Biobrassica" class="w-full aspect-4/3 object-cover bg-paper" loading="lazy"></div></article>
    <article class="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12 items-center bg-forest/5 rounded-sm p-6 md:p-8"><div class="space-y-4 md:order-2"><h2 class="font-serif text-3xl md:text-4xl italic">Como escolhemos os produtos</h2><p class="text-muted leading-relaxed">Somos, acima de tudo, uma loja. Escolhemos produtos de época com foco em frescura, origem e consistência, trabalhando com fornecedores e produtores de confiança alinhados com os nossos valores. A qualidade é acompanhada diariamente em loja, desde a receção ao acondicionamento e à exposição, para garantir produtos frescos, seguros e com origem clara para os nossos clientes.</p></div><div class="border border-stone/40 rounded-sm overflow-hidden md:order-1"><img src="{{ asset('images/products/001.jpg') }}" alt="Produção biológica" class="w-full aspect-4/3 object-cover bg-paper" loading="lazy"></div></article>
  </div>
</section>

<section class="max-w-7xl mx-auto px-6 sm:px-8 pt-12 pb-12">
  <article class="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12 items-center bg-forest/5 rounded-sm p-6 md:p-8"><div class="space-y-4"><h2 class="font-serif text-3xl md:text-4xl italic">A nossa quinta biológica</h2><p class="text-muted leading-relaxed">A nossa quinta biológica é um projeto complementar, em pequena escala, que apoia a atividade da loja. Serve para reforçar alguns produtos e manter ligação direta à terra, sem substituir a nossa atividade principal: selecionar e disponibilizar, em loja, produtos de qualidade para a comunidade.</p></div><div class="border border-stone/40 rounded-sm overflow-hidden"><img src="{{ asset('images/people/001.jpg') }}" alt="Quinta biológica da Biobrassica" class="w-full aspect-4/3 object-cover bg-paper" loading="lazy"></div></article>
</section>

@if(isset($teamMembers) && $teamMembers->isNotEmpty())
<section class="max-w-7xl mx-auto px-6 sm:px-8 pt-6 pb-16"><div class="flex flex-col gap-4 text-center"><p class="text-xs uppercase tracking-[0.3em] text-muted">A equipa Biobrassica</p><h2 class="font-serif text-3xl md:text-4xl italic">Pessoas reais, produtos de confiança</h2><p class="mx-auto max-w-2xl text-muted">Conheça a equipa que acompanha diariamente o atendimento, o aprovisionamento e a curadoria da loja.</p></div><div class="mt-10 grid gap-6 sm:grid-cols-2 xl:grid-cols-4">@foreach($teamMembers as $member)<article class="overflow-hidden rounded-2xl border border-stone/20 bg-paper shadow-sm"><div class="aspect-4/5 overflow-hidden bg-forest/5">@php($photo = $member->photo && str_starts_with($member->photo, 'images/') ? asset($member->photo) : ($member->photo ? asset('storage/'.$member->photo) : asset('images/people/006.jpg')))<img src="{{ $photo }}" alt="{{ $member->name }}" class="h-full w-full object-cover" loading="lazy"></div><div class="space-y-2 p-5 text-center"><h3 class="font-serif text-2xl italic text-forest">{{ $member->name }}</h3><p class="text-sm uppercase tracking-[0.22em] text-muted">{{ $member->role }}</p></div></article>@endforeach</div></section>
@endif

<section class="px-6 sm:px-8 pb-24"><div class="max-w-4xl mx-auto bg-forest rounded-2xl p-6 sm:p-10"><p class="text-xs uppercase tracking-[0.3em] text-paper/50 mb-3 text-center">As nossas lojas</p><h2 class="text-2xl md:text-3xl font-serif italic text-paper text-center mb-8">Conheça os nossos espaços</h2><div class="rounded-lg overflow-hidden shadow-2xl mb-10"><video class="w-full" controls preload="metadata" poster="{{ asset('images/brand/logo-white-no-bg.png') }}"><source src="{{ asset('videos/video_brassica.mp4') }}" type="video/mp4">O seu navegador não suporta vídeo.</video></div><div class="text-center"><p class="text-paper/70 mb-8">Visite as nossas lojas em Braga e Guimarães para conhecer os nossos produtos e a nossa equipa.</p><a href="{{ route('website.contacts') }}" class="inline-block px-8 py-3 bg-paper text-forest text-sm uppercase tracking-widest font-medium rounded-sm hover:bg-paper/90 transition-colors">Ver Localizações</a></div></div></section>
@endsection
