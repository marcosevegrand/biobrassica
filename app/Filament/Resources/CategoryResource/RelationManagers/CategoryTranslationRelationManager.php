<?php

namespace App\Filament\Resources\CategoryResource\RelationManagers;

use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\RelationManagers\RelationManager;
use Filament\Tables;
use Filament\Tables\Table;

class CategoryTranslationRelationManager extends RelationManager
{
    protected static string $relationship = 'translations';

    protected static ?string $title = 'Traduções';

    public function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Select::make('language')
                    ->required()
                    ->options([
                        'pt' => 'Português',
                        'en' => 'English',
                    ]),
                Forms\Components\TextInput::make('name')
                    ->required()
                    ->maxLength(255),
                Forms\Components\Textarea::make('featured_message')
                    ->maxLength(65535),
            ]);
    }

    public function table(Table $table): Table
    {
        return $table
            ->recordTitleAttribute('name')
            ->columns([
                Tables\Columns\TextColumn::make('language')
                    ->badge(),
                Tables\Columns\TextColumn::make('name'),
            ])
            ->filters([
                //
            ])
            ->headerActions([
                Tables\Actions\CreateAction::make(),
            ])
            ->actions([
                Tables\Actions\EditAction::make(),
                Tables\Actions\DeleteAction::make(),
            ])
            ->bulkActions([
                Tables\Actions\BulkActionGroup::make([
                    Tables\Actions\DeleteBulkAction::make(),
                ]),
            ]);
    }
}
