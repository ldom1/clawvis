import "./style.css";
import { escapeHtml } from "./utils.js";

const app = document.getElementById("app");
const path = window.location.pathname;

function theme() {
  return localStorage.getItem("hub-theme") || "dark";
}
function applyTheme(next) {
  localStorage.setItem("hub-theme", next);
  document.body.classList.toggle("theme-light", next === "light");
  document.querySelectorAll("[data-theme]").forEach((el) => {
    el.classList.toggle("active", el.dataset.theme === next);
  });
}

function topbar() {
  return `
    <div class="topbar">
      <div class="left">
        <a class="logo-link" href="/" aria-label="Clawvis home">
          <img src="/clawvis-mascot.svg" alt="Clawvis" class="logo-small" />
          <span>Clawvis</span>
        </a>
      </div>
      <div class="right">
        <div class="icon-row">
          <a class="icon-link" href="/logs/" title="Logs" aria-label="Logs">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
          </a>
          <a class="icon-link" href="/settings/" title="Settings" aria-label="Settings">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09A1.65 1.65 0 0 0 19.4 15z"></path>
            </svg>
          </a>
          <button class="icon-link icon-button" id="theme-toggle" title="Apparence" aria-label="Apparence">
            <span id="theme-toggle-icon">🌙</span>
          </button>
        </div>
      </div>
    </div>
  `;
}

