@extends('layouts.website')

@section('title', 'Página não encontrada | Biobrassica')

@section('content')
<section class="min-h-[70vh] flex items-center justify-center bg-paper px-6 py-24">
    <div class="max-w-xl text-center">
        <p class="text-xs uppercase tracking-[0.3em] text-muted mb-4">Erro 404</p>
        <h1 class="font-serif text-4xl md:text-5xl italic text-forest mb-6">Página não encontrada</h1>
        <p class="text-muted leading-relaxed mb-8">A página que procura pode ter sido movida ou já não estar disponível.</p>
        <a href="{{ route('website.home') }}" class="inline-flex items-center justify-center px-8 py-3 bg-forest text-paper text-sm uppercase tracking-widest font-medium rounded-sm hover:bg-forest/90 transition-colors">
            Voltar ao início
        </a>
    </div>
</section>
@endsection
