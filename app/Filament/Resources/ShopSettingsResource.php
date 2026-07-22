<?php

namespace App\Filament\Resources;

use App\Filament\Resources\ShopSettingsResource\Pages;
use App\Models\ShopSettings;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables\Table;
use Illuminate\Support\HtmlString;

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
                        Forms\Components\Select::make('shop_mode')
                            ->label('Modo')
                            ->options([
                                'brevemente' => 'Brevemente',
                                'inativa' => 'Inativa',
                                'ativada' => 'Ativada',
                            ])
                            ->default('ativada')
                            ->required()
                            ->reactive()
                            ->afterStateHydrated(function (Forms\Components\Select $component, ?ShopSettings $record): void {
                                if (! $record) {
                                    $component->state('ativada');

                                    return;
                                }
                                if ($record->is_shop_brevemente) {
                                    $component->state('brevemente');
                                } elseif (! $record->is_shop_active) {
                                    $component->state('inativa');
                                } else {
                                    $component->state('ativada');
                                }
                            })
                            ->afterStateUpdated(function (Forms\Set $set, $state): void {
                                match ($state) {
                                    'brevemente' => tap($set, function ($set) {
                                        $set('is_shop_active', true);
                                        $set('is_shop_brevemente', true);
                                    }),
                                    'inativa' => tap($set, function ($set) {
                                        $set('is_shop_active', false);
                                        $set('is_shop_brevemente', false);
                                    }),
                                    'ativada' => tap($set, function ($set) {
                                        $set('is_shop_active', true);
                                        $set('is_shop_brevemente', false);
                                    }),
                                    default => null,
                                };
                            })
                            ->helperText(new HtmlString('
                                <span class="text-xs text-gray-500 dark:text-gray-400">
                                    <strong>Brevemente</strong>: página de lançamento.
                                    <strong>Inativa</strong>: permite navegar e adicionar ao carrinho, mas bloqueia finalização.
                                    <strong>Ativada</strong>: loja totalmente operacional.
                                </span>
                            ')),
                        Forms\Components\Hidden::make('is_shop_active')
                            ->default(true)
                            ->dehydrated(true),
                        Forms\Components\Hidden::make('is_shop_brevemente')
                            ->default(false)
                            ->dehydrated(true),
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
                            ->label('Timeout local de pagamento')
                            ->numeric()
                            ->suffix('minutos')
                            ->minValue(1)
                            ->default(30)
                            ->helperText('Tempo (em minutos) que o sistema aguarda antes de considerar um pagamento pendente como expirado e poder cancelá-lo automaticamente. Controlo local, independente da IfThenPay.'),
                        Forms\Components\TextInput::make('payment_expiry_grace_minutes')
                            ->label('Margem de segurança local')
                            ->numeric()
                            ->suffix('minutos')
                            ->minValue(0)
                            ->default(10)
                            ->helperText('Minutos extra adicionados ao timeout local e/ou expiração do fornecedor como margem de segurança antes do cancelamento. Evita cancelar um pagamento que ainda possa ser confirmado.'),
                        Forms\Components\TextInput::make('mbway_minutes_to_expire')
                            ->label('Expiração MB WAY (IfThenPay)')
                            ->numeric()
                            ->suffix('minutos')
                            ->minValue(1)
                            ->default(4)
                            ->helperText('Prazo de expiração enviado à IfThenPay para pedidos MB WAY. O cliente terá este tempo para confirmar na app. Independente do timeout local.'),
                        Forms\Components\TextInput::make('multibanco_days_to_expire')
                            ->label('Expiração Multibanco (IfThenPay)')
                            ->numeric()
                            ->suffix('dias')
                            ->minValue(1)
                            ->default(3)
                            ->helperText('Prazo em dias enviado à IfThenPay para referências Multibanco. A referência expira após este número de dias. Independente do timeout local.'),
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

    /**
     * Derive is_shop_active, is_shop_brevemente from the virtual shop_mode select.
     */
    public static function mapShopModeToBooleans(array $data): array
    {
        $state = $data['shop_mode'] ?? 'ativada';

        return match ($state) {
            'brevemente' => array_merge($data, [
                'is_shop_active' => true,
                'is_shop_brevemente' => true,
            ]),
            'inativa' => array_merge($data, [
                'is_shop_active' => false,
                'is_shop_brevemente' => false,
            ]),
            'ativada' => array_merge($data, [
                'is_shop_active' => true,
                'is_shop_brevemente' => false,
            ]),
            default => $data,
        };
    }
}
