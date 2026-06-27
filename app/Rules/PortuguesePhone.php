<?php

namespace App\Rules;

use Closure;
use Illuminate\Contracts\Validation\ValidationRule;

class PortuguesePhone implements ValidationRule
{
    public function validate(string $attribute, mixed $value, Closure $fail): void
    {
        if ($value === null || $value === '') {
            return;
        }

        $value = (string) $value;

        if (! preg_match('/^9\d{8}$/', $value)) {
            $fail('O número de telefone deve começar com 9 e conter 9 dígitos.');
        }
    }
}
