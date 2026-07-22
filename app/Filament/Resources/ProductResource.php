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

    protected static ?string $navigationGroup = 'Catálogo';

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
                Forms\Components\TextInput::make('quantity')
                    ->label('Unidade / formato')
                    ->maxLength(80)
                    ->helperText('Ex.: 500g, 1kg, molho, caixa 6 un.'),
                Forms\Components\FileUpload::make('image')
                    ->label('Imagem')
                    ->image()
                    ->acceptedFileTypes(['image/jpeg', 'image/png', 'image/webp', 'image/gif'])
                    ->maxSize(4096)
                    ->directory('products')
                    ->imageEditor(),
                Forms\Components\Section::make('Visibilidade')
                    ->schema([
                        Forms\Components\Select::make('visibility')
                            ->label('Visibilidade')
                            ->options([
                                'hidden' => 'Escondido',
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
                                        $set('is_highlight', false);
                                    }),
                                    'normal' => tap($set, function ($set) {
                                        $set('is_active', true);
                                        $set('is_highlight', false);
                                    }),
                                    'highlighted' => tap($set, function ($set) {
                                        $set('is_active', true);
                                        $set('is_highlight', true);
                                    }),
                                    default => null,
                                };
                            })
                            ->helperText(new HtmlString('
                                <span class="text-xs text-gray-500 dark:text-gray-400">
                                    <strong>Escondido</strong>: não visível no catálogo.
                                    <strong>Normal</strong>: visível no catálogo.
                                    <strong>Destacado</strong>: visível com destaque na página inicial.
                                </span>
                            ')),
                        Forms\Components\Hidden::make('is_active')
                            ->default(true)
                            ->dehydrated(true),
                        Forms\Components\Hidden::make('is_highlight')
                            ->default(false)
                            ->dehydrated(true),
                    ]),
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
                Tables\Columns\TextColumn::make('quantity')
                    ->label('Formato'),
                Tables\Columns\TextColumn::make('visibilityLabel')
                    ->label('Visibilidade')
                    ->badge()
                    ->color(fn ($state): string => match ($state) {
                        'Escondido' => 'danger',
                        'Normal' => 'success',
                        'Destacado' => 'info',
                        default => 'gray',
                    }),
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
     * Derive is_active, is_highlight from the virtual visibility select.
     */
    public static function mapVisibilityToBooleans(array $data): array
    {
        $state = $data['visibility'] ?? 'normal';

        return match ($state) {
            'hidden' => array_merge($data, [
                'is_active' => false,
                'is_highlight' => false,
            ]),
            'normal' => array_merge($data, [
                'is_active' => true,
                'is_highlight' => false,
            ]),
            'highlighted' => array_merge($data, [
                'is_active' => true,
                'is_highlight' => true,
            ]),
            default => $data,
        };
    }
}
