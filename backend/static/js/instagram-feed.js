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

  const script = document.createElement('script');
  script.src = 'https://elfsightcdn.com/platform.js';
  script.async = true;
  script.onerror = showFallback;
  script.onload = () => {
    window.setTimeout(() => {
      if (!feed.children.length) {
        showFallback();
      }
    }, 3000);
  };

  document.head.appendChild(script);
});