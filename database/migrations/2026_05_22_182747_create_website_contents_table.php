<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('website_contents', function (Blueprint $table) {
            $table->id();
            $table->string('company_legal_name');
            $table->string('company_address')->nullable();
            $table->string('company_nif')->nullable();
            $table->string('support_email');
            $table->string('whatsapp_number')->nullable();
            $table->text('hero_title')->nullable();
            $table->text('hero_subtitle')->nullable();
            $table->text('hero_cta_text')->nullable();
            $table->text('hero_cta_url')->nullable();
            $table->text('about_title')->nullable();
            $table->text('about_content')->nullable();
            $table->text('about_image')->nullable();
            $table->text('agriculture_title')->nullable();
            $table->text('agriculture_content')->nullable();
            $table->text('agriculture_image')->nullable();
            $table->text('contacts_title')->nullable();
            $table->text('contacts_content')->nullable();
            $table->text('footer_about')->nullable();
            $table->text('footer_address')->nullable();
            $table->text('footer_email')->nullable();
            $table->text('footer_phone')->nullable();
            $table->text('seo_title')->nullable();
            $table->text('seo_description')->nullable();
            $table->text('seo_keywords')->nullable();
            $table->text('facebook_url')->nullable();
            $table->text('instagram_url')->nullable();
            $table->text('youtube_url')->nullable();
            $table->text('linkedin_url')->nullable();
            $table->text('cookies_text')->nullable();
            $table->text('privacy_policy_text')->nullable();
            $table->text('terms_conditions_text')->nullable();
            $table->text('custom_css')->nullable();
            $table->text('custom_js')->nullable();
            $table->text('google_analytics_id')->nullable();
            $table->text('google_tag_manager_id')->nullable();
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('website_contents');
    }
};
