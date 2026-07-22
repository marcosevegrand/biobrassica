<?php

namespace App\Providers;

use App\Models\WebsiteContent;
use Illuminate\Support\Facades\View;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        if ($publicPath = env('APP_PUBLIC_PATH')) {
            $this->app->usePublicPath($publicPath);
        }
    }

    public function boot(): void
    {
        $websiteDefaultsResolver = function (): WebsiteContent {
            static $websiteDefaults = null;

            if ($websiteDefaults instanceof WebsiteContent) {
                return $websiteDefaults;
            }

            try {
                $websiteDefaults = WebsiteContent::first();
            } catch (\Throwable) {
                $websiteDefaults = null;
            }

            if (! $websiteDefaults) {
                $websiteDefaults = new WebsiteContent([
                    'company_legal_name' => config('app.name', 'BioBrassica'),
                    'support_email' => config('mail.from.address', 'hello@example.com'),
                ]);
            }

            return $websiteDefaults;
        };

        View::composer('*', function ($view) use ($websiteDefaultsResolver) {
            $data = $view->getData();

            if (! isset($data['websiteDefaults']) || ! $data['websiteDefaults']) {
                $view->with('websiteDefaults', $websiteDefaultsResolver());
            }
        });
    }
}
