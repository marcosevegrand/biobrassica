<?php

namespace App\Filament\Resources\OrderResource\RelationManagers;

use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\RelationManagers\RelationManager;
use Filament\Tables;
use Filament\Tables\Table;

class OrderItemsRelationManager extends RelationManager
{
    protected static string $relationship = 'items';

    protected static ?string $title = 'Produtos da encomenda';

    public function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Select::make('product_id')
                    ->label('Produto')
                    ->relationship('product', 'name')
                    ->searchable()
                    ->preload()
                    ->disabled()
                    ->required(),
                Forms\Components\TextInput::make('product_name')
                    ->label('Nome do produto')
                    ->disabled()
                    ->required()
                    ->maxLength(255),
                Forms\Components\TextInput::make('price')
                    ->label('Preço')
                    ->required()
                    ->numeric()
                    ->disabled()
                    ->prefix('€'),
                Forms\Components\TextInput::make('quantity')
                    ->label('Quantidade')
                    ->required()
                    ->numeric()
                    ->disabled()
                    ->default(1),
            ]);
    }

    public function table(Table $table): Table
    {
        return $table
            ->recordTitleAttribute('product_name')
            ->columns([
                Tables\Columns\TextColumn::make('product_name')
                    ->label('Produto'),
                Tables\Columns\TextColumn::make('price')
                    ->label('Preço')
                    ->money('EUR'),
                Tables\Columns\TextColumn::make('quantity')
                    ->label('Quantidade'),
                Tables\Columns\TextColumn::make('subtotal')
                    ->label('Subtotal')
                    ->state(fn ($record) => number_format($record->price * $record->quantity, 2).' €'),
            ])
            ->filters([
                //
            ])
            ->headerActions([
                // Order items are immutable audit records after checkout.
            ])
            ->actions([
                // Use a dedicated audited adjustment flow if order edits are needed later.
            ])
            ->bulkActions([
                // No bulk destructive actions for order financial lines.
            ]);
    }
}
