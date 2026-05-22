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
        $websiteContent = WebsiteContent::first();
        $instagramPosts = InstagramPost::where('is_active', true)
            ->orderBy('sort_order')
            ->take(5)
            ->get();
        $teamMembers = $this->getActiveTeamMembers();

        return view('website.home', compact('websiteContent', 'instagramPosts', 'teamMembers'));
    }

    public function about()
    {
        $websiteContent = WebsiteContent::first();
        $teamMembers = $this->getActiveTeamMembers();

        return view('website.about', compact('websiteContent', 'teamMembers'));
    }

    public function agriculture()
    {
        $websiteContent = WebsiteContent::first();

        return view('website.agriculture', compact('websiteContent'));
    }

    public function contacts()
    {
        $websiteContent = WebsiteContent::first();
        $locations = Location::query()
            ->select('locations.*')
            ->join('location_positions', 'locations.id', '=', 'location_positions.location_id')
            ->where('locations.is_active', true)
            ->orderBy('location_positions.position')
            ->get();

        return view('website.contacts', compact('websiteContent', 'locations'));
    }

    public function privacy()
    {
        $websiteContent = WebsiteContent::first();

        return view('website.privacy', compact('websiteContent'));
    }

    public function terms()
    {
        $websiteContent = WebsiteContent::first();

        return view('website.terms', compact('websiteContent'));
    }

    private function getActiveTeamMembers()
    {
        return TeamMember::query()
            ->select('team_members.*')
            ->join('team_member_positions', 'team_members.id', '=', 'team_member_positions.team_member_id')
            ->where('team_members.is_active', true)
            ->orderBy('team_member_positions.position')
            ->get();
    }
}
