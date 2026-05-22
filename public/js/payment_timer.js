document.addEventListener('DOMContentLoaded', () => {
  const timerEl = document.getElementById('payment-timer');
  if (!timerEl) {
    return;
  }

  const expiresIso = timerEl.dataset.expiresIso;
  if (!expiresIso) {
    return;
  }

  const expiresAt = new Date(expiresIso);

  function updateTimer() {
    const diff = Math.max(0, Math.floor((expiresAt - Date.now()) / 1000));
    const mins = Math.floor(diff / 60);
    const secs = String(diff % 60).padStart(2, '0');
    timerEl.textContent = `${mins}:${secs}`;
    if (diff <= 0) {
      window.location.reload();
    }
  }

  updateTimer();
  setInterval(updateTimer, 1000);
});
