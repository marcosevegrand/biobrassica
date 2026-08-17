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
                    'shop_coming_soon' => true,
                ]);
            }

            return $websiteDefaults;
        };

        $shopCtaResolver = function () use ($websiteDefaultsResolver): array {
            $comingSoon = (bool) ($websiteDefaultsResolver()->shop_coming_soon ?? true);

            return [
                'coming_soon' => $comingSoon,
                'url' => $comingSoon ? '#' : (string) config('biobrassica.shop_url', '#'),
                'label' => $comingSoon ? 'Em breve' : 'Loja',
            ];
        };

        View::composer('*', function ($view) use ($websiteDefaultsResolver, $shopCtaResolver) {
            $data = $view->getData();

            if (! isset($data['websiteDefaults']) || ! $data['websiteDefaults']) {
                $view->with('websiteDefaults', $websiteDefaultsResolver());
            }

            if (! isset($data['shopCta']) || ! $data['shopCta']) {
                $view->with('shopCta', $shopCtaResolver());
            }
        });
    }
}
