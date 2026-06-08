<?php

namespace App\Providers;

use App\Models\WebsiteContent;
use Illuminate\Support\Facades\View;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        if ($publicPath = config('biobrassica.public_path')) {
            $this->app->usePublicPath($publicPath);
        }
    }

    public function boot(): void
    {
        View::composer('*', function ($view) {
            $data = $view->getData();

            if (!isset($data['websiteDefaults']) || !$data['websiteDefaults']) {
                $websiteDefaults = WebsiteContent::first();

                if (!$websiteDefaults) {
                    $websiteDefaults = new WebsiteContent([
                        'company_legal_name' => config('app.name', 'BioBrassica'),
                        'support_email' => config('mail.from.address', 'hello@example.com'),
                    ]);
                }

                $view->with('websiteDefaults', $websiteDefaults);
            }
        });
    }
}
