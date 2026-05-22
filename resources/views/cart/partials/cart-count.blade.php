<a href="{{ route('cart.detail') }}" class="relative p-2 block text-forest hover:text-terracotta transition-colors">
    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z"/>
    </svg>
    @if($count > 0)
        <span class="absolute -top-1 -right-1 bg-terracotta text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
            {{ $count }}
        </span>
    @endif
</a>
