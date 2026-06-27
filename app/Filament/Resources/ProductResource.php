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
                        Forms\Components\Toggle::make('is_active')
                            ->label('Visível na loja')
                            ->default(true),
                        Forms\Components\Toggle::make('is_highlight')
                            ->label('Destacar produto')
                            ->default(false),
                        Forms\Components\Toggle::make('is_preview')
                            ->label('Pré-visualização apenas')
                            ->helperText('Mostra o produto no catálogo, mas impede compra.')
                            ->default(false),
                        Forms\Components\Toggle::make('allow_shipping')
                            ->label('Permitir envio')
                            ->default(true),
                        Forms\Components\Toggle::make('allow_pickup')
                            ->label('Permitir levantamento')
                            ->default(true)
                            ->accepted(fn (Forms\Get $get): bool => ! (bool) $get('allow_shipping')),
                    ])->columns(3),
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
                Tables\Columns\IconColumn::make('is_active')
                    ->label('Ativo')
                    ->boolean(),
                Tables\Columns\IconColumn::make('is_highlight')
                    ->label('Destaque')
                    ->boolean(),
            ])
            ->filters([
                Tables\Filters\SelectFilter::make('category')
                    ->relationship('category', 'name'),
                Tables\Filters\TernaryFilter::make('is_active'),
                Tables\Filters\TernaryFilter::make('is_highlight'),
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
}
