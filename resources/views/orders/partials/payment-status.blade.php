<div class="bg-white rounded-lg border border-stone/40 p-4">
    @if($order->payment && $order->payment->status === 'paid')
        <div class="flex items-center gap-2 text-green-700">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
            </svg>
            <span class="text-sm font-medium">Pagamento confirmado!</span>
        </div>
        <script>
            window.location.href = "{{ route('checkout.confirm', ['order' => $order->id]) }}";
        </script>
    @elseif($order->payment && in_array($order->payment->status, ['failed', 'rejected'], true))
        <div class="flex items-center gap-2 text-red-600">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
            <span class="text-sm font-medium">Pagamento rejeitado.</span>
        </div>
    @elseif($order->payment && $order->payment->status === 'expired')
        <div class="flex items-center gap-2 text-red-600">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <span class="text-sm font-medium">Tempo de pagamento expirado.</span>
        </div>
    @else
        <p class="text-sm text-muted">A aguardar pagamento...</p>
    @endif
</div>
