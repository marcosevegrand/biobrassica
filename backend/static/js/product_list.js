document.addEventListener('DOMContentLoaded', () => {
  const grid = document.getElementById('product-grid');
  if (!grid) {
    return;
  }

  grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
});