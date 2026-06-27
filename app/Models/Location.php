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
}
