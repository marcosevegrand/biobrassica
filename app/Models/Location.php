<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Location extends Model
{
    public const ALLOWED_MAP_EMBED_HOSTS = [
        'www.google.com',
        'google.com',
        'maps.google.com',
        'maps.app.goo.gl',
    ];

    protected $fillable = [
        'name',
        'pickup_location_code',
        'address',
        'image',
        'phone',
        'email',
        'opening_hours',
        'pickup_hours',
        'map_embed_url',
        'is_active',
    ];

    protected function casts(): array
    {
        return [
            'opening_hours' => 'array',
            'pickup_hours' => 'array',
            'is_active' => 'boolean',
        ];
    }

    protected static function booted(): void
    {
        static::created(function (Location $location): void {
            LocationPosition::firstOrCreate(
                ['location_id' => $location->id],
                ['position' => ((int) LocationPosition::max('position')) + 1],
            );
        });
    }

    public function position()
    {
        return $this->hasOne(LocationPosition::class);
    }

    public function products()
    {
        return $this->belongsToMany(Product::class, 'product_pickup_location');
    }

    public static function isAllowedMapEmbedUrl(?string $url): bool
    {
        if (! is_string($url) || trim($url) === '') {
            return true;
        }

        $parts = parse_url(trim($url));

        if ($parts === false || ! in_array($parts['scheme'] ?? '', ['https'], true)) {
            return false;
        }

        $host = strtolower($parts['host'] ?? '');

        return in_array($host, self::ALLOWED_MAP_EMBED_HOSTS, true)
            || str_ends_with($host, '.google.com');
    }

    public function safeMapEmbedUrl(): ?string
    {
        return self::isAllowedMapEmbedUrl($this->map_embed_url) ? $this->map_embed_url : null;
    }

    /**
     * Public-facing store locations (Braga and Guimarães).
     * Always returns hardcoded data; does not query the pickup locations DB.
     *
     * @return \Illuminate\Support\Collection
     */
    public static function stores()
    {
        return collect([
            (object) [
                'name' => 'Loja Braga',
                'pickup_location_code' => 'braga',
                'address' => "Avenida Doutor António Palha\nBraga",
                'image' => 'images/shop/loja-braga.webp',
                'phone' => '253 271 187',
                'email' => 'geral@biobrassica.pt',
                'opening_hours' => "Segunda a Sábado\n9h00 – 19h30",
                'map_embed_url' => 'https://maps.google.com/maps?q=Biobr%C3%A1ssica+Braga+Avenida+Doutor+Ant%C3%B3nio+Palha&t=&z=16&ie=UTF8&iwloc=&output=embed',
            ],
            (object) [
                'name' => 'Loja Guimarães',
                'pickup_location_code' => 'guimaraes',
                'address' => "Rua Calouste Gulbenkian\nGuimarães",
                'image' => 'images/shop/loja-guima.webp',
                'phone' => '253 145 388',
                'email' => 'geral@biobrassica.pt',
                'opening_hours' => "Segunda a Sábado\n9h00 – 19h30",
                'map_embed_url' => 'https://maps.google.com/maps?q=Biobr%C3%A1ssica+Guimar%C3%A3es+Rua+Calouste+Gulbenkian&t=&z=16&ie=UTF8&iwloc=&output=embed',
            ],
        ]);
    }
}
