document.addEventListener('DOMContentLoaded', () => {
  const feed = document.querySelector('[data-instagram-feed]');
  const fallback = document.querySelector('[data-instagram-fallback]');

  if (!feed) {
    return;
  }

  const showFallback = () => {
    if (fallback) {
      fallback.classList.remove('hidden');
    }
  };

  setTimeout(() => {
    if (feed.querySelector('.feed-powered-by-es')) {
      showFallback();
    }
  }, 4000);
});