function renderHome() {
  app.innerHTML = `
    <div class="wrap">
      ${topbar()}
      <div class="hero">
        <img src="/clawvis-mascot.svg" alt="Clawvis" />
        <div>
          <h1>Clawvis</h1>
          <p class="services-line"><span class="status-dot"></span>7 active services</p>
        </div>
      </div>
      <div id="system-card" class="system-card">
        <div class="system-title">📊 System Status</div>
        <div class="system-row">
          <div class="system-stat">
            <div class="stat-label">CPU</div>
            <div class="stat-value" id="cpu-percent">—%</div>
            <div class="progress-bar"><div class="progress-fill" id="cpu-fill" style="width:0%"></div></div>
          </div>
          <div class="system-stat">
            <div class="stat-label">RAM</div>
            <div class="stat-value" id="ram-percent">—%</div>
            <div class="progress-bar"><div class="progress-fill" id="ram-fill" style="width:0%; background: #22c55e;"></div></div>
            <div class="stat-detail" id="ram-detail">— GB</div>
          </div>
          <div class="system-stat">
            <div class="stat-label">Disk</div>
            <div class="stat-value" id="disk-percent">—%</div>
            <div class="progress-bar"><div class="progress-fill" id="disk-fill" style="width:0%; background: #f59e0b;"></div></div>
            <div class="stat-detail" id="disk-detail">— GB</div>
          </div>
        </div>
      </div>
      <div class="section">
        <h2>Core tools</h2>
        <div class="grid">
          <a class="tile" href="/logs/">
            <div class="title">📜 Logs</div>
            <div class="desc">Execution feed and monitoring.</div>
            <div class="chips"><span class="chip">Stream</span><span class="chip">Search</span><span class="chip">Ops</span></div>
          </a>
          <a class="tile" href="/kanban/">
            <div class="title">📋 Kanban</div>
            <div class="desc">Drive initiatives and execution.</div>
            <div class="chips"><span class="chip">Tasks</span><span class="chip">Sync</span><span class="chip">Ops</span></div>
          </a>
          <a class="tile" href="/memory/">
            <div class="title">🧠 Logseq Brain</div>
            <div class="desc">Edit and structure project markdown pages.</div>
            <div class="chips"><span class="chip">Markdown</span><span class="chip">Projects</span><span class="chip">Logseq</span></div>
          </a>
        </div>
      </div>
      <div class="section">
        <h2>Projects</h2>
        <div id="projects-grid" class="grid"><button id="new-project" class="card new" type="button">+</button></div>
        <div class="project-hub" id="project-hub"></div>
      </div>
    </div>
    <div class="modal" id="modal">
      <div class="panel">
        <div style="display:flex;justify-content:space-between;align-items:center;"><strong>Créer un projet</strong><button class="btn" id="close-modal" type="button">×</button></div>
        <div class="row">
          <input id="project-name" placeholder="Nom du projet" />
          <textarea id="project-description" rows="4" placeholder="Description"></textarea>
          <div id="project-tags-wrap" class="tags-wrap">
            <div id="project-tags-list" class="tags-list"></div>
            <input id="project-tags" placeholder="Tags (Entrée pour ajouter)" />
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">
            <select id="project-template">
              <option value="python-fastapi">Python FastAPI</option>
              <option value="node-api">Node API</option>
              <option value="frontend-vite">Frontend Vite</option>
              <option value="python">Python (legacy)</option>
              <option value="vite">Vite (legacy)</option>
              <option value="nextjs">Next.js (legacy)</option>
              <option value="empty">Other</option>
            </select>
            <select id="project-stage"><option value="PoC">PoC</option><option value="MVP">MVP</option><option value="Production">Production</option></select>
            <button id="create-project" class="btn" type="button">Créer</button>
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderLogs() {
  app.innerHTML = `
    <div class="wrap">
      ${topbar()}
      <div class="hero">
        <img src="/clawvis-mascot.svg" alt="Clawvis" />
        <div><h1>Logs</h1><p>Execution feed for onboarding and debugging</p></div>
      </div>
      <div class="tile">
        <div style="display:flex;gap:8px;align-items:center;">
          <input id="log-search" placeholder="Search logs" />
          <button id="log-refresh" class="btn" type="button">Refresh</button>
        </div>
        <div id="logs-list" class="list" style="margin-top:10px;"></div>
      </div>
    </div>
  `;
}

function renderKanbanPage() {
  app.innerHTML = `
    <div class="wrap">
      ${topbar()}
      <div class="hero">
        <img src="/clawvis-mascot.svg" alt="Clawvis" />
        <div><h1>Kanban</h1><p>Interactive board for project tasks</p></div>
      </div>
      <div id="kanban-board" class="kanban-board"></div>
    </div>
  `;
}

function renderMemoryPage() {
  app.innerHTML = `
    <div class="wrap">
      ${topbar()}
      <div class="hero">
        <img src="/clawvis-mascot.svg" alt="Clawvis" />
        <div><h1>Logseq Brain</h1><p>Markdown editor for project pages</p></div>
      </div>
      <div class="tile">
        <div class="title">Project pages</div>
        <div style="display:grid;grid-template-columns:260px 1fr;gap:10px;margin-top:10px;">
          <div>
            <select id="memory-file-select" size="12" style="height:360px;"></select>
          </div>
          <div>
            <input id="memory-file-name" placeholder="example-project.md" />
            <textarea id="memory-content" rows="14" placeholder="# Project"></textarea>
            <div style="display:flex;gap:8px;margin-top:8px;">
              <button id="memory-save" class="btn" type="button">Save markdown</button>
              <button id="memory-refresh" class="btn" type="button">Refresh files</button>
            </div>
          </div>
        </div>
      </div>
      <div class="tile" style="margin-top:10px;">
        <div class="title">Structure</div>
        <div class="chips">
          <span class="chip">projects/</span>
          <span class="chip">resources/</span>
          <span class="chip">daily/</span>
          <span class="chip">archive/</span>
          <span class="chip">todo/</span>
        </div>
        <div class="desc" style="margin-top:8px;">Edition directe Markdown depuis l'interface Hub.</div>
      </div>
    </div>
  `;
}

function renderSettings() {
  app.innerHTML = `
    <div class="wrap">
      ${topbar()}
      <div class="hero">
        <img src="/clawvis-mascot.svg" alt="Clawvis" />
        <div><h1>Settings</h1><p>Global project hub configuration</p></div>
      </div>
      <div class="tile" style="max-width:760px;">
        <div class="title">Projects path</div>
        <input id="projects-root" placeholder="/home/user/lab_perso/projects" />
        <button id="save-settings" class="btn" style="margin-top:10px;" type="button">Save</button>
      </div>
      <div class="tile" style="max-width:760px; margin-top:10px;">
        <div class="title">Apparence</div>
        <div class="desc">Choisis le theme de l'interface.</div>
        <div style="display:flex;gap:8px;margin-top:10px;">
          <button id="appearance-dark" class="btn" type="button">🌙 Sombre</button>
          <button id="appearance-light" class="btn" type="button">☀️ Clair</button>
        </div>
      </div>
    </div>
  `;
}

function renderProjectPage(projectSlug) {
  app.innerHTML = `
    <div class="wrap">
      ${topbar()}
      <div class="hero">
        <img src="/clawvis-mascot.svg" alt="Clawvis" />
        <div><h1>Project</h1><p id="project-subtitle">${escapeHtml(projectSlug || "")}</p></div>
      </div>
      <div style="margin-bottom:10px;">
        <a class="btn" href="/">← Back to Hub</a>
        <button class="btn" id="archive-project-btn" type="button" style="margin-left:8px;">Archive project</button>
        <button class="btn" id="delete-project-btn" type="button" style="margin-left:8px;border-color:#ef4444;color:#ef4444;">Delete project</button>
      </div>
      <div id="project-details" class="tile"></div>
      <div id="project-kanban" class="kanban-board"></div>
    </div>
  `;
}

const STATUSES = [
  "Backlog",
  "To Start",
  "In Progress",
  "Blocked",
  "Review",
  "Done",
];

function createKanbanBoard(tasks, target, projectSlug = null) {
  const byStatus = Object.fromEntries(STATUSES.map((s) => [s, []]));
  (tasks || []).forEach((task) => {
    if (byStatus[task.status]) byStatus[task.status].push(task);
  });
  target.innerHTML = `
    ${STATUSES.map(
      (status) => `
      <div class="kanban-column">
        <h3>${status}</h3>
        ${
          (byStatus[status] || [])
            .map(
              (task) => `
          <div class="kanban-card" data-task-id="${task.id}">
            <div class="title">${escapeHtml(task.title)}</div>
            <div class="desc">${escapeHtml(task.description || "")}</div>
            <div class="chips"><span class="chip">${escapeHtml(task.priority || "Medium")}</span></div>
            <div class="status-actions">
              ${STATUSES.map((next) => `<button class="mini-btn ${next === status ? "active" : ""}" data-task-id="${task.id}" data-next-status="${next}">${next}</button>`).join("")}
            </div>
          </div>
        `,
            )
            .join("") || '<div class="task">No tasks</div>'
        }
      </div>
    `,
    ).join("")}
  `;
  target.querySelectorAll(".mini-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const taskId = btn.dataset.taskId;
      const nextStatus = btn.dataset.nextStatus;
      const res = await fetch(
        `/api/kanban/tasks/${encodeURIComponent(taskId)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: nextStatus }),
        },
      );
      if (!res.ok) return alert("Update failed");
      if (projectSlug) {
        const refresh = await fetch(
          `/api/kanban/tasks?project=${encodeURIComponent(projectSlug)}`,
        );
        const payload = refresh.ok ? await refresh.json() : { tasks: [] };
        createKanbanBoard(payload.tasks || [], target, projectSlug);
      } else {
        const refresh = await fetch("/api/kanban/tasks");
        const payload = refresh.ok ? await refresh.json() : { tasks: [] };
        createKanbanBoard(payload.tasks || [], target, null);
      }
    });
  });
}

