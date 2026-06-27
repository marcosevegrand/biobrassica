<?php

namespace App\Filament\Resources;

use App\Filament\Resources\LocationResource\Pages;
use App\Models\Location;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables;
use Filament\Tables\Table;

class LocationResource extends Resource
{
    protected static ?string $model = Location::class;

    protected static ?string $navigationIcon = 'heroicon-o-map';

    protected static ?string $navigationGroup = 'Loja';

    protected static ?string $navigationLabel = 'Locais de levantamento';

    protected static ?string $modelLabel = 'local de levantamento';

    protected static ?string $pluralModelLabel = 'locais de levantamento';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\TextInput::make('name')
                    ->required()
                    ->maxLength(255),
                Forms\Components\TextInput::make('pickup_location_code')
                    ->maxLength(255),
                Forms\Components\Textarea::make('address')
                    ->required()
                    ->columnSpanFull(),
                Forms\Components\TextInput::make('phone')
                    ->tel()
                    ->maxLength(255),
                Forms\Components\TextInput::make('email')
                    ->email()
                    ->maxLength(255),
                Forms\Components\FileUpload::make('image')
                    ->image()
                    ->acceptedFileTypes(['image/jpeg', 'image/png', 'image/webp', 'image/gif'])
                    ->maxSize(4096)
                    ->directory('locations')
                    ->imageEditor(),
                Forms\Components\KeyValue::make('opening_hours')
                    ->keyLabel('Day / Period')
                    ->valueLabel('Hours')
                    ->helperText('e.g., "Monday - Friday" => "09:00 - 18:00"'),
                Forms\Components\KeyValue::make('pickup_hours')
                    ->keyLabel('Day / Period')
                    ->valueLabel('Hours')
                    ->helperText('e.g., "Monday - Friday" => "09:00 - 18:00"'),
                Forms\Components\Textarea::make('map_embed_url')
                    ->helperText('Google Maps embed URL')
                    ->rules([
                        fn (): \Closure => function (string $attribute, mixed $value, \Closure $fail): void {
                            if (! Location::isAllowedMapEmbedUrl($value)) {
                                $fail('Indique um URL HTTPS de Google Maps válido.');
                            }
                        },
                    ])
                    ->columnSpanFull(),
                Forms\Components\Toggle::make('is_active')
                    ->default(true),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('name')
                    ->searchable(),
                Tables\Columns\TextColumn::make('phone')
                    ->searchable(),
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
            'index' => Pages\ListLocations::route('/'),
            'create' => Pages\CreateLocation::route('/create'),
            'edit' => Pages\EditLocation::route('/{record}/edit'),
        ];
    }
}
