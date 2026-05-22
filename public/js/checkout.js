document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('[data-checkout-form]');
  if (!form) {
    return;
  }

  const methodRadios = form.querySelectorAll('input[name="fulfillment_method"]');
  const pickupSection = form.querySelector('[data-section="pickup"]');
  const shippingSection = form.querySelector('[data-section="shipping"]');
  const pickupSelect = pickupSection ? pickupSection.querySelector('select') : null;
  const shippingInputs = shippingSection
    ? shippingSection.querySelectorAll('input[data-conditional-required], textarea[data-conditional-required]')
    : [];

  function getMethodLabel(method) {
    return form.querySelector(`label[data-method="${method}"]`);
  }

  function updateUI(method) {
    if (pickupSection) {
      pickupSection.hidden = method !== 'pickup';
    }
    if (shippingSection) {
      shippingSection.hidden = method !== 'shipping';
    }

    if (pickupSelect) {
      pickupSelect.required = method === 'pickup';
    }
    shippingInputs.forEach((input) => {
      input.required = method === 'shipping';
    });

    const pickupLabel = getMethodLabel('pickup');
    const shippingLabel = getMethodLabel('shipping');
    if (pickupLabel) {
      pickupLabel.classList.toggle('border-forest', method === 'pickup');
      pickupLabel.classList.toggle('text-forest', method === 'pickup');
    }
    if (shippingLabel) {
      shippingLabel.classList.toggle('border-forest', method === 'shipping');
      shippingLabel.classList.toggle('text-forest', method === 'shipping');
    }
  }

  methodRadios.forEach((radio) => {
    radio.addEventListener('change', () => {
      updateUI(radio.value);
    });
  });

  const checked = form.querySelector('input[name="fulfillment_method"]:checked');
  if (checked) {
    updateUI(checked.value);
  }
});
