<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class TeamMember extends Model
{
    protected $fillable = [
        'name',
        'role',
        'photo',
        'is_active',
    ];

    protected function casts(): array
    {
        return [
            'is_active' => 'boolean',
        ];
    }

    protected static function booted(): void
    {
        static::created(function (TeamMember $teamMember): void {
            TeamMemberPosition::firstOrCreate(
                ['team_member_id' => $teamMember->id],
                ['position' => ((int) TeamMemberPosition::max('position')) + 1],
            );
        });
    }

    public function position()
    {
        return $this->hasOne(TeamMemberPosition::class);
    }
}