async function loadProjects() {
  const grid = document.getElementById("projects-grid");
  const res = await fetch("/api/kanban/hub/projects");
  if (!res.ok) return;
  const data = await res.json();
  (data.projects || []).forEach((project) => {
    const card = document.createElement("a");
    card.href = `/project/${encodeURIComponent(project.slug)}`;
    card.className = "card";
    const tags = (project.tags || [])
      .map((t) => `<span class="chip">${t}</span>`)
      .join("");
    card.innerHTML = `<div class="title">${project.name} · ${project.stage || "PoC"}</div><div class="desc">${project.description || ""}</div>${tags ? `<div class="chips">${tags}</div>` : ""}`;
    grid.appendChild(card);
  });
}

async function wireProjectPage() {
  const slug = decodeURIComponent(
    path.replace("/project/", "").split("/")[0] || "",
  );
  if (!slug) return;
  const [projectRes, taskRes] = await Promise.all([
    fetch(`/api/kanban/hub/projects/${encodeURIComponent(slug)}`),
    fetch(`/api/kanban/tasks?project=${encodeURIComponent(slug)}`),
  ]);
  if (!projectRes.ok) {
    document.getElementById("project-details").innerHTML =
      `<div class="title">Project not found</div>`;
    return;
  }
  const payload = await projectRes.json();
  const tasks = taskRes.ok ? await taskRes.json() : { tasks: [] };
  const major = payload.major || {};
  document.getElementById("project-subtitle").textContent =
    payload.project?.name || slug;
  document.getElementById("project-details").innerHTML = `
    <div class="title">${escapeHtml(major.title || payload.project?.name || slug)}</div>
    ${major.objective ? `<div class="desc"><strong>Objective</strong><br>${escapeHtml(major.objective)}</div>` : ""}
    ${major.context ? `<div class="desc" style="margin-top:8px;"><strong>Context</strong><br>${escapeHtml(major.context)}</div>` : ""}
    ${major.kanban ? `<div class="desc" style="margin-top:8px;"><strong>Kanban</strong><br>${escapeHtml(major.kanban)}</div>` : ""}
    ${major.links ? `<div class="desc" style="margin-top:8px;"><strong>Links</strong><br>${escapeHtml(major.links)}</div>` : ""}
    ${major.notes ? `<div class="desc" style="margin-top:8px;"><strong>Notes</strong><br>${escapeHtml(major.notes)}</div>` : ""}
  `;
  createKanbanBoard(
    tasks.tasks || [],
    document.getElementById("project-kanban"),
    slug,
  );
  document
    .getElementById("archive-project-btn")
    .addEventListener("click", async () => {
      if (
        !confirm(
          "Archive this project? Repo will move to archived folder and tasks will be archived.",
        )
      )
        return;
      const res = await fetch(
        `/api/kanban/hub/projects/${encodeURIComponent(slug)}/archive`,
        {
          method: "POST",
        },
      );
      if (!res.ok) return alert("Archive failed");
      window.location.href = "/";
    });
  document
    .getElementById("delete-project-btn")
    .addEventListener("click", async () => {
      if (
        !confirm(
          "Delete this project permanently? Repo, memory file and tasks will be removed.",
        )
      )
        return;
      const res = await fetch(
        `/api/kanban/hub/projects/${encodeURIComponent(slug)}`,
        {
          method: "DELETE",
        },
      );
      if (!res.ok) return alert("Delete failed");
      window.location.href = "/";
    });
}

