<?php

namespace App\Filament\Resources;

use App\Filament\Resources\ProductResource\Pages;
use App\Filament\Resources\ProductResource\RelationManagers;
use App\Models\Category;
use App\Models\Location;
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

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Select::make('category_id')
                    ->relationship('category', 'name')
                    ->searchable()
                    ->preload()
                    ->required(),
                Forms\Components\TextInput::make('name')
                    ->required()
                    ->maxLength(255),
                Forms\Components\TextInput::make('slug')
                    ->required()
                    ->maxLength(255)
                    ->unique(ignoreRecord: true),
                Forms\Components\TextInput::make('brand')
                    ->maxLength(255),
                Forms\Components\TextInput::make('bio_code')
                    ->label('BIO Code')
                    ->maxLength(255),
                Forms\Components\RichEditor::make('description')
                    ->columnSpanFull(),
                Forms\Components\Textarea::make('allergens')
                    ->columnSpanFull(),
                Forms\Components\TextInput::make('price')
                    ->required()
                    ->numeric()
                    ->prefix('€'),
                Forms\Components\TextInput::make('quantity')
                    ->numeric()
                    ->helperText('Quantity per unit (e.g., weight/volume)'),
                Forms\Components\TextInput::make('stock')
                    ->required()
                    ->numeric()
                    ->default(0),
                Forms\Components\FileUpload::make('image')
                    ->image()
                    ->directory('products')
                    ->imageEditor(),
                Forms\Components\Select::make('pickupLocations')
                    ->relationship('pickupLocations', 'name')
                    ->multiple()
                    ->preload(),
                Forms\Components\Section::make('Flags')
                    ->schema([
                        Forms\Components\Toggle::make('is_active')
                            ->default(true),
                        Forms\Components\Toggle::make('is_highlight')
                            ->default(false),
                        Forms\Components\Toggle::make('is_preview')
                            ->default(false),
                        Forms\Components\Toggle::make('allow_shipping')
                            ->default(true),
                        Forms\Components\Toggle::make('allow_pickup')
                            ->default(true),
                    ])->columns(3),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('name')
                    ->searchable(),
                Tables\Columns\TextColumn::make('category.name')
                    ->searchable()
                    ->sortable(),
                Tables\Columns\TextColumn::make('price')
                    ->money('EUR')
                    ->sortable(),
                Tables\Columns\TextColumn::make('stock')
                    ->numeric()
                    ->sortable(),
                Tables\Columns\IconColumn::make('is_active')
                    ->boolean(),
                Tables\Columns\IconColumn::make('is_highlight')
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
