<?php

use App\Http\Controllers\CatalogController;
use Illuminate\Support\Facades\Route;

// Catalog — public product showcase
Route::get('/', [CatalogController::class, 'shopHome'])->name('shop.home');
Route::get('/produtos', [CatalogController::class, 'productList'])->name('catalog.products');
Route::get('/produto/{slug}', [CatalogController::class, 'productDetail'])->name('catalog.product');
Route::get('/categoria/{slug}', [CatalogController::class, 'categoryDetail'])->name('catalog.category');
