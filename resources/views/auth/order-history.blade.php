@extends('layouts.shop')

@section('title', 'Encomendas - BioBrassica')

@section('content')
<div class="mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8">
    <div class="flex items-center justify-between">
        <h1 class="font-serif text-3xl font-bold text-forest">As Minhas Encomendas</h1>
        <a href="{{ route('shop.profile') }}" class="text-sm text-terracotta hover:underline">Voltar ao Perfil</a>
    </div>

    @if ($orders->isEmpty())
        <div class="mt-12 text-center">
            <p class="text-muted">Ainda não fez nenhuma encomenda.</p>
            <a href="{{ route('shop.home') }}" class="mt-4 inline-block text-sm text-terracotta hover:underline">Ver Produtos</a>
        </div>
    @else
        <div class="mt-8 space-y-6">
            @foreach ($orders as $order)
                <div class="rounded-lg border border-stone/40 bg-white p-6 shadow-sm">
                    <div class="flex flex-wrap items-center justify-between gap-4">
                        <div>
                            <h2 class="font-serif text-lg font-semibold text-forest">
                                Encomenda #{{ $order->id }}
                            </h2>
                            <p class="mt-1 text-sm text-muted">
                                {{ $order->created_at->format('d/m/Y \à\s H:i') }}
                            </p>
                        </div>
                        <div class="text-right">
                            <p class="text-lg font-semibold text-forest">{{ number_format($order->total, 2, ',', ' ') }} &euro;</p>
                            @if((float) $order->shipping_cost > 0)
                                <p class="text-xs text-muted">inclui {{ number_format($order->shipping_cost, 2, ',', ' ') }} &euro; de envio</p>
                            @endif
                            <span class="inline-block mt-1 rounded-full px-2 py-0.5 text-xs font-medium
                                @if ($order->status === 'delivered') bg-green-100 text-green-800
                                @elseif ($order->status === 'cancelled') bg-red-100 text-red-800
                                @elseif ($order->status === 'preparing') bg-blue-100 text-blue-800
                                @elseif ($order->status === 'ready') bg-emerald-100 text-emerald-800
                                @elseif ($order->status === 'in_transit') bg-yellow-100 text-yellow-800
                                @else bg-stone-100 text-stone-800
                                @endif
                            ">
                                {{ \App\Models\Order::statusLabels()[$order->status] ?? 'Pendente' }}
                            </span>
                            @if($order->payment?->refund_state)
                                <span class="inline-block mt-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-800">
                                    Reembolso: {{ \App\Models\Payment::refundStateLabels()[$order->payment->refund_state] ?? $order->payment->refund_state }}
                                </span>
                            @endif
                        </div>
                    </div>

                    @if ($order->items->isNotEmpty())
                        <div class="mt-4 border-t border-stone/40 pt-4">
                            <ul class="divide-y divide-stone/20">
                                @foreach ($order->items as $item)
                                    <li class="flex justify-between py-2 text-sm">
                                        <span class="text-forest">{{ $item->product_name }}</span>
                                        <span class="text-muted">{{ $item->quantity }}x {{ number_format($item->price, 2, ',', ' ') }} &euro;</span>
                                    </li>
                                @endforeach
                            </ul>
                        </div>
                    @endif

                    @if ($order->fulfillment_method === 'pickup' && $order->pickup_location)
                        <div class="mt-4 border-t border-stone/40 pt-4 text-sm text-muted">
                            Levantamento em:
                            @if($order->pickupLocation)
                                <span class="font-medium text-forest">{{ $order->pickupLocation->name }}</span>
                                @if($order->pickupLocation->address)
                                    <br><span class="whitespace-pre-line">{{ $order->pickupLocation->address }}</span>
                                @endif
                            @else
                                Local indisponível
                            @endif
                        </div>
                    @endif

                    @if ($order->fulfillment_method === 'shipping')
                        <div class="mt-4 border-t border-stone/40 pt-4 text-sm text-muted">
                            Envio para: {{ $order->shipping_address_line1 }}, {{ $order->shipping_postal_code }} {{ $order->shipping_city }}
                        </div>
                    @endif
                </div>
            @endforeach
        </div>

        <div class="mt-8">
            {{ $orders->links() }}
        </div>
    @endif
</div>
@endsection
