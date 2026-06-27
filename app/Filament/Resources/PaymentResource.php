<?php

namespace App\Filament\Resources;

use App\Filament\Resources\PaymentResource\Pages;
use App\Models\Order;
use App\Models\Payment;
use App\Services\PaymentService;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;

class PaymentResource extends Resource
{
    protected static ?string $model = Payment::class;

    protected static ?string $navigationIcon = 'heroicon-o-credit-card';

    protected static ?string $navigationGroup = 'Operação';

    protected static ?string $navigationLabel = 'Pagamentos';

    protected static ?string $modelLabel = 'pagamento';

    protected static ?string $pluralModelLabel = 'pagamentos';

    public static function canCreate(): bool
    {
        return false;
    }

    public static function canDelete($record): bool
    {
        return false;
    }

    public static function canDeleteAny(): bool
    {
        return false;
    }

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Section::make('Dados do pagamento')
                    ->schema([
                        Forms\Components\TextInput::make('id')
                            ->label('ID')
                            ->disabled(),
                        Forms\Components\TextInput::make('order_id')
                            ->label('N.º encomenda')
                            ->disabled(),
                        Forms\Components\TextInput::make('method')
                            ->label('Método')
                            ->disabled(),
                        Forms\Components\Select::make('status')
                            ->label('Estado')
                            ->options(Payment::statusLabels())
                            ->disabled(),
                        Forms\Components\TextInput::make('amount')
                            ->label('Valor')
                            ->numeric()
                            ->prefix('€')
                            ->disabled(),
                    ])->columns(2),
                Forms\Components\Section::make('Dados do fornecedor')
                    ->schema([
                        Forms\Components\TextInput::make('provider_reference')
                            ->label('Referência')
                            ->disabled(),
                        Forms\Components\TextInput::make('provider_payment_id')
                            ->label('ID transação')
                            ->disabled(),
                        Forms\Components\Textarea::make('provider_data')
                            ->label('Dados técnicos')
                            ->disabled()
                            ->columnSpanFull(),
                        Forms\Components\TextInput::make('checkout_url')
                            ->label('URL checkout')
                            ->disabled(),
                        Forms\Components\Textarea::make('last_error')
                            ->label('Último erro')
                            ->disabled(),
                    ])->columns(2),
                Forms\Components\Section::make('Datas')
                    ->schema([
                        Forms\Components\DateTimePicker::make('expires_at')
                            ->label('Expira em')
                            ->disabled(),
                        Forms\Components\DateTimePicker::make('paid_at')
                            ->label('Pago em')
                            ->disabled(),
                        Forms\Components\DateTimePicker::make('created_at')
                            ->label('Criado em')
                            ->disabled(),
                    ])->columns(3),
                Forms\Components\Section::make('Reembolso')
                    ->schema([
                        Forms\Components\Select::make('refund_state')
                            ->label('Estado')
                            ->options(Payment::refundStateLabels())
                            ->disabled(),
                        Forms\Components\TextInput::make('refund_amount')
                            ->label('Valor')
                            ->numeric()
                            ->prefix('€')
                            ->disabled(),
                        Forms\Components\Textarea::make('refund_reason')
                            ->label('Motivo')
                            ->disabled()
                            ->columnSpanFull(),
                        Forms\Components\TextInput::make('refund_reference')
                            ->label('Referência')
                            ->disabled(),
                        Forms\Components\Textarea::make('refund_notes')
                            ->label('Notas')
                            ->disabled()
                            ->columnSpanFull(),
                        Forms\Components\DateTimePicker::make('refund_requested_at')
                            ->label('Pedido em')
                            ->disabled(),
                        Forms\Components\DateTimePicker::make('refunded_at')
                            ->label('Concluído em')
                            ->disabled(),
                    ])->columns(2),
            ]);
    }

    public static function getEloquentQuery(): Builder
    {
        return parent::getEloquentQuery()->with('order');
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('order_id')
                    ->label('N.º encomenda')
                    ->sortable()
                    ->searchable(),
                Tables\Columns\TextColumn::make('method')
                    ->label('Método')
                    ->searchable(),
                Tables\Columns\BadgeColumn::make('status')
                    ->label('Estado')
                    ->formatStateUsing(fn (string $state): string => Payment::statusLabels()[$state] ?? $state)
                    ->colors([
                        'warning' => 'pending',
                        'success' => 'confirmed',
                        'danger' => 'cancelled',
                        'gray' => 'refunded',
                    ]),
                Tables\Columns\TextColumn::make('amount')
                    ->label('Valor')
                    ->money('EUR')
                    ->sortable(),
                Tables\Columns\BadgeColumn::make('refund_state')
                    ->label('Reembolso')
                    ->formatStateUsing(fn (?string $state): string => $state ? (Payment::refundStateLabels()[$state] ?? $state) : '—')
                    ->colors([
                        'warning' => Payment::REFUND_REQUESTED,
                        'success' => Payment::REFUND_COMPLETED,
                        'danger' => Payment::REFUND_FAILED,
                    ])
                    ->toggleable(),
                Tables\Columns\TextColumn::make('created_at')
                    ->label('Criado em')
                    ->dateTime()
                    ->sortable(),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('status')
                    ->label('Estado')
                    ->options(Payment::statusLabels()),
                Tables\Filters\SelectFilter::make('method')
                    ->label('Método')
                    ->options([
                        'mbway' => 'MB WAY',
                        'multibanco' => 'Multibanco',
                    ]),
                Tables\Filters\SelectFilter::make('refund_state')
                    ->label('Reembolso')
                    ->options(Payment::refundStateLabels()),
            ])
            ->actions([
                Tables\Actions\Action::make('confirm')
                    ->label('Confirmar no fornecedor')
                    ->icon('heroicon-o-check-circle')
                    ->color('success')
                    ->visible(fn (Payment $record): bool => $record->status === Payment::STATUS_PENDING)
                    ->action(fn (Payment $record) => app(PaymentService::class)->confirmPaymentIfPaidAtProvider($record))
                    ->requiresConfirmation()
                    ->modalDescription('A ação só avança se a IfThenPay confirmar que o pagamento está pago.'),
                Tables\Actions\Action::make('cancel')
                    ->label('Cancelar')
                    ->icon('heroicon-o-x-circle')
                    ->color('danger')
                    ->visible(fn (Payment $record): bool => $record->status === Payment::STATUS_PENDING)
                    ->action(fn (Payment $record) => app(PaymentService::class)->rejectPayment($record, 'Pagamento cancelado no backoffice.'))
                    ->requiresConfirmation(),
                Tables\Actions\Action::make('request_refund')
                    ->label('Pedir reembolso')
                    ->icon('heroicon-o-arrow-uturn-left')
                    ->color('warning')
                    ->visible(fn (Payment $record): bool => $record->status === Payment::STATUS_CONFIRMED && in_array($record->refund_state, [null, Payment::REFUND_FAILED], true))
                    ->form([
                        Forms\Components\Textarea::make('reason')
                            ->label('Motivo')
                            ->required()
                            ->maxLength(1000),
                    ])
                    ->action(fn (Payment $record, array $data) => app(PaymentService::class)->requestRefund($record, $data['reason'], auth()->user())),
                Tables\Actions\Action::make('complete_refund')
                    ->label('Marcar reembolso manual concluído')
                    ->icon('heroicon-o-check-badge')
                    ->color('success')
                    ->visible(fn (Payment $record): bool => $record->refund_state === Payment::REFUND_REQUESTED)
                    ->form([
                        Forms\Components\TextInput::make('reference')
                            ->label('Referência'),
                        Forms\Components\Textarea::make('notes')
                            ->label('Notas'),
                        Forms\Components\Checkbox::make('restock')
                            ->label('Repor stock')
                            ->visible(fn (Payment $record): bool => $record->order?->status !== Order::STATUS_DELIVERED)
                            ->default(false),
                    ])
                    ->action(fn (Payment $record, array $data) => app(PaymentService::class)->completeRefund(
                        $record,
                        $data['reference'] ?? null,
                        auth()->user(),
                        $data['notes'] ?? null,
                        (bool) ($data['restock'] ?? false),
                    )),
                Tables\Actions\Action::make('fail_refund')
                    ->label('Falha no reembolso')
                    ->icon('heroicon-o-exclamation-triangle')
                    ->color('danger')
                    ->visible(fn (Payment $record): bool => $record->refund_state === Payment::REFUND_REQUESTED)
                    ->form([
                        Forms\Components\Textarea::make('notes')
                            ->label('Notas')
                            ->required(),
                    ])
                    ->action(fn (Payment $record, array $data) => app(PaymentService::class)->failRefund($record, $data['notes'], auth()->user())),
                Tables\Actions\EditAction::make(),
            ])
            ->bulkActions([
                // Financial records should not be bulk-deleted from the backoffice.
            ])
            ->defaultSort('created_at', 'desc');
    }

    public static function getRelations(): array
    {
        return [
            //
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListPayments::route('/'),
            'edit' => Pages\EditPayment::route('/{record}/edit'),
        ];
    }
}
