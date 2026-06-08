<?php

use App\Http\Controllers\ContentController;
use App\Http\Controllers\WebsiteController;
use Illuminate\Support\Facades\Route;

Route::get('/', [WebsiteController::class, 'home'])->name('website.home');
Route::get('/quem-somos', [WebsiteController::class, 'about'])->name('website.about');
Route::get('/agricultura-bio', [WebsiteController::class, 'agriculture'])->name('website.agriculture');
Route::get('/contactos', [WebsiteController::class, 'contacts'])->name('website.contacts');
Route::get('/privacidade', [WebsiteController::class, 'privacy'])->name('website.privacy');
Route::get('/termos', [WebsiteController::class, 'terms'])->name('website.terms');

Route::get('/blog', [ContentController::class, 'blogList'])->name('content.blog');
Route::get('/blog/{slug}', [ContentController::class, 'blogDetail'])->name('content.blog-detail');
Route::get('/receitas', [ContentController::class, 'recipeList'])->name('content.recipes');
Route::get('/receitas/{slug}', [ContentController::class, 'recipeDetail'])->name('content.recipe-detail');
