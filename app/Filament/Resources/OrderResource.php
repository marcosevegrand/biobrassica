<?php

namespace App\Filament\Resources;

use App\Filament\Resources\OrderResource\Pages;
use App\Filament\Resources\OrderResource\RelationManagers;
use App\Models\Order;
use App\Models\Payment;
use App\Services\OrderStateMachine;
use App\Services\PaymentService;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;

class OrderResource extends Resource
{
    protected static ?string $model = Order::class;

    protected static ?string $navigationIcon = 'heroicon-o-shopping-cart';

    protected static ?string $navigationGroup = 'Operação';

    protected static ?string $navigationLabel = 'Encomendas';

    protected static ?string $modelLabel = 'encomenda';

    protected static ?string $pluralModelLabel = 'encomendas';

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
                Forms\Components\Section::make('Dados da encomenda')
                    ->schema([
                        Forms\Components\TextInput::make('id')
                            ->label('N.º encomenda')
                            ->disabled(),
                        Forms\Components\Select::make('user_id')
                            ->label('Cliente')
                            ->relationship('user', 'name')
                            ->disabled(),
                        Forms\Components\TextInput::make('email')
                            ->label('Email')
                            ->email()
                            ->disabled(),
                        Forms\Components\TextInput::make('phone')
                            ->label('Telefone')
                            ->disabled(),
                        Forms\Components\TextInput::make('nif')
                            ->label('NIF')
                            ->disabled(),
                        Forms\Components\TextInput::make('name')
                            ->label('Nome')
                            ->disabled(),
                        Forms\Components\Select::make('status')
                            ->label('Estado')
                            ->options(Order::statusLabels())
                            ->disabled(),
                        Forms\Components\Select::make('payment_state')
                            ->label('Pagamento')
                            ->options(Order::paymentStateLabels())
                            ->disabled(),
                        Forms\Components\TextInput::make('fulfillment_method')
                            ->label('Entrega')
                            ->formatStateUsing(fn (?string $state): string => match ($state) {
                                'pickup' => 'Levantamento',
                                'shipping' => 'Envio',
                                default => $state ?? '—',
                            })
                            ->disabled(),
                        Forms\Components\TextInput::make('pickup_location')
                            ->label('Local de levantamento')
                            ->disabled(),
                        Forms\Components\TextInput::make('language')
                            ->label('Idioma')
                            ->disabled(),
                    ])->columns(2),
                Forms\Components\Section::make('Morada de envio')
                    ->schema([
                        Forms\Components\TextInput::make('shipping_address_line1')
                            ->label('Morada')
                            ->disabled(),
                        Forms\Components\TextInput::make('shipping_address_line2')
                            ->label('Complemento')
                            ->disabled(),
                        Forms\Components\TextInput::make('shipping_city')
                            ->label('Localidade')
                            ->disabled(),
                        Forms\Components\TextInput::make('shipping_postal_code')
                            ->label('Código postal')
                            ->disabled(),
                    ])->columns(2),
                Forms\Components\Section::make('Valores')
                    ->schema([
                        Forms\Components\TextInput::make('subtotal')
                            ->label('Subtotal')
                            ->numeric()
                            ->prefix('€')
                            ->disabled(),
                        Forms\Components\TextInput::make('shipping_cost')
                            ->label('Envio')
                            ->numeric()
                            ->prefix('€')
                            ->disabled(),
                        Forms\Components\TextInput::make('total')
                            ->label('Total')
                            ->numeric()
                            ->prefix('€')
                            ->disabled(),
                    ])->columns(3),
                Forms\Components\Section::make('Reembolso')
                    ->relationship('payment')
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
                        Forms\Components\DateTimePicker::make('refund_requested_at')
                            ->label('Pedido em')
                            ->disabled(),
                        Forms\Components\DateTimePicker::make('refunded_at')
                            ->label('Concluído em')
                            ->disabled(),
                    ])->columns(2),
                Forms\Components\Section::make('Notas')
                    ->schema([
                        Forms\Components\Textarea::make('notes')
                            ->label('Notas')
                            ->disabled()
                            ->columnSpanFull(),
                    ]),
            ]);
    }

    public static function getEloquentQuery(): Builder
    {
        return parent::getEloquentQuery()->with(['user', 'payment']);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('id')
                    ->label('N.º')
                    ->sortable()
                    ->searchable(),
                Tables\Columns\TextColumn::make('user.name')
                    ->label('Cliente')
                    ->searchable()
                    ->sortable(),
                Tables\Columns\TextColumn::make('total')
                    ->label('Total')
                    ->money('EUR')
                    ->sortable(),
                Tables\Columns\TextColumn::make('shipping_cost')
                    ->label('Envio')
                    ->money('EUR')
                    ->toggleable(isToggledHiddenByDefault: true),
                Tables\Columns\BadgeColumn::make('status')
                    ->label('Estado')
                    ->formatStateUsing(fn (string $state): string => Order::statusLabels()[$state] ?? $state)
                    ->colors([
                        'warning' => 'pending',
                        'info' => 'preparing',
                        'primary' => 'ready',
                        'gray' => 'in_transit',
                        'success' => 'delivered',
                        'danger' => 'cancelled',
                    ]),
                Tables\Columns\BadgeColumn::make('payment_state')
                    ->label('Pagamento')
                    ->formatStateUsing(fn (string $state): string => Order::paymentStateLabels()[$state] ?? $state)
                    ->colors([
                        'warning' => 'pending',
                        'success' => 'confirmed',
                        'danger' => 'cancelled',
                        'gray' => 'refunded',
                    ]),
                Tables\Columns\TextColumn::make('created_at')
                    ->label('Criada em')
                    ->dateTime()
                    ->sortable(),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('status')
                    ->label('Estado')
                    ->options(Order::statusLabels()),
                Tables\Filters\SelectFilter::make('payment_state')
                    ->label('Pagamento')
                    ->options(Order::paymentStateLabels()),
                Tables\Filters\SelectFilter::make('fulfillment_method')
                    ->label('Entrega')
                    ->options([
                        'pickup' => 'Levantamento',
                        'shipping' => 'Envio',
                    ]),
                Tables\Filters\Filter::make('refund_requested')
                    ->label('Reembolso pedido')
                    ->query(fn ($query) => $query->whereHas('payment', fn ($paymentQuery) => $paymentQuery->where('refund_state', Payment::REFUND_REQUESTED))),
            ])
            ->actions([
                Tables\Actions\Action::make('confirm_payment')
                    ->label('Confirmar no fornecedor')
                    ->icon('heroicon-o-check-circle')
                    ->color('success')
                    ->visible(fn (Order $record): bool => $record->payment_state === Order::PAYMENT_PENDING && $record->payment !== null)
                    ->action(function (Order $record) {
                        app(PaymentService::class)->confirmPaymentIfPaidAtProvider($record->payment);
                    })
                    ->requiresConfirmation()
                    ->modalHeading('Confirmar pagamento no fornecedor')
                    ->modalDescription('A ação só avança se a IfThenPay confirmar que o pagamento está pago.'),
                Tables\Actions\Action::make('reject_payment')
                    ->label('Rejeitar pagamento')
                    ->icon('heroicon-o-x-circle')
                    ->color('danger')
                    ->visible(fn (Order $record): bool => $record->payment_state === Order::PAYMENT_PENDING && $record->payment !== null)
                    ->action(function (Order $record) {
                        app(PaymentService::class)->rejectPayment($record->payment, 'Pagamento rejeitado no backoffice.');
                    })
                    ->requiresConfirmation()
                    ->modalHeading('Rejeitar pagamento')
                    ->modalDescription('Cancelar o pagamento desta encomenda?'),
                Tables\Actions\Action::make('request_refund')
                    ->label('Pedir reembolso')
                    ->icon('heroicon-o-arrow-uturn-left')
                    ->color('warning')
                    ->visible(fn (Order $record): bool => $record->payment?->status === Payment::STATUS_CONFIRMED && in_array($record->payment?->refund_state, [null, Payment::REFUND_FAILED], true))
                    ->form([
                        Forms\Components\Textarea::make('reason')
                            ->label('Motivo')
                            ->required()
                            ->maxLength(1000),
                    ])
                    ->action(fn (Order $record, array $data) => app(PaymentService::class)->requestRefund($record->payment, $data['reason'], auth()->user())),
                Tables\Actions\Action::make('complete_refund')
                    ->label('Marcar reembolso manual concluído')
                    ->icon('heroicon-o-check-badge')
                    ->color('success')
                    ->visible(fn (Order $record): bool => $record->payment?->refund_state === Payment::REFUND_REQUESTED)
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
                    ->action(fn (Order $record, array $data) => app(PaymentService::class)->completeRefund(
                        $record->payment,
                        $data['reference'] ?? null,
                        auth()->user(),
                        $data['notes'] ?? null,
                        (bool) ($data['restock'] ?? false),
                    )),
                Tables\Actions\Action::make('fail_refund')
                    ->label('Falha no reembolso')
                    ->icon('heroicon-o-exclamation-triangle')
                    ->color('danger')
                    ->visible(fn (Order $record): bool => $record->payment?->refund_state === Payment::REFUND_REQUESTED)
                    ->form([
                        Forms\Components\Textarea::make('notes')
                            ->label('Notas')
                            ->required(),
                    ])
                    ->action(fn (Order $record, array $data) => app(PaymentService::class)->failRefund($record->payment, $data['notes'], auth()->user())),
                Tables\Actions\Action::make('mark_preparing')
                    ->label('Marcar em preparação')
                    ->icon('heroicon-o-arrow-path')
                    ->color('info')
                    ->visible(fn (Order $record): bool => $record->status === Order::STATUS_PENDING && $record->payment_state === Order::PAYMENT_CONFIRMED && $record->payment?->refund_state !== Payment::REFUND_REQUESTED)
                    ->action(fn (Order $record) => app(OrderStateMachine::class)->transition($record, Order::STATUS_PREPARING))
                    ->requiresConfirmation(),
                Tables\Actions\Action::make('mark_ready')
                    ->label('Marcar pronta')
                    ->icon('heroicon-o-check-circle')
                    ->color('primary')
                    ->visible(fn (Order $record): bool => $record->status === Order::STATUS_PREPARING && $record->fulfillment_method === 'pickup' && $record->payment?->refund_state !== Payment::REFUND_REQUESTED)
                    ->action(fn (Order $record) => app(OrderStateMachine::class)->transition($record, Order::STATUS_READY))
                    ->requiresConfirmation(),
                Tables\Actions\Action::make('mark_in_transit')
                    ->label('Marcar em distribuição')
                    ->icon('heroicon-o-truck')
                    ->color('gray')
                    ->visible(fn (Order $record): bool => $record->status === Order::STATUS_PREPARING && $record->fulfillment_method === 'shipping' && $record->payment?->refund_state !== Payment::REFUND_REQUESTED)
                    ->action(fn (Order $record) => app(OrderStateMachine::class)->transition($record, Order::STATUS_IN_TRANSIT))
                    ->requiresConfirmation(),
                Tables\Actions\Action::make('mark_delivered')
                    ->label('Marcar entregue')
                    ->icon('heroicon-o-check')
                    ->color('success')
                    ->visible(fn (Order $record): bool => in_array($record->status, [Order::STATUS_READY, Order::STATUS_IN_TRANSIT], true) && $record->payment?->refund_state !== Payment::REFUND_REQUESTED)
                    ->action(fn (Order $record) => app(OrderStateMachine::class)->transition($record, Order::STATUS_DELIVERED))
                    ->requiresConfirmation()
                    ->modalHeading('Marcar entregue')
                    ->modalDescription('Marcar esta encomenda como entregue?'),
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
            RelationManagers\OrderItemsRelationManager::class,
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListOrders::route('/'),
            'edit' => Pages\EditOrder::route('/{record}/edit'),
        ];
    }
}
