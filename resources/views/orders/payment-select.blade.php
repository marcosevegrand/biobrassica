@extends('layouts.shop')

@section('title', 'Selecionar Pagamento - BioBrassica')

@section('content')
<div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <h1 class="font-serif text-3xl font-bold text-forest mb-8">Selecionar Método de Pagamento</h1>

    <div class="bg-white rounded-lg border border-stone/40 p-6 mb-6">
        <h2 class="font-serif text-xl font-bold text-forest mb-2">Encomenda #{{ $order->id }}</h2>
        <p class="text-sm text-muted">Total: &euro;{{ number_format($order->total, 2) }}</p>
    </div>

    @php $settings = \App\Models\ShopSettings::first(); @endphp

    <form action="{{ route('payment.show', ['order' => $order->id]) }}" method="GET">
        <div class="bg-white rounded-lg border border-stone/40 p-6 mb-6">
            <h2 class="font-serif text-xl font-bold text-forest mb-4">Método de Pagamento</h2>

            <div class="space-y-3">
                @if($settings->mbway_enabled)
                    <label class="flex items-center gap-3 cursor-pointer p-3 rounded-md border border-stone/40 hover:bg-paper transition-colors">
                        <input type="radio" name="method" value="mbway" checked
                               class="text-forest focus:ring-forest">
                        <span class="text-sm text-forest font-medium">MB WAY</span>
                    </label>
                @endif

                @if($settings->bank_transfer_enabled)
                    <label class="flex items-center gap-3 cursor-pointer p-3 rounded-md border border-stone/40 hover:bg-paper transition-colors">
                        <input type="radio" name="method" value="bank_transfer"
                               class="text-forest focus:ring-forest">
                        <span class="text-sm text-forest font-medium">Transferência Bancária</span>
                    </label>
                @endif
            </div>
        </div>

        <button type="submit"
                class="w-full py-3 px-6 bg-forest text-white rounded-md font-semibold hover:bg-forest/90 transition-colors">
            Continuar para Pagamento
        </button>
    </form>
</div>
@endsection
