<?php

use Illuminate\Support\Facades\Route;

Route::redirect('/', '/'.trim((string) config('biobrassica.paths.admin', 'admin'), '/'));
