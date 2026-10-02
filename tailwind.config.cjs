/** Run: npx --yes tailwindcss@3.4.17 -i css/tailwind.css -o css/utilities.css --minify */
module.exports = {
  content: ['./*.html', './js/*.js'],
  theme: {
    extend: {
      colors: { paper: '#FBF9F6', forest: '#2C3F2D', terracotta: '#B07850', stone: '#D1D1CC', muted: '#6B6B6B' },
      fontFamily: { serif: ['Lora', 'serif'], sans: ['Inter', 'sans-serif'] },
      maxWidth: { '384': '96rem', '6xl': '72rem' },
    },
  },
};
