@php
    $t = $recipe->translations->where('language', $locale)->first() ?? $recipe->translations->first();
@endphp

<article class="bg-white rounded-lg border border-stone/40 overflow-hidden shadow-sm hover:shadow-md transition-shadow flex flex-col">
    <a href="{{ route('content.recipe-detail', $recipe->slug) }}" class="block">
        <div class="aspect-[16/10] overflow-hidden bg-paper">
            @if($recipe->cover_image)
                @php($recipeImage = str_starts_with($recipe->cover_image, 'images/') ? asset($recipe->cover_image) : asset('storage/' . $recipe->cover_image))
                <img src="{{ $recipeImage }}"
                     alt="{{ $t?->title }}"
                     class="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                     loading="lazy">
            @else
                <div class="w-full h-full flex items-center justify-center bg-paper">
                    <svg class="w-12 h-12 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                    </svg>
                </div>
            @endif
        </div>
    </a>

    <div class="p-5 flex flex-col flex-1">
        <a href="{{ route('content.recipe-detail', $recipe->slug) }}" class="block group">
            <h2 class="font-serif text-forest font-bold text-lg leading-tight group-hover:text-terracotta transition-colors">
                {{ $t?->title }}
            </h2>
        </a>

        <div class="flex flex-wrap items-center gap-3 mt-2 text-xs text-muted">
            @if($recipe->difficulty)
                <span class="inline-flex items-center gap-1">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M13 10V3L4 14h7v7l9-11h-7z"/>
                    </svg>
                    {{ $recipe->difficulty }}
                </span>
            @endif
            @if($recipe->prep_time || $recipe->cook_time)
                <span class="inline-flex items-center gap-1">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    @if($recipe->prep_time && $recipe->cook_time)
                        {{ $recipe->prep_time }} + {{ $recipe->cook_time }}
                    @else
                        {{ $recipe->prep_time ?? $recipe->cook_time }}
                    @endif
                </span>
            @endif
        </div>

        @if($recipe->tags && count($recipe->tags))
            <div class="flex flex-wrap gap-1.5 mt-auto pt-4">
                @foreach($recipe->tags as $tag)
                    <a href="{{ route('content.recipes', ['tag' => $tag]) }}"
                       class="inline-block px-2.5 py-0.5 bg-paper border border-stone/40 rounded-full text-xs text-muted hover:bg-terracotta/10 hover:text-terracotta transition-colors">
                        {{ $tag }}
                    </a>
                @endforeach
            </div>
        @endif
    </div>
</article>
