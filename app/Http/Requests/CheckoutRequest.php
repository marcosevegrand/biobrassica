<?php

namespace App\Http\Requests;

use App\Rules\Nif;
use App\Rules\PortuguesePhone;
use Illuminate\Foundation\Http\FormRequest;

class CheckoutRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'name' => ['required', 'string', 'max:255'],
            'email' => ['required', 'email', 'max:255'],
            'phone' => ['required', 'string', new PortuguesePhone],
            'nif' => ['nullable', 'string', new Nif],
            'payment_method' => ['required', 'string', 'in:mbway,bank_transfer'],
            'fulfillment_method' => ['required', 'string', 'in:pickup,shipping'],
            'pickup_location' => ['required_if:fulfillment_method,pickup', 'exists:locations,id'],
            'shipping_address_line1' => ['required_if:fulfillment_method,shipping', 'string', 'max:255'],
            'shipping_address_line2' => ['nullable', 'string', 'max:255'],
            'shipping_city' => ['required_if:fulfillment_method,shipping', 'string', 'max:255'],
            'shipping_postal_code' => ['required_if:fulfillment_method,shipping', 'string', 'max:20'],
            'notes' => ['nullable', 'string', 'max:1000'],
        ];
    }

    public function messages(): array
    {
        return [
            'name.required' => 'O nome é obrigatório.',
            'email.required' => 'O email é obrigatório.',
            'email.email' => 'O email introduzido não é válido.',
            'phone.required' => 'O número de telefone é obrigatório.',
            'payment_method.required' => 'Selecione um método de pagamento.',
            'payment_method.in' => 'O método de pagamento selecionado não é válido.',
            'fulfillment_method.required' => 'Selecione o método de entrega.',
            'fulfillment_method.in' => 'O método de entrega selecionado não é válido.',
            'pickup_location.required_if' => 'Selecione o local de levantamento.',
            'pickup_location.exists' => 'O local de levantamento selecionado não é válido.',
            'shipping_address_line1.required_if' => 'A morada de envio é obrigatória.',
            'shipping_city.required_if' => 'A localidade é obrigatória.',
            'shipping_postal_code.required_if' => 'O código postal é obrigatório.',
        ];
    }
}
