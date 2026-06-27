<?php

namespace App\Filament\Resources;

use App\Filament\Resources\InstagramPostResource\Pages;
use App\Models\InstagramPost;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class InstagramPostResource extends Resource
{
    protected static ?string $model = InstagramPost::class;

    protected static ?string $navigationIcon = 'heroicon-o-camera';

    protected static ?string $navigationGroup = 'Website';

    protected static ?string $navigationLabel = 'Instagram';

    protected static ?string $modelLabel = 'publicação de Instagram';

    protected static ?string $pluralModelLabel = 'publicações de Instagram';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\TextInput::make('instagram_id')
                    ->label('Shortcode')
                    ->helperText('Parte do URL depois de /p/, /reel/ ou /tv/. Ex.: C7abc123XYZ')
                    ->required()
                    ->maxLength(255)
                    ->regex('/^[A-Za-z0-9_-]+$/'),
                Forms\Components\TextInput::make('permalink')
                    ->label('URL da publicação')
                    ->url()
                    ->maxLength(255)
                    ->helperText('Pode ser /p/, /reel/ ou /tv/. Se ficar vazio, use o shortcode para gerar/importar.'),
                Forms\Components\TextInput::make('image_url')
                    ->label('URL da imagem')
                    ->url()
                    ->maxLength(255),
                Forms\Components\Textarea::make('caption')
                    ->label('Legenda')
                    ->maxLength(65535),
                Forms\Components\DateTimePicker::make('posted_at')
                    ->label('Publicado em'),
                Forms\Components\DateTimePicker::make('fetched_at')
                    ->label('Importado em'),
                Forms\Components\TextInput::make('sort_order')
                    ->label('Ordem')
                    ->numeric()
                    ->default(0),
                Forms\Components\Toggle::make('is_active')
                    ->label('Ativa')
                    ->default(true),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('instagram_id')
                    ->label('Shortcode')
                    ->searchable(),
                Tables\Columns\TextColumn::make('sort_order')
                    ->label('Ordem')
                    ->numeric()
                    ->sortable(),
                Tables\Columns\IconColumn::make('is_active')
                    ->label('Ativa')
                    ->boolean(),
            ])
            ->filters([
                Tables\Filters\TernaryFilter::make('is_active'),
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ])
            ->defaultSort('sort_order');
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
            'index' => Pages\ListInstagramPosts::route('/'),
            'create' => Pages\CreateInstagramPost::route('/create'),
            'edit' => Pages\EditInstagramPost::route('/{record}/edit'),
        ];
    }
}
