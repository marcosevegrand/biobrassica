document.addEventListener('DOMContentLoaded', () => {
  const inlineGroups = Array.from(document.querySelectorAll('.js-inline-admin-formset'));

  const getPrefix = (group) => {
    const groupId = group.id || '';
    return groupId.endsWith('-group') ? groupId.slice(0, -6) : '';
  };

  const getTotalFormsInput = (prefix) => document.getElementById(`id_${prefix}-TOTAL_FORMS`);

  const getFormset = (group) => group.querySelector('.formset');

  const getDefaultAddLink = (group) =>
    group.querySelector('.formset .add-row');

  const getMaxFormsInput = (group) =>
    group.querySelector("input[type=hidden][name$='MAX_NUM_FORMS']");

  const getTemplateRow = (group) =>
    group.querySelector('.formset > .form-group.empty-form, .formset tbody.form-group.empty-form');

  const getVisibleRows = (group) =>
    group.querySelectorAll('.formset > .form-group:not(.empty-form), .formset tbody.form-group:not(.empty-form)');

  const syncInternalAddRow = (group, hasForms, totalFormsValue) => {
    const defaultAddRow = group.querySelector('.formset .add-row');
    const maxNumFormsInput = getMaxFormsInput(group);
    if (!defaultAddRow) {
      return;
    }

    const maxFormsValue = Number(maxNumFormsInput?.value || 0);
    const hasCapacity = !maxFormsValue || totalFormsValue < maxFormsValue;
    defaultAddRow.classList.toggle('hidden', !hasForms || !hasCapacity);
  };

  const dispatchInlineAddedEvent = (row, prefix, index) => {
    row.dispatchEvent(
      new CustomEvent('formsetGroup:added', {
        bubbles: true,
        detail: {
          formsetName: prefix,
          row,
          index,
        },
      })
    );
  };

  const addInlineRow = (group) => {
    const prefix = getPrefix(group);
    const totalFormsInput = getTotalFormsInput(prefix);
    const maxNumFormsInput = getMaxFormsInput(group);
    const templateRow = getTemplateRow(group);

    if (!totalFormsInput || !templateRow) {
      return false;
    }

    const totalFormsValue = Number(totalFormsInput.value || 0);
    const maxFormsValue = Number(maxNumFormsInput?.value || 0);

    if (maxFormsValue && totalFormsValue >= maxFormsValue) {
      return false;
    }

    const row = templateRow.cloneNode(true);
    row.classList.remove('empty-form', 'hidden', 'template', 'last-related');
    row.querySelectorAll('.empty-form, .hidden, .template').forEach((element) => {
      element.classList.remove('empty-form', 'hidden', 'template');
    });

    row.innerHTML = row.innerHTML
      .replaceAll(`${prefix}-__prefix__`, `${prefix}-${totalFormsValue}`)
      .replaceAll(/__prefix__/g, String(totalFormsValue));

    if (row.id) {
      row.id = row.id.replace(`${prefix}-__prefix__`, `${prefix}-${totalFormsValue}`);
    }

    templateRow.parentNode.insertBefore(row, templateRow);
    totalFormsInput.value = String(totalFormsValue + 1);

    dispatchInlineAddedEvent(row, prefix, totalFormsValue);
    return true;
  };

  const updateEmptyState = (group) => {
    const prefix = getPrefix(group);
    const totalFormsInput = getTotalFormsInput(prefix);
    const emptyState = group.querySelector(`[data-inline-empty-state="${prefix}"]`);
    if (!totalFormsInput || !emptyState) {
      return;
    }

    const hasForms = Number(totalFormsInput.value || 0) > 0;
    emptyState.classList.toggle('hidden', hasForms);
    syncInternalAddRow(group, hasForms, Number(totalFormsInput.value || 0));
  };

  const bindCustomButtons = (group) => {
    const prefix = getPrefix(group);
    const buttons = group.querySelectorAll(`[data-inline-add="${prefix}"]`);
    buttons.forEach((button) => {
      if (button.dataset.inlineBound === 'true') {
        return;
      }

      button.dataset.inlineBound = 'true';
      button.addEventListener('click', () => {
        const added = addInlineRow(group);
        if (!added) {
          const defaultAddLink = getDefaultAddLink(group);
          if (defaultAddLink) {
            defaultAddLink.click();
          }
        }
        requestAnimationFrame(() => updateEmptyState(group));
      });
    });
  };

  inlineGroups.forEach((group) => {
    bindCustomButtons(group);
    updateEmptyState(group);

    const observer = new MutationObserver(() => {
      bindCustomButtons(group);
      updateEmptyState(group);
    });

    observer.observe(group, { childList: true, subtree: true });
  });
});