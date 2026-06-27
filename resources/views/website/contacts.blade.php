@extends('layouts.website')

@section('title', 'Contactos | Biobrassica')
@section('meta_description', 'Entre em contacto com a Biobrassica. Lojas em Braga e Guimarães, ou contacte-nos por telefone e email.')

@section('content')
<section class="bg-forest text-paper pt-28 pb-16">
  <div class="max-w-4xl xl:max-w-5xl mx-auto px-6 sm:px-8 text-center"><p class="text-xs uppercase tracking-[0.3em] text-paper/60 mb-3">Biobrassica</p><h1 class="font-serif text-4xl md:text-5xl italic mb-4">Encontre-nos</h1><p class="text-paper/70 text-sm">Visite-nos nas nossas lojas ou entre em contacto por telefone e email.</p></div>
</section>

<section class="max-w-6xl mx-auto px-6 py-20">
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-12">
    @forelse($locations as $location)
      @php($image = $location->image ? (str_starts_with($location->image, 'images/') ? asset($location->image) : asset('storage/'.$location->image)) : asset($location->pickup_location_code === 'guimaraes' ? 'images/shop/loja-guima.webp' : 'images/shop/loja-braga.webp'))
      <div class="bg-stone/15 rounded-lg p-8">
        <div class="mb-6 rounded-sm overflow-hidden border border-stone/20"><img src="{{ $image }}" alt="{{ $location->name }}" class="w-full aspect-video object-cover"></div>
        <h2 class="font-serif text-2xl italic mb-4 text-center">{{ $location->name }}</h2>
        <div class="space-y-3 text-sm text-muted">
          <div class="flex items-start gap-3"><svg class="w-5 h-5 text-forest shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z"/></svg><div class="whitespace-pre-line">{{ $location->address }}</div></div>
          <div class="flex items-center gap-3"><svg class="w-5 h-5 text-forest shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 0 0 2.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 0 1-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 0 0-1.091-.852H4.5A2.25 2.25 0 0 0 2.25 4.5v2.25Z"/></svg><a href="tel:+351{{ preg_replace('/\D+/', '', $location->phone ?? '') }}" class="hover:text-forest transition-colors">{{ $location->phone }}</a></div>
          <div class="flex items-center gap-3"><svg class="w-5 h-5 text-forest shrink-0" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75"/></svg><a href="mailto:{{ $location->email }}" class="hover:text-forest transition-colors">{{ $location->email }}</a></div>
          <div class="flex items-start gap-3"><svg class="w-5 h-5 text-forest shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"/></svg><div class="whitespace-pre-line">{{ $location->opening_hours }}</div></div>
        </div>
        @php($mapEmbedUrl = method_exists($location, 'safeMapEmbedUrl') ? $location->safeMapEmbedUrl() : (\App\Models\Location::isAllowedMapEmbedUrl($location->map_embed_url ?? null) ? ($location->map_embed_url ?? null) : null))
        @if($mapEmbedUrl)<div class="mt-6 overflow-hidden rounded-sm border border-stone/20"><iframe src="{{ $mapEmbedUrl }}" width="100%" height="250" class="border-0" allowfullscreen loading="lazy" referrerpolicy="no-referrer-when-downgrade" title="{{ $location->name }}"></iframe></div>@endif
      </div>
    @empty
      <div class="col-span-full text-center text-muted">As localizações serão apresentadas aqui assim que forem configuradas no backoffice.</div>
    @endforelse
  </div>
</section>

<section class="bg-forest/5 py-16"><div class="max-w-3xl mx-auto px-6 text-center"><h2 class="font-serif text-2xl italic mb-4">Prefere enviar mensagem?</h2><p class="text-muted text-sm mb-8">Fale connosco pelo WhatsApp para encomendas, dúvidas ou informações.</p><a href="https://wa.me/{{ preg_replace('/\D+/', '', $websiteDefaults->whatsapp_number ?? '+351938722638') }}" target="_blank" rel="noopener" class="inline-flex items-center gap-3 px-8 py-3 bg-[#25D366] text-white rounded-sm text-sm uppercase tracking-widest font-medium hover:bg-[#20bd5a] transition-colors">Enviar Mensagem</a></div></section>
@endsection
