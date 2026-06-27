<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;

class AdminUserSeeder extends Seeder
{
    public function run(): void
    {
        $adminEmail = config('biobrassica.admin.email');
        $adminPassword = config('biobrassica.admin.password');

        if (! $adminEmail || ! $adminPassword) {
            return;
        }

        User::query()->updateOrCreate(
            ['email' => $adminEmail],
            [
                'name' => config('biobrassica.admin.name', 'Biobrassica Admin'),
                'password' => $adminPassword,
                'email_verified_at' => now(),
                'is_admin' => true,
                'preferred_language' => 'pt',
            ],
        );
    }
}
