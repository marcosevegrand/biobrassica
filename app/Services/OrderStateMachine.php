<?php

namespace App\Services;

use App\Models\Order;
use RuntimeException;

class OrderStateMachine
{
    private const TRANSITIONS = [
        'pending' => ['confirmed', 'cancelled'],
        'confirmed' => ['completed'],
        'cancelled' => [],
        'completed' => [],
    ];

    public function transition(Order $order, string $newState): void
    {
        $currentState = $order->status;

        if (!isset(self::TRANSITIONS[$currentState])) {
            throw new RuntimeException("Estado desconhecido: {$currentState}");
        }

        if (!in_array($newState, self::TRANSITIONS[$currentState], true)) {
            throw new RuntimeException(
                "Transição inválida de {$currentState} para {$newState}."
            );
        }

        $order->status = $newState;
        $order->save();
    }

    public static function canTransition(string $from, string $to): bool
    {
        return isset(self::TRANSITIONS[$from])
            && in_array($to, self::TRANSITIONS[$from], true);
    }
}
