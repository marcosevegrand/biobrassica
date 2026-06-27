@extends('layouts.website')

@section('title', $translation?->title ?? 'Artigo')

@section('content')
<article>
    <div class="relative h-64 md:h-96 bg-forest/10">
        @if($post->cover_image)
            @php($postImage = str_starts_with($post->cover_image, 'images/') ? asset($post->cover_image) : asset('storage/' . $post->cover_image))
            <img src="{{ $postImage }}"
                 alt="{{ $translation?->title }}"
                 class="w-full h-full object-cover">
        @else
            <div class="w-full h-full flex items-center justify-center bg-paper">
                <svg class="w-16 h-16 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                          d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2.5 2.5 0 00-2.5-2.5H15"/>
                </svg>
            </div>
        @endif
    </div>

    <div class="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 py-10">
        <nav class="flex items-center space-x-2 text-sm text-muted mb-8">
            <a href="{{ route('website.home') }}" class="hover:text-forest transition-colors">Início</a>
            <span>/</span>
            <a href="{{ route('content.blog') }}" class="hover:text-forest transition-colors">Blog</a>
            <span>/</span>
            <span class="text-forest font-medium truncate max-w-[200px]">{{ $translation?->title }}</span>
        </nav>

        <h1 class="font-serif text-3xl md:text-4xl font-bold text-forest mb-4">
            {{ $translation?->title }}
        </h1>

        <div class="flex flex-wrap items-center gap-4 text-sm text-muted mb-8">
            @if($post->author)
                <span>{{ $post->author->name }}</span>
            @endif
            @if($post->published_at)
                <span class="hidden sm:inline">&middot;</span>
                <span>{{ $post->published_at->format('d/m/Y') }}</span>
            @endif
        </div>

        @if($post->tags && count($post->tags))
            <div class="flex flex-wrap gap-2 mb-8">
                @foreach($post->tags as $tag)
                    <a href="{{ route('content.blog', ['tag' => $tag]) }}"
                       class="inline-block px-3 py-1 bg-paper border border-stone/40 rounded-full text-xs text-forest hover:bg-forest/10 hover:border-forest/30 transition-colors">
                        {{ $tag }}
                    </a>
                @endforeach
            </div>
        @endif

        @if($translation?->excerpt)
            <p class="text-lg text-muted leading-relaxed mb-10 border-l-4 border-terracotta pl-4">
                {{ $translation->excerpt }}
            </p>
        @endif

        @if($translation?->content)
            <div class="prose prose-forest max-w-none text-forest leading-relaxed space-y-4">
                {!! nl2br(e($translation->content)) !!}
            </div>
        @endif

        <div class="mt-12 pt-8 border-t border-stone/40">
            <a href="{{ route('content.blog') }}" class="inline-flex items-center gap-2 text-terracotta hover:underline font-medium">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
                </svg>
                Voltar para o blog
            </a>
        </div>
    </div>
</article>
@endsection
