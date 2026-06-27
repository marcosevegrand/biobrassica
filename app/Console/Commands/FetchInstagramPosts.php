<?php

namespace App\Console\Commands;

use App\Models\InstagramPost;
use Illuminate\Console\Command;

class FetchInstagramPosts extends Command
{
    protected $signature = 'instagram:fetch {shortcodes?* : Instagram post shortcodes to activate}';

    protected $description = 'Refresh the curated Instagram post list from supplied shortcode arguments.';

    public function handle(): int
    {
        $shortcodes = $this->argument('shortcodes');

        if (empty($shortcodes)) {
            $this->warn('No Instagram shortcodes supplied. Manage Instagram posts in the admin panel, or pass shortcodes as command arguments.');

            return self::SUCCESS;
        }

        InstagramPost::query()->update(['is_active' => false]);

        foreach (array_values($shortcodes) as $index => $shortcode) {
            InstagramPost::query()->updateOrCreate(
                ['instagram_id' => $shortcode],
                [
                    'permalink' => "https://www.instagram.com/p/{$shortcode}/",
                    'sort_order' => $index + 1,
                    'is_active' => $index < 5,
                    'fetched_at' => now(),
                ],
            );
        }

        $this->info('Instagram post list refreshed.');

        return self::SUCCESS;
    }
}
