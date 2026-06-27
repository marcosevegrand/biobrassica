<x-filament-panels::page>
    @php
        $buckets = $this->getOperationalBuckets();
    @endphp

    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        @foreach($buckets as $bucket)
            <section class="rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-700 dark:bg-gray-900">
                <div class="mb-4 flex items-center justify-between">
                    <h2 class="text-sm font-semibold text-gray-950 dark:text-white">{{ $bucket['label'] }}</h2>
                    <span class="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700 dark:bg-gray-800 dark:text-gray-200">{{ $bucket['orders']->count() }} / {{ $bucket['total'] }}</span>
                </div>

                <div class="space-y-3">
                    @forelse($bucket['orders'] as $order)
                        <a href="{{ \App\Filament\Resources\OrderResource::getUrl('edit', ['record' => $order]) }}" class="block rounded-lg border border-gray-100 p-3 hover:border-primary-500 dark:border-gray-800">
                            <div class="flex items-start justify-between gap-3">
                                <div>
                                    <p class="font-medium text-gray-950 dark:text-white">#{{ $order->id }} — {{ $order->name }}</p>
                                    <p class="mt-1 text-xs text-gray-500">{{ $order->items->sum('quantity') }} artigo(s) · {{ $order->created_at->format('d/m H:i') }}</p>
                                    <p class="mt-1 text-xs text-gray-500">{{ $order->fulfillment_method === 'shipping' ? 'Envio' : 'Levantamento' }}</p>
                                </div>
                                <p class="text-sm font-semibold text-gray-950 dark:text-white">€{{ number_format((float) $order->total, 2, ',', '.') }}</p>
                            </div>
                            <p class="mt-2 text-xs {{ $order->payment_state === \App\Models\Order::PAYMENT_CONFIRMED ? 'text-green-600' : 'text-amber-600' }}">
                                Pagamento: {{ \App\Models\Order::paymentStateLabels()[$order->payment_state] ?? $order->payment_state }}
                            </p>
                        </a>
                    @empty
                        <p class="rounded-lg border border-dashed border-gray-200 p-4 text-center text-sm text-gray-500 dark:border-gray-700">Sem encomendas.</p>
                    @endforelse
                </div>
            </section>
        @endforeach
    </div>
</x-filament-panels::page>