async function wireLogs() {
  async function refreshLogs() {
    const q = document.getElementById("log-search").value.trim();
    const url = q
      ? `/api/kanban/logs?search=${encodeURIComponent(q)}&limit=200`
      : "/api/kanban/logs?limit=200";
    const res = await fetch(url);
    const data = res.ok ? await res.json() : { logs: [] };
    const list = document.getElementById("logs-list");
    const logs = data.logs || [];
    if (!logs.length) {
      list.innerHTML = `<div class="task">Aucun log pour le moment.</div>`;
      return;
    }
    list.innerHTML = logs
      .slice(0, 200)
      .map(
        (entry) => `
      <div class="task">
        <strong>${escapeHtml(entry.level || "INFO")}</strong>
        <div>${escapeHtml(entry.ts || "")} · ${escapeHtml(entry.process || "")} · ${escapeHtml(entry.action || "")}</div>
        <div>${escapeHtml(entry.message || entry.msg || "")}</div>
      </div>
    `,
      )
      .join("");
  }

  document.getElementById("log-refresh").addEventListener("click", refreshLogs);
  await refreshLogs();
}

async function wireKanbanPage() {
  const res = await fetch("/api/kanban/tasks");
  const data = res.ok ? await res.json() : { tasks: [] };
  createKanbanBoard(
    data.tasks || [],
    document.getElementById("kanban-board"),
    null,
  );
}

