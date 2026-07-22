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

    protected static ?string $navigationGroup = 'Catálogo';

    protected static ?string $navigationLabel = 'Definições do catálogo';

    protected static ?string $modelLabel = 'definições do catálogo';

    protected static ?string $slug = 'catalog-settings';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Section::make('Estado do catálogo')
                    ->schema([
                        Forms\Components\Select::make('shop_mode')
                            ->label('Modo')
                            ->options([
                                'brevemente' => 'Brevemente',
                                'inativa' => 'Inativo',
                                'ativada' => 'Ativo',
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
                                    <strong>Brevemente</strong>: mostra página de lançamento.
                                    <strong>Inativo</strong>: catálogo indisponível.
                                    <strong>Ativo</strong>: catálogo totalmente visível.
                                </span>
                            ')),
                        Forms\Components\Hidden::make('is_shop_active')
                            ->default(true)
                            ->dehydrated(true),
                        Forms\Components\Hidden::make('is_shop_brevemente')
                            ->default(false)
                            ->dehydrated(true),
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
