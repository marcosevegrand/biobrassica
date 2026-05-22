(function () {
  const slugInput = document.getElementById('id_slug');
  const quantityInput = document.getElementById('id_quantity');

  if (!slugInput || !quantityInput) {
    return;
  }

  let slugLocked = slugInput.value.trim() !== '';

  const normalize = (value) =>
    value
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');

  const findPortugueseNameInput = () => {
    const languageInputs = document.querySelectorAll('[id$="-language"]');
    for (const languageInput of languageInputs) {
      if (languageInput.value !== 'pt') {
        continue;
      }

      const nameInputId = languageInput.id.replace(/-language$/, '-name');
      const nameInput = document.getElementById(nameInputId);
      if (nameInput) {
        return nameInput;
      }
    }

    return null;
  };

  const updateSlug = () => {
    if (slugLocked) {
      return;
    }

    const ptNameInput = findPortugueseNameInput();
    const name = ptNameInput ? ptNameInput.value.trim() : '';
    const quantity = quantityInput.value.trim();
    const generated = normalize([name, quantity].filter(Boolean).join(' '));

    slugInput.value = generated;
  };

  const bindPortugueseNameListener = () => {
    const ptNameInput = findPortugueseNameInput();
    if (ptNameInput && !ptNameInput.dataset.slugAutofillBound) {
      ptNameInput.addEventListener('input', updateSlug);
      ptNameInput.dataset.slugAutofillBound = 'true';
    }
  };

  slugInput.addEventListener('input', function () {
    slugLocked = slugInput.value.trim() !== '';
  });

  quantityInput.addEventListener('input', updateSlug);
  bindPortugueseNameListener();
  updateSlug();

  const observer = new MutationObserver(function () {
    bindPortugueseNameListener();
    updateSlug();
  });

  observer.observe(document.body, { childList: true, subtree: true });
})();
