/* Biobrassica admin – dynamic list widgets (tags, ingredients & steps)
 * Handles add/remove rows and keeps a hidden JSON field in sync.
 */
(function () {
  'use strict';

  // ── helpers ──────────────────────────────────────────────────────────────

  function getContainer(el) {
    return el.closest('.bb-widget-container');
  }

  function syncTags(container) {
    var inputs = container.querySelectorAll('.bb-tag-input');
    var values = [];
    inputs.forEach(function (inp) {
      var v = inp.value.trim();
      if (v) values.push(v);
    });
    container.querySelector('.bb-json-value').value = JSON.stringify(values);
  }

  function syncIngredients(container) {
    var inputs = container.querySelectorAll('.bb-ingredient-input');
    var values = [];
    inputs.forEach(function (inp) {
      var v = inp.value.trim();
      if (v) values.push(v);
    });
    container.querySelector('.bb-json-value').value = JSON.stringify(values);
  }

  function syncSteps(container) {
    var textareas = container.querySelectorAll('.bb-step-input');
    var values = [];
    textareas.forEach(function (ta) {
      var v = ta.value.trim();
      if (v) values.push(v);
    });
    container.querySelector('.bb-json-value').value = JSON.stringify(values);
    renumberSteps(container);
  }

  function renumberSteps(container) {
    var rows = container.querySelectorAll('.bb-step-row');
    rows.forEach(function (row, i) {
      var num = row.querySelector('.bb-step-num');
      if (num) num.textContent = (i + 1) + '.';
    });
  }

  function syncContainer(container) {
    if (container.dataset.type === 'tags')        syncTags(container);
    if (container.dataset.type === 'ingredients') syncIngredients(container);
    if (container.dataset.type === 'steps')       syncSteps(container);
  }

  // ── remove ───────────────────────────────────────────────────────────────

  window.bbRemoveItem = function (btn) {
    var row = btn.closest('.bb-tag-row, .bb-ingredient-row, .bb-step-row');
    var container = getContainer(btn);
    row.remove();
    syncContainer(container);
  };

  // ── add tag ──────────────────────────────────────────────────────────────

  window.bbAddTag = function (containerId) {
    var container = document.getElementById(containerId);
    var tagsDiv = container.querySelector('.bb-tags-container');

    var row = document.createElement('div');
    row.className = 'bb-tag-row';
    row.style.cssText = 'display:flex;align-items:center;gap:6px;margin-bottom:6px;';
    row.innerHTML =
      '<input type="text" class="bb-tag-input" placeholder="nova tag"'
      + ' style="flex:1;padding:6px 10px;border:1px solid #d1d5db;border-radius:4px;font-size:14px;background:#fff;" />'
      + '<button type="button" onclick="bbRemoveItem(this)"'
      + ' style="padding:4px 10px;background:#fee2e2;color:#dc2626;border:none;border-radius:4px;cursor:pointer;font-size:15px;line-height:1;">×</button>';

    tagsDiv.appendChild(row);

    var newInput = row.querySelector('.bb-tag-input');
    newInput.addEventListener('input', function () { syncTags(container); });
    newInput.focus();
  };

  // ── add ingredient ───────────────────────────────────────────────────────

  window.bbAddIngredient = function (containerId) {
    var container = document.getElementById(containerId);
    var div = container.querySelector('.bb-ingredients-container');

    var row = document.createElement('div');
    row.className = 'bb-ingredient-row';
    row.style.cssText = 'display:flex;align-items:center;gap:6px;margin-bottom:6px;';
    row.innerHTML =
      '<input type="text" class="bb-ingredient-input" placeholder="ex: 200g farinha espelta"'
      + ' style="flex:1;padding:5px 8px;border:1px solid #d1d5db;border-radius:4px;font-size:14px;background:#fff;" />'
      + '<button type="button" onclick="bbRemoveItem(this)"'
      + ' style="padding:3px 10px;background:#fee2e2;color:#dc2626;border:none;border-radius:4px;cursor:pointer;font-size:15px;line-height:1;">×</button>';

    div.appendChild(row);

    var newInput = row.querySelector('.bb-ingredient-input');
    newInput.addEventListener('input', function () { syncIngredients(container); });
    newInput.focus();
  };

  // ── add step ─────────────────────────────────────────────────────────────

  window.bbAddStep = function (containerId) {
    var container = document.getElementById(containerId);
    var stepsDiv = container.querySelector('.bb-steps-container');
    var existingRows = stepsDiv.querySelectorAll('.bb-step-row');
    var nextNum = existingRows.length + 1;

    var row = document.createElement('div');
    row.className = 'bb-step-row';
    row.style.cssText = 'display:flex;align-items:flex-start;gap:8px;margin-bottom:10px;';
    row.innerHTML =
      '<span class="bb-step-num" style="min-width:24px;padding-top:7px;font-weight:700;font-size:13px;color:#6b7280;text-align:right;">'
      + nextNum + '.</span>'
      + '<textarea class="bb-step-input" rows="2" placeholder="Descreva este passo…"'
      + ' style="flex:1;padding:5px 8px;border:1px solid #d1d5db;border-radius:4px;font-size:14px;background:#fff;resize:vertical;"></textarea>'
      + '<button type="button" onclick="bbRemoveItem(this)"'
      + ' style="padding:3px 10px;background:#fee2e2;color:#dc2626;border:none;border-radius:4px;cursor:pointer;font-size:15px;line-height:1;margin-top:4px;">×</button>';

    stepsDiv.appendChild(row);

    var newTA = row.querySelector('.bb-step-input');
    newTA.addEventListener('input', function () { syncSteps(container); });
    newTA.focus();
  };

  // ── wire existing rows on load ───────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.bb-widget-container[data-type="tags"]').forEach(function (container) {
      container.querySelectorAll('.bb-tag-input').forEach(function (inp) {
        inp.addEventListener('input', function () { syncTags(container); });
      });
    });

    document.querySelectorAll('.bb-widget-container[data-type="ingredients"]').forEach(function (container) {
      container.querySelectorAll('.bb-ingredient-input').forEach(function (inp) {
        inp.addEventListener('input', function () { syncIngredients(container); });
      });
    });

    document.querySelectorAll('.bb-widget-container[data-type="steps"]').forEach(function (container) {
      container.querySelectorAll('.bb-step-input').forEach(function (ta) {
        ta.addEventListener('input', function () { syncSteps(container); });
      });
    });
  });

})();
