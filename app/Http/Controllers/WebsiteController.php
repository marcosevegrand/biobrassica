<?php

namespace App\Http\Controllers;

use App\Models\InstagramPost;
use App\Models\Recipe;
use App\Models\WebsiteContent;

class WebsiteController extends Controller
{
    public function home()
    {
        $websiteContent = $this->websiteContent();
        $instagramPosts = $this->safeCollection(fn () => InstagramPost::where('is_active', true)
            ->orderBy('sort_order')
            ->take(5)
            ->get());
        $featuredRecipes = $this->safeCollection(fn () => Recipe::query()
            ->with('translations')
            ->where('is_published', true)
            ->latest('published_at')
            ->take(3)
            ->get());
        $locale = app()->getLocale();

        return view('website.home', compact('websiteContent', 'instagramPosts', 'featuredRecipes', 'locale'));
    }

    public function about()
    {
        $websiteContent = $this->websiteContent();

        return view('website.about', compact('websiteContent'));
    }

    public function agriculture()
    {
        $websiteContent = $this->websiteContent();

        return view('website.agriculture', compact('websiteContent'));
    }

    public function contacts()
    {
        $websiteContent = $this->websiteContent();
        $stores = $this->stores();

        return view('website.contacts', compact('websiteContent', 'stores'));
    }

    public function privacy()
    {
        $websiteContent = $this->websiteContent();

        return view('website.privacy', compact('websiteContent'));
    }

    public function terms()
    {
        $websiteContent = $this->websiteContent();

        return view('website.terms', compact('websiteContent'));
    }

    private function websiteContent(): ?WebsiteContent
    {
        try {
            return WebsiteContent::first();
        } catch (\Throwable) {
            return null;
        }
    }

    /**
     * Physical store locations for display on contacts and footer.
     */
    private function stores(): array
    {
        return [
            (object) [
                'name' => 'Loja Braga',
                'address' => "Avenida Doutor António Palha\nBraga",
                'phone' => '253 271 187',
                'email' => 'geral@biobrassica.pt',
                'opening_hours' => "Segunda a Sábado\n9h00 – 19h30",
                'image' => 'images/shop/loja-braga.webp',
                'map_embed_url' => 'https://maps.google.com/maps?q=Biobr%C3%A1ssica+Braga+Avenida+Doutor+Ant%C3%B3nio+Palha&t=&z=16&ie=UTF8&iwloc=&output=embed',
            ],
            (object) [
                'name' => 'Loja Guimarães',
                'address' => "Rua Calouste Gulbenkian\nGuimarães",
                'phone' => '253 145 388',
                'email' => 'geral@biobrassica.pt',
                'opening_hours' => "Segunda a Sábado\n9h00 – 19h30",
                'image' => 'images/shop/loja-guima.webp',
                'map_embed_url' => 'https://maps.google.com/maps?q=Biobr%C3%A1ssica+Guimar%C3%A3es+Rua+Calouste+Gulbenkian&t=&z=16&ie=UTF8&iwloc=&output=embed',
            ],
        ];
    }

    private function safeCollection(callable $callback, $fallback = null)
    {
        try {
            return $callback();
        } catch (\Throwable) {
            return $fallback ?? collect();
        }
    }

}
