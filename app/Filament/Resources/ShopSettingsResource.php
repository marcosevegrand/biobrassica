<?php

namespace App\Filament\Resources;

use App\Filament\Resources\ShopSettingsResource\Pages;
use App\Models\ShopSettings;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables\Table;

class ShopSettingsResource extends Resource
{
    protected static ?string $model = ShopSettings::class;

    protected static ?string $navigationIcon = 'heroicon-o-cog-6-tooth';

    protected static ?string $navigationGroup = 'Loja';

    protected static ?string $navigationLabel = 'Definições da loja';

    protected static ?string $modelLabel = 'definições da loja';

    protected static ?string $slug = 'shop-settings';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Section::make('Estado da loja')
                    ->schema([
                        Forms\Components\Toggle::make('is_shop_active')
                            ->label('Loja ativa')
                            ->default(true),
                        Forms\Components\Toggle::make('is_shop_brevemente')
                            ->label('Modo “brevemente”')
                            ->default(false),
                    ]),
                Forms\Components\Section::make('Encomendas e envio')
                    ->schema([
                        Forms\Components\TextInput::make('min_order_total')
                            ->label('Valor mínimo de encomenda')
                            ->numeric()
                            ->prefix('€')
                            ->minValue(0)
                            ->default(0)
                            ->helperText('Subtotal mínimo de produtos exigido para finalizar compra.'),
                        Forms\Components\TextInput::make('shipping_flat_rate')
                            ->label('Custo fixo de envio')
                            ->numeric()
                            ->prefix('€')
                            ->minValue(0)
                            ->default(0)
                            ->helperText('Custo aplicado a encomendas com envio.'),
                        Forms\Components\TextInput::make('free_shipping_min_subtotal')
                            ->label('Envio grátis a partir de')
                            ->numeric()
                            ->prefix('€')
                            ->minValue(0)
                            ->helperText('Subtotal de produtos que torna o envio gratuito.'),
                        Forms\Components\TextInput::make('checkout_reservation_minutes')
                            ->label('Reserva no checkout')
                            ->numeric()
                            ->suffix('minutes')
                            ->minValue(1)
                            ->default(30)
                            ->helperText('Durante quantos minutos o stock fica reservado no checkout.'),
                    ])->columns(2),
                Forms\Components\Section::make('Pagamentos')
                    ->schema([
                        Forms\Components\Toggle::make('mbway_enabled')
                            ->label('MB WAY ativo')
                            ->default(true),
                        Forms\Components\Toggle::make('bank_transfer_enabled')
                            ->label('Multibanco ativo')
                            ->default(true),
                        Forms\Components\Placeholder::make('manual_payment_credentials')
                            ->label('Credenciais IfThenPay')
                            ->content('Por segurança, as chaves IfThenPay são lidas apenas do ficheiro .env.'),
                        Forms\Components\TextInput::make('payment_timeout_minutes')
                            ->label('Tempo limite local')
                            ->numeric()
                            ->suffix('minutes')
                            ->minValue(1)
                            ->default(30)
                            ->helperText('Tempo local antes de um pagamento pendente poder ser cancelado.'),
                        Forms\Components\TextInput::make('payment_expiry_grace_minutes')
                            ->label('Margem após expiração')
                            ->numeric()
                            ->suffix('minutes')
                            ->minValue(0)
                            ->default(10)
                            ->helperText('Margem de segurança após expiração no fornecedor antes de cancelamento local.'),
                        Forms\Components\TextInput::make('mbway_minutes_to_expire')
                            ->label('Expiração MB WAY')
                            ->numeric()
                            ->suffix('minutes')
                            ->minValue(1)
                            ->default(4)
                            ->helperText('Expiração do pedido MB WAY enviada para a IfThenPay.'),
                        Forms\Components\TextInput::make('multibanco_days_to_expire')
                            ->label('Expiração Multibanco')
                            ->numeric()
                            ->suffix('days')
                            ->minValue(1)
                            ->default(3)
                            ->helperText('Expiração da referência Multibanco enviada para a IfThenPay.'),
                        Forms\Components\Textarea::make('staff_notification_emails')
                            ->label('Emails de notificação')
                            ->rows(2)
                            ->helperText('Emails da equipa notificados quando pagamentos são confirmados, separados por vírgulas.'),
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
