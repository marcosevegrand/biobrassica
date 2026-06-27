@php
    $t = $post->translations->where('language', $locale)->first() ?? $post->translations->first();
@endphp

<article class="bg-white rounded-lg border border-stone/40 overflow-hidden shadow-sm hover:shadow-md transition-shadow flex flex-col">
    <a href="{{ route('content.blog-detail', $post->slug) }}" class="block">
        <div class="aspect-[16/10] overflow-hidden bg-paper">
            @if($post->cover_image)
                @php($postImage = str_starts_with($post->cover_image, 'images/') ? asset($post->cover_image) : asset('storage/' . $post->cover_image))
                <img src="{{ $postImage }}"
                     alt="{{ $t?->title }}"
                     class="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                     loading="lazy">
            @else
                <div class="w-full h-full flex items-center justify-center bg-paper">
                    <svg class="w-12 h-12 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                              d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9.5a2.5 2.5 0 00-2.5-2.5H15"/>
                    </svg>
                </div>
            @endif
        </div>
    </a>

    <div class="p-5 flex flex-col flex-1">
        @if($post->published_at)
            <time datetime="{{ $post->published_at->toDateString() }}" class="text-xs text-muted mb-2">
                {{ $post->published_at->format('d/m/Y') }}
            </time>
        @endif

        <a href="{{ route('content.blog-detail', $post->slug) }}" class="block group">
            <h2 class="font-serif text-forest font-bold text-lg leading-tight group-hover:text-terracotta transition-colors">
                {{ $t?->title }}
            </h2>
        </a>

        @if($t?->excerpt)
            <p class="text-sm text-muted mt-2 leading-relaxed line-clamp-3">
                {{ $t->excerpt }}
            </p>
        @endif

        @if($post->tags && count($post->tags))
            <div class="flex flex-wrap gap-1.5 mt-auto pt-4">
                @foreach($post->tags as $tag)
                    <a href="{{ route('content.blog', ['tag' => $tag]) }}"
                       class="inline-block px-2.5 py-0.5 bg-paper border border-stone/40 rounded-full text-xs text-muted hover:bg-forest/10 hover:text-forest transition-colors">
                        {{ $tag }}
                    </a>
                @endforeach
            </div>
        @endif
    </div>
</article>
