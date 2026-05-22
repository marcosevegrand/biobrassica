<?php

namespace App\Filament\Resources\BlogPostResource\RelationManagers;

use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\RelationManagers\RelationManager;
use Filament\Tables;
use Filament\Tables\Table;

class BlogPostTranslationRelationManager extends RelationManager
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
                Forms\Components\TextInput::make('title')
                    ->required()
                    ->maxLength(255),
                Forms\Components\Textarea::make('excerpt')
                    ->maxLength(65535),
                Forms\Components\RichEditor::make('content')
                    ->columnSpanFull(),
                Forms\Components\Textarea::make('meta_description')
                    ->maxLength(65535),
            ]);
    }

    public function table(Table $table): Table
    {
        return $table
            ->recordTitleAttribute('title')
            ->columns([
                Tables\Columns\TextColumn::make('language')
                    ->badge(),
                Tables\Columns\TextColumn::make('title'),
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
