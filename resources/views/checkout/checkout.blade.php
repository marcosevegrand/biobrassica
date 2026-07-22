@extends('layouts.shop')

@section('title', 'Checkout - BioBrassica')

@section('content')
@php($hasPaymentMethods = collect($paymentMethods)->contains(fn ($method) => $method['enabled']))
@php($firstEnabledPaymentMethod = collect($paymentMethods)->filter(fn ($method) => $method['enabled'])->keys()->first())
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

            @if(!empty($warning))
            <div class="bg-amber-50 border border-amber-200 rounded-md p-4 mb-6">
                <p class="text-sm text-amber-800">{{ $warning }}</p>
            </div>
            @endif

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
                    <label class="flex items-center gap-2 {{ $canPickup ? 'cursor-pointer' : 'cursor-not-allowed opacity-60' }}">
                        <input type="radio" name="fulfillment_method" value="pickup"
                                id="fulfillment_pickup"
                                {{ $selectedFulfillmentMethod === 'pickup' ? 'checked' : '' }}
                                @disabled(! $canPickup)
                                class="text-forest focus:ring-forest">
                        <span class="text-sm text-forest font-medium">Levantamento</span>
                    </label>
                    <label class="flex items-center gap-2 {{ $canShipping ? 'cursor-pointer' : 'cursor-not-allowed opacity-60' }}">
                        <input type="radio" name="fulfillment_method" value="shipping"
                                id="fulfillment_shipping"
                                {{ $selectedFulfillmentMethod === 'shipping' ? 'checked' : '' }}
                                @disabled(! $canShipping)
                                class="text-forest focus:ring-forest">
                        <span class="text-sm text-forest font-medium">Envio</span>
                    </label>
                </div>
                @if(! $canPickup || ! $canShipping)
                    <p class="mb-4 text-xs text-muted">Só mostramos como selecionáveis os métodos disponíveis para todos os produtos do carrinho.</p>
                @endif
                @error('fulfillment_method') <p class="mt-1 text-sm text-red-600">{{ $message }}</p> @enderror

                <div id="pickup-section" class="{{ $selectedFulfillmentMethod === 'shipping' ? 'hidden' : '' }}">
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

                <div id="shipping-section" class="{{ $selectedFulfillmentMethod === 'shipping' ? '' : 'hidden' }}">
                    @if($addresses->isNotEmpty())
                        <div class="mb-4">
                            <label for="saved_address" class="block text-sm font-medium text-forest">Moradas guardadas</label>
                            <select id="saved_address"
                                    class="mt-1 block w-full rounded-md border border-stone/40 bg-white px-3 py-2 text-forest shadow-sm focus:border-forest focus:outline-none focus:ring-1 focus:ring-forest">
                                <option value="">Preencher manualmente...</option>
                                @foreach($addresses as $address)
                                    <option value="{{ $address->id }}"
                                            data-line1="{{ e($address->line1) }}"
                                            data-line2="{{ e($address->line2) }}"
                                            data-city="{{ e($address->city) }}"
                                            data-postal-code="{{ e($address->postal_code) }}">
                                        {{ $address->name }} — {{ $address->line1 }}, {{ $address->city }}
                                    </option>
                                @endforeach
                            </select>
                        </div>
                    @endif

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
                    @foreach($paymentMethods as $method => $paymentMethod)
                        @if($paymentMethod['enabled'])
                            <label class="flex items-start gap-3 cursor-pointer p-3 rounded-md border border-stone/40 hover:bg-paper transition-colors">
                                <input type="radio" name="payment_method" value="{{ $method }}"
                                       required
                                       {{ old('payment_method') === $method || (!old('payment_method') && $method === $firstEnabledPaymentMethod) ? 'checked' : '' }}
                                       class="mt-1 text-forest focus:ring-forest">
                                <span>
                                    <span class="block text-sm text-forest font-medium">{{ $paymentMethod['label'] }}</span>
                                    <span class="block text-xs text-muted mt-0.5">{{ $paymentMethod['description'] }}</span>
                                </span>
                            </label>
                        @endif
                    @endforeach

                    @if(!$hasPaymentMethods)
                        <div class="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                            Nenhum método de pagamento está configurado. Contacte a equipa Biobrassica.
                        </div>
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
            <div class="bg-white rounded-lg border border-stone/40 p-6 mb-6"
                 data-pickup-shipping="{{ number_format($pickupShippingCost, 2, '.', '') }}"
                 data-shipping-cost="{{ number_format($shippingCost, 2, '.', '') }}"
                 data-subtotal="{{ number_format($subtotal, 2, '.', '') }}"
                 id="checkout-summary">
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
                    <div class="flex items-center justify-between text-sm mb-2">
                        <span class="text-muted">Subtotal</span>
                        <span class="text-forest font-medium">&euro;<span id="checkout-subtotal">{{ number_format($subtotal, 2) }}</span></span>
                    </div>
                    <div class="flex items-center justify-between text-sm mb-2">
                        <span class="text-muted">Envio</span>
                        <span class="text-forest font-medium">&euro;<span id="checkout-shipping">{{ number_format($selectedFulfillmentMethod === 'shipping' ? $shippingCost : $pickupShippingCost, 2) }}</span></span>
                    </div>
                    @if((float) $settings->free_shipping_min_subtotal > 0)
                        <p class="text-xs text-muted mb-3">Envio gratuito a partir de &euro;{{ number_format((float) $settings->free_shipping_min_subtotal, 2) }} em produtos.</p>
                    @endif
                    <div class="flex items-center justify-between border-t border-stone/40 pt-3">
                        <span class="font-serif text-lg font-bold text-forest">Total</span>
                        <span class="text-xl font-bold text-forest">&euro;<span id="checkout-total">{{ number_format($total, 2) }}</span></span>
                    </div>
                </div>
            </div>

            {{-- Submit --}}
            <button type="submit"
                    @disabled(!$hasPaymentMethods || (! $canPickup && ! $canShipping))
                    class="w-full py-3 px-6 bg-forest text-white rounded-md font-semibold hover:bg-forest/90 disabled:cursor-not-allowed disabled:bg-muted transition-colors">
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
    const savedAddress = document.getElementById('saved_address');
    const summary = document.getElementById('checkout-summary');
    const shippingEl = document.getElementById('checkout-shipping');
    const totalEl = document.getElementById('checkout-total');

    function formatCurrency(value) {
        return Number(value).toLocaleString('pt-PT', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function updateSummary() {
        if (!summary || !shippingEl || !totalEl) return;

        const subtotal = Number(summary.dataset.subtotal || 0);
        const shipping = shippingRadio && shippingRadio.checked
            ? Number(summary.dataset.shippingCost || 0)
            : Number(summary.dataset.pickupShipping || 0);

        shippingEl.textContent = formatCurrency(shipping);
        totalEl.textContent = formatCurrency(subtotal + shipping);
    }

    function toggleSections() {
        if (shippingRadio && shippingRadio.checked) {
            pickupSection.classList.add('hidden');
            shippingSection.classList.remove('hidden');
        } else {
            pickupSection.classList.remove('hidden');
            shippingSection.classList.add('hidden');
        }

        updateSummary();
    }

    if (pickupRadio) pickupRadio.addEventListener('change', toggleSections);
    if (shippingRadio) shippingRadio.addEventListener('change', toggleSections);

    if (savedAddress) {
        savedAddress.addEventListener('change', function () {
            const option = savedAddress.selectedOptions[0];

            if (!option || !option.value) {
                return;
            }

            document.getElementById('shipping_address_line1').value = option.dataset.line1 || '';
            document.getElementById('shipping_address_line2').value = option.dataset.line2 || '';
            document.getElementById('shipping_city').value = option.dataset.city || '';
            document.getElementById('shipping_postal_code').value = option.dataset.postalCode || '';
        });
    }

    toggleSections();
});
</script>
@endsection
