@extends('layouts.shop')

@section('title', 'Encomenda - BioBrassica')

@section('content')
<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="flex items-center justify-between mb-8">
        <h1 class="font-serif text-3xl font-bold text-forest">Encomenda #{{ $order->id }}</h1>
        <a href="{{ route('shop.orders') }}" class="text-sm text-terracotta hover:underline">
            &larr; Voltar às encomendas
        </a>
    </div>

    <div class="space-y-6">
        {{-- Status --}}
        <div class="bg-white rounded-lg border border-stone/40 p-6">
            <h2 class="font-serif text-xl font-bold text-forest mb-4">Estado</h2>
            <div class="flex items-center gap-3">
                @if($order->status === 'pending')
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                        Pendente
                    </span>
                @elseif($order->status === 'confirmed')
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                        Confirmada
                    </span>
                @elseif($order->status === 'completed')
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                        Concluída
                    </span>
                @elseif($order->status === 'cancelled')
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                        Cancelada
                    </span>
                @endif

                @if($order->payment)
                    @if($order->payment->status === 'pending')
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
                            Pagamento Pendente
                        </span>
                    @elseif($order->payment->status === 'paid')
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                            Pago
                        </span>
                    @elseif($order->payment->status === 'failed')
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                            Pagamento Falhou
                        </span>
                    @endif
                @endif
            </div>
        </div>

        {{-- Items --}}
        <div class="bg-white rounded-lg border border-stone/40 p-6">
            <h2 class="font-serif text-xl font-bold text-forest mb-4">Produtos</h2>
            <div class="space-y-3">
                @foreach($order->items as $item)
                    <div class="flex items-center justify-between py-2 border-b border-stone/40 last:border-0">
                        <div>
                            <p class="text-forest font-medium">{{ $item->product_name }}</p>
                            <p class="text-xs text-muted">Qtd: {{ $item->quantity }} x &euro;{{ number_format($item->price, 2) }}</p>
                        </div>
                        <span class="text-forest font-bold">&euro;{{ number_format($item->quantity * $item->price, 2) }}</span>
                    </div>
                @endforeach
            </div>

            <div class="mt-4 pt-4 border-t border-stone/40 flex items-center justify-between">
                <span class="font-serif text-lg font-bold text-forest">Total</span>
                <span class="text-xl font-bold text-forest">&euro;{{ number_format($order->total, 2) }}</span>
            </div>
        </div>

        {{-- Delivery Info --}}
        <div class="bg-white rounded-lg border border-stone/40 p-6">
            <h2 class="font-serif text-xl font-bold text-forest mb-4">Entrega</h2>
            <p class="text-sm text-forest">
                <span class="font-medium">Método:</span>
                {{ $order->fulfillment_method === 'pickup' ? 'Levantamento' : 'Envio' }}
            </p>

            @if($order->fulfillment_method === 'pickup' && $order->pickup_location)
                @php $location = \App\Models\Location::find($order->pickup_location); @endphp
                @if($location)
                    <p class="text-sm text-forest mt-1">
                        <span class="font-medium">Local:</span> {{ $location->name }}
                    </p>
                    <p class="text-sm text-muted">{{ $location->address }}</p>
                @endif
            @elseif($order->fulfillment_method === 'shipping')
                <p class="text-sm text-forest mt-1">
                    <span class="font-medium">Morada:</span>
                    {{ $order->shipping_address_line1 }}
                    @if($order->shipping_address_line2), {{ $order->shipping_address_line2 }}@endif
                </p>
                <p class="text-sm text-forest">
                    {{ $order->shipping_postal_code }} {{ $order->shipping_city }}
                </p>
            @endif
        </div>

        {{-- Payment --}}
        @if($order->payment)
            <div class="bg-white rounded-lg border border-stone/40 p-6">
                <h2 class="font-serif text-xl font-bold text-forest mb-4">Pagamento</h2>
                <p class="text-sm text-forest">
                    <span class="font-medium">Método:</span>
                    {{ $order->payment->method === 'mbway' ? 'MB WAY' : 'Transferência Bancária' }}
                </p>
                <p class="text-sm text-forest mt-1">
                    <span class="font-medium">Valor:</span> &euro;{{ number_format($order->payment->amount, 2) }}
                </p>
                <p class="text-sm text-forest mt-1">
                    <span class="font-medium">Estado:</span>
                    @if($order->payment->status === 'pending')
                        Pendente
                    @elseif($order->payment->status === 'paid')
                        Pago
                    @elseif($order->payment->status === 'failed')
                        Falhou
                    @elseif($order->payment->status === 'cancelled')
                        Cancelado
                    @endif
                </p>

                @if($order->payment->expires_at)
                    <p class="text-sm text-muted mt-1">
                        Expira: {{ $order->payment->expires_at->format('d/m/Y H:i') }}
                    </p>
                @endif

                @if($order->payment->status === 'pending')
                    <div class="mt-4">
                        <a href="{{ route('payment.show', ['order' => $order->id]) }}"
                           class="inline-flex items-center px-4 py-2 bg-forest text-white rounded-md font-medium hover:bg-forest/90 transition-colors text-sm">
                            Efetuar Pagamento
                        </a>
                    </div>
                @endif
            </div>
        @endif

        {{-- Actions --}}
        @if($order->status === 'pending')
            <div class="flex gap-4">
                <a href="{{ route('checkout.confirm', ['order' => $order->id]) }}"
                   class="px-6 py-2 bg-forest text-white rounded-md font-medium hover:bg-forest/90 transition-colors text-sm">
                    Confirmar Encomenda
                </a>
                <a href="{{ route('checkout.discard', ['order' => $order->id]) }}"
                   onclick="return confirm('Tem a certeza que deseja cancelar esta encomenda?')"
                   class="px-6 py-2 border border-red-300 text-red-600 rounded-md font-medium hover:bg-red-50 transition-colors text-sm">
                    Cancelar Encomenda
                </a>
            </div>
        @endif
    </div>
</div>
@endsection
