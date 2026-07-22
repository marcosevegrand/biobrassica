<?php

namespace App\Filament\Resources;

use App\Filament\Resources\UserResource\Pages;
use App\Models\User;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Support\Facades\Hash;

class UserResource extends Resource
{
    protected static ?string $model = User::class;

    protected static ?string $navigationIcon = 'heroicon-o-users';

    protected static ?string $navigationGroup = 'Configuração';

    protected static ?string $navigationLabel = 'Clientes';

    protected static ?string $modelLabel = 'cliente';

    protected static ?string $pluralModelLabel = 'clientes';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Section::make('Dados do cliente')
                    ->schema([
                        Forms\Components\TextInput::make('name')
                            ->label('Nome')
                            ->required()
                            ->maxLength(255),
                        Forms\Components\TextInput::make('email')
                            ->label('Email')
                            ->email()
                            ->required()
                            ->maxLength(255)
                            ->unique(ignoreRecord: true),
                        Forms\Components\TextInput::make('phone')
                            ->label('Telefone')
                            ->tel()
                            ->maxLength(255),
                        Forms\Components\TextInput::make('nif')
                            ->label('NIF')
                            ->maxLength(255),
                        Forms\Components\Select::make('preferred_language')
                            ->label('Idioma preferido')
                            ->options([
                                'pt' => 'Português',
                                'en' => 'English',
                            ])
                            ->default('pt'),
                        Forms\Components\DateTimePicker::make('email_verified_at')
                            ->label('Email verificado em'),
                        Forms\Components\Toggle::make('is_admin')
                            ->label('Administrador')
                            ->helperText('Só utilizadores administradores com email verificado podem aceder ao backoffice.'),
                        Forms\Components\TextInput::make('password')
                            ->label('Palavra-passe')
                            ->password()
                            ->dehydrateStateUsing(fn ($state) => filled($state) ? Hash::make($state) : null)
                            ->dehydrated(fn ($state) => filled($state))
                            ->required(fn (string $context): bool => $context === 'create'),
                    ])
                    ->columns(2),
                Forms\Components\Section::make('Moradas')
                    ->schema([
                        Forms\Components\Repeater::make('addresses')
                            ->label('Moradas')
                            ->relationship('addresses')
                            ->schema([
                                Forms\Components\TextInput::make('name')
                                    ->label('Nome')
                                    ->required()
                                    ->maxLength(255),
                                Forms\Components\TextInput::make('line1')
                                    ->label('Morada')
                                    ->required()
                                    ->maxLength(255),
                                Forms\Components\TextInput::make('line2')
                                    ->label('Complemento')
                                    ->maxLength(255),
                                Forms\Components\TextInput::make('city')
                                    ->label('Localidade')
                                    ->required()
                                    ->maxLength(255),
                                Forms\Components\TextInput::make('postal_code')
                                    ->label('Código postal')
                                    ->maxLength(255),
                                Forms\Components\TextInput::make('country')
                                    ->label('País')
                                    ->maxLength(255)
                                    ->default('Portugal'),
                                Forms\Components\Toggle::make('is_default')
                                    ->label('Morada predefinida'),
                            ])
                            ->columns(2)
                            ->collapsible(),
                    ]),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('name')
                    ->searchable(),
                Tables\Columns\TextColumn::make('email')
                    ->searchable(),
                Tables\Columns\TextColumn::make('phone')
                    ->searchable(),
                Tables\Columns\IconColumn::make('is_admin')
                    ->label('Admin')
                    ->boolean(),
                Tables\Columns\TextColumn::make('created_at')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                //
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
            //
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListUsers::route('/'),
            'create' => Pages\CreateUser::route('/create'),
            'edit' => Pages\EditUser::route('/{record}/edit'),
        ];
    }
}
