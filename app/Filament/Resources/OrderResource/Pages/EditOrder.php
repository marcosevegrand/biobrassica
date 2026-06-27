<?php

namespace App\Filament\Resources\OrderResource\Pages;

use App\Filament\Resources\OrderResource;
use App\Models\Order;
use App\Models\Payment;
use App\Services\OrderStateMachine;
use App\Services\PaymentService;
use Filament\Actions;
use Filament\Forms;
use Filament\Notifications\Notification;
use Filament\Resources\Pages\EditRecord;

class EditOrder extends EditRecord
{
    protected static string $resource = OrderResource::class;

    protected function getHeaderActions(): array
    {
        $record = $this->getRecord();

        $actions = [];

        if ($record->payment_state === Order::PAYMENT_PENDING && $record->payment) {
            $actions[] = Actions\Action::make('confirm_payment')
                ->label('Confirmar no fornecedor')
                ->icon('heroicon-o-check-circle')
                ->color('success')
                ->action(function (Order $record) {
                    app(PaymentService::class)->confirmPaymentIfPaidAtProvider($record->payment);
                    Notification::make()
                        ->title('Payment confirmed')
                        ->success()
                        ->send();
                })
                ->requiresConfirmation()
                ->modalHeading('Confirmar pagamento no fornecedor')
                ->modalDescription('A ação só avança se a IfThenPay confirmar que o pagamento está pago.');

            $actions[] = Actions\Action::make('reject_payment')
                ->label('Rejeitar pagamento')
                ->icon('heroicon-o-x-circle')
                ->color('danger')
                ->action(function (Order $record) {
                    app(PaymentService::class)->rejectPayment($record->payment, 'Pagamento rejeitado no backoffice.');
                    Notification::make()
                        ->title('Payment rejected')
                        ->danger()
                        ->send();
                })
                ->requiresConfirmation()
                ->modalHeading('Rejeitar pagamento')
                ->modalDescription('Cancelar o pagamento desta encomenda?');
        }

        if ($record->payment?->status === Payment::STATUS_CONFIRMED && in_array($record->payment?->refund_state, [null, Payment::REFUND_FAILED], true)) {
            $actions[] = Actions\Action::make('request_refund')
                ->label('Pedir reembolso')
                ->icon('heroicon-o-arrow-uturn-left')
                ->color('warning')
                ->form([
                    Forms\Components\Textarea::make('reason')
                        ->label('Motivo')
                        ->required()
                        ->maxLength(1000),
                ])
                ->action(function (Order $record, array $data): void {
                    app(PaymentService::class)->requestRefund($record->payment, $data['reason'], auth()->user());
                    Notification::make()->title('Reembolso pedido')->success()->send();
                });
        }

        if ($record->payment?->refund_state === Payment::REFUND_REQUESTED) {
            $actions[] = Actions\Action::make('complete_refund')
                ->label('Marcar reembolso manual concluído')
                ->icon('heroicon-o-check-badge')
                ->color('success')
                ->form([
                    Forms\Components\TextInput::make('reference')
                        ->label('Referência'),
                    Forms\Components\Textarea::make('notes')
                        ->label('Notas'),
                    Forms\Components\Checkbox::make('restock')
                        ->label('Repor stock')
                        ->visible(fn (Order $record): bool => $record->status !== Order::STATUS_DELIVERED)
                        ->default(false),
                ])
                ->action(function (Order $record, array $data): void {
                    app(PaymentService::class)->completeRefund(
                        $record->payment,
                        $data['reference'] ?? null,
                        auth()->user(),
                        $data['notes'] ?? null,
                        (bool) ($data['restock'] ?? false),
                    );
                    Notification::make()->title('Reembolso concluído')->success()->send();
                });

            $actions[] = Actions\Action::make('fail_refund')
                ->label('Falha no reembolso')
                ->icon('heroicon-o-exclamation-triangle')
                ->color('danger')
                ->form([
                    Forms\Components\Textarea::make('notes')
                        ->label('Notas')
                        ->required(),
                ])
                ->action(function (Order $record, array $data): void {
                    app(PaymentService::class)->failRefund($record->payment, $data['notes'], auth()->user());
                    Notification::make()->title('Reembolso marcado como falhado')->danger()->send();
                });
        }

        foreach (OrderStateMachine::validNextStates($record->status) as $nextState) {
            if ($nextState === Order::STATUS_CANCELLED && ($record->payment_state !== Order::PAYMENT_PENDING || ! $record->payment)) {
                continue;
            }

            if ($nextState !== Order::STATUS_CANCELLED && $record->payment_state !== Order::PAYMENT_CONFIRMED) {
                continue;
            }

            if ($nextState !== Order::STATUS_CANCELLED && $record->payment?->refund_state === Payment::REFUND_REQUESTED) {
                continue;
            }

            if ($nextState === Order::STATUS_READY && $record->fulfillment_method !== 'pickup') {
                continue;
            }

            if ($nextState === Order::STATUS_IN_TRANSIT && $record->fulfillment_method !== 'shipping') {
                continue;
            }

            $actions[] = Actions\Action::make('mark_'.$nextState)
                ->label('Marcar: '.(Order::statusLabels()[$nextState] ?? $nextState))
                ->icon($nextState === Order::STATUS_CANCELLED ? 'heroicon-o-x-circle' : 'heroicon-o-check')
                ->color($nextState === Order::STATUS_CANCELLED ? 'danger' : 'success')
                ->action(function (Order $record) use ($nextState) {
                    if ($nextState === Order::STATUS_CANCELLED) {
                        app(PaymentService::class)->rejectPayment($record->payment, 'Encomenda cancelada no backoffice.');
                    } else {
                        app(OrderStateMachine::class)->transition($record, $nextState);
                    }
                    Notification::make()
                        ->title('Estado da encomenda atualizado')
                        ->success()
                        ->send();
                })
                ->requiresConfirmation();
        }

        return $actions;
    }
}
