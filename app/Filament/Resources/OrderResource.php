<?php

namespace App\Filament\Resources;

use App\Filament\Resources\OrderResource\Pages;
use App\Filament\Resources\OrderResource\RelationManagers;
use App\Models\Order;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class OrderResource extends Resource
{
    protected static ?string $model = Order::class;

    protected static ?string $navigationIcon = 'heroicon-o-shopping-cart';

    protected static ?string $navigationGroup = 'Encomendas';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Section::make('Order Info')
                    ->schema([
                        Forms\Components\TextInput::make('id')
                            ->label('Order ID')
                            ->disabled(),
                        Forms\Components\Select::make('user_id')
                            ->relationship('user', 'name')
                            ->disabled(),
                        Forms\Components\TextInput::make('email')
                            ->email()
                            ->disabled(),
                        Forms\Components\TextInput::make('phone')
                            ->disabled(),
                        Forms\Components\TextInput::make('nif')
                            ->label('NIF')
                            ->disabled(),
                        Forms\Components\TextInput::make('name')
                            ->disabled(),
                        Forms\Components\Select::make('status')
                            ->options([
                                'pending' => 'Pending',
                                'confirmed' => 'Confirmed',
                                'processing' => 'Processing',
                                'completed' => 'Completed',
                                'cancelled' => 'Cancelled',
                            ]),
                        Forms\Components\Select::make('payment_state')
                            ->options([
                                'pending' => 'Pending',
                                'paid' => 'Paid',
                                'rejected' => 'Rejected',
                                'expired' => 'Expired',
                            ])
                            ->disabled(),
                        Forms\Components\TextInput::make('fulfillment_method')
                            ->disabled(),
                        Forms\Components\TextInput::make('pickup_location')
                            ->disabled(),
                        Forms\Components\TextInput::make('language')
                            ->disabled(),
                    ])->columns(2),
                Forms\Components\Section::make('Shipping Address')
                    ->schema([
                        Forms\Components\TextInput::make('shipping_address_line1')
                            ->disabled(),
                        Forms\Components\TextInput::make('shipping_address_line2')
                            ->disabled(),
                        Forms\Components\TextInput::make('shipping_city')
                            ->disabled(),
                        Forms\Components\TextInput::make('shipping_postal_code')
                            ->disabled(),
                    ])->columns(2),
                Forms\Components\Section::make('Financials')
                    ->schema([
                        Forms\Components\TextInput::make('subtotal')
                            ->numeric()
                            ->prefix('€')
                            ->disabled(),
                        Forms\Components\TextInput::make('total')
                            ->numeric()
                            ->prefix('€')
                            ->disabled(),
                    ])->columns(2),
                Forms\Components\Section::make('Notes')
                    ->schema([
                        Forms\Components\Textarea::make('notes')
                            ->disabled()
                            ->columnSpanFull(),
                    ]),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('id')
                    ->sortable()
                    ->searchable(),
                Tables\Columns\TextColumn::make('user.name')
                    ->searchable()
                    ->sortable(),
                Tables\Columns\TextColumn::make('total')
                    ->money('EUR')
                    ->sortable(),
                Tables\Columns\BadgeColumn::make('status')
                    ->colors([
                        'warning' => 'pending',
                        'info' => 'confirmed',
                        'primary' => 'processing',
                        'success' => 'completed',
                        'danger' => 'cancelled',
                    ]),
                Tables\Columns\BadgeColumn::make('payment_state')
                    ->label('Payment')
                    ->colors([
                        'warning' => 'pending',
                        'success' => 'paid',
                        'danger' => 'rejected',
                        'gray' => 'expired',
                    ]),
                Tables\Columns\TextColumn::make('created_at')
                    ->dateTime()
                    ->sortable(),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('status')
                    ->options([
                        'pending' => 'Pending',
                        'confirmed' => 'Confirmed',
                        'processing' => 'Processing',
                        'completed' => 'Completed',
                        'cancelled' => 'Cancelled',
                    ]),
                Tables\Filters\SelectFilter::make('payment_state')
                    ->options([
                        'pending' => 'Pending',
                        'paid' => 'Paid',
                        'rejected' => 'Rejected',
                        'expired' => 'Expired',
                    ]),
            ])
            ->actions([
                Tables\Actions\Action::make('confirm_payment')
                    ->label('Confirm Payment')
                    ->icon('heroicon-o-check-circle')
                    ->color('success')
                    ->visible(fn(Order $record): bool => $record->payment_state === 'pending')
                    ->action(function (Order $record) {
                        $record->update(['payment_state' => 'paid']);
                        if ($record->payment) {
                            $record->payment->update(['status' => 'paid', 'paid_at' => now()]);
                        }
                    })
                    ->requiresConfirmation()
                    ->modalHeading('Confirm Payment')
                    ->modalDescription('Mark this order as paid?'),
                Tables\Actions\Action::make('reject_payment')
                    ->label('Reject Payment')
                    ->icon('heroicon-o-x-circle')
                    ->color('danger')
                    ->visible(fn(Order $record): bool => $record->payment_state === 'pending')
                    ->action(function (Order $record) {
                        $record->update(['payment_state' => 'rejected']);
                        if ($record->payment) {
                            $record->payment->update(['status' => 'rejected']);
                        }
                    })
                    ->requiresConfirmation()
                    ->modalHeading('Reject Payment')
                    ->modalDescription('Mark this order payment as rejected?'),
                Tables\Actions\Action::make('mark_completed')
                    ->label('Mark Completed')
                    ->icon('heroicon-o-check')
                    ->color('success')
                    ->action(fn(Order $record) => $record->update(['status' => 'completed']))
                    ->requiresConfirmation()
                    ->modalHeading('Mark Completed')
                    ->modalDescription('Mark this order as completed?'),
                Tables\Actions\EditAction::make(),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
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
            'create' => Pages\CreateOrder::route('/create'),
            'edit' => Pages\EditOrder::route('/{record}/edit'),
        ];
    }
}
