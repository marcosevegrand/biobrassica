(() => {
  // Optional header setup (not required for dropdowns to work)
  const header = document.getElementById('site-header');

  if (header) {
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
      syncHamburger();
    }

    menuBtn?.addEventListener('click', () => {
      setMenuOpen(!isMenuOpen);
    });

    function applyHeaderTheme(isScrolled) {
      if (isScrolled) {
        header.classList.remove('bg-forest', 'text-paper');
        header.classList.add('bg-paper', 'text-forest', 'shadow-sm');
        if (logoWhite) {
          logoWhite.style.display = 'none';
        }
        if (logoGreen) {
          logoGreen.style.display = 'block';
        }
        if (lojaCta) {
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
      if (lojaCta) {
        lojaCta.classList.remove('bg-forest', 'text-paper', 'hover:bg-forest/90');
        lojaCta.classList.add('bg-paper', 'text-forest', 'hover:bg-paper/90');
      }
    }

    function syncHeaderTheme() {
      applyHeaderTheme(window.scrollY > 50);
    }

    window.addEventListener('scroll', syncHeaderTheme);
    syncHeaderTheme();
  }

  // Dropdown menu handling - works independently
  const cartTrigger = document.getElementById('cart-trigger');
  const userMenuTrigger = document.getElementById('user-menu-trigger');

  function setPopupOpen(id, open) {
    const element = document.getElementById(id);
    if (!element) {
      return;
    }
    
    // Ensure proper visibility using display styles
    if (open) {
      element.classList.remove('hidden');
      element.classList.add('block');
      element.style.display = 'block';
    } else {
      element.classList.add('hidden');
      element.classList.remove('block');
      element.style.display = 'none';
    }
  }

  function closeCartPopup() {
    setPopupOpen('cart-popup', false);
  }

  function openCartPopup() {
    setPopupOpen('cart-popup', true);
  }

  function closeUserMenu() {
    setPopupOpen('user-menu', false);
  }

  function openUserMenu() {
    setPopupOpen('user-menu', true);
  }

  if (cartTrigger) {
    cartTrigger.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      closeUserMenu();
      const cartPopup = document.getElementById('cart-popup');
      if (!cartPopup) {
        return;
      }
      if (cartPopup.classList.contains('hidden')) {
        openCartPopup();
        return;
      }
      closeCartPopup();
    });
  }

  if (userMenuTrigger) {
    userMenuTrigger.addEventListener('click', (event) => {
      event.preventDefault();
      event.stopPropagation();
      closeCartPopup();
      const userMenu = document.getElementById('user-menu');
      if (!userMenu) {
        return;
      }
      if (userMenu.classList.contains('hidden')) {
        openUserMenu();
        return;
      }
      closeUserMenu();
    });
  }

  // Close dropdowns when clicking outside
  document.addEventListener('click', (event) => {
    const cartPopup = document.getElementById('cart-popup');
    if (cartPopup && !cartPopup.classList.contains('hidden')) {
      const clickedInsidePopup = cartPopup.contains(event.target);
      const clickedTrigger = cartTrigger?.contains(event.target);
      if (!clickedInsidePopup && !clickedTrigger) {
        closeCartPopup();
      }
    }

    const userMenu = document.getElementById('user-menu');
    if (userMenu && !userMenu.classList.contains('hidden')) {
      const clickedInsideMenu = userMenu.contains(event.target);
      const clickedTrigger = userMenuTrigger?.contains(event.target);
      if (!clickedInsideMenu && !clickedTrigger) {
        closeUserMenu();
      }
    }

    if (event.target && event.target.id === 'cart-popup-close') {
      closeCartPopup();
    }
  });

  // Handle HTMX swaps
  document.body.addEventListener('htmx:afterSwap', (event) => {
    if (event.target && event.target.id === 'cart-popup' && !event.target.classList.contains('hidden')) {
      openCartPopup();
    }
  });
})();