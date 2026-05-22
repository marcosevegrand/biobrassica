<?php

use Illuminate\Support\Facades\Route;

// Password reset routes for the web guard
Route::get('password/reset', [\App\Http\Controllers\Auth\ForgotPasswordController::class, 'showLinkRequestForm'])
    ->name('password.request');
Route::post('password/email', [\App\Http\Controllers\Auth\ForgotPasswordController::class, 'sendResetLinkEmail'])
    ->name('password.email');
Route::get('password/reset/{token}', [\App\Http\Controllers\Auth\ResetPasswordController::class, 'showResetForm'])
    ->name('password.reset');
Route::post('password/reset', [\App\Http\Controllers\Auth\ResetPasswordController::class, 'reset'])
    ->name('password.update');
