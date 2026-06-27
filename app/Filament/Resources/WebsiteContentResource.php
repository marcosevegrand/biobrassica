<?php

namespace App\Filament\Resources;

use App\Filament\Resources\WebsiteContentResource\Pages;
use App\Models\WebsiteContent;
use Filament\Forms;
use Filament\Forms\Form;
use Filament\Resources\Resource;
use Filament\Tables\Table;

class WebsiteContentResource extends Resource
{
    protected static ?string $model = WebsiteContent::class;

    protected static ?string $navigationIcon = 'heroicon-o-globe-alt';

    protected static ?string $navigationGroup = 'Website';

    protected static ?string $navigationLabel = 'Website Content';

    protected static ?string $slug = 'website-content';

    public static function form(Form $form): Form
    {
        return $form
            ->schema([
                Forms\Components\Tabs::make('Content')
                    ->tabs([
                        Forms\Components\Tabs\Tab::make('Company Info')
                            ->schema([
                                Forms\Components\TextInput::make('company_legal_name')
                                    ->maxLength(255),
                                Forms\Components\Textarea::make('company_address')
                                    ->maxLength(65535)
                                    ->columnSpanFull(),
                                Forms\Components\TextInput::make('company_nif')
                                    ->label('NIF')
                                    ->maxLength(255),
                                Forms\Components\TextInput::make('support_email')
                                    ->email()
                                    ->maxLength(255),
                            ]),
                        Forms\Components\Tabs\Tab::make('Homepage Hero')
                            ->schema([
                                Forms\Components\TextInput::make('hero_title')
                                    ->maxLength(255),
                                Forms\Components\Textarea::make('hero_subtitle')
                                    ->maxLength(65535),
                                Forms\Components\TextInput::make('hero_cta_text')
                                    ->maxLength(255),
                                Forms\Components\TextInput::make('hero_cta_url')
                                    ->url()
                                    ->maxLength(255),
                            ]),
                        Forms\Components\Tabs\Tab::make('About Page')
                            ->schema([
                                Forms\Components\TextInput::make('about_title')
                                    ->maxLength(255),
                                Forms\Components\RichEditor::make('about_content')
                                    ->columnSpanFull(),
                                Forms\Components\FileUpload::make('about_image')
                                    ->image()
                                    ->acceptedFileTypes(['image/jpeg', 'image/png', 'image/webp', 'image/gif'])
                                    ->maxSize(4096)
                                    ->directory('website')
                                    ->imageEditor(),
                            ]),
                        Forms\Components\Tabs\Tab::make('Agriculture Page')
                            ->schema([
                                Forms\Components\TextInput::make('agriculture_title')
                                    ->maxLength(255),
                                Forms\Components\RichEditor::make('agriculture_content')
                                    ->columnSpanFull(),
                                Forms\Components\FileUpload::make('agriculture_image')
                                    ->image()
                                    ->acceptedFileTypes(['image/jpeg', 'image/png', 'image/webp', 'image/gif'])
                                    ->maxSize(4096)
                                    ->directory('website')
                                    ->imageEditor(),
                            ]),
                        Forms\Components\Tabs\Tab::make('Contacts Page')
                            ->schema([
                                Forms\Components\TextInput::make('contacts_title')
                                    ->maxLength(255),
                                Forms\Components\RichEditor::make('contacts_content')
                                    ->columnSpanFull(),
                            ]),
                        Forms\Components\Tabs\Tab::make('WhatsApp')
                            ->schema([
                                Forms\Components\TextInput::make('whatsapp_number')
                                    ->tel()
                                    ->maxLength(255)
                                    ->helperText('Full phone number with country code'),
                            ]),
                        Forms\Components\Tabs\Tab::make('Footer')
                            ->schema([
                                Forms\Components\Textarea::make('footer_about')
                                    ->maxLength(65535),
                                Forms\Components\TextInput::make('footer_address')
                                    ->maxLength(255),
                                Forms\Components\TextInput::make('footer_email')
                                    ->email()
                                    ->maxLength(255),
                                Forms\Components\TextInput::make('footer_phone')
                                    ->tel()
                                    ->maxLength(255),
                            ]),
                        Forms\Components\Tabs\Tab::make('Social Media')
                            ->schema([
                                Forms\Components\TextInput::make('facebook_url')
                                    ->url()
                                    ->maxLength(255),
                                Forms\Components\TextInput::make('instagram_url')
                                    ->url()
                                    ->maxLength(255),
                                Forms\Components\TextInput::make('youtube_url')
                                    ->url()
                                    ->maxLength(255),
                                Forms\Components\TextInput::make('linkedin_url')
                                    ->url()
                                    ->maxLength(255),
                            ]),
                        Forms\Components\Tabs\Tab::make('SEO')
                            ->schema([
                                Forms\Components\TextInput::make('seo_title')
                                    ->maxLength(255),
                                Forms\Components\Textarea::make('seo_description')
                                    ->maxLength(65535),
                                Forms\Components\Textarea::make('seo_keywords')
                                    ->maxLength(65535),
                            ]),
                        Forms\Components\Tabs\Tab::make('Legal')
                            ->schema([
                                Forms\Components\RichEditor::make('cookies_text')
                                    ->columnSpanFull(),
                                Forms\Components\RichEditor::make('privacy_policy_text')
                                    ->columnSpanFull(),
                                Forms\Components\RichEditor::make('terms_conditions_text')
                                    ->columnSpanFull(),
                            ]),
                        Forms\Components\Tabs\Tab::make('Tracking & Scripts')
                            ->schema([
                                Forms\Components\TextInput::make('google_analytics_id')
                                    ->maxLength(255)
                                    ->placeholder('G-XXXXXXXXXX'),
                                Forms\Components\TextInput::make('google_tag_manager_id')
                                    ->maxLength(255)
                                    ->placeholder('GTM-XXXXXXX'),
                            ]),
                    ])
                    ->columnSpanFull(),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([])
            ->actions([])
            ->bulkActions([]);
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
            'index' => Pages\ManageWebsiteContent::route('/'),
        ];
    }
}
