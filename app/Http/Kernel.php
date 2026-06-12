<?php

namespace App\Http;

use Illuminate\Foundation\Bootstrap\BootProviders;
use Illuminate\Foundation\Bootstrap\HandleExceptions;
use Illuminate\Foundation\Bootstrap\LoadConfiguration;
use Illuminate\Foundation\Bootstrap\RegisterFacades;
use Illuminate\Foundation\Bootstrap\RegisterProviders;
use Illuminate\Foundation\Http\Kernel as FoundationKernel;

class Kernel extends FoundationKernel
{
    /**
     * The application bootstrappers, excluding LoadEnvironmentVariables.
     * bootstrap/env.php already loads .env in a cPanel-safe way.
     *
     * @var string[]
     */
    protected $bootstrappers = [
        LoadConfiguration::class,
        HandleExceptions::class,
        RegisterFacades::class,
        RegisterProviders::class,
        BootProviders::class,
    ];
}
