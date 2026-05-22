<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class TeamMemberPosition extends Model
{
    protected $fillable = [
        'team_member_id',
        'position',
    ];

    public function teamMember()
    {
        return $this->belongsTo(TeamMember::class);
    }
}
