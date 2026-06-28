<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::dropIfExists('team_member_positions');
        Schema::dropIfExists('team_members');
    }

    public function down(): void
    {
        // The Team Members feature has been removed intentionally.
    }
};
