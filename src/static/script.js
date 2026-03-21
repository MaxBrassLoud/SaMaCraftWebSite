/* ════════════════════════════════════════════════════════════════
   SAMACRAFT – Global JS v2
════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Theme ─────────────────────────────────────────────────── */
  const root       = document.documentElement;
  const themeBtn   = document.getElementById('theme-btn');
  const ICONS      = { dark: '🌙', light: '☀️' };

  // Default dark – load saved or system preference
  const saved  = localStorage.getItem('sc-theme');
  const system = window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  const theme  = saved || system;
  setTheme(theme, false);

  function setTheme(t, save = true) {
    root.setAttribute('data-theme', t === 'light' ? 'light' : '');
    if (themeBtn) themeBtn.textContent = t === 'light' ? ICONS.dark : ICONS.light;
    if (save) localStorage.setItem('sc-theme', t);
  }

  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const cur = root.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
      setTheme(cur === 'light' ? 'dark' : 'light');
    });
  }

  /* ── Hamburger / Mobile drawer ─────────────────────────────── */
  const hamburger = document.getElementById('hamburger-btn');
  const drawer    = document.getElementById('mobile-drawer');

  if (hamburger && drawer) {
    hamburger.addEventListener('click', () => {
      const open = drawer.classList.toggle('open');
      hamburger.classList.toggle('open', open);
    });

    // Close on nav link click
    drawer.querySelectorAll('.nav-link').forEach(l =>
      l.addEventListener('click', () => {
        drawer.classList.remove('open');
        hamburger.classList.remove('open');
      })
    );

    // Close on outside click
    document.addEventListener('click', e => {
      if (!hamburger.contains(e.target) && !drawer.contains(e.target)) {
        drawer.classList.remove('open');
        hamburger.classList.remove('open');
      }
    });
  }

  /* ── Sidebar active link on scroll (Rules page) ────────────── */
  const sidebarLinks = document.querySelectorAll('.sidebar-link[href^="#"]');
  if (sidebarLinks.length) {
    const targets = Array.from(sidebarLinks)
      .map(l => document.querySelector(l.getAttribute('href')))
      .filter(Boolean);

    const io = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          sidebarLinks.forEach(l =>
            l.classList.toggle('active', l.getAttribute('href') === `#${e.target.id}`)
          );
        }
      });
    }, { rootMargin: `-${parseInt(getComputedStyle(root).getPropertyValue('--header-h')) + 20}px 0px -55% 0px` });

    targets.forEach(t => io.observe(t));
  }

  /* ── Rules search ──────────────────────────────────────────── */
  const ruleSearch = document.getElementById('rule-search');
  if (ruleSearch) {
    const sections  = document.querySelectorAll('.rule-card');
    const chapters  = document.querySelectorAll('.rule-chapter');
    const noResults = document.getElementById('rules-no-results');

    function removeMarks(el) {
      el.querySelectorAll('mark').forEach(m => {
        m.parentNode.replaceChild(document.createTextNode(m.textContent), m);
        m.parentNode?.normalize();
      });
    }
    function addMarks(el, q) {
      const re = new RegExp(`(${q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
      for (const node of el.childNodes) {
        if (node.nodeType === 3 && re.test(node.textContent)) {
          const s = document.createElement('span');
          s.innerHTML = node.textContent.replace(re, '<mark>$1</mark>');
          node.replaceWith(s);
        } else if (node.nodeType === 1 && node.tagName !== 'MARK') {
          addMarks(node, q);
        }
      }
    }

    ruleSearch.addEventListener('input', () => {
      const q = ruleSearch.value.trim();
      let vis = 0;
      sections.forEach(s => {
        removeMarks(s);
        if (!q) { s.classList.remove('hidden'); vis++; return; }
        if (s.textContent.toLowerCase().includes(q.toLowerCase())) {
          s.classList.remove('hidden');
          addMarks(s, q);
          vis++;
        } else {
          s.classList.add('hidden');
        }
      });
      chapters.forEach(ch => {
        if (!q) { ch.classList.remove('hidden'); return; }
        let sib = ch.nextElementSibling;
        let has = false;
        while (sib && !sib.classList.contains('rule-chapter')) {
          if (sib.classList.contains('rule-card') && !sib.classList.contains('hidden')) { has = true; break; }
          sib = sib.nextElementSibling;
        }
        ch.classList.toggle('hidden', !has);
      });
      if (noResults) noResults.classList.toggle('visible', !!q && vis === 0);
    });
  }

  /* ── Team search ───────────────────────────────────────────── */
  const teamSearch = document.getElementById('team-search');
  if (teamSearch) {
    const cards  = document.querySelectorAll('.team-card');
    const labels = document.querySelectorAll('.team-section-label');
    const noRes  = document.getElementById('team-no-results');
    teamSearch.addEventListener('input', () => {
      const q = teamSearch.value.toLowerCase().trim();
      let vis = 0;
      cards.forEach(c => {
        const match = !q || (c.dataset.name||'').includes(q) || (c.dataset.role||'').includes(q);
        c.style.display = match ? '' : 'none';
        if (match) vis++;
      });
      labels.forEach(l => { l.style.display = q ? 'none' : ''; });
      if (noRes) noRes.classList.toggle('visible', vis === 0);
    });
  }

  /* ── News filter ───────────────────────────────────────────── */
  const filterBtns = document.querySelectorAll('.filter-btn');
  if (filterBtns.length) {
    const newCards  = document.querySelectorAll('.news-card');
    const noResults = document.getElementById('news-no-results');
    const countEl   = document.getElementById('news-count');

    function updateCount() {
      const vis = Array.from(newCards).filter(c => !c.classList.contains('hidden')).length;
      if (countEl) countEl.textContent = vis > 0 ? `${vis} Eintra${vis === 1 ? 'g' : 'äge'}` : '';
      if (noResults) noResults.classList.toggle('visible', vis === 0);
    }

    filterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const t = btn.dataset.type;
        newCards.forEach(c => c.classList.toggle('hidden', t !== 'all' && c.dataset.type !== t));
        updateCount();
      });
    });
    updateCount();

    const hash = location.hash.slice(1);
    if (hash) setTimeout(() => {
      const el = document.getElementById(hash);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 120);
  }

});

/* ── Server status (called inline per page) ──────────────────── */
async function fetchServerStatus(badgeId, textId, playersId) {
  const badge   = document.getElementById(badgeId);
  const text    = document.getElementById(textId);
  const players = playersId ? document.getElementById(playersId) : null;
  if (!badge || !text) return;

  try {
    const res  = await fetch('https://api.mcsrvstat.us/3/mc.samacraft.de');
    const data = await res.json();
    if (data.online) {
      badge.className = 'badge badge-green';
      badge.querySelector('.status-dot')?.classList.add('online');
      const on = data.players?.online ?? 0, mx = data.players?.max ?? 0;
      text.textContent = `Online · ${on}/${mx}`;
      if (players) { players.textContent = `${on} / ${mx}`; players.closest?.('.players-wrap')?.classList.remove('hidden'); }
    } else {
      badge.className = 'badge badge-red';
      text.textContent = 'Offline';
    }
  } catch {
    badge.className = 'badge badge-muted';
    text.textContent = 'Unbekannt';
  }
}

/* ── Copy IP ─────────────────────────────────────────────────── */
function copyIP(btnId) {
  const btn = document.getElementById(btnId || 'copy-ip-btn');
  navigator.clipboard.writeText('mc.samacraft.de').then(() => {
    const orig = btn.innerHTML;
    btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> Kopiert!`;
    btn.style.background = '#4ade80';
    btn.style.color = '#000';
    setTimeout(() => { btn.innerHTML = orig; btn.style.background = ''; btn.style.color = ''; }, 2500);
  });
}