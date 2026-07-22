<?php

namespace App\Filament\Resources;

use App\Filament\Resources\RecipeResource\Pages;
use App\Filament\Resources\RecipeResource\RelationManagers;
use App\Models\Recipe;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class RecipeResource extends Resource
{
    protected static ?string $model = Recipe::class;

    protected static ?string $navigationIcon = 'heroicon-o-book-open';

    protected static ?string $navigationGroup = 'Conteúdo';

    protected static ?string $navigationLabel = 'Receitas';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\TextInput::make('slug')
                    ->required()
                    ->maxLength(255)
                    ->unique(ignoreRecord: true),
                Forms\Components\FileUpload::make('cover_image')
                    ->image()
                    ->acceptedFileTypes(['image/jpeg', 'image/png', 'image/webp', 'image/gif'])
                    ->maxSize(4096)
                    ->directory('recipes')
                    ->imageEditor(),
                Forms\Components\TextInput::make('prep_time')
                    ->numeric()
                    ->suffix('min'),

                Forms\Components\TextInput::make('cook_time')
                    ->numeric()
                    ->suffix('min'),

                Forms\Components\TextInput::make('servings')
                    ->numeric(),

                Forms\Components\Select::make('difficulty')
                    ->options([
                        'easy' => 'Easy',
                        'medium' => 'Medium',
                        'hard' => 'Hard',
                    ])
                    ->required(),

                Forms\Components\TagsInput::make('tags'),

                Forms\Components\Select::make('products')
                    ->relationship('products', 'name')
                    ->multiple()
                    ->preload()
                    ->label('Related Products'),

                Forms\Components\Toggle::make('is_published')
                    ->default(false),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('title')
                    ->label('Title')
                    ->state(function (Recipe $record): string {
                        $pt = $record->translations->where('language', 'pt')->first();

                        return $pt?->title ?? $record->slug;
                    })
                    ->searchable(query: function ($query, $search) {
                        $query->whereHas('translations', function ($q) use ($search) {
                            $q->where('language', 'pt')->where('title', 'like', "%{$search}%");
                        });
                    }),
                Tables\Columns\IconColumn::make('is_published')
                    ->boolean(),
                Tables\Columns\TextColumn::make('created_at')
                    ->dateTime()
                    ->sortable(),
            ])
            ->filters([
                Tables\Filters\TernaryFilter::make('is_published'),
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
            RelationManagers\RecipeTranslationRelationManager::class,
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListRecipes::route('/'),
            'create' => Pages\CreateRecipe::route('/create'),
            'edit' => Pages\EditRecipe::route('/{record}/edit'),
        ];
    }
}
