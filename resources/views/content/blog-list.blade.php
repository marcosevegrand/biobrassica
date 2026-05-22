@extends('layouts.website')

@section('title', $currentTag ? 'Blog — ' . $currentTag : 'Blog')

@section('content')
<div class="bg-forest/5 border-b border-stone/40">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-16">
        <h1 class="font-serif text-4xl font-bold text-forest">Blog</h1>
        @if($currentTag)
            <p class="mt-3 text-muted">
                Artigos com a tag <span class="font-medium text-terracotta">{{ $currentTag }}</span>
                &mdash; <a href="{{ route('content.blog') }}" class="text-forest hover:underline">Ver todos</a>
            </p>
        @else
            <p class="mt-3 text-muted max-w-2xl">Descubra artigos sobre agricultura biológica, sustentabilidade e alimentação saudável.</p>
        @endif
    </div>
</div>

<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
    @if($posts->isEmpty())
        <div class="bg-white rounded-lg border border-stone/40 p-12 text-center">
            <svg class="w-16 h-16 text-muted mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                      d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2.5 2.5 0 00-2.5-2.5H15"/>
            </svg>
            <h3 class="font-serif text-lg font-semibold text-forest mb-2">Nenhum artigo encontrado</h3>
            <p class="text-muted text-sm">Ainda não há artigos publicados. Volte em breve.</p>
        </div>
    @else
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
            @foreach($posts as $post)
                @include('content.partials.blog-card', ['post' => $post, 'locale' => $locale])
            @endforeach
        </div>

        <div class="mt-12">
            {{ $posts->appends(request()->query())->links() }}
        </div>
    @endif
</div>
@endsection
