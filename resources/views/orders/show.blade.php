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
                @elseif($order->status === 'preparing')
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                        Em preparação
                    </span>
                @elseif($order->status === 'ready')
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-emerald-100 text-emerald-800">
                        Pronta para levantamento
                    </span>
                @elseif($order->status === 'in_transit')
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-sky-100 text-sky-800">
                        Em distribuição
                    </span>
                @elseif($order->status === 'delivered')
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                        Entregue
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
                    @elseif($order->payment->status === 'confirmed')
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                            Pagamento Confirmado
                        </span>
                    @elseif($order->payment->status === 'cancelled')
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                            Pagamento Cancelado
                        </span>
                    @elseif($order->payment->status === 'refunded')
                        <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                            Pagamento Reembolsado
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

            <div class="mt-4 pt-4 border-t border-stone/40 space-y-2">
                <div class="flex items-center justify-between text-sm">
                    <span class="text-muted">Subtotal</span>
                    <span class="text-forest font-medium">&euro;{{ number_format($order->subtotal, 2) }}</span>
                </div>
                <div class="flex items-center justify-between text-sm">
                    <span class="text-muted">Envio</span>
                    <span class="text-forest font-medium">&euro;{{ number_format($order->shipping_cost, 2) }}</span>
                </div>
                <div class="flex items-center justify-between border-t border-stone/40 pt-3">
                    <span class="font-serif text-lg font-bold text-forest">Total</span>
                    <span class="text-xl font-bold text-forest">&euro;{{ number_format($order->total, 2) }}</span>
                </div>
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
                @if($order->pickupLocation)
                    <p class="text-sm text-forest mt-1">
                        <span class="font-medium">Local:</span> {{ $order->pickupLocation->name }}
                    </p>
                    <p class="text-sm text-muted">{{ $order->pickupLocation->address }}</p>
                @else
                    <p class="text-sm text-muted mt-1">Local indisponível</p>
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
                    {{ $order->payment->method === 'mbway' ? 'MB WAY' : ($order->payment->method === 'multibanco' ? 'Multibanco' : $order->payment->method) }}
                </p>
                <p class="text-sm text-forest mt-1">
                    <span class="font-medium">Valor:</span> &euro;{{ number_format($order->payment->amount, 2) }}
                </p>
                <p class="text-sm text-forest mt-1">
                    <span class="font-medium">Estado:</span>
                    @if($order->payment->status === 'pending')
                        Pendente
                    @elseif($order->payment->status === 'confirmed')
                        Confirmado
                    @elseif($order->payment->status === 'refunded')
                        Reembolsado
                    @elseif($order->payment->status === 'cancelled')
                        Cancelado
                    @endif
                </p>

                @if($order->payment->expires_at)
                    <p class="text-sm text-muted mt-1">
                        Expira: {{ $order->payment->expires_at->format('d/m/Y H:i') }}
                    </p>
                @endif

                @if($order->payment->refund_state)
                    <div class="mt-4 rounded-md bg-paper p-4 text-sm text-forest">
                        <p class="font-medium">Reembolso: {{ \App\Models\Payment::refundStateLabels()[$order->payment->refund_state] ?? $order->payment->refund_state }}</p>
                        @if($order->payment->refund_reason)
                            <p class="mt-1 text-muted">Motivo: {{ $order->payment->refund_reason }}</p>
                        @endif
                        @if($order->payment->refunded_at)
                            <p class="mt-1 text-muted">Concluído em {{ $order->payment->refunded_at->format('d/m/Y H:i') }}</p>
                        @endif
                    </div>
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
                @if($order->payment && $order->payment->status === 'pending')
                    <a href="{{ route('payment.show', ['order' => $order->id]) }}"
                       class="px-6 py-2 bg-forest text-white rounded-md font-medium hover:bg-forest/90 transition-colors text-sm">
                        Efetuar Pagamento
                    </a>
                @else
                    <a href="{{ route('checkout.confirm', ['order' => $order->id]) }}"
                       class="px-6 py-2 bg-forest text-white rounded-md font-medium hover:bg-forest/90 transition-colors text-sm">
                        Ver resumo
                    </a>
                @endif
                <form method="POST" action="{{ route('checkout.discard', ['order' => $order->id]) }}" onsubmit="return confirm('Tem a certeza que deseja cancelar esta encomenda?')">
                    @csrf
                    <button type="submit" class="px-6 py-2 border border-red-300 text-red-600 rounded-md font-medium hover:bg-red-50 transition-colors text-sm">
                        Cancelar Encomenda
                    </button>
                </form>
            </div>
        @endif
    </div>
</div>
@endsection
