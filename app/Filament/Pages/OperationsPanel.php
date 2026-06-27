<?php

namespace App\Filament\Pages;

use App\Models\Order;
use App\Models\Payment;
use Filament\Pages\Page;

class OperationsPanel extends Page
{
    protected static ?string $navigationIcon = 'heroicon-o-view-columns';

    protected static ?string $navigationGroup = 'Operação';

    protected static ?string $navigationLabel = 'Painel Operacional';

    protected static ?string $title = 'Painel Operacional';

    protected static ?string $slug = 'operacoes/painel';

    protected static string $view = 'filament.pages.operations-panel';

    public function getOperationalBuckets(): array
    {
        return [
            'awaiting_payment' => [
                'label' => 'A aguardar pagamento',
                'orders' => $this->ordersForBucket(fn ($query) => $query
                    ->where('status', Order::STATUS_PENDING)
                    ->where('payment_state', Order::PAYMENT_PENDING)),
                'total' => $this->countForBucket(fn ($query) => $query
                    ->where('status', Order::STATUS_PENDING)
                    ->where('payment_state', Order::PAYMENT_PENDING)),
            ],
            'ready_to_prepare' => [
                'label' => 'Prontas para preparar',
                'orders' => $this->ordersForBucket(fn ($query) => $query
                    ->where('status', Order::STATUS_PENDING)
                    ->where('payment_state', Order::PAYMENT_CONFIRMED)),
                'total' => $this->countForBucket(fn ($query) => $query
                    ->where('status', Order::STATUS_PENDING)
                    ->where('payment_state', Order::PAYMENT_CONFIRMED)),
            ],
            'preparing' => [
                'label' => 'Em preparação',
                'orders' => $this->ordersForBucket(fn ($query) => $query->where('status', Order::STATUS_PREPARING)),
                'total' => $this->countForBucket(fn ($query) => $query->where('status', Order::STATUS_PREPARING)),
            ],
            'fulfilment' => [
                'label' => 'Prontas / em distribuição',
                'orders' => $this->ordersForBucket(fn ($query) => $query->whereIn('status', [Order::STATUS_READY, Order::STATUS_IN_TRANSIT])),
                'total' => $this->countForBucket(fn ($query) => $query->whereIn('status', [Order::STATUS_READY, Order::STATUS_IN_TRANSIT])),
            ],
        ];
    }

    private function ordersForBucket(callable $constraint)
    {
        return $constraint(Order::query())
            ->whereDoesntHave('payment', fn ($query) => $query->where('refund_state', Payment::REFUND_REQUESTED))
            ->with(['items', 'payment'])
            ->oldest()
            ->limit(20)
            ->get();
    }

    private function countForBucket(callable $constraint): int
    {
        return (int) $constraint(Order::query())
            ->whereDoesntHave('payment', fn ($query) => $query->where('refund_state', Payment::REFUND_REQUESTED))
            ->count();
    }
}
