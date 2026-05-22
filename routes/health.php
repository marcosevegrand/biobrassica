<?php

use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Route;

Route::get('/_health', function () {
    DB::connection()->getPdo();

    return response()->json(['status' => 'ok']);
});
