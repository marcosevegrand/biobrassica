<?php

namespace App\Rules;

use Closure;
use Illuminate\Contracts\Validation\ValidationRule;

class PortuguesePostalCode implements ValidationRule
{
    public function validate(string $attribute, mixed $value, Closure $fail): void
    {
        if ($value === null || $value === '') {
            return;
        }

        if (!preg_match('/^\d{4}-\d{3}$/', (string) $value)) {
            $fail('O código postal deve ter o formato 0000-000.');
        }
    }
}
