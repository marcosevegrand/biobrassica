// Scroll to the first field with .errors and focus its input on page load.
(function () {
    document.addEventListener('DOMContentLoaded', function () {
        var firstError = document.querySelector('.errors, .form-row.errors');
        if (!firstError) {
            return;
        }
        firstError.classList.add('admin-required-error-target');
        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        var input = firstError.querySelector('input, select, textarea');
        if (input && typeof input.focus === 'function') {
            try {
                input.focus({ preventScroll: true });
            } catch (e) {
                input.focus();
            }
        }
    });
})();
