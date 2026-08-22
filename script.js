
(() => {
  const root = document.documentElement;
  const storedTheme = (() => {
    try { return localStorage.getItem('theme'); } catch (error) { return null; }
  })();
  if (!root.dataset.theme) {
    root.dataset.theme = storedTheme || (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  }

  document.addEventListener('DOMContentLoaded', () => {
    const setLanguage = (language) => {
      root.dataset.language = language;
      root.lang = language;
      document.querySelectorAll('[data-language-control]').forEach((button) => {
        button.setAttribute('aria-pressed', String(button.dataset.languageControl === language));
      });
      try { localStorage.setItem('language', language); } catch (error) {}
      const toggle = document.querySelector('[data-theme-toggle]');
      if (toggle) {
        toggle.setAttribute('aria-label', language === 'es' ? 'Cambiar modo de color' : 'Change color mode');
      }
      const navToggle = document.querySelector('[data-menu-toggle]');
      if (navToggle) {
        navToggle.setAttribute('aria-label', language === 'es' ? 'Abrir menú' : 'Open menu');
      }
    };

    const savedLanguage = (() => {
      try { return localStorage.getItem('language'); } catch (error) { return null; }
    })();
    setLanguage(savedLanguage === 'en' ? 'en' : 'es');

    document.querySelectorAll('[data-language-control]').forEach((button) => {
      button.addEventListener('click', () => setLanguage(button.dataset.languageControl));
    });

    const themeToggle = document.querySelector('[data-theme-toggle]');
    if (themeToggle) {
      const renderThemeToggle = () => {
        const isDark = root.dataset.theme === 'dark';
        themeToggle.textContent = isDark ? '☀' : '◐';
        themeToggle.setAttribute('aria-pressed', String(isDark));
      };
      renderThemeToggle();
      themeToggle.addEventListener('click', () => {
        root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
        try { localStorage.setItem('theme', root.dataset.theme); } catch (error) {}
        renderThemeToggle();
      });
    }

    const nav = document.querySelector('[data-primary-nav]');
    const menuToggle = document.querySelector('[data-menu-toggle]');
    if (nav && menuToggle) {
      menuToggle.addEventListener('click', () => {
        const isOpen = nav.classList.toggle('is-open');
        menuToggle.setAttribute('aria-expanded', String(isOpen));
      });
      nav.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
        nav.classList.remove('is-open');
        menuToggle.setAttribute('aria-expanded', 'false');
      }));
    }

    document.querySelectorAll('.nav-links a').forEach((link) => {
      const current = window.location.pathname.split('/').pop() || 'index.html';
      if (link.getAttribute('href') === current) link.setAttribute('aria-current', 'page');
    });

    const list = document.querySelector('[data-publication-list]');
    const searchInput = document.querySelector('[data-publication-search]');
    const filters = document.querySelector('[data-publication-filters]');
    const status = document.querySelector('[data-publication-status]');
    if (list && searchInput && filters && status) {
      const items = Array.from(list.querySelectorAll('li'));
      const years = Array.from(new Set(items.map((item) => {
        const match = item.textContent.match(/\b(19|20)\d{2}\b/);
        return match ? match[0] : null;
      }).filter(Boolean))).sort((a, b) => Number(b) - Number(a));
      let activeYear = 'all';

      const renderButtons = () => {
        const labels = ['all', ...years];
        filters.replaceChildren(...labels.map((year) => {
          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'filter-button';
          button.dataset.year = year;
          button.textContent = year === 'all' ? (root.dataset.language === 'es' ? 'Todas' : 'All') : year;
          button.setAttribute('aria-pressed', String(year === activeYear));
          button.addEventListener('click', () => {
            activeYear = year;
            renderButtons();
            applyFilters();
          });
          return button;
        }));
      };

      const applyFilters = () => {
        const term = searchInput.value.trim().toLocaleLowerCase();
        let visible = 0;
        items.forEach((item) => {
          const matchesYear = activeYear === 'all' || item.textContent.includes(activeYear);
          const matchesTerm = !term || item.textContent.toLocaleLowerCase().includes(term);
          const show = matchesYear && matchesTerm;
          item.hidden = !show;
          if (show) visible += 1;
        });
        status.textContent = root.dataset.language === 'es'
          ? visible + ' publicaciones visibles'
          : visible + ' publications shown';
      };

      searchInput.addEventListener('input', applyFilters);
      const observer = new MutationObserver(() => {
        renderButtons();
        applyFilters();
      });
      observer.observe(root, { attributes: true, attributeFilter: ['data-language'] });
      renderButtons();
      applyFilters();
    }
  });
})();
