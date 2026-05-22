@extends('layouts.shop')

@section('title', 'Pagamento - BioBrassica')

@section('content')
<div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <h1 class="font-serif text-3xl font-bold text-forest mb-8">Pagamento</h1>

    {{-- Order Summary --}}
    <div class="bg-white rounded-lg border border-stone/40 p-6 mb-6">
        <h2 class="font-serif text-xl font-bold text-forest mb-2">Encomenda #{{ $order->id }}</h2>
        <p class="text-forest font-bold text-lg">&euro;{{ number_format($order->total, 2) }}</p>
        <p class="text-sm text-muted mt-1">Estado: {{ $order->status === 'pending' ? 'Aguardar Pagamento' : $order->status }}</p>
    </div>

    {{-- Payment Instructions --}}
    <div class="bg-white rounded-lg border border-stone/40 p-6 mb-6">
        <h2 class="font-serif text-xl font-bold text-forest mb-4">
            {{ $paymentDetails['label'] ?? 'Instruções de Pagamento' }}
        </h2>

        @if($order->payment->method === 'mbway')
            <div class="space-y-4">
                <div class="bg-paper rounded-md p-6 text-center">
                    <p class="text-sm text-muted mb-2">Envie o valor de</p>
                    <p class="text-3xl font-bold text-forest mb-2">&euro;{{ number_format($order->total, 2) }}</p>
                    <p class="text-sm text-muted mb-4">por MB WAY para o número</p>
                    <p class="text-2xl font-bold text-forest tracking-wider">
                        {{ $paymentDetails['phone'] }}
                    </p>
                </div>
                <p class="text-sm text-muted text-center">
                    Após o pagamento, a encomenda será confirmada automaticamente.
                </p>
            </div>
        @elseif($order->payment->method === 'bank_transfer')
            <div class="space-y-4">
                <div class="bg-paper rounded-md p-6">
                    <p class="text-sm text-muted mb-4">Transfira o valor de <strong>&euro;{{ number_format($order->total, 2) }}</strong> para:</p>
                    <div class="space-y-3">
                        <div>
                            <span class="text-xs text-muted uppercase tracking-wide">IBAN</span>
                            <p class="text-lg font-mono font-bold text-forest tracking-wider">
                                {{ $paymentDetails['iban'] }}
                            </p>
                        </div>
                        <div>
                            <span class="text-xs text-muted uppercase tracking-wide">BIC/SWIFT</span>
                            <p class="text-lg font-mono font-bold text-forest tracking-wider">
                                {{ $paymentDetails['bic'] }}
                            </p>
                        </div>
                        <div>
                            <span class="text-xs text-muted uppercase tracking-wide">Beneficiário</span>
                            <p class="text-lg font-bold text-forest">
                                {{ $paymentDetails['beneficiary'] }}
                            </p>
                        </div>
                    </div>
                </div>
                <p class="text-sm text-muted text-center">
                    Após a transferência, a confirmação do pagamento pode demorar até 48h úteis.
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
             hx-trigger="every 10s"
             hx-swap="innerHTML">
            @include('orders.partials.payment-status', ['order' => $order])
        </div>
    @endif

    <div class="flex gap-4 mt-6">
        <a href="{{ route('order.show', ['order' => $order->id]) }}"
           class="flex-1 text-center py-3 px-6 border border-forest text-forest rounded-md font-medium hover:bg-forest hover:text-white transition-colors">
            Ver Encomenda
        </a>
        <a href="{{ route('checkout.discard', ['order' => $order->id]) }}"
           onclick="return confirm('Tem a certeza que deseja cancelar esta encomenda?')"
           class="flex-1 text-center py-3 px-6 border border-red-300 text-red-600 rounded-md font-medium hover:bg-red-50 transition-colors">
            Cancelar
        </a>
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
