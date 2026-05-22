<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class LoginRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'email' => ['required', 'string', 'email'],
            'password' => ['required', 'string'],
        ];
    }

    public function messages(): array
    {
        return [
            'email.required' => 'O email é obrigatório.',
            'email.email' => 'O email deve ser um endereço de email válido.',
            'password.required' => 'A palavra-passe é obrigatória.',
        ];
    }
}
