@php($currentLocale = app()->getLocale())
<div class="flex items-center gap-1" aria-label="Selecionar idioma">
    @foreach(['pt' => 'PT', 'en' => 'EN', 'fr' => 'FR'] as $locale => $label)
        <form method="POST" action="{{ route('locale.switch', ['locale' => $locale]) }}" class="inline">
            @csrf
            <button type="submit" class="px-2 py-1 text-[0.65rem] uppercase tracking-widest rounded-sm transition-colors {{ $currentLocale === $locale ? 'bg-paper text-forest' : 'text-current opacity-70 hover:opacity-100' }}" aria-current="{{ $currentLocale === $locale ? 'true' : 'false' }}">
                {{ $label }}
            </button>
        </form>
    @endforeach
</div>
