<?php

namespace App\Filament\Resources;

use App\Filament\Resources\PaymentResource\Pages;
use App\Models\Payment;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class PaymentResource extends Resource
{
    protected static ?string $model = Payment::class;

    protected static ?string $navigationIcon = 'heroicon-o-credit-card';

    protected static ?string $navigationGroup = 'Encomendas';

    protected static ?string $navigationLabel = 'Payments';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Section::make('Payment Info')
                    ->schema([
                        Forms\Components\TextInput::make('id')
                            ->disabled(),
                        Forms\Components\TextInput::make('order_id')
                            ->disabled(),
                        Forms\Components\TextInput::make('method')
                            ->disabled(),
                        Forms\Components\Select::make('status')
                            ->options([
                                'pending' => 'Pending',
                                'paid' => 'Paid',
                                'rejected' => 'Rejected',
                                'expired' => 'Expired',
                            ]),
                        Forms\Components\TextInput::make('amount')
                            ->numeric()
                            ->prefix('€')
                            ->disabled(),
                    ])->columns(2),
                Forms\Components\Section::make('Provider Details')
                    ->schema([
                        Forms\Components\TextInput::make('provider_reference')
                            ->disabled(),
                        Forms\Components\TextInput::make('provider_payment_id')
                            ->disabled(),
                        Forms\Components\Textarea::make('provider_data')
                            ->disabled()
                            ->columnSpanFull(),
                        Forms\Components\TextInput::make('checkout_url')
                            ->disabled(),
                        Forms\Components\Textarea::make('last_error')
                            ->disabled(),
                    ])->columns(2),
                Forms\Components\Section::make('Dates')
                    ->schema([
                        Forms\Components\DateTimePicker::make('expires_at')
                            ->disabled(),
                        Forms\Components\DateTimePicker::make('paid_at')
                            ->disabled(),
                        Forms\Components\DateTimePicker::make('created_at')
                            ->disabled(),
                    ])->columns(3),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('order_id')
                    ->sortable()
                    ->searchable(),
                Tables\Columns\TextColumn::make('method')
                    ->searchable(),
                Tables\Columns\BadgeColumn::make('status')
                    ->colors([
                        'warning' => 'pending',
                        'success' => 'paid',
                        'danger' => 'rejected',
                        'gray' => 'expired',
                    ]),
                Tables\Columns\TextColumn::make('amount')
                    ->money('EUR')
                    ->sortable(),
                Tables\Columns\TextColumn::make('created_at')
                    ->dateTime()
                    ->sortable(),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('status')
                    ->options([
                        'pending' => 'Pending',
                        'paid' => 'Paid',
                        'rejected' => 'Rejected',
                        'expired' => 'Expired',
                    ]),
                Tables\Filters\SelectFilter::make('method')
                    ->options([
                        'mbway' => 'MB WAY',
                        'bank_transfer' => 'Bank Transfer',
                    ]),
            ])
            ->actions([
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
            //
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListPayments::route('/'),
            'create' => Pages\CreatePayment::route('/create'),
            'edit' => Pages\EditPayment::route('/{record}/edit'),
        ];
    }
}
