<?php

use App\Http\Controllers\Auth\AuthController;
use App\Http\Controllers\CartController;
use App\Http\Controllers\CatalogController;
use App\Http\Controllers\CheckoutController;
use App\Http\Controllers\OrderController;
use App\Http\Controllers\PaymentController;
use Illuminate\Support\Facades\Route;

Route::get('/', [CatalogController::class, 'shopHome'])->name('shop.home');
Route::get('/produtos', [CatalogController::class, 'productList'])->name('catalog.products');
Route::get('/produto/{slug}', [CatalogController::class, 'productDetail'])->name('catalog.product');
Route::get('/categoria/{slug}', [CatalogController::class, 'categoryDetail'])->name('catalog.category');

Route::get('/carrinho', [CartController::class, 'detail'])->name('cart.detail');
Route::get('/carrinho/contagem', [CartController::class, 'count'])->name('cart.count');
Route::get('/carrinho/popup', [CartController::class, 'popup'])->name('cart.popup');
Route::post('/carrinho/adicionar/{product}', [CartController::class, 'add'])->name('cart.add');
Route::post('/carrinho/atualizar/{item}', [CartController::class, 'update'])->name('cart.update');
Route::post('/carrinho/remover/{item}', [CartController::class, 'remove'])->name('cart.remove');

Route::get('/conta/registar', [AuthController::class, 'showRegister'])->name('shop.register');
Route::post('/conta/registar', [AuthController::class, 'register']);
Route::get('/conta/entrar', [AuthController::class, 'showLogin'])->name('login');
Route::post('/conta/entrar', [AuthController::class, 'login']);
Route::post('/conta/sair', [AuthController::class, 'logout'])->name('shop.logout');

Route::middleware('auth')->group(function () {
    Route::get('/conta/perfil', [AuthController::class, 'profile'])->name('shop.profile');
    Route::post('/conta/perfil', [AuthController::class, 'updateProfile'])->name('shop.profile.update');
    Route::get('/conta/encomendas', [AuthController::class, 'orderHistory'])->name('shop.orders');

    Route::get('/checkout', [CheckoutController::class, 'show'])->name('checkout');
    Route::post('/checkout', [CheckoutController::class, 'store'])->name('checkout.store');
    Route::get('/checkout/confirmar/{order}', [CheckoutController::class, 'confirm'])->name('checkout.confirm');
    Route::get('/checkout/cancelar/{order}', [CheckoutController::class, 'discard'])->name('checkout.discard');

    Route::get('/encomenda/{order}', [OrderController::class, 'show'])->name('order.show');
    Route::get('/pagamento/{order}', [PaymentController::class, 'show'])->name('payment.show');
    Route::get('/pagamento/{order}/estado', [OrderController::class, 'paymentStatus'])->name('payment.status');
});

Route::get('/api/payments/callback', [PaymentController::class, 'callback'])->name('payment.callback');
