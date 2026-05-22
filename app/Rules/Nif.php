<?php

namespace App\Rules;

use Closure;
use Illuminate\Contracts\Validation\ValidationRule;

class Nif implements ValidationRule
{
    public function validate(string $attribute, mixed $value, Closure $fail): void
    {
        if ($value === null || $value === '') {
            return;
        }

        $value = (string) $value;

        if (!preg_match('/^\d{9}$/', $value)) {
            $fail('O NIF deve conter exatamente 9 dígitos.');
            return;
        }

        $sum = 0;
        for ($i = 0; $i < 8; $i++) {
            $sum += (int) $value[$i] * (9 - $i);
        }

        $checksum = 11 - ($sum % 11);

        if ($checksum >= 10) {
            $checksum = 0;
        }

        if ((int) $value[8] !== $checksum) {
            $fail('O NIF introduzido não é válido.');
        }
    }
}
