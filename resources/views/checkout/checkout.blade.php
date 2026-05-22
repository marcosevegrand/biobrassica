@extends('layouts.shop')

@section('title', 'Checkout - BioBrassica')

@section('content')
<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <h1 class="font-serif text-3xl font-bold text-forest mb-8">Checkout</h1>

    @if($count === 0)
        <div class="bg-white rounded-lg border border-stone/40 p-12 text-center">
            <p class="text-muted text-sm mb-6">O carrinho está vazio.</p>
            <a href="{{ route('catalog.products') }}"
               class="inline-flex items-center px-6 py-3 bg-forest text-white rounded-md font-medium hover:bg-forest/90 transition-colors">
                Ver Produtos
            </a>
        </div>
    @else
        <form action="{{ route('checkout.store') }}" method="POST" id="checkout-form">
            @csrf

            {{-- User Info --}}
            <div class="bg-white rounded-lg border border-stone/40 p-6 mb-6">
                <h2 class="font-serif text-xl font-bold text-forest mb-4">Dados Pessoais</h2>
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                        <label for="name" class="block text-sm font-medium text-forest">Nome *</label>
                        <input type="text" name="name" id="name"
                               value="{{ old('name', $user->name) }}"
                               required
                               class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest">
                        @error('name') <p class="mt-1 text-sm text-red-600">{{ $message }}</p> @enderror
                    </div>
                    <div>
                        <label for="email" class="block text-sm font-medium text-forest">Email *</label>
                        <input type="email" name="email" id="email"
                               value="{{ old('email', $user->email) }}"
                               required
                               class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest">
                        @error('email') <p class="mt-1 text-sm text-red-600">{{ $message }}</p> @enderror
                    </div>
                    <div>
                        <label for="phone" class="block text-sm font-medium text-forest">Telefone *</label>
                        <input type="text" name="phone" id="phone"
                               value="{{ old('phone', $user->phone) }}"
                               placeholder="912345678"
                               required
                               class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest">
                        @error('phone') <p class="mt-1 text-sm text-red-600">{{ $message }}</p> @enderror
                    </div>
                    <div>
                        <label for="nif" class="block text-sm font-medium text-forest">NIF</label>
                        <input type="text" name="nif" id="nif"
                               value="{{ old('nif', $user->nif) }}"
                               placeholder="123456789"
                               class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest">
                        @error('nif') <p class="mt-1 text-sm text-red-600">{{ $message }}</p> @enderror
                    </div>
                </div>
            </div>

            {{-- Fulfillment Method --}}
            <div class="bg-white rounded-lg border border-stone/40 p-6 mb-6">
                <h2 class="font-serif text-xl font-bold text-forest mb-4">Método de Entrega</h2>

                <div class="flex gap-4 mb-6">
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="radio" name="fulfillment_method" value="pickup"
                               id="fulfillment_pickup"
                               {{ old('fulfillment_method', 'pickup') === 'pickup' ? 'checked' : '' }}
                               class="text-forest focus:ring-forest">
                        <span class="text-sm text-forest font-medium">Levantamento</span>
                    </label>
                    <label class="flex items-center gap-2 cursor-pointer">
                        <input type="radio" name="fulfillment_method" value="shipping"
                               id="fulfillment_shipping"
                               {{ old('fulfillment_method') === 'shipping' ? 'checked' : '' }}
                               class="text-forest focus:ring-forest">
                        <span class="text-sm text-forest font-medium">Envio</span>
                    </label>
                </div>
                @error('fulfillment_method') <p class="mt-1 text-sm text-red-600">{{ $message }}</p> @enderror

                <div id="pickup-section" class="{{ old('fulfillment_method', 'pickup') === 'shipping' ? 'hidden' : '' }}">
                    <label for="pickup_location" class="block text-sm font-medium text-forest">Local de Levantamento *</label>
                    <select name="pickup_location" id="pickup_location"
                            class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest">
                        <option value="">Selecione um local...</option>
                        @foreach($locations as $location)
                            <option value="{{ $location->id }}"
                                {{ old('pickup_location') == $location->id ? 'selected' : '' }}>
                                {{ $location->name }} - {{ $location->address }}
                            </option>
                        @endforeach
                    </select>
                    @error('pickup_location') <p class="mt-1 text-sm text-red-600">{{ $message }}</p> @enderror
                </div>

                <div id="shipping-section" class="{{ old('fulfillment_method') === 'shipping' ? '' : 'hidden' }}">
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div class="sm:col-span-2">
                            <label for="shipping_address_line1" class="block text-sm font-medium text-forest">Morada *</label>
                            <input type="text" name="shipping_address_line1" id="shipping_address_line1"
                                   value="{{ old('shipping_address_line1') }}"
                                   class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest">
                            @error('shipping_address_line1') <p class="mt-1 text-sm text-red-600">{{ $message }}</p> @enderror
                        </div>
                        <div class="sm:col-span-2">
                            <label for="shipping_address_line2" class="block text-sm font-medium text-forest">Complemento</label>
                            <input type="text" name="shipping_address_line2" id="shipping_address_line2"
                                   value="{{ old('shipping_address_line2') }}"
                                   class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest">
                        </div>
                        <div>
                            <label for="shipping_city" class="block text-sm font-medium text-forest">Localidade *</label>
                            <input type="text" name="shipping_city" id="shipping_city"
                                   value="{{ old('shipping_city') }}"
                                   class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest">
                            @error('shipping_city') <p class="mt-1 text-sm text-red-600">{{ $message }}</p> @enderror
                        </div>
                        <div>
                            <label for="shipping_postal_code" class="block text-sm font-medium text-forest">Código Postal *</label>
                            <input type="text" name="shipping_postal_code" id="shipping_postal_code"
                                   value="{{ old('shipping_postal_code') }}"
                                   class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest">
                            @error('shipping_postal_code') <p class="mt-1 text-sm text-red-600">{{ $message }}</p> @enderror
                        </div>
                    </div>
                </div>
            </div>

            {{-- Payment Method --}}
            <div class="bg-white rounded-lg border border-stone/40 p-6 mb-6">
                <h2 class="font-serif text-xl font-bold text-forest mb-4">Método de Pagamento</h2>

                <div class="space-y-3">
                    @if($settings->mbway_enabled)
                        <label class="flex items-center gap-3 cursor-pointer p-3 rounded-md border border-stone/40 hover:bg-paper transition-colors">
                            <input type="radio" name="payment_method" value="mbway"
                                   {{ old('payment_method') === 'mbway' ? 'checked' : '' }}
                                   class="text-forest focus:ring-forest">
                            <span class="text-sm text-forest font-medium">MB WAY</span>
                        </label>
                    @endif

                    @if($settings->bank_transfer_enabled)
                        <label class="flex items-center gap-3 cursor-pointer p-3 rounded-md border border-stone/40 hover:bg-paper transition-colors">
                            <input type="radio" name="payment_method" value="bank_transfer"
                                   {{ old('payment_method') === 'bank_transfer' ? 'checked' : '' }}
                                   class="text-forest focus:ring-forest">
                            <span class="text-sm text-forest font-medium">Transferência Bancária</span>
                        </label>
                    @endif
                </div>
                @error('payment_method') <p class="mt-1 text-sm text-red-600">{{ $message }}</p> @enderror
            </div>

            {{-- Notes --}}
            <div class="bg-white rounded-lg border border-stone/40 p-6 mb-6">
                <h2 class="font-serif text-xl font-bold text-forest mb-4">Notas</h2>
                <label for="notes" class="block text-sm font-medium text-forest">Observações sobre a encomenda</label>
                <textarea name="notes" id="notes" rows="3"
                          class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest">{{ old('notes') }}</textarea>
                @error('notes') <p class="mt-1 text-sm text-red-600">{{ $message }}</p> @enderror
            </div>

            {{-- Summary --}}
            <div class="bg-white rounded-lg border border-stone/40 p-6 mb-6">
                <h2 class="font-serif text-xl font-bold text-forest mb-4">Resumo</h2>

                <div class="space-y-2">
                    @foreach($cart->items as $item)
                        <div class="flex items-center justify-between text-sm">
                            <span class="text-forest">{{ $item->product->name }} x{{ $item->quantity }}</span>
                            <span class="text-forest font-medium">&euro;{{ number_format($item->quantity * $item->product->price, 2) }}</span>
                        </div>
                    @endforeach
                </div>

                <div class="mt-4 pt-4 border-t border-stone/40">
                    <div class="flex items-center justify-between">
                        <span class="font-serif text-lg font-bold text-forest">Total</span>
                        <span class="text-xl font-bold text-forest">&euro;{{ number_format($total, 2) }}</span>
                    </div>
                </div>
            </div>

            {{-- Submit --}}
            <button type="submit"
                    class="w-full py-3 px-6 bg-forest text-white rounded-md font-semibold hover:bg-forest/90 transition-colors">
                Confirmar Encomenda
            </button>
        </form>
    @endif
</div>

<script>
document.addEventListener('DOMContentLoaded', function () {
    const pickupRadio = document.getElementById('fulfillment_pickup');
    const shippingRadio = document.getElementById('fulfillment_shipping');
    const pickupSection = document.getElementById('pickup-section');
    const shippingSection = document.getElementById('shipping-section');

    function toggleSections() {
        if (shippingRadio.checked) {
            pickupSection.classList.add('hidden');
            shippingSection.classList.remove('hidden');
        } else {
            pickupSection.classList.remove('hidden');
            shippingSection.classList.add('hidden');
        }
    }

    pickupRadio.addEventListener('change', toggleSections);
    shippingRadio.addEventListener('change', toggleSections);
    toggleSections();
});
</script>
@endsection
