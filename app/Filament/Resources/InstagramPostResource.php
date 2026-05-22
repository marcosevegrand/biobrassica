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

    protected static ?string $navigationLabel = 'Instagram Posts';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\TextInput::make('instagram_id')
                    ->required()
                    ->maxLength(255),
                Forms\Components\TextInput::make('permalink')
                    ->url()
                    ->maxLength(255),
                Forms\Components\TextInput::make('image_url')
                    ->url()
                    ->maxLength(255),
                Forms\Components\Textarea::make('caption')
                    ->maxLength(65535),
                Forms\Components\DateTimePicker::make('posted_at'),
                Forms\Components\DateTimePicker::make('fetched_at'),
                Forms\Components\TextInput::make('sort_order')
                    ->numeric()
                    ->default(0),
                Forms\Components\Toggle::make('is_active')
                    ->default(true),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('instagram_id')
                    ->searchable(),
                Tables\Columns\TextColumn::make('sort_order')
                    ->numeric()
                    ->sortable(),
                Tables\Columns\IconColumn::make('is_active')
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
