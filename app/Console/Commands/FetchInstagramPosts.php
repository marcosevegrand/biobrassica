<?php

namespace App\Console\Commands;

use App\Models\InstagramPost;
use Illuminate\Console\Command;

class FetchInstagramPosts extends Command
{
    protected $signature = 'instagram:fetch {shortcodes?* : Instagram post shortcodes to activate}';

    protected $description = 'Refresh the curated Instagram post list from arguments or INSTAGRAM_POST_SHORTCODES.';

    public function handle(): int
    {
        $shortcodes = $this->argument('shortcodes');

        if (empty($shortcodes)) {
            $shortcodes = array_filter(array_map('trim', explode(',', (string) env('INSTAGRAM_POST_SHORTCODES', ''))));
        }

        if (empty($shortcodes)) {
            $this->warn('No Instagram shortcodes supplied.');

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
