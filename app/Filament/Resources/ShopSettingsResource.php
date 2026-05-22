<?php

namespace App\Filament\Resources;

use App\Filament\Resources\ShopSettingsResource\Pages;
use App\Models\ShopSettings;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class ShopSettingsResource extends Resource
{
    protected static ?string $model = ShopSettings::class;

    protected static ?string $navigationIcon = 'heroicon-o-cog-6-tooth';

    protected static ?string $navigationGroup = 'Configuração';

    protected static ?string $navigationLabel = 'Shop Settings';

    protected static ?string $slug = 'shop-settings';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Section::make('Shop Status')
                    ->schema([
                        Forms\Components\Toggle::make('is_shop_active')
                            ->label('Shop Active')
                            ->default(true),
                        Forms\Components\Toggle::make('is_shop_brevemente')
                            ->label('Shop "Coming Soon" Mode')
                            ->default(false),
                    ]),
                Forms\Components\Section::make('Order Settings')
                    ->schema([
                        Forms\Components\TextInput::make('min_order_total')
                            ->numeric()
                            ->prefix('€')
                            ->helperText('Minimum order total required'),
                        Forms\Components\TextInput::make('checkout_reservation_minutes')
                            ->numeric()
                            ->suffix('minutes')
                            ->helperText('How long a checkout session reserves stock'),
                    ]),
                Forms\Components\Section::make('Payment Settings')
                    ->schema([
                        Forms\Components\Toggle::make('mbway_enabled')
                            ->label('MB WAY Enabled')
                            ->default(true),
                        Forms\Components\Toggle::make('bank_transfer_enabled')
                            ->label('Bank Transfer Enabled')
                            ->default(true),
                        Forms\Components\TextInput::make('payment_timeout_minutes')
                            ->numeric()
                            ->suffix('minutes')
                            ->helperText('Time before a pending payment expires'),
                    ]),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([])
            ->actions([])
            ->bulkActions([]);
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
            'index' => Pages\ManageShopSettings::route('/'),
        ];
    }
}
