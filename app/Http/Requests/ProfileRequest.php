<?php

namespace App\Http\Requests;

use App\Rules\Nif;
use App\Rules\PortuguesePhone;
use Illuminate\Foundation\Http\FormRequest;

class ProfileRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'name' => ['required', 'string', 'max:255'],
            'phone' => ['nullable', 'string', new PortuguesePhone],
            'nif' => ['nullable', 'string', new Nif],
            'preferred_language' => ['required', 'string', 'in:pt,en'],
        ];
    }

    public function messages(): array
    {
        return [
            'name.required' => 'O nome é obrigatório.',
            'preferred_language.required' => 'O idioma preferido é obrigatório.',
            'preferred_language.in' => 'O idioma selecionado não é válido.',
        ];
    }
}
