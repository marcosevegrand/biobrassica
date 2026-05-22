<?php

namespace App\Http\Controllers;

use App\Models\BlogPost;
use App\Models\Recipe;
use Illuminate\Http\Request;

class ContentController extends Controller
{
    public function blogList(Request $request)
    {
        $query = BlogPost::with(['translations', 'author'])
            ->where('is_published', true)
            ->where('published_at', '<=', now());

        if ($request->filled('tag')) {
            $query->whereJsonContains('tags', $request->input('tag'));
        }

        $posts = $query->orderBy('published_at', 'desc')->paginate(9);
        $locale = app()->getLocale();
        $currentTag = $request->input('tag');

        return view('content.blog-list', compact('posts', 'locale', 'currentTag'));
    }

    public function blogDetail($slug)
    {
        $post = BlogPost::with(['translations', 'author'])
            ->where('slug', $slug)
            ->where('is_published', true)
            ->where('published_at', '<=', now())
            ->firstOrFail();

        $locale = app()->getLocale();
        $translation = $post->translations->where('language', $locale)->first()
            ?? $post->translations->first();

        return view('content.blog-detail', compact('post', 'translation', 'locale'));
    }

    public function recipeList(Request $request)
    {
        $query = Recipe::with('translations')
            ->where('is_published', true);

        if ($request->filled('tag')) {
            $query->whereJsonContains('tags', $request->input('tag'));
        }

        $recipes = $query->orderBy('id', 'desc')->paginate(9);
        $locale = app()->getLocale();
        $currentTag = $request->input('tag');

        return view('content.recipe-list', compact('recipes', 'locale', 'currentTag'));
    }

    public function recipeDetail($slug)
    {
        $recipe = Recipe::with(['translations', 'products'])
            ->where('slug', $slug)
            ->where('is_published', true)
            ->firstOrFail();

        $locale = app()->getLocale();
        $translation = $recipe->translations->where('language', $locale)->first()
            ?? $recipe->translations->first();

        return view('content.recipe-detail', compact('recipe', 'translation', 'locale'));
    }
}
