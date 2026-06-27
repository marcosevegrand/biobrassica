<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class WebsiteContent extends Model
{
    protected $fillable = [
        'company_legal_name',
        'company_address',
        'company_nif',
        'support_email',
        'whatsapp_number',
        'hero_title',
        'hero_subtitle',
        'hero_cta_text',
        'hero_cta_url',
        'about_title',
        'about_content',
        'about_image',
        'agriculture_title',
        'agriculture_content',
        'agriculture_image',
        'contacts_title',
        'contacts_content',
        'footer_about',
        'footer_address',
        'footer_email',
        'footer_phone',
        'seo_title',
        'seo_description',
        'seo_keywords',
        'facebook_url',
        'instagram_url',
        'youtube_url',
        'linkedin_url',
        'cookies_text',
        'privacy_policy_text',
        'terms_conditions_text',
        'google_analytics_id',
        'google_tag_manager_id',
    ];
}
