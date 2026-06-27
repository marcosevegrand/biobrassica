<?php

use Illuminate\Foundation\Inspiring;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\Schedule;

Artisan::command('inspire', function () {
    $this->comment(Inspiring::quote());
})->purpose('Display an inspiring quote');

Schedule::command('payments:expire')->everyFiveMinutes()->withoutOverlapping();
Schedule::command('cart:release-expired-reservations')->everyFiveMinutes()->withoutOverlapping();
Schedule::command('instagram:fetch')->dailyAt('03:15');
