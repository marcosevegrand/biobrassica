<?php

namespace App\Services;

use App\Models\Order;
use RuntimeException;

class OrderStateMachine
{
    private const TRANSITIONS = [
        'pending' => ['preparing', 'cancelled'],
        'preparing' => ['ready', 'in_transit', 'cancelled'],
        'ready' => ['delivered', 'cancelled'],
        'in_transit' => ['delivered', 'cancelled'],
        'delivered' => [],
        'cancelled' => [],
    ];

    public const LABELS = [
        'pending' => 'Pendente',
        'preparing' => 'Em preparação',
        'ready' => 'Pronta para levantamento',
        'in_transit' => 'Em distribuição',
        'delivered' => 'Entregue',
        'cancelled' => 'Cancelada',
    ];

    public function transition(Order $order, string $newState): void
    {
        $currentState = $order->status;

        if (! isset(self::TRANSITIONS[$currentState])) {
            throw new RuntimeException("Estado desconhecido: {$currentState}");
        }

        if (! in_array($newState, self::TRANSITIONS[$currentState], true)) {
            throw new RuntimeException(
                "Transição inválida de {$currentState} para {$newState}."
            );
        }

        if ($newState !== 'cancelled' && $currentState === 'pending' && $order->payment_state !== 'confirmed') {
            throw new RuntimeException('A encomenda só pode avançar após confirmação do pagamento.');
        }

        if ($newState !== 'cancelled' && $order->payment?->refund_state === 'requested') {
            throw new RuntimeException('A encomenda tem um reembolso pedido e não pode avançar na preparação.');
        }

        $order->status = $newState;
        $order->save();
    }

    public static function canTransition(string $from, string $to): bool
    {
        return isset(self::TRANSITIONS[$from])
            && in_array($to, self::TRANSITIONS[$from], true);
    }

    public static function validNextStates(string $from): array
    {
        return self::TRANSITIONS[$from] ?? [];
    }

    public static function labels(): array
    {
        return self::LABELS;
    }
}
