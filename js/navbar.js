(() => {
  const header = document.getElementById('site-header');

  if (!header) {
    return;
  }

  const menuBtn = document.getElementById('mobile-menu-btn');
  const mobileMenu = document.getElementById('mobile-menu');
  const hTop = document.getElementById('hamburger-top');
  const hMid = document.getElementById('hamburger-mid');
  const hBot = document.getElementById('hamburger-bot');
  const logoWhite = document.getElementById('logo-white');
  const logoGreen = document.getElementById('logo-green');
  const lojaCta = document.getElementById('loja-cta');

  let isMenuOpen = false;

  function syncHamburger() {
    if (hTop) {
      hTop.style.transform = isMenuOpen ? 'rotate(45deg) translate(3px, 3px)' : '';
    }
    if (hMid) {
      hMid.style.opacity = isMenuOpen ? '0' : '';
    }
    if (hBot) {
      hBot.style.transform = isMenuOpen ? 'rotate(-45deg) translate(3px, -3px)' : '';
    }
  }

  function setMenuOpen(open) {
    isMenuOpen = open;
    mobileMenu?.classList.toggle('hidden', !open);
    menuBtn?.setAttribute('aria-expanded', String(open));
    menuBtn?.setAttribute('aria-label', open ? 'Fechar menu' : 'Abrir menu');
    syncHamburger();
  }

  menuBtn?.setAttribute('aria-controls', 'mobile-menu');
  setMenuOpen(false);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && isMenuOpen) {
      setMenuOpen(false);
      menuBtn?.focus();
    }
  });
  document.addEventListener('click', (event) => {
    if (isMenuOpen && !header.contains(event.target)) setMenuOpen(false);
  });
  mobileMenu?.addEventListener('click', (event) => {
    if (event.target.closest('a')) setMenuOpen(false);
  });
  const desktop = window.matchMedia('(min-width: 1024px)');
  desktop.addEventListener('change', () => setMenuOpen(false));

  const page = location.pathname.split('/').pop() || 'index.html';
  header.querySelectorAll('a[href]').forEach((link) => {
    if (link.getAttribute('href') === page) link.setAttribute('aria-current', 'page');
  });

  menuBtn?.addEventListener('click', () => {
    setMenuOpen(!isMenuOpen);
  });

  function applyHeaderTheme(isScrolled) {
    // The "Loja" CTA only gets scroll theming when it is a real link (not the
    // muted "Em breve" placeholder).
    const isLiveLink = lojaCta && lojaCta.tagName === 'A';

    if (isScrolled) {
      header.classList.remove('bg-forest', 'text-paper');
      header.classList.add('bg-paper', 'text-forest', 'shadow-sm');
      if (logoWhite) {
        logoWhite.style.display = 'none';
      }
      if (logoGreen) {
        logoGreen.style.display = 'block';
      }
      if (isLiveLink) {
        lojaCta.classList.remove('bg-paper', 'text-forest', 'hover:bg-paper/90');
        lojaCta.classList.add('bg-forest', 'text-paper', 'hover:bg-forest/90');
      }
      return;
    }

    header.classList.add('bg-forest', 'text-paper');
    header.classList.remove('bg-paper', 'text-forest', 'shadow-sm');
    if (logoWhite) {
      logoWhite.style.display = 'block';
    }
    if (logoGreen) {
      logoGreen.style.display = 'none';
    }
    if (isLiveLink) {
      lojaCta.classList.remove('bg-forest', 'text-paper', 'hover:bg-forest/90');
      lojaCta.classList.add('bg-paper', 'text-forest', 'hover:bg-paper/90');
    }
  }

  function syncHeaderTheme() {
    applyHeaderTheme(window.scrollY > 50);
  }

  window.addEventListener('scroll', syncHeaderTheme, { passive: true });
  syncHeaderTheme();
})();
