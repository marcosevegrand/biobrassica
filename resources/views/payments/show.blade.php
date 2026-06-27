@extends('layouts.shop')

@section('title', 'Pagamento - BioBrassica')

@section('content')
<div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <h1 class="font-serif text-3xl font-bold text-forest mb-8">Pagamento</h1>

    {{-- Order Summary --}}
    <div class="bg-white rounded-lg border border-stone/40 p-6 mb-6">
        <h2 class="font-serif text-xl font-bold text-forest mb-2">Encomenda #{{ $order->id }}</h2>
        <div class="space-y-1 text-sm">
            <div class="flex items-center justify-between"><span class="text-muted">Subtotal</span><span class="text-forest">&euro;{{ number_format($order->subtotal, 2) }}</span></div>
            <div class="flex items-center justify-between"><span class="text-muted">Envio</span><span class="text-forest">&euro;{{ number_format($order->shipping_cost, 2) }}</span></div>
            <div class="flex items-center justify-between border-t border-stone/40 pt-2"><span class="font-medium text-forest">Total</span><span class="text-forest font-bold text-lg">&euro;{{ number_format($order->total, 2) }}</span></div>
        </div>
        @php $orderStatusLabels = \App\Models\Order::statusLabels(); @endphp
        <p class="text-sm text-muted mt-1">Estado: {{ $orderStatusLabels[$order->status] ?? $order->status }}</p>
        @if($order->payment->refund_state)
            <p class="text-sm text-muted mt-1">Reembolso: {{ \App\Models\Payment::refundStateLabels()[$order->payment->refund_state] ?? $order->payment->refund_state }}</p>
        @endif
    </div>

    {{-- Payment Instructions --}}
    <div class="bg-white rounded-lg border border-stone/40 p-6 mb-6">
        <h2 class="font-serif text-xl font-bold text-forest mb-4">
            {{ $paymentDetails['label'] ?? 'Instruções de Pagamento' }}
        </h2>

        @if($order->payment->method === 'mbway')
            <div class="space-y-4">
                <div class="bg-paper rounded-md p-6 text-center">
                    <p class="text-sm text-muted mb-2">Pedido MB WAY enviado para</p>
                    <p class="text-2xl font-bold text-forest tracking-wider mb-4">
                        {{ $paymentDetails['mobile_number'] ?? $order->phone }}
                    </p>
                    <p class="text-sm text-muted mb-2">Valor</p>
                    <p class="text-3xl font-bold text-forest mb-2">&euro;{{ number_format($order->total, 2) }}</p>
                    <p class="text-xs text-muted">Pedido: {{ $paymentDetails['transaction_id'] ?? '—' }}</p>
                </div>
                <p class="text-sm text-muted text-center">
                    Abra a aplicação MB WAY e confirme o pagamento. O estado é atualizado automaticamente pela IfThenPay.
                </p>
            </div>
        @elseif($order->payment->method === 'multibanco')
            <div class="space-y-4">
                <div class="bg-paper rounded-md p-6">
                    <p class="text-sm text-muted mb-4">Pague <strong>&euro;{{ number_format($order->total, 2) }}</strong> por referência Multibanco:</p>
                    <div class="space-y-3">
                        <div>
                            <span class="text-xs text-muted uppercase tracking-wide">Entidade</span>
                            <p class="text-lg font-mono font-bold text-forest tracking-wider">
                                {{ $paymentDetails['entity'] ?? '—' }}
                            </p>
                        </div>
                        <div>
                            <span class="text-xs text-muted uppercase tracking-wide">Referência</span>
                            <p class="text-lg font-mono font-bold text-forest tracking-wider">
                                {{ $paymentDetails['reference'] ?? '—' }}
                            </p>
                        </div>
                        <div>
                            <span class="text-xs text-muted uppercase tracking-wide">Valor</span>
                            <p class="text-lg font-bold text-forest">
                                &euro;{{ number_format($order->total, 2) }}
                            </p>
                        </div>
                    </div>
                </div>
                <p class="text-sm text-muted text-center">
                    A confirmação é automática via callback IfThenPay assim que o pagamento for recebido.
                </p>
            </div>
        @endif
    </div>

    {{-- Timer --}}
    @if($order->payment->expires_at)
        <div class="bg-white rounded-lg border border-stone/40 p-6 mb-6">
            <div class="text-center">
                <p class="text-sm text-muted mb-2">Tempo restante para pagamento</p>
                <p id="payment-timer" class="text-2xl font-bold text-terracotta font-mono"
                   data-expires="{{ $order->payment->expires_at->timestamp }}">
                    --
                </p>
            </div>
        </div>
    @endif

    {{-- Status polling for HTMX --}}
    @if($order->payment->status === 'pending')
        <div id="payment-status-area"
             hx-get="{{ route('payment.status', ['order' => $order->id]) }}"
             hx-trigger="every 30s"
             hx-swap="outerHTML">
            @include('orders.partials.payment-status', ['order' => $order])
        </div>
    @endif

    <div class="flex gap-4 mt-6">
        <a href="{{ route('order.show', ['order' => $order->id]) }}"
           class="flex-1 text-center py-3 px-6 border border-forest text-forest rounded-md font-medium hover:bg-forest hover:text-white transition-colors">
            Ver Encomenda
        </a>
        @if($order->payment->status === \App\Models\Payment::STATUS_PENDING)
            <form method="POST" action="{{ route('checkout.discard', ['order' => $order->id]) }}" class="flex-1" onsubmit="return confirm('Tem a certeza que deseja cancelar esta encomenda?')">
                @csrf
                <button type="submit" class="w-full text-center py-3 px-6 border border-red-300 text-red-600 rounded-md font-medium hover:bg-red-50 transition-colors">
                    Cancelar
                </button>
            </form>
        @endif
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function () {
    const timerEl = document.getElementById('payment-timer');
    if (!timerEl) return;

    const expiresAt = parseInt(timerEl.dataset.expires) * 1000;

    function updateTimer() {
        const now = Date.now();
        const remaining = Math.max(0, expiresAt - now);

        if (remaining <= 0) {
            timerEl.textContent = 'Expirado';
            timerEl.classList.add('text-red-600');
            timerEl.classList.remove('text-terracotta');
            return;
        }

        const mins = Math.floor(remaining / 60000);
        const secs = Math.floor((remaining % 60000) / 1000);
        timerEl.textContent = String(mins).padStart(2, '0') + ':' + String(secs).padStart(2, '0');
    }

    updateTimer();
    setInterval(updateTimer, 1000);
});
</script>
@endsection
