<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    /**
     * Seed the application's database.
     */
    public function run(): void
    {
        $this->call(BiobrassicaContentSeeder::class);

        $adminEmail = config('biobrassica.admin.email');
        $adminPassword = config('biobrassica.admin.password');

        if (!$adminEmail || !$adminPassword) {
            return;
        }

        User::query()->updateOrCreate(
            ['email' => $adminEmail],
            [
                'name' => config('biobrassica.admin.name', 'Biobrassica Admin'),
                'password' => $adminPassword,
                'preferred_language' => 'pt',
            ],
        );
    }
}
