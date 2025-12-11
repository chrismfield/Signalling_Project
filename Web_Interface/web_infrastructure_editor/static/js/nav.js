(function () {
  const frame = document.getElementById('pageFrame');
  const links = Array.from(document.querySelectorAll('.nav__link'));

  // Apply active class based on current key
  function setActive(key) {
    links.forEach(a => {
      if (a.dataset.key === key) a.classList.add('nav__link--active');
      else a.classList.remove('nav__link--active');
    });
  }

  // Load a page into the iframe and update hash
  function loadPage(page, key, push = true) {
    if (!frame) return; // if this page isn't using the iframe shell
    frame.src = page;
    setActive(key);
    if (push) location.hash = key;
  }

  // Enhance clicks: keep href for fallback but use data-page for SPA
  links.forEach(a => {
    a.addEventListener('click', (e) => {
      if (!frame) return; // allow normal nav if no iframe
      e.preventDefault();
      const page = a.dataset.page;
      const key  = a.dataset.key;
      loadPage(page, key, true);
    });
  });

  // Support deep links via hash (e.g. index.html#mqtt)
  function initFromHash() {
    const key = (location.hash || '').replace(/^#/, '') || 'svg';
    const link = links.find(a => a.dataset.key === key) || links[0];
    if (!link) return;
    // If on the shell page, load into iframe; otherwise just highlight
    if (frame) loadPage(link.dataset.page, link.dataset.key, false);
    else setActive(link.dataset.key);
  }

  window.addEventListener('hashchange', initFromHash);
  initFromHash();
})();
