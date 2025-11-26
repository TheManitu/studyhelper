// Simple UI logic for StudyHelper (no backend):
// - Fetch user info from oauth2-proxy to toggle admin link
// - ToDos, Termine, Achievements via localStorage
// - Pomodoro timer (client-side)

(function () {
  const qs = (sel) => document.querySelector(sel);
  const qsa = (sel) => Array.from(document.querySelectorAll(sel));

  // User/Role detection via oauth2-proxy userinfo
  async function initUser() {
    try {
      const res = await fetch('/oauth2/userinfo', { credentials: 'include' });
      if (!res.ok) return; // not expected since page is protected
      const info = await res.json();
      const username = (info.preferred_username || info.user || info.email || '').toString();
      // Try to detect admin by roles in userinfo (various claim shapes)
      const roles = new Set();
      if (Array.isArray(info.roles)) info.roles.forEach(r => roles.add(String(r).toLowerCase()));
      if (info.realm_access && Array.isArray(info.realm_access.roles)) info.realm_access.roles.forEach(r => roles.add(String(r).toLowerCase()));
      if (info.resource_access) {
        Object.values(info.resource_access).forEach(v => {
          if (v && Array.isArray(v.roles)) v.roles.forEach(r => roles.add(String(r).toLowerCase()));
        });
      }
      if (Array.isArray(info.groups)) info.groups.forEach(g => roles.add(String(g).toLowerCase()));

      const isAdmin = roles.has('admin') || username.toLowerCase() === 'admin';
      if (isAdmin) qs('#admin-link')?.removeAttribute('hidden');
    } catch (e) {
      // ignore for now
    }
  }

  // LocalStorage helpers
  const store = {
    get(key, fallback) {
      try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
    },
    set(key, value) { localStorage.setItem(key, JSON.stringify(value)); }
  };

  // Achievements
  const statsKey = 'sh_stats';
  let stats = store.get(statsKey, { done: 0, pomos: 0 });
  function updateStatsDisplay() {
    qs('#stat-done').textContent = String(stats.done);
    qs('#stat-pomos').textContent = String(stats.pomos);
  }
  function incDone() { stats.done += 1; store.set(statsKey, stats); updateStatsDisplay(); }
  function incPomos() { stats.pomos += 1; store.set(statsKey, stats); updateStatsDisplay(); }

  // ToDos
  const todosKey = 'sh_todos';
  let todos = store.get(todosKey, []);
  function renderTodos() {
    const list = qs('#todo-list');
    list.innerHTML = '';
    todos.forEach((t) => {
      const li = document.createElement('li');
      li.className = 'item';
      const left = document.createElement('div');
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.checked = !!t.done;
      const span = document.createElement('span');
      span.textContent = t.text;
      if (t.done) span.classList.add('done');
      left.append(cb, span);
      left.style.display = 'flex';
      left.style.gap = '8px';
      const del = document.createElement('button');
      del.textContent = 'Löschen';
      del.type = 'button';
      del.addEventListener('click', () => {
        todos = todos.filter(x => x.id !== t.id);
        store.set(todosKey, todos);
        renderTodos();
      });
      cb.addEventListener('change', () => {
        t.done = cb.checked;
        if (t.done) incDone();
        store.set(todosKey, todos);
        renderTodos();
      });
      li.append(left, del);
      list.appendChild(li);
    });
  }
  qs('#todo-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const input = qs('#todo-input');
    const text = input.value.trim();
    if (!text) return;
    todos.unshift({ id: crypto.randomUUID(), text, done: false });
    store.set(todosKey, todos);
    input.value = '';
    renderTodos();
  });

  // Termine
  const datesKey = 'sh_dates';
  let dates = store.get(datesKey, []);
  function renderDates() {
    const list = qs('#date-list');
    list.innerHTML = '';
    // sort by date ascending
    dates.sort((a, b) => (a.when || '').localeCompare(b.when || ''));
    dates.forEach((d) => {
      const li = document.createElement('li');
      li.className = 'item';
      const left = document.createElement('div');
      const span = document.createElement('span');
      span.textContent = `${d.when || '—'} – ${d.text}`;
      left.append(span);
      const del = document.createElement('button');
      del.textContent = 'Löschen';
      del.type = 'button';
      del.addEventListener('click', () => {
        dates = dates.filter(x => x.id !== d.id);
        store.set(datesKey, dates);
        renderDates();
      });
      li.append(left, del);
      list.appendChild(li);
    });
  }
  qs('#date-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = qs('#date-text').value.trim();
    const when = qs('#date-when').value;
    if (!text) return;
    dates.unshift({ id: crypto.randomUUID(), text, when });
    store.set(datesKey, dates);
    qs('#date-text').value = '';
    renderDates();
  });

  // Pomodoro Timer
  let phase = 'work'; // 'work' | 'break'
  let running = false;
  let remaining = 25 * 60;
  let interval = null;
  function fmt(sec) {
    const m = Math.floor(sec / 60).toString().padStart(2, '0');
    const s = (sec % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  }
  function updatePomoDisplay() {
    qs('#pomo-display').textContent = fmt(remaining);
    qs('#pomo-phase').textContent = `Phase: ${phase === 'work' ? 'Arbeit' : 'Pause'}`;
  }
  function startPomo() {
    if (running) return;
    running = true;
    interval = setInterval(() => {
      remaining -= 1;
      if (remaining <= 0) {
        if (phase === 'work') {
          incPomos();
          phase = 'break';
          const br = Math.max(1, parseInt(qs('#pomo-break').value || '5', 10));
          remaining = br * 60;
        } else {
          phase = 'work';
          const wk = Math.max(1, parseInt(qs('#pomo-work').value || '25', 10));
          remaining = wk * 60;
        }
      }
      updatePomoDisplay();
    }, 1000);
  }
  function pausePomo() {
    running = false;
    if (interval) clearInterval(interval);
    interval = null;
  }
  function resetPomo() {
    pausePomo();
    phase = 'work';
    remaining = Math.max(1, parseInt(qs('#pomo-work').value || '25', 10)) * 60;
    updatePomoDisplay();
  }
  qs('#pomo-start')?.addEventListener('click', startPomo);
  qs('#pomo-pause')?.addEventListener('click', pausePomo);
  qs('#pomo-reset')?.addEventListener('click', resetPomo);
  qs('#pomo-work')?.addEventListener('change', () => { if (!running && phase === 'work') { remaining = Math.max(1, parseInt(qs('#pomo-work').value || '25', 10)) * 60; updatePomoDisplay(); } });
  qs('#pomo-break')?.addEventListener('change', () => { if (!running && phase === 'break') { remaining = Math.max(1, parseInt(qs('#pomo-break').value || '5', 10)) * 60; updatePomoDisplay(); } });

  // Init
  updateStatsDisplay();
  renderTodos();
  renderDates();
  resetPomo();
  initUser();
})();
