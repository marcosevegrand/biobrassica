<?php

namespace App\Filament\Resources;

use App\Filament\Resources\ProductResource\Pages;
use App\Filament\Resources\ProductResource\RelationManagers;
use App\Models\Product;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Support\HtmlString;

class ProductResource extends Resource
{
    protected static ?string $model = Product::class;

    protected static ?string $navigationIcon = 'heroicon-o-shopping-bag';

    protected static ?string $navigationGroup = 'Loja';

    protected static ?string $navigationLabel = 'Produtos';

    protected static ?string $modelLabel = 'produto';

    protected static ?string $pluralModelLabel = 'produtos';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Select::make('category_id')
                    ->label('Categoria')
                    ->relationship('category', 'name')
                    ->searchable()
                    ->preload()
                    ->required(),
                Forms\Components\TextInput::make('name')
                    ->label('Nome')
                    ->required()
                    ->maxLength(255),
                Forms\Components\TextInput::make('slug')
                    ->label('Slug')
                    ->required()
                    ->maxLength(255)
                    ->unique(ignoreRecord: true),
                Forms\Components\TextInput::make('brand')
                    ->label('Marca')
                    ->maxLength(255),
                Forms\Components\TextInput::make('bio_code')
                    ->label('Código BIO')
                    ->maxLength(255),
                Forms\Components\RichEditor::make('description')
                    ->label('Descrição')
                    ->columnSpanFull(),
                Forms\Components\Textarea::make('allergens')
                    ->label('Alergénios')
                    ->columnSpanFull(),
                Forms\Components\TextInput::make('price')
                    ->label('Preço')
                    ->required()
                    ->numeric()
                    ->prefix('€'),
                Forms\Components\TextInput::make('quantity')
                    ->label('Unidade / formato de venda')
                    ->maxLength(80)
                    ->helperText('Ex.: 500g, 1kg, molho, caixa 6 un.'),
                Forms\Components\TextInput::make('stock')
                    ->label('Stock')
                    ->required()
                    ->numeric()
                    ->default(0),
                Forms\Components\FileUpload::make('image')
                    ->label('Imagem')
                    ->image()
                    ->acceptedFileTypes(['image/jpeg', 'image/png', 'image/webp', 'image/gif'])
                    ->maxSize(4096)
                    ->directory('products')
                    ->imageEditor(),
                Forms\Components\Select::make('pickupLocations')
                    ->label('Locais de levantamento')
                    ->relationship('pickupLocations', 'name')
                    ->multiple()
                    ->preload(),
                Forms\Components\Section::make('Visibilidade e entrega')
                    ->schema([
                        Forms\Components\Select::make('visibility')
                            ->label('Visibilidade')
                            ->options([
                                'hidden' => 'Escondido',
                                'preview' => 'Pré-visualização',
                                'normal' => 'Normal',
                                'highlighted' => 'Destacado',
                            ])
                            ->default('normal')
                            ->required()
                            ->reactive()
                            ->afterStateHydrated(function (Forms\Components\Select $component, ?Product $record): void {
                                if (! $record) {
                                    $component->state('normal');

                                    return;
                                }
                                if (! $record->is_active) {
                                    $component->state('hidden');
                                } elseif ($record->is_preview) {
                                    $component->state('preview');
                                } elseif ($record->is_highlight) {
                                    $component->state('highlighted');
                                } else {
                                    $component->state('normal');
                                }
                            })
                            ->afterStateUpdated(function (Forms\Set $set, $state): void {
                                match ($state) {
                                    'hidden' => tap($set, function ($set) {
                                        $set('is_active', false);
                                        $set('is_preview', false);
                                        $set('is_highlight', false);
                                    }),
                                    'preview' => tap($set, function ($set) {
                                        $set('is_active', true);
                                        $set('is_preview', true);
                                        $set('is_highlight', false);
                                    }),
                                    'normal' => tap($set, function ($set) {
                                        $set('is_active', true);
                                        $set('is_preview', false);
                                        $set('is_highlight', false);
                                    }),
                                    'highlighted' => tap($set, function ($set) {
                                        $set('is_active', true);
                                        $set('is_preview', false);
                                        $set('is_highlight', true);
                                    }),
                                    default => null,
                                };
                            })
                            ->helperText(new HtmlString('
                                <span class="text-xs text-gray-500 dark:text-gray-400">
                                    <strong>Escondido</strong>: não visível na loja.
                                    <strong>Pré-vis.</strong>: visível mas sem compra.
                                    <strong>Normal</strong>: visível, permite compra.
                                    <strong>Destacado</strong>: visível com destaque na loja.
                                </span>
                            ')),
                        Forms\Components\Select::make('delivery')
                            ->label('Entrega')
                            ->options([
                                'pickup_only' => 'Apenas Levantamento',
                                'shipping_only' => 'Apenas Envio',
                                'both' => 'Ambos',
                            ])
                            ->default('both')
                            ->required()
                            ->reactive()
                            ->afterStateHydrated(function (Forms\Components\Select $component, ?Product $record): void {
                                if (! $record) {
                                    $component->state('both');

                                    return;
                                }
                                if (! $record->allow_shipping && $record->allow_pickup) {
                                    $component->state('pickup_only');
                                } elseif ($record->allow_shipping && ! $record->allow_pickup) {
                                    $component->state('shipping_only');
                                } else {
                                    $component->state('both');
                                }
                            })
                            ->afterStateUpdated(function (Forms\Set $set, $state): void {
                                match ($state) {
                                    'pickup_only' => tap($set, function ($set) {
                                        $set('allow_shipping', false);
                                        $set('allow_pickup', true);
                                    }),
                                    'shipping_only' => tap($set, function ($set) {
                                        $set('allow_shipping', true);
                                        $set('allow_pickup', false);
                                    }),
                                    'both' => tap($set, function ($set) {
                                        $set('allow_shipping', true);
                                        $set('allow_pickup', true);
                                    }),
                                    default => null,
                                };
                            }),
                        // Hidden fields that store the actual DB column values.
                        // Select afterStateUpdated keeps them in sync; Filament dehydrates them on save.
                        Forms\Components\Hidden::make('is_active')
                            ->default(true)
                            ->dehydrated(true),
                        Forms\Components\Hidden::make('is_highlight')
                            ->default(false)
                            ->dehydrated(true),
                        Forms\Components\Hidden::make('is_preview')
                            ->default(false)
                            ->dehydrated(true),
                        Forms\Components\Hidden::make('allow_shipping')
                            ->default(true)
                            ->dehydrated(true),
                        Forms\Components\Hidden::make('allow_pickup')
                            ->default(true)
                            ->dehydrated(true),
                    ])->columns(2),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('name')
                    ->label('Nome')
                    ->searchable(),
                Tables\Columns\TextColumn::make('category.name')
                    ->label('Categoria')
                    ->searchable()
                    ->sortable(),
                Tables\Columns\TextColumn::make('price')
                    ->label('Preço')
                    ->money('EUR')
                    ->sortable(),
                Tables\Columns\TextColumn::make('stock')
                    ->label('Stock')
                    ->numeric()
                    ->sortable(),
                Tables\Columns\TextColumn::make('visibilityLabel')
                    ->label('Visibilidade')
                    ->badge()
                    ->color(fn ($state): string => match ($state) {
                        'Escondido' => 'danger',
                        'Pré-visualização' => 'warning',
                        'Normal' => 'success',
                        'Destacado' => 'info',
                        default => 'gray',
                    }),
                Tables\Columns\TextColumn::make('deliveryLabel')
                    ->label('Entrega'),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('category')
                    ->relationship('category', 'name'),
                Tables\Filters\TernaryFilter::make('is_active')
                    ->label('Ativo'),
                Tables\Filters\TernaryFilter::make('is_highlight')
                    ->label('Destacado'),
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ]);
    }

    public static function getRelations(): array
    {
        return [
            RelationManagers\ProductTranslationRelationManager::class,
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListProducts::route('/'),
            'create' => Pages\CreateProduct::route('/create'),
            'edit' => Pages\EditProduct::route('/{record}/edit'),
        ];
    }

    /**
     * Derive is_active, is_preview, is_highlight from the virtual visibility select.
     */
    public static function mapVisibilityToBooleans(array $data): array
    {
        $state = $data['visibility'] ?? 'normal';

        return match ($state) {
            'hidden' => array_merge($data, [
                'is_active' => false,
                'is_preview' => false,
                'is_highlight' => false,
            ]),
            'preview' => array_merge($data, [
                'is_active' => true,
                'is_preview' => true,
                'is_highlight' => false,
            ]),
            'normal' => array_merge($data, [
                'is_active' => true,
                'is_preview' => false,
                'is_highlight' => false,
            ]),
            'highlighted' => array_merge($data, [
                'is_active' => true,
                'is_preview' => false,
                'is_highlight' => true,
            ]),
            default => $data,
        };
    }

    /**
     * Derive allow_pickup, allow_shipping from the virtual delivery select.
     */
    public static function mapDeliveryToBooleans(array $data): array
    {
        $state = $data['delivery'] ?? 'both';

        return match ($state) {
            'pickup_only' => array_merge($data, [
                'allow_shipping' => false,
                'allow_pickup' => true,
            ]),
            'shipping_only' => array_merge($data, [
                'allow_shipping' => true,
                'allow_pickup' => false,
            ]),
            'both' => array_merge($data, [
                'allow_shipping' => true,
                'allow_pickup' => true,
            ]),
            default => $data,
        };
    }
}
