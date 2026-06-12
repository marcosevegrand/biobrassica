<?php

namespace App\Http\Controllers;

use App\Models\InstagramPost;
use App\Models\Location;
use App\Models\TeamMember;
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
        $teamMembers = $this->getActiveTeamMembers();

        return view('website.home', compact('websiteContent', 'instagramPosts', 'teamMembers'));
    }

    public function about()
    {
        $websiteContent = $this->websiteContent();
        $teamMembers = $this->getActiveTeamMembers();

        return view('website.about', compact('websiteContent', 'teamMembers'));
    }

    public function agriculture()
    {
        $websiteContent = $this->websiteContent();

        return view('website.agriculture', compact('websiteContent'));
    }

    public function contacts()
    {
        $websiteContent = $this->websiteContent();
        $locations = $this->safeCollection(fn () => Location::query()
            ->select('locations.*')
            ->join('location_positions', 'locations.id', '=', 'location_positions.location_id')
            ->where('locations.is_active', true)
            ->orderBy('location_positions.position')
            ->get(), $this->fallbackLocations());

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

    private function getActiveTeamMembers()
    {
        return $this->safeCollection(fn () => TeamMember::query()
            ->select('team_members.*')
            ->join('team_member_positions', 'team_members.id', '=', 'team_member_positions.team_member_id')
            ->where('team_members.is_active', true)
            ->orderBy('team_member_positions.position')
            ->get());
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

    private function fallbackLocations()
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
