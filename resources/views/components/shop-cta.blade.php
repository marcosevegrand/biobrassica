@props([
    'variant' => 'nav',
    'label' => null,
    'shopCta' => null,
])

@php
    $shopCta = $shopCta ?? [
        'coming_soon' => true,
        'url' => '#',
        'label' => 'Em breve',
    ];

    $styles = [
        'nav' => [
            'live' => 'whitespace-nowrap px-5 py-2 bg-paper text-forest text-xs font-medium uppercase tracking-[0.22em] rounded-sm hover:bg-paper/90 transition-colors',
            'soon' => 'whitespace-nowrap px-5 py-2 bg-paper/20 text-paper/60 text-xs font-medium uppercase tracking-[0.22em] rounded-sm cursor-default',
        ],
        'footer' => [
            'live' => 'hover:text-paper transition-colors',
            'soon' => 'text-paper/40 cursor-default',
        ],
        'home' => [
            'live' => 'inline-block px-10 py-4 bg-paper text-forest text-sm uppercase tracking-widest font-medium rounded-sm hover:bg-paper/90 transition-colors',
            'soon' => 'inline-block px-10 py-4 bg-paper/20 text-paper/60 text-sm uppercase tracking-widest font-medium rounded-sm cursor-default',
        ],
        'agriculture' => [
            'live' => 'inline-block px-8 py-3 bg-forest text-paper text-sm uppercase tracking-widest font-medium rounded-sm hover:bg-forest/90 transition-colors',
            'soon' => 'inline-block px-8 py-3 bg-forest/20 text-forest/60 text-sm uppercase tracking-widest font-medium rounded-sm cursor-default',
        ],
    ][$variant] ?? [
        'live' => '',
        'soon' => '',
    ];
@endphp

@if($shopCta['coming_soon'])
    <span {{ $attributes->merge(['class' => $styles['soon']]) }}>Em breve</span>
@else
    <a href="{{ $shopCta['url'] }}" {{ $attributes->merge(['class' => $styles['live']]) }}>{{ $label ?: 'Loja' }}</a>
@endif
