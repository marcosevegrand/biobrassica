<?php

namespace App\Filament\Resources\OrderResource\Pages;

use App\Filament\Resources\OrderResource;
use App\Models\Order;
use Filament\Actions;
use Filament\Notifications\Notification;
use Filament\Resources\Pages\EditRecord;

class EditOrder extends EditRecord
{
    protected static string $resource = OrderResource::class;

    protected function getHeaderActions(): array
    {
        $record = $this->getRecord();

        $actions = [];

        if ($record->payment_state === 'pending') {
            $actions[] = Actions\Action::make('confirm_payment')
                ->label('Confirm Payment')
                ->icon('heroicon-o-check-circle')
                ->color('success')
                ->action(function (Order $record) {
                    $record->update(['payment_state' => 'paid']);
                    if ($record->payment) {
                        $record->payment->update(['status' => 'paid', 'paid_at' => now()]);
                    }
                    Notification::make()
                        ->title('Payment confirmed')
                        ->success()
                        ->send();
                })
                ->requiresConfirmation()
                ->modalHeading('Confirm Payment')
                ->modalDescription('Mark this order as paid?');

            $actions[] = Actions\Action::make('reject_payment')
                ->label('Reject Payment')
                ->icon('heroicon-o-x-circle')
                ->color('danger')
                ->action(function (Order $record) {
                    $record->update(['payment_state' => 'rejected']);
                    if ($record->payment) {
                        $record->payment->update(['status' => 'rejected']);
                    }
                    Notification::make()
                        ->title('Payment rejected')
                        ->danger()
                        ->send();
                })
                ->requiresConfirmation()
                ->modalHeading('Reject Payment')
                ->modalDescription('Mark this order payment as rejected?');
        }

        $actions[] = Actions\Action::make('mark_completed')
            ->label('Mark Completed')
            ->icon('heroicon-o-check')
            ->color('success')
            ->action(function (Order $record) {
                $record->update(['status' => 'completed']);
                Notification::make()
                    ->title('Order marked as completed')
                    ->success()
                    ->send();
            })
            ->requiresConfirmation()
            ->modalHeading('Mark Completed')
            ->modalDescription('Mark this order as completed?');

        $actions[] = Actions\DeleteAction::make();

        return $actions;
    }
}