async function wireHome() {
  const modal = document.getElementById("modal");
  const tagsInput = document.getElementById("project-tags");
  const tagsList = document.getElementById("project-tags-list");
  let tagValues = [];

  function renderTags() {
    tagsList.innerHTML = tagValues
      .map(
        (t, i) =>
          `<button type="button" class="tag-pill" data-tag-index="${i}">${escapeHtml(t)} ×</button>`,
      )
      .join("");
    tagsList.querySelectorAll(".tag-pill").forEach((el) => {
      el.addEventListener("click", () => {
        const idx = Number(el.dataset.tagIndex);
        tagValues = tagValues.filter((_, i) => i !== idx);
        renderTags();
      });
    });
  }

  function addTag(raw) {
    const tag = (raw || "").trim().replace(/^#/, "");
    if (!tag) return;
    if (tagValues.find((t) => t.toLowerCase() === tag.toLowerCase())) return;
    tagValues.push(tag.slice(0, 24));
    tagValues = tagValues.slice(0, 8);
    renderTags();
  }

  tagsInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addTag(tagsInput.value);
      tagsInput.value = "";
      return;
    }
    if (e.key === "Backspace" && !tagsInput.value && tagValues.length) {
      tagValues.pop();
      renderTags();
    }
  });

  tagsInput.addEventListener("blur", () => {
    if (tagsInput.value.trim()) {
      addTag(tagsInput.value);
      tagsInput.value = "";
    }
  });

  document.getElementById("new-project").addEventListener("click", () => {
    tagValues = [];
    renderTags();
    modal.classList.add("open");
  });
  document
    .getElementById("close-modal")
    .addEventListener("click", () => modal.classList.remove("open"));
  document
    .getElementById("create-project")
    .addEventListener("click", async () => {
      const name = document.getElementById("project-name").value.trim();
      const description = document
        .getElementById("project-description")
        .value.trim();
      if (!name || !description) return;
      if (tagsInput.value.trim()) {
        addTag(tagsInput.value);
        tagsInput.value = "";
      }
      const tags = tagValues;
      const template = document.getElementById("project-template").value;
      const stage = document.getElementById("project-stage").value;
      const res = await fetch("/api/kanban/hub/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          description,
          tags,
          template,
          stage,
          init_git: true,
        }),
      });
      if (!res.ok) return alert("Creation impossible");
      location.reload();
    });
  await loadProjects();
  wireSystemStatus();
}

function wireSystemStatus() {
  const card = document.getElementById("system-card");
  if (!card) return;

  async function loadStats() {
    try {
      const response = await fetch("/api/system.json");
      if (response.ok) {
        const stats = await response.json();
        if (stats.success) {
          document.getElementById("cpu-percent").textContent =
            stats.cpu_percent + "%";
          document.getElementById("cpu-fill").style.width =
            Math.min(stats.cpu_percent, 100) + "%";

          document.getElementById("ram-percent").textContent =
            stats.ram_percent + "%";
          document.getElementById("ram-fill").style.width =
            stats.ram_percent + "%";
          document.getElementById("ram-detail").textContent =
            stats.ram_used_gb + " / " + stats.ram_total_gb + " GB";

          if (stats.disk_percent !== undefined) {
            document.getElementById("disk-percent").textContent =
              stats.disk_percent + "%";
            document.getElementById("disk-fill").style.width =
              stats.disk_percent + "%";
            document.getElementById("disk-detail").textContent =
              stats.disk_used_gb + " / " + stats.disk_total_gb + " GB";

            const fill = document.getElementById("disk-fill");
            if (stats.disk_percent > 90) fill.style.background = "#ef4444";
            else if (stats.disk_percent > 75) fill.style.background = "#f59e0b";
          }
        }
      }
    } catch (e) {}
  }

  loadStats();
  setInterval(loadStats, 30000);
}

