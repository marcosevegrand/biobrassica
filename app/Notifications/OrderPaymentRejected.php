<?php

namespace App\Notifications;

use App\Models\Order;
use Illuminate\Bus\Queueable;
use Illuminate\Notifications\Messages\MailMessage;
use Illuminate\Notifications\Notification;

class OrderPaymentRejected extends Notification
{
    use Queueable;

    public function __construct(
        private readonly Order $order,
        private readonly string $reason = '',
    ) {}

    public function via(object $notifiable): array
    {
        return ['mail'];
    }

    public function toMail(object $notifiable): MailMessage
    {
        $message = (new MailMessage)
            ->subject("Pagamento cancelado — Encomenda #{$this->order->id}")
            ->greeting("Olá {$this->order->name},")
            ->line("O pagamento da encomenda #{$this->order->id} foi cancelado.")
            ->line('Total: €'.number_format((float) $this->order->total, 2, ',', '.'));

        if ($this->reason !== '') {
            $message->line("Motivo: {$this->reason}");
        }

        return $message
            ->line('Se acredita que houve um engano, contacte-nos para que possamos ajudar.')
            ->salutation('BioBrassica');
    }
}
