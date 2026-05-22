document.addEventListener('click', (event) => {
  if (!(event.target instanceof Element)) {
    return;
  }

  const control = event.target.closest('[data-cart-quantity-action]');
  if (!control) {
    return;
  }

  const form = control.closest('form');
  const input = form ? form.querySelector('input[name="quantity"]') : null;
  if (!input) {
    return;
  }

  const minimum = Number(input.min || 1);
  const maximum = Number(input.max || 99);
  const clamp = (value) => Math.min(Math.max(value, minimum), maximum);
  const action = control.dataset.cartQuantityAction;

  if (action === 'decrement') {
    input.value = String(clamp(Number(input.value || minimum) - 1));
  } else if (action === 'increment') {
    input.value = String(clamp(Number(input.value || minimum) + 1));
  } else if (action === 'set') {
    input.value = String(clamp(Number(control.dataset.cartQuantityValue || minimum)));
  }

  input.dispatchEvent(new Event('change', { bubbles: true }));
});