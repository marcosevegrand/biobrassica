<?php

namespace App\Console;

use App\Console\Commands\ExpirePayments;
use App\Console\Commands\FetchInstagramPosts;
use App\Console\Commands\RegisterIfthenpayWebhooks;
use App\Console\Commands\ReleaseExpiredReservations;
use Illuminate\Foundation\Bootstrap\BootProviders;
use Illuminate\Foundation\Bootstrap\HandleExceptions;
use Illuminate\Foundation\Bootstrap\LoadConfiguration;
use Illuminate\Foundation\Bootstrap\RegisterFacades;
use Illuminate\Foundation\Bootstrap\RegisterProviders;
use Illuminate\Foundation\Bootstrap\SetRequestForConsole;
use Illuminate\Foundation\Console\Kernel as FoundationKernel;

class Kernel extends FoundationKernel
{
    protected $commands = [
        ExpirePayments::class,
        FetchInstagramPosts::class,
        RegisterIfthenpayWebhooks::class,
        ReleaseExpiredReservations::class,
    ];

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
        SetRequestForConsole::class,
        RegisterProviders::class,
        BootProviders::class,
    ];
}
