<?php

use App\Http\Controllers\Auth\ForgotPasswordController;
use App\Http\Controllers\Auth\ResetPasswordController;
use Illuminate\Support\Facades\Route;

// Password reset routes for the web guard
Route::get('password/reset', [ForgotPasswordController::class, 'showLinkRequestForm'])
    ->name('password.request');
Route::post('password/email', [ForgotPasswordController::class, 'sendResetLinkEmail'])
    ->middleware('throttle:5,1')
    ->name('password.email');
Route::get('password/reset/enviado', [ForgotPasswordController::class, 'showLinkSentPage'])
    ->name('password.sent');
Route::get('password/reset/concluido', [ResetPasswordController::class, 'showCompletePage'])
    ->name('password.complete');
Route::get('password/reset/{token}', [ResetPasswordController::class, 'showResetForm'])
    ->name('password.reset');
Route::post('password/reset', [ResetPasswordController::class, 'reset'])
    ->middleware('throttle:5,1')
    ->name('password.update');
