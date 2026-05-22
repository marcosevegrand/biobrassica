@extends('layouts.shop')

@section('title', 'Encomenda Confirmada - BioBrassica')

@section('content')
<div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
    <div class="bg-white rounded-lg border border-stone/40 p-12 text-center">
        <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
        </div>

        <h1 class="font-serif text-3xl font-bold text-forest mb-4">Encomenda Confirmada!</h1>
        <p class="text-muted mb-2">A sua encomenda #{{ $order->id }} foi registada com sucesso.</p>
        <p class="text-sm text-muted mb-8">
            @if($order->payment)
                @if($order->payment->status === 'pending')
                    O pagamento está pendente. Por favor, efetue o pagamento para confirmar a encomenda.
                @elseif($order->payment->status === 'paid')
                    O pagamento foi confirmado. Iremos processar a sua encomenda brevemente.
                @endif
            @endif
        </p>

        <div class="flex flex-col sm:flex-row gap-4 justify-center">
            <a href="{{ route('order.show', ['order' => $order->id]) }}"
               class="px-6 py-3 bg-forest text-white rounded-md font-medium hover:bg-forest/90 transition-colors">
                Ver Encomenda
            </a>

            @if($order->payment && $order->payment->status === 'pending')
                <a href="{{ route('payment.show', ['order' => $order->id]) }}"
                   class="px-6 py-3 border border-forest text-forest rounded-md font-medium hover:bg-forest hover:text-white transition-colors">
                    Efetuar Pagamento
                </a>
            @endif

            <a href="{{ route('catalog.products') }}"
               class="px-6 py-3 border border-stone/40 text-forest rounded-md font-medium hover:bg-paper transition-colors">
                Continuar a Comprar
            </a>
        </div>
    </div>
</div>
@endsection
