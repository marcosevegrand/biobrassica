@php
    $footerLocations = [
        (object) ['name' => 'Loja Braga', 'address' => "Avenida Doutor António Palha\nBraga", 'phone' => '253 271 187', 'email' => 'geral@biobrassica.pt'],
        (object) ['name' => 'Loja Guimarães', 'address' => "Rua Calouste Gulbenkian\nGuimarães", 'phone' => '253 145 388', 'email' => 'geral@biobrassica.pt'],
    ];
    $whatsapp = preg_replace('/\D+/', '', $websiteDefaults->whatsapp_number ?? '+351938722638');
@endphp
<footer class="bg-forest text-paper">
  <div class="max-w-7xl mx-auto px-6 py-16">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-12">
      <div>
        <a href="{{ route('website.home') }}"><img src="{{ asset('images/brand/logo-white-no-bg.png') }}" alt="Biobrassica" class="h-10 mb-4"></a>
        <p class="text-paper/70 text-sm leading-relaxed max-w-xs">Produtos biológicos frescos, selecionados com cuidado no coração do Minho.</p>
        <div class="flex items-center gap-4 mt-6">
          <a href="https://www.instagram.com/biobrassica/" target="_blank" rel="noopener" aria-label="Instagram" class="text-paper/60 hover:text-paper transition-colors"><svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069z"/></svg></a>
          <a href="https://www.facebook.com/biobrassica" target="_blank" rel="noopener" aria-label="Facebook" class="text-paper/60 hover:text-paper transition-colors"><svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg></a>
          <a href="https://wa.me/{{ $whatsapp }}" target="_blank" rel="noopener" aria-label="WhatsApp" class="text-paper/60 hover:text-paper transition-colors"><svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347"/></svg></a>
        </div>
        <div class="mt-6"><h4 class="font-semibold text-xs uppercase tracking-widest mb-2">Certificações</h4><div class="flex items-center gap-3"><img src="{{ asset('images/certs/eu-bio-logo.jpg') }}" alt="EU Organic Logo" class="h-10 object-contain" loading="lazy"><img src="{{ asset('images/certs/certiplanet-logo.png') }}" alt="Certiplanet" class="h-10 object-contain" loading="lazy"></div></div>
      </div>
      <div>
        <h3 class="font-semibold text-sm uppercase tracking-widest mb-4">As Nossas Lojas</h3>
        <div class="space-y-6 text-sm text-paper/70">
          @forelse($footerLocations as $location)
            <div><p class="font-medium text-paper">{{ $location->name }}</p><p class="whitespace-pre-line">{{ $location->address }}</p><p>{{ $location->phone }}</p><p>{{ $location->email }}</p></div>
          @empty
            <p>As localizações serão apresentadas aqui assim que forem configuradas no backoffice.</p>
          @endforelse
        </div>
      </div>
      <div>
        <h3 class="font-semibold text-sm uppercase tracking-widest mb-4">Navegação</h3>
        <ul class="space-y-2 text-sm text-paper/70">
          <li><a href="{{ route('website.about') }}" class="hover:text-paper transition-colors">Quem Somos</a></li><li><a href="{{ route('website.agriculture') }}" class="hover:text-paper transition-colors">Agricultura Bio</a></li><li><a href="{{ route('content.blog') }}" class="hover:text-paper transition-colors">Blog</a></li><li><a href="{{ route('content.recipes') }}" class="hover:text-paper transition-colors">Receitas</a></li><li><a href="{{ route('shop.home') }}" class="hover:text-paper transition-colors">Catálogo</a></li><li><a href="{{ route('website.contacts') }}" class="hover:text-paper transition-colors">Contactos</a></li>
        </ul>
      </div>
    </div>
    <div class="mt-12 pt-6 border-t border-paper/10 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-paper/50"><p>&copy; {{ date('Y') }} Biobrassica. Todos os direitos reservados.</p><div class="flex items-center gap-4"><a href="{{ route('website.privacy') }}" class="hover:text-paper transition-colors">Política de Privacidade</a><a href="{{ route('website.terms') }}" class="hover:text-paper transition-colors">Termos e Condições</a></div></div>
  </div>
</footer>