async function wireSettings() {
  const res = await fetch("/api/kanban/hub/settings");
  if (res.ok) {
    const data = await res.json();
    document.getElementById("projects-root").value = data.projects_root || "";
  }
  document
    .getElementById("save-settings")
    .addEventListener("click", async () => {
      const projects_root = document
        .getElementById("projects-root")
        .value.trim();
      const save = await fetch("/api/kanban/hub/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ projects_root }),
      });
      if (!save.ok) return alert("Save failed");
      alert("Saved");
    });
  const dark = document.getElementById("appearance-dark");
  const light = document.getElementById("appearance-light");
  if (dark && light) {
    dark.addEventListener("click", () => applyTheme("dark"));
    light.addEventListener("click", () => applyTheme("light"));
  }
}

async function wireMemoryEditor() {
  const select = document.getElementById("memory-file-select");
  const name = document.getElementById("memory-file-name");
  const content = document.getElementById("memory-content");
  async function loadList() {
    const res = await fetch("/api/kanban/memory/projects");
    const payload = res.ok ? await res.json() : { files: [] };
    select.innerHTML = (payload.files || [])
      .map((f) => `<option value="${escapeHtml(f)}">${escapeHtml(f)}</option>`)
      .join("");
    if ((payload.files || [])[0] && !name.value) {
      name.value = payload.files[0];
      await loadFile(payload.files[0]);
      select.value = payload.files[0];
    }
  }
  async function loadFile(filename) {
    const res = await fetch(
      `/api/kanban/memory/projects/${encodeURIComponent(filename)}`,
    );
    if (!res.ok) return;
    const payload = await res.json();
    name.value = payload.filename;
    content.value = payload.content || "";
  }
  select.addEventListener("change", async () => {
    if (!select.value) return;
    await loadFile(select.value);
  });
  document.getElementById("memory-refresh").addEventListener("click", loadList);
  document.getElementById("memory-save").addEventListener("click", async () => {
    const filename = name.value.trim();
    if (!filename) return;
    const res = await fetch("/api/kanban/memory/projects", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename, content: content.value }),
    });
    if (!res.ok) return alert("Save failed");
    await loadList();
    alert("Saved");
  });
  await loadList();
}

async function boot() {
  if (path.startsWith("/settings")) renderSettings();
  else if (path.startsWith("/logs")) renderLogs();
  else if (path.startsWith("/kanban")) renderKanbanPage();
  else if (path.startsWith("/memory")) renderMemoryPage();
  else if (path.startsWith("/project/"))
    renderProjectPage(path.replace("/project/", ""));
  else renderHome();
  applyTheme(theme());
  const themeToggle = document.getElementById("theme-toggle");
  const themeToggleIcon = document.getElementById("theme-toggle-icon");
  if (themeToggle) {
    themeToggleIcon.textContent = theme() === "light" ? "☀️" : "🌙";
    themeToggle.addEventListener("click", () => {
      const next = theme() === "light" ? "dark" : "light";
      applyTheme(next);
      themeToggleIcon.textContent = next === "light" ? "☀️" : "🌙";
    });
  }
  if (path.startsWith("/settings")) await wireSettings();
  else if (path.startsWith("/logs")) await wireLogs();
  else if (path.startsWith("/kanban")) await wireKanbanPage();
  else if (path.startsWith("/memory")) await wireMemoryEditor();
  else if (path.startsWith("/project/")) await wireProjectPage();
  else await wireHome();
}

boot();
