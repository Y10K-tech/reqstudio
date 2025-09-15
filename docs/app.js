// ReqStudio Docs — Vanilla JS SPA (hash routing + search)

(function () {
  const NAV = [
    {
      title: "Getting Started",
      items: [
        { id: "overview", title: "Overview" },
        { id: "install", title: "Install" },
        { id: "getting-started", title: "Quickstart" },
        { id: "ui", title: "UI Guide" },
      ],
    },
    {
      title: "Core Concepts",
      items: [
        { id: "srs-ids", title: "SRS IDs" },
        { id: "templates", title: "Templates" },
        { id: "git", title: "Git Integration" },
        { id: "export", title: "Export (PDF)" },
        { id: "configuration", title: "Configuration" },
      ],
    },
    {
      title: "Interfaces",
      items: [
        { id: "cli", title: "CLI" },
        { id: "api", title: "API & MCP" },
        { id: "docs-server", title: "Docs Server" },
      ],
    },
    {
      title: "Architecture",
      items: [
        { id: "architecture", title: "System Overview" },
        { id: "app", title: "App (PyQt6)" },
        { id: "core", title: "Core Package" },
        { id: "core-git-backend", title: "Git Backend" },
        { id: "core-highlighter", title: "Markdown Highlighter" },
        { id: "core-templates", title: "Template Library" },
        { id: "core-utils", title: "Utilities" },
        { id: "dbms", title: "DBMS (future)" },
      ],
    },
    {
      title: "Project",
      items: [
        { id: "roadmap", title: "Roadmap" },
        { id: "troubleshooting", title: "Troubleshooting" },
        { id: "faq", title: "FAQ" },
        { id: "contributing", title: "Contributing" },
        { id: "changelog", title: "Changelog" },
        { id: "license", title: "License" },
        { id: "glossary", title: "Glossary" },
        { id: "docs-static", title: "Docs Static Build" },
      ],
    },
  ];

  const state = {
    current: null,
    pages: new Map(), // id -> { title, html, text }
    indexBuilt: false,
  };

  const el = {
    sidebar: document.getElementById("sidebar"),
    content: document.getElementById("docContent"),
    searchInput: document.getElementById("searchInput"),
    searchResults: document.getElementById("searchResults"),
    lastUpdated: document.getElementById("lastUpdated"),
  };

  // Build sidebar
  function buildSidebar() {
    const frag = document.createDocumentFragment();
    NAV.forEach(section => {
      const sec = document.createElement("div");
      sec.className = "nav-section";
      const h = document.createElement("div");
      h.className = "nav-title";
      h.textContent = section.title;
      sec.appendChild(h);
      const ul = document.createElement("ul");
      ul.className = "nav-list";
      section.items.forEach(item => {
        const li = document.createElement("li");
        li.className = "nav-item";
        const a = document.createElement("a");
        a.href = `#${item.id}`;
        a.textContent = item.title;
        a.dataset.id = item.id;
        li.appendChild(a);
        ul.appendChild(li);
      });
      sec.appendChild(ul);
      frag.appendChild(sec);
    });
    el.sidebar.innerHTML = "";
    el.sidebar.appendChild(frag);
  }

  // Fetch and cache a page by id
  async function loadPage(id) {
    if (state.pages.has(id)) return state.pages.get(id);
    const res = await fetch(`pages/${id}.html`);
    if (!res.ok) throw new Error(`Failed to load page: ${id}`);
    const html = await res.text();
    const tmp = document.createElement("div");
    tmp.innerHTML = html;
    const titleEl = tmp.querySelector("h1");
    const title = titleEl ? titleEl.textContent.trim() : id;
    const text = tmp.textContent.replace(/\s+/g, " ").trim();
    const page = { id, title, html, text };
    state.pages.set(id, page);
    return page;
  }

  function setActiveNav(id) {
    document.querySelectorAll('.nav-item a').forEach(a => {
      a.classList.toggle('active', a.dataset.id === id);
    });
  }

  async function render(id) {
    try {
      const page = await loadPage(id);
      el.content.innerHTML = page.html;
      document.title = `${page.title} — ReqStudio Docs`;
      setActiveNav(id);
      state.current = id;
      localStorage.setItem('reqstudio.docs.current', id);
    } catch (err) {
      el.content.innerHTML = `<h1>Not Found</h1><p>Page <code>${id}</code> was not found.</p>`;
    }
    // update footer timestamp
    el.lastUpdated.textContent = `Last updated: ${new Date().toLocaleString()}`;
  }

  async function ensureIndex() {
    if (state.indexBuilt) return;
    const allIds = NAV.flatMap(s => s.items.map(i => i.id));
    await Promise.all(allIds.map(id => loadPage(id)));
    state.indexBuilt = true;
  }

  function search(query) {
    const q = query.trim().toLowerCase();
    if (!q) return [];
    const results = [];
    for (const page of state.pages.values()) {
      const iTitle = page.title.toLowerCase().indexOf(q);
      const iText = page.text.toLowerCase().indexOf(q);
      if (iTitle !== -1 || iText !== -1) {
        let idx = Math.max(0, iText !== -1 ? iText : iTitle);
        const start = Math.max(0, idx - 40);
        const end = Math.min(page.text.length, idx + 120);
        const excerpt = page.text.slice(start, end);
        results.push({ id: page.id, title: page.title, excerpt });
      }
    }
    return results.slice(0, 20);
  }

  function renderSearchResults(items) {
    const box = el.searchResults;
    box.innerHTML = "";
    if (!items.length) { box.classList.remove('active'); return; }
    const frag = document.createDocumentFragment();
    items.forEach((it, idx) => {
      const div = document.createElement('div');
      div.className = 'search-item' + (idx === 0 ? ' active' : '');
      div.tabIndex = 0;
      div.dataset.id = it.id;
      div.innerHTML = `<div class="title">${it.title}</div><div class="excerpt">${escapeHtml(it.excerpt)}</div>`;
      div.addEventListener('click', () => {
        location.hash = `#${it.id}`;
        box.classList.remove('active');
      });
      frag.appendChild(div);
    });
    box.appendChild(frag);
    box.classList.add('active');
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
  }

  // Event wiring
  window.addEventListener('hashchange', () => {
    const id = (location.hash || '').replace(/^#/, '') || 'overview';
    render(id);
  });

  el.searchInput.addEventListener('input', async (e) => {
    await ensureIndex();
    const value = e.target.value;
    const items = search(value);
    renderSearchResults(items);
  });
  el.searchInput.addEventListener('keydown', (e) => {
    const items = [...el.searchResults.querySelectorAll('.search-item')];
    const active = el.searchResults.querySelector('.search-item.active');
    const idx = items.indexOf(active);
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      const next = items[Math.min(items.length - 1, idx + 1)] || items[0];
      items.forEach(x => x.classList.remove('active'));
      next.classList.add('active');
      next.scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const prev = items[Math.max(0, idx - 1)] || items[items.length - 1];
      items.forEach(x => x.classList.remove('active'));
      prev.classList.add('active');
      prev.scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'Enter') {
      const chosen = (el.searchResults.querySelector('.search-item.active')) || items[0];
      if (chosen) {
        location.hash = `#${chosen.dataset.id}`;
        el.searchResults.classList.remove('active');
        el.searchInput.blur();
      }
    } else if (e.key === 'Escape') {
      el.searchResults.classList.remove('active');
      el.searchInput.value = '';
    }
  });

  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
      e.preventDefault();
      el.searchInput.focus();
    }
  });

  // Init
  buildSidebar();
  const initial = (location.hash || '').replace(/^#/, '') || localStorage.getItem('reqstudio.docs.current') || 'overview';
  if (!location.hash) location.hash = `#${initial}`;
  render(initial);
})();
