<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Payment extends Model
{
    public const STATUS_PENDING = 'pending';

    public const STATUS_CONFIRMED = 'confirmed';

    public const STATUS_CANCELLED = 'cancelled';

    public const STATUS_REFUNDED = 'refunded';

    public const REFUND_REQUESTED = 'requested';

    public const REFUND_COMPLETED = 'completed';

    public const REFUND_FAILED = 'failed';

    protected $fillable = [
        'order_id',
        'method',
        'status',
        'amount',
        'provider_reference',
        'provider_payment_id',
        'provider_data',
        'checkout_url',
        'last_error',
        'expires_at',
        'paid_at',
        'refund_state',
        'refund_amount',
        'refund_reason',
        'refund_reference',
        'refund_notes',
        'refund_requested_at',
        'refunded_at',
        'refund_requested_by',
        'refunded_by',
    ];

    protected function casts(): array
    {
        return [
            'amount' => 'decimal:2',
            'provider_data' => 'array',
            'expires_at' => 'datetime',
            'paid_at' => 'datetime',
            'refund_amount' => 'decimal:2',
            'refund_requested_at' => 'datetime',
            'refunded_at' => 'datetime',
        ];
    }

    public function order()
    {
        return $this->belongsTo(Order::class);
    }

    public function refundRequestedBy()
    {
        return $this->belongsTo(User::class, 'refund_requested_by');
    }

    public function refundedBy()
    {
        return $this->belongsTo(User::class, 'refunded_by');
    }

    public static function statusLabels(): array
    {
        return [
            self::STATUS_PENDING => 'Pendente',
            self::STATUS_CONFIRMED => 'Confirmado',
            self::STATUS_CANCELLED => 'Cancelado',
            self::STATUS_REFUNDED => 'Reembolsado',
        ];
    }

    public static function refundStateLabels(): array
    {
        return [
            self::REFUND_REQUESTED => 'Pedido',
            self::REFUND_COMPLETED => 'Concluído',
            self::REFUND_FAILED => 'Falhou',
        ];
    }
}
