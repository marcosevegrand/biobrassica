<?php

namespace App\Http\Controllers;

use App\Models\InstagramPost;
use App\Models\Location;
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
        $locations = Location::stores();

        return view('website.contacts', compact('websiteContent', 'locations'));
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

    private function safeCollection(callable $callback, $fallback = null)
    {
        try {
            return $callback();
        } catch (\Throwable) {
            return $fallback ?? collect();
        }
    }

}
