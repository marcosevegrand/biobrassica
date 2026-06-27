<?php

namespace App\Notifications;

use App\Models\Order;
use Illuminate\Bus\Queueable;
use Illuminate\Notifications\Messages\MailMessage;
use Illuminate\Notifications\Notification;

class OrderPaymentConfirmed extends Notification
{
    use Queueable;

    public function __construct(
        private readonly Order $order,
        private readonly bool $staffCopy = false,
    ) {}

    public function via(object $notifiable): array
    {
        return ['mail'];
    }

    public function toMail(object $notifiable): MailMessage
    {
        $subject = $this->staffCopy
            ? "Pagamento confirmado — Encomenda #{$this->order->id}"
            : "Pagamento confirmado — Encomenda #{$this->order->id}";

        $message = (new MailMessage)
            ->subject($subject)
            ->greeting($this->staffCopy ? 'Olá equipa Biobrassica,' : "Olá {$this->order->name},")
            ->line("O pagamento da encomenda #{$this->order->id} foi confirmado.")
            ->line('Total: €'.number_format((float) $this->order->total, 2, ',', '.'));

        if ($this->staffCopy) {
            $message->line("Cliente: {$this->order->name} <{$this->order->email}>")
                ->line('Telefone: '.($this->order->phone ?: '—'));
        } else {
            $message->line('Vamos começar a preparar a sua encomenda. Receberá novidades assim que o estado for atualizado.');
        }

        return $message->salutation('BioBrassica');
    }
}
