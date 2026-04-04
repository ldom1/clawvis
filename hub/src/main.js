import "./style.css";
import { marked } from "marked";
import { escapeHtml, projectInitials, projectAvatarHue } from "./utils.js";

marked.use({ gfm: true, breaks: true });

const BRAIN_MD_PAGE_CSS = `
:root{color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:#0d1117;color:#e6edf3;font-family:Georgia,"Iowan Old Style","Palatino Linotype",Palatino,serif;font-size:18px;line-height:1.65}
article{max-width:42rem;margin:0 auto;padding:2rem 1.25rem 3rem}
.markdown-body h1{font-family:system-ui,sans-serif;font-size:2rem;font-weight:700;margin:0 0 1rem;letter-spacing:-.02em;color:#f0f6fc;border-bottom:1px solid #30363d;padding-bottom:.5rem}
.markdown-body h2{font-family:system-ui,sans-serif;font-size:1.35rem;margin:2rem 0 .75rem;color:#58a6ff}
.markdown-body h3{font-size:1.15rem;margin:1.5rem 0 .5rem;color:#c9d1d9}
.markdown-body p{margin:.85rem 0}
.markdown-body ul,.markdown-body ol{margin:.75rem 0;padding-left:1.35rem}
.markdown-body li{margin:.35rem 0}
.markdown-body a{color:#58a6ff;text-decoration:none}
.markdown-body a:hover{text-decoration:underline}
.markdown-body code{font-family:ui-monospace,Menlo,monospace;font-size:.88em;background:#161b22;padding:.15em .4em;border-radius:4px;color:#ff7b72}
.markdown-body pre{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:1rem;overflow:auto;font-size:.85rem;line-height:1.5}
.markdown-body pre code{background:none;padding:0;color:#e6edf3}
.markdown-body blockquote{margin:1rem 0;padding-left:1rem;border-left:4px solid #388bfd;color:#8b949e}
.markdown-body table{border-collapse:collapse;width:100%;font-size:.95rem}
.markdown-body th,.markdown-body td{border:1px solid #30363d;padding:.5rem .65rem}
.markdown-body th{background:#161b22}
`;

function markdownToBrainSrcdoc(markdown) {
  const raw = (markdown || "").trim();
  const inner = raw
    ? marked.parse(raw, { gfm: true, breaks: false })
    : '<p style="color:#8b949e">—</p>';
  const lang = settingsLocale();
  return `<!DOCTYPE html><html lang="${lang}"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/><style>${BRAIN_MD_PAGE_CSS}</style><base target="_blank"/></head><body><article class="markdown-body">${inner}</article></body></html>`;
}

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

function settingsLocale() {
  const saved = localStorage.getItem("clawvis-locale");
  if (saved === "fr" || saved === "en") return saved;
  return (navigator.language || "en").toLowerCase().startsWith("fr")
    ? "fr"
    : "en";
}

function ensureGlobalConfirmModal() {
  if (document.getElementById("global-confirm-overlay")) return;
  const wrap = document.createElement("div");
  wrap.id = "global-confirm-overlay";
  wrap.className = "modal-overlay confirm-modal-overlay";
  wrap.innerHTML = `
    <div class="panel confirm-modal-panel" role="dialog" aria-modal="true" aria-labelledby="confirm-modal-title">
      <h2 id="confirm-modal-title" class="confirm-modal-title"></h2>
      <p id="confirm-modal-message" class="confirm-modal-message"></p>
      <div class="confirm-modal-actions">
        <button type="button" class="btn" id="confirm-modal-cancel"></button>
        <button type="button" class="btn btn-primary" id="confirm-modal-ok"></button>
      </div>
    </div>
  `;
  document.body.appendChild(wrap);
}

/** @param {{ title: string; message: string; confirmLabel: string; cancelLabel: string }} opts */
function showConfirm(opts) {
  ensureGlobalConfirmModal();
  const overlay = document.getElementById("global-confirm-overlay");
  const titleEl = document.getElementById("confirm-modal-title");
  const msgEl = document.getElementById("confirm-modal-message");
  const okBtn = document.getElementById("confirm-modal-ok");
  const cancelBtn = document.getElementById("confirm-modal-cancel");
  titleEl.textContent = opts.title;
  msgEl.textContent = opts.message;
  okBtn.textContent = opts.confirmLabel;
  cancelBtn.textContent = opts.cancelLabel;
  return new Promise((resolve) => {
    let settled = false;
    const finish = (v) => {
      if (settled) return;
      settled = true;
      overlay.classList.remove("open");
      document.removeEventListener("keydown", onKey);
      okBtn.removeEventListener("click", onOk);
      cancelBtn.removeEventListener("click", onCancel);
      overlay.removeEventListener("click", onOverlay);
      resolve(v);
    };
    const onOk = () => finish(true);
    const onCancel = () => finish(false);
    const onOverlay = (e) => {
      if (e.target === overlay) onCancel();
    };
    const onKey = (e) => {
      if (e.key === "Escape") onCancel();
    };
    okBtn.addEventListener("click", onOk);
    cancelBtn.addEventListener("click", onCancel);
    overlay.addEventListener("click", onOverlay);
    document.addEventListener("keydown", onKey);
    overlay.classList.add("open");
    okBtn.focus();
  });
}

const SETTINGS_TEXT = {
  fr: {
    title: "Paramètres",
    subtitle:
      "Configure ton runtime IA, ton workspace et l'apparence en un seul endroit.",
    back: "Retour au hub",
    intro:
      "Configure le provider IA actif, puis teste la connexion avant de sauvegarder.",
    step1: "1. Runtime IA",
    step2: "2. Workspace",
    step3: "3. Instances",
    step4: "4. Apparence",
    healthTitle: "Health resume",
    runtimeHealth: "Runtime config",
    workspaceHealth: "Workspace config",
    instancesHealth: "Instances liees",
    configured: "Configure",
    notConfigured: "À configurer",
    linked: "liée(s)",
    runtimeTitle: "Runtime IA",
    runtimeDesc:
      "Le modele ou service utilise quand le Hub appelle l'intelligence artificielle.",
    runtimeInfo:
      "Le runtime IA relie le Hub a un fournisseur : Claude (Anthropic), Mistral ou OpenClaw (auto-heberge). La cle active est transmise via le backend Clawvis — configure le fichier .env sur le serveur pour la persistance.",
    moreInfo: "Plus d'infos",
    configureRuntime: "Configurer",
    modifyRuntime: "Modifier",
    getClaudeKey: "Obtiens ta cle sur console.anthropic.com.",
    getMistralKey: "Obtiens ta cle sur console.mistral.ai.",
    openclawHint:
      "Pour un serveur distant, renseigne une URL complete (ex: https://openclaw.domain.tld).",
    saveRuntime: "Sauvegarder le runtime",
    testConnection: "Tester la connexion",
    gotoActiveProvider: "Aller au provider actif",
    runtimeSaved: "Runtime IA sauvegarde",
    workspaceTitle: "Workspace",
    workspaceDesc:
      "Chemins sur ta machine que le Hub utilise pour retrouver projets et instances.",
    workspaceInfo:
      "Dossier projets : racine ou tu stockes le code ou les depots que tu veux voir dans le Hub. Instances externes (optionnel) : un repertoire supplementaire ou se trouvent d'autres dossiers d'instance Clawvis, en plus de ceux dans le depot (dossier instances/). Ces valeurs sont sauvegardees cote API Kanban.",
    projectsRoot: "Projects root",
    externalInstances: "Instances externes (optionnel)",
    saveWorkspace: "Sauvegarder le workspace",
    workspaceSaved: "Workspace sauvegarde",
    saveFailed: "Échec sauvegarde",
    instancesTitle: "Instances Clawvis",
    instancesDesc:
      "Dossiers Clawvis detectes dans le depot et chemins externes.",
    instancesInfo:
      "Une instance est un deploiement Clawvis (compose local, .env, etc.). Lie ou retire chaque ligne au Hub pour les menus et la configuration. Plusieurs instances liees : l'API choisit d'abord celle dont le dossier memoire est egal a MEMORY_ROOT, sinon la premiere apres tri de chemins.",
    refreshInstances: "Rafraichir",
    loadingInstances: "Chargement des instances...",
    loadInstancesFailed: "Impossible de charger les instances.",
    noInstances: "Aucune instance detectee.",
    linkedStatus: "Liee",
    notLinkedStatus: "Non liee",
    missingStatus: "manquante",
    link: "Lier",
    unlink: "Retirer",
    actionFailed: "Action echouee",
    appearanceTitle: "Apparence",
    appearanceDesc: "Theme clair ou sombre du Hub (ce navigateur).",
    appearanceInfo:
      "Le choix est enregistre localement : il s'applique a cette session et sera reutilise au prochain passage sur le Hub.",
    connected: "Connecte",
    connectionFailed: "Connexion echouee",
    checkKeyOrUrl: "Erreur: verifie la cle ou l'URL",
    runtimeBannerTitle: "Runtime IA",
    runtimeBannerNotConfigured: "Non configuré",
    runtimeBannerCta: "Configurer →",
    runtimeBannerConfigured: "Connecté",
    runtimeBannerChange: "Modifier",
    kpiProjects: "Projets",
    kpiTasks: "Tâches actives",
    kpiDone: "Terminées",
    kpiBrain: "Notes Brain",
    systemStatus: "État du système",
    healthBannerTitle: "Santé",
    languageTitle: "Langue",
    languageDesc: "Langue de l'interface (ce navigateur).",
    languageInfo:
      "Le choix est enregistré localement et appliqué immédiatement.",
    languageFr: "Français",
    languageEn: "English",
  },
  en: {
    title: "Settings",
    subtitle:
      "Configure your AI runtime, workspace, and appearance in one place.",
    back: "Back to hub",
    intro:
      "Configure the active AI provider, then test the connection before saving.",
    step1: "1. AI runtime",
    step2: "2. Workspace",
    step3: "3. Instances",
    step4: "4. Appearance",
    healthTitle: "Health summary",
    runtimeHealth: "Runtime config",
    workspaceHealth: "Workspace config",
    instancesHealth: "Linked instances",
    configured: "Configured",
    notConfigured: "Needs setup",
    linked: "linked",
    runtimeTitle: "AI runtime",
    runtimeDesc:
      "The model or service used when the Hub calls artificial intelligence.",
    runtimeInfo:
      "The AI runtime connects the Hub to a provider: Claude (Anthropic), Mistral, or self-hosted OpenClaw. The active key is forwarded via the Clawvis backend — set .env on the server for persistence.",
    moreInfo: "More info",
    configureRuntime: "Configure",
    modifyRuntime: "Change",
    getClaudeKey: "Get your key at console.anthropic.com.",
    getMistralKey: "Get your key at console.mistral.ai.",
    openclawHint:
      "For a remote server, use a full URL (e.g. https://openclaw.domain.tld).",
    saveRuntime: "Save runtime",
    testConnection: "Test connection",
    gotoActiveProvider: "Go to active provider",
    runtimeSaved: "AI runtime saved",
    workspaceTitle: "Workspace",
    workspaceDesc: "Paths on disk the Hub uses to find projects and instances.",
    workspaceInfo:
      "Projects root: where your code or repos live that you want the Hub to reference. External instances (optional): an extra folder that holds additional Clawvis instance directories, besides this repo's instances/ folder. Values are saved via the Kanban API.",
    projectsRoot: "Projects root",
    externalInstances: "External instances (optional)",
    saveWorkspace: "Save workspace",
    workspaceSaved: "Workspace saved",
    saveFailed: "Save failed",
    instancesTitle: "Clawvis instances",
    instancesDesc: "Clawvis folders detected in the repo and external paths.",
    instancesInfo:
      "An instance is a Clawvis deployment folder (local compose, .env, etc.). Use Link or Unlink on each row for Hub menus and settings. With several linked instances, the API first picks the one whose memory folder equals MEMORY_ROOT, otherwise the first after sorting paths.",
    refreshInstances: "Refresh",
    loadingInstances: "Loading instances...",
    loadInstancesFailed: "Unable to load instances.",
    noInstances: "No instances found.",
    linkedStatus: "Linked",
    notLinkedStatus: "Not linked",
    missingStatus: "missing",
    link: "Link",
    unlink: "Unlink",
    actionFailed: "Action failed",
    appearanceTitle: "Appearance",
    appearanceDesc: "Light or dark Hub theme (this browser).",
    appearanceInfo:
      "Your choice is stored locally and reused the next time you open the Hub.",
    connected: "Connected",
    connectionFailed: "Connection failed",
    checkKeyOrUrl: "Error: check key or URL",
    runtimeBannerTitle: "AI Runtime",
    runtimeBannerNotConfigured: "Not configured",
    runtimeBannerCta: "Configure →",
    runtimeBannerConfigured: "Connected",
    runtimeBannerChange: "Change",
    kpiProjects: "Projects",
    kpiTasks: "Active tasks",
    kpiDone: "Done",
    kpiBrain: "Brain notes",
    systemStatus: "System status",
    healthBannerTitle: "Health",
    languageTitle: "Language",
    languageDesc: "Interface language (this browser).",
    languageInfo: "Your choice is stored locally and applied immediately.",
    languageFr: "Français",
    languageEn: "English",
  },
};

const SUBPAGE_TEXT = {
  fr: {
    logs: {
      title: "Logs",
      sub: "Filtrer et consulter l'activité système et les agents.",
    },
    kanban: {
      title: "Kanban",
      sub: "Tableau, vues et pilotage par projet.",
    },
    brain: {
      title: "Brain",
      sub: "Votre espace connaissance.",
    },
    brainEdit: {
      title: "Modifier le Brain",
      sub: "Éditez vos fichiers projets markdown. Pour les tâches, utilisez le Kanban.",
    },
    runtime: {
      title: "Runtime IA",
      sub: "Statut, test de connexion et accès au chat OpenClaw.",
    },
  },
  en: {
    logs: {
      title: "Logs",
      sub: "Filter and review system and agent activity.",
    },
    kanban: {
      title: "Kanban",
      sub: "Board, views, and project steering.",
    },
    brain: {
      title: "Brain",
      sub: "Your knowledge space.",
    },
    brainEdit: {
      title: "Edit Brain",
      sub: "Edit your project markdown files. For tasks, use Kanban.",
    },
    runtime: {
      title: "AI Runtime",
      sub: "Status, connection test, and access to OpenClaw chat.",
    },
  },
};

function subpageHeader(pageKey) {
  const loc = settingsLocale();
  const pack = SUBPAGE_TEXT[loc]?.[pageKey] || SUBPAGE_TEXT.en[pageKey];
  const t = SETTINGS_TEXT[loc];
  if (!pack) return "";
  return `
    <header class="settings-page-header">
      <div class="title">
        <h1>${escapeHtml(pack.title)} · <span>Clawvis</span></h1>
        <p>${escapeHtml(pack.sub)}</p>
      </div>
      <div class="sub-page-header-actions">
        <a href="/" class="back-btn"><span class="icon">←</span><span>${escapeHtml(t.back)}</span></a>
        <div class="locale-menu">
          <button class="header-icon icon-button" type="button" id="locale-toggle" title="${escapeHtml(t.languageTitle)}" aria-label="${escapeHtml(t.languageTitle)}" aria-expanded="false" aria-haspopup="true">🌐</button>
          <div class="locale-dropdown" id="locale-dropdown" hidden role="menu">
            <button class="locale-option" data-locale="fr" type="button" role="menuitem" title="${escapeHtml(t.languageFr)}">FR</button>
            <button class="locale-option" data-locale="en" type="button" role="menuitem" title="${escapeHtml(t.languageEn)}">EN</button>
          </div>
        </div>
        <button class="header-icon icon-button" type="button" id="theme-toggle" title="${escapeHtml(t.appearanceTitle)}" aria-label="${escapeHtml(t.appearanceTitle)}">
          <span id="theme-toggle-icon">🌙</span>
        </button>
      </div>
    </header>
  `;
}

/** Kanban/Logs-style header for a single project; subtitle = display name (synced from API). */
function projectPageHeader(displayName) {
  const loc = settingsLocale();
  const fr = loc === "fr";
  const t = SETTINGS_TEXT[loc];
  const titleWord = fr ? "Projet" : "Project";
  const sub = (displayName || "").trim();
  return `
    <header class="settings-page-header project-page-top">
      <div class="title">
        <h1>${escapeHtml(titleWord)} · <span>Clawvis</span></h1>
        <p id="project-subtitle" class="project-page-name-line">${escapeHtml(sub)}</p>
      </div>
      <div class="sub-page-header-actions">
        <a href="/" class="back-btn"><span class="icon">←</span><span>${escapeHtml(t.back)}</span></a>
        <div class="locale-menu">
          <button class="header-icon icon-button" type="button" id="locale-toggle" title="${escapeHtml(t.languageTitle)}" aria-label="${escapeHtml(t.languageTitle)}" aria-expanded="false" aria-haspopup="true">🌐</button>
          <div class="locale-dropdown" id="locale-dropdown" hidden role="menu">
            <button class="locale-option" data-locale="fr" type="button" role="menuitem" title="${escapeHtml(t.languageFr)}">FR</button>
            <button class="locale-option" data-locale="en" type="button" role="menuitem" title="${escapeHtml(t.languageEn)}">EN</button>
          </div>
        </div>
        <button class="header-icon icon-button" type="button" id="theme-toggle" title="${escapeHtml(t.appearanceTitle)}" aria-label="${escapeHtml(t.appearanceTitle)}">
          <span id="theme-toggle-icon">🌙</span>
        </button>
      </div>
    </header>
  `;
}

function topbar() {
  const t = SETTINGS_TEXT[settingsLocale()];
  return `
    <header class="hub-header">
      <div class="hub-brand">
        <img src="/clawvis-mascot.svg" alt="Clawvis logo" class="header-logo" />
        <h1><span>Clawvis</span></h1>
        <p><span class="status-dot"></span><span id="active-services-count">…</span> active services</p>
      </div>
      <div class="header-icons">
          <a class="header-icon" href="/logs/" title="Logs" aria-label="Logs">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
          </a>
          <a class="header-icon" href="/settings/" title="Settings" aria-label="Settings">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="3"></circle>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09A1.65 1.65 0 0 0 19.4 15z"></path>
            </svg>
          </a>
          <div class="locale-menu">
            <button class="header-icon icon-button" type="button" id="locale-toggle" title="${escapeHtml(t.languageTitle)}" aria-label="${escapeHtml(t.languageTitle)}" aria-expanded="false" aria-haspopup="true">🌐</button>
            <div class="locale-dropdown" id="locale-dropdown" hidden role="menu">
              <button class="locale-option" data-locale="fr" type="button" role="menuitem" title="${escapeHtml(t.languageFr)}">FR</button>
              <button class="locale-option" data-locale="en" type="button" role="menuitem" title="${escapeHtml(t.languageEn)}">EN</button>
            </div>
          </div>
          <button class="header-icon icon-button" id="theme-toggle" title="${escapeHtml(t.appearanceTitle)}" aria-label="${escapeHtml(t.appearanceTitle)}">
            <span id="theme-toggle-icon">🌙</span>
          </button>
      </div>
    </header>
  `;
}

function wireActiveServicesCount() {
  const el = document.getElementById("active-services-count");
  if (!el) return;
  const services = [
    { name: "Hub", url: "/" },
    { name: "Kanban", url: "/kanban/" },
    { name: "Logs", url: "/logs/" },
    { name: "Settings", url: "/settings/" },
    { name: "Memory", url: "/memory/" },
    {
      name: "OpenClaw",
      url: "/openclaw/",
      optional: true,
    },
  ];
  const countUp = async () => {
    try {
      const checks = await Promise.all(
        services.map(async (svc) => {
          try {
            const res = await fetch(svc.url, { cache: "no-store" });
            return { ...svc, up: !!res.ok };
          } catch {
            return { ...svc, up: false };
          }
        }),
      );
      const required = checks.filter((s) => !s.optional);
      const upCount = required.filter((s) => s.up).length;
      const total = required.length;
      const down = required.filter((s) => !s.up).map((s) => s.name);
      el.textContent = String(upCount);
      el.title = down.length
        ? `${upCount}/${total} up\nDown: ${down.join(", ")}`
        : `${upCount}/${total} up\nAll services operational`;
    } catch {
      el.textContent = "0";
      el.title = "0/0 up";
    }
  };
  countUp();
  setInterval(countUp, 30000);
}

function renderHome() {
  const fr = settingsLocale() === "fr";
  const t = SETTINGS_TEXT[settingsLocale()];
  const M = fr
    ? {
        modalTitle: "Nouveau projet",
        nameLbl: "Nom du projet",
        nameHint: "Affiché sur la carte et dans la page projet.",
        descLbl: "En bref",
        descHint: "1–2 phrases : objectif ou périmètre.",
        tagsLbl: "Tags",
        tagsHint: "Entrée après chaque mot-clé.",
        stackLbl: "Modèle de dépôt",
        stackHint: "Fichiers de démarrage générés dans le dossier du projet.",
        stageLbl: "Phase",
        stageHint: "Maturité : essai, produit, ou production.",
        create: "Créer le projet",
      }
    : {
        modalTitle: "New project",
        nameLbl: "Project name",
        nameHint: "Shown on the card and project page.",
        descLbl: "Summary",
        descHint: "1–2 sentences: goal or scope.",
        tagsLbl: "Tags",
        tagsHint: "Press Enter after each tag.",
        stackLbl: "Repo template",
        stackHint: "Starter files created in the project folder.",
        stageLbl: "Stage",
        stageHint: "Maturity: experiment, product, or production.",
        create: "Create project",
      };
  app.innerHTML = `
    <div class="container">
      ${topbar()}
      <!-- AI Runtime banner (unconfigured) / chip (configured) -->
      <div id="ai-runtime-banner" class="ai-runtime-banner">
        <div class="ai-runtime-banner-left">
          <span class="ai-runtime-banner-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a4 4 0 0 1 4 4v1h1a3 3 0 0 1 3 3v7a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3v-7a3 3 0 0 1 3-3h1V6a4 4 0 0 1 4-4z"/><circle cx="12" cy="13" r="2"/></svg>
          </span>
          <div class="ai-runtime-banner-info">
            <span class="ai-runtime-banner-title">${escapeHtml(t.runtimeBannerTitle)}</span>
            <span id="ai-runtime-status" class="ai-runtime-status-badge warn">${escapeHtml(t.runtimeBannerNotConfigured)}</span>
            <span id="ai-runtime-provider-label" class="ai-runtime-provider-label"></span>
          </div>
        </div>
        <div class="ai-runtime-banner-right">
          <a href="/setup/runtime/" id="ai-runtime-cta" class="btn btn-primary ai-runtime-cta">${escapeHtml(t.runtimeBannerCta)}</a>
        </div>
      </div>
      <!-- AI Runtime chip (shown when configured, hides banner) -->
      <div id="ai-runtime-chip" class="ai-runtime-chip" style="display:none">
        <button type="button" class="ai-runtime-chip-btn" id="ai-runtime-chip-btn" aria-expanded="false" aria-controls="ai-runtime-chip-panel">
          <span class="ai-runtime-chip-dot"></span>
          <span class="ai-runtime-chip-label">${escapeHtml(t.runtimeBannerTitle)} · <span id="ai-runtime-chip-provider"></span></span>
          <span class="ai-runtime-chip-arrow">▾</span>
        </button>
        <div id="ai-runtime-chip-panel" class="ai-runtime-chip-panel" style="display:none">
          <div class="ai-runtime-chip-panel-row">
            <span id="ai-runtime-chip-panel-status"></span>
          </div>
          <a href="/setup/runtime/" class="btn ai-runtime-chip-settings">${escapeHtml(t.runtimeBannerChange)}</a>
        </div>
      </div>

      <div class="section-header" style="margin-top:4px">
        <div class="section-label">${escapeHtml(t.systemStatus)}</div>
      </div>
      <div id="system-card" class="system-card">
        <div class="system-kpi-row">
          <div class="system-kpi">
            <div class="kpi-value" id="kpi-projects">—</div>
            <div class="kpi-label">${escapeHtml(t.kpiProjects)}</div>
          </div>
          <div class="system-kpi">
            <div class="kpi-value" id="kpi-tasks-active">—</div>
            <div class="kpi-label">${escapeHtml(t.kpiTasks)}</div>
          </div>
          <div class="system-kpi">
            <div class="kpi-value" id="kpi-tasks-done">—</div>
            <div class="kpi-label">${escapeHtml(t.kpiDone)}</div>
          </div>
          <div class="system-kpi">
            <div class="kpi-value" id="kpi-brain-notes">—</div>
            <div class="kpi-label">${escapeHtml(t.kpiBrain)}</div>
          </div>
        </div>
        <div class="system-infra-strip">
          <span class="infra-item">
            <span class="infra-label">CPU</span>
            <span class="infra-bar"><span class="infra-bar-fill" id="cpu-fill" style="width:0%"></span></span>
            <span class="infra-value" id="cpu-percent">—%</span>
          </span>
          <span class="infra-item">
            <span class="infra-label">RAM</span>
            <span class="infra-bar"><span class="infra-bar-fill" id="ram-fill" style="width:0%;background:#22c55e"></span></span>
            <span class="infra-value" id="ram-percent">—%</span>
            <span class="infra-detail" id="ram-detail"></span>
          </span>
          <span class="infra-item">
            <span class="infra-label">Disk</span>
            <span class="infra-bar"><span class="infra-bar-fill" id="disk-fill" style="width:0%;background:#f59e0b"></span></span>
            <span class="infra-value" id="disk-percent">—%</span>
            <span class="infra-detail" id="disk-detail"></span>
          </span>
        </div>
      </div>

      <section>
        <div class="section-header">
          <div class="section-label">Core tools</div>
        </div>
        <div class="tools-bar">
          <a class="tool-tile" href="/kanban/">
            <span class="tool-open">&#x2197;</span>
            <div class="tool-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <rect x="3" y="4" width="18" height="16" rx="2"></rect>
                <line x1="7" y1="8" x2="17" y2="8"></line>
                <line x1="7" y1="12" x2="14" y2="12"></line>
                <line x1="7" y1="16" x2="12" y2="16"></line>
              </svg>
            </div>
            <div class="tool-meta">
              <div class="tool-name">Kanban</div>
              <div class="tool-desc">Drive initiatives and execution.</div>
              <div class="tool-chiprow"><span class="tool-chip">Tasks</span><span class="tool-chip">Sync</span><span class="tool-chip">Ops</span></div>
            </div>
          </a>
          <a class="tool-tile" href="/memory/">
            <span class="tool-open">&#x2197;</span>
            <div class="tool-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M8.5 7.2C7 7.2 5.8 8.4 5.8 9.9c0 .9.4 1.7 1 2.3-.6.5-1 1.3-1 2.2 0 1.6 1.3 2.9 2.9 2.9"></path>
                <path d="M15.5 7.2c1.5 0 2.7 1.2 2.7 2.7 0 .9-.4 1.7-1 2.3.6.5 1 1.3 1 2.2 0 1.6-1.3 2.9-2.9 2.9"></path>
                <path d="M8.5 7.2C9 5.5 10.4 4.5 12 4.5s3 .9 3.5 2.7"></path>
                <path d="M8.5 19.8C9 21.5 10.4 22.5 12 22.5s3-.9 3.5-2.7"></path>
                <path d="M12 5.2v13.6"></path>
                <path d="M10 10.2c.4-.3.9-.5 1.4-.5s1 .2 1.4.5"></path>
                <path d="M10 15.2c.4.3.9.5 1.4.5s1-.2 1.4-.5"></path>
              </svg>
            </div>
            <div class="tool-meta">
              <div class="tool-name">Brain</div>
              <div class="tool-desc">Explore your knowledge space and edit your notes.</div>
              <div class="tool-chiprow"><span class="tool-chip">Quartz</span><span class="tool-chip">Projects</span><span class="tool-chip">Notes</span></div>
            </div>
          </a>
          <a class="tool-tile" href="/runtime/">
            <span class="tool-open">&#x2197;</span>
            <div class="tool-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <rect x="2" y="3" width="20" height="14" rx="2"></rect>
                <path d="M8 21h8M12 17v4"></path>
                <circle cx="12" cy="10" r="2"></circle>
              </svg>
            </div>
            <div class="tool-meta">
              <div class="tool-name">Runtime IA</div>
              <div class="tool-desc">Statut du runtime, test de connexion et accès OpenClaw.</div>
              <div class="tool-chiprow"><span class="tool-chip">Status</span><span class="tool-chip">Test</span><span class="tool-chip">OpenClaw</span></div>
            </div>
          </a>
        </div>
      </section>
      <section>
        <div class="section-header">
          <div class="section-label">Projects</div>
        </div>
        <div id="projects-grid" class="grid-3"><button id="new-project" class="card new" type="button">+</button></div>
        <div class="project-hub" id="project-hub"></div>
      </section>
    </div>
    <div class="modal" id="modal">
      <div class="panel create-project-panel">
        <div class="create-project-head">
          <div>
            <div class="create-project-title">${escapeHtml(M.modalTitle)}</div>
            <p class="create-project-lead">${fr ? "Remplissez les champs obligatoires, le reste peut attendre." : "Required fields only; you can refine later."}</p>
          </div>
          <button class="btn modal-icon-close" id="close-modal" type="button" aria-label="${fr ? "Fermer" : "Close"}">×</button>
        </div>
        <div class="create-project-body">
          <div class="create-project-field">
            <label for="project-name">${escapeHtml(M.nameLbl)} <span class="req">*</span></label>
            <p class="field-hint">${escapeHtml(M.nameHint)}</p>
            <input id="project-name" type="text" autocomplete="off" placeholder="${fr ? "ex. Mon service API" : "e.g. My API service"}" />
          </div>
          <div class="create-project-field">
            <label for="project-description">${escapeHtml(M.descLbl)} <span class="req">*</span></label>
            <p class="field-hint">${escapeHtml(M.descHint)}</p>
            <textarea id="project-description" rows="3" placeholder="${fr ? "Décrivez l'objectif en une phrase." : "Describe the goal in one sentence."}"></textarea>
          </div>
          <div class="create-project-field">
            <label for="project-tags">${escapeHtml(M.tagsLbl)}</label>
            <p class="field-hint">${escapeHtml(M.tagsHint)}</p>
            <div id="project-tags-wrap" class="tags-wrap">
              <div id="project-tags-list" class="tags-list"></div>
              <input id="project-tags" placeholder="${fr ? "ex. api, interne…" : "e.g. api, internal…"}" />
            </div>
          </div>
          <div class="create-project-row2">
            <div class="create-project-field">
              <label for="project-template">${escapeHtml(M.stackLbl)}</label>
              <p class="field-hint">${escapeHtml(M.stackHint)}</p>
              <select id="project-template">
                <option value="python-fastapi">Python FastAPI</option>
                <option value="node-api">Node API</option>
                <option value="frontend-vite">Frontend Vite</option>
                <option value="python">Python (legacy)</option>
                <option value="vite">Vite (legacy)</option>
                <option value="nextjs">Next.js (legacy)</option>
                <option value="empty">Other</option>
              </select>
            </div>
            <div class="create-project-field">
              <label for="project-stage">${escapeHtml(M.stageLbl)}</label>
              <p class="field-hint">${escapeHtml(M.stageHint)}</p>
              <select id="project-stage"><option value="PoC">PoC</option><option value="MVP">MVP</option><option value="Production">Production</option></select>
            </div>
          </div>
          <div class="create-project-actions">
            <button id="create-project" class="btn btn-primary" type="button">${escapeHtml(M.create)}</button>
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderLogs() {
  app.innerHTML = `
    <div class="container">
      ${subpageHeader("logs")}
      <div class="logs-shell">
        <div class="logs-toolbar-bar">
          <div class="logs-toolbar">
            <select id="log-level-filter" aria-label="Level">
              <option value="">All Levels</option>
              <option value="INFO">INFO</option>
              <option value="WARN">WARN</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="DEBUG">DEBUG</option>
            </select>
            <select id="log-process-filter" aria-label="Process"><option value="">All Processes</option></select>
            <input id="log-search" type="search" placeholder="Search..." autocomplete="off" />
            <button id="log-refresh" class="btn btn-primary" type="button">Refresh</button>
            <button type="button" id="log-auto-toggle" class="logs-auto-btn">Auto: OFF</button>
          </div>
        </div>
        <div class="logs-summary" id="logs-summary">
          <span class="logs-summary-item logs-kpi-filter" data-log-level="INFO" role="button" tabindex="0" title="Filter INFO"><span class="dot green-dot" aria-hidden="true"></span>INFO<strong id="kpi-info">0</strong></span>
          <span class="logs-summary-item logs-kpi-filter" data-log-level="WARN" role="button" tabindex="0" title="Filter WARN"><span class="dot amber-dot" aria-hidden="true"></span>WARN<strong id="kpi-warn">0</strong></span>
          <span class="logs-summary-item logs-kpi-filter" data-log-level="ERROR" role="button" tabindex="0" title="Filter ERROR"><span class="dot red-dot" aria-hidden="true"></span>ERROR<strong id="kpi-error">0</strong></span>
          <span class="logs-summary-item logs-kpi-filter" data-log-level="DEBUG" role="button" tabindex="0" title="Filter DEBUG"><span class="dot purple-dot" aria-hidden="true"></span>DEBUG<strong id="kpi-debug">0</strong></span>
          <span class="logs-summary-item logs-kpi-filter" data-log-level="" role="button" tabindex="0" title="Show all"><span class="dot gray-dot" aria-hidden="true"></span>Total<strong id="kpi-total">0</strong></span>
        </div>
        <div class="logs-table-wrap">
          <table class="logs-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Level</th>
                <th>Process</th>
                <th>Model</th>
                <th>Action</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody id="logs-tbody"></tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

function renderKanbanPage() {
  const k = kanbanUi();
  app.innerHTML = `
    <div class="container">
      ${subpageHeader("kanban")}
      <div class="codir-card" id="codir-card">
        <div class="codir-header" id="codir-toggle">
          <div class="codir-title">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 9h6M9 13h4"/><circle cx="17" cy="17" r="3"/><path d="M15.5 18.5l1 1"/></svg>
            ${escapeHtml(k.codirTitle)}
            <span id="codir-proj-count" style="font-weight:400;font-size:0.72rem"></span>
          </div>
          <span id="codir-chevron" style="font-size:0.75rem;color:var(--muted)">▾</span>
        </div>
        <div class="codir-body" id="codir-body">
          <div class="codir-grid" id="codir-grid"></div>
        </div>
      </div>
      <div class="kanban-controls">
        <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;">
          <span class="view-toggle">
            <button id="view-board" class="active" type="button">${escapeHtml(k.viewBoard)}</button>
            <button id="view-gantt" type="button">${escapeHtml(k.viewGantt)}</button>
            <button id="view-graph" type="button">${escapeHtml(k.viewGraph)}</button>
          </span>
          <select id="kanban-project-filter"><option value="">${escapeHtml(k.allProjects)}</option></select>
        </div>
        <div style="display:flex;gap:0.5rem;flex-wrap:wrap;align-items:center;">
          <button id="kanban-new-task" class="btn-primary" type="button">${escapeHtml(k.newTask)}</button>
          <button id="kanban-open-archive" type="button">${escapeHtml(k.archive)}</button>
          <button id="kanban-bulk-delete-open" type="button" class="btn" style="border-color:#ef4444;color:#ef4444;margin-left:auto;">${escapeHtml(k.deleteMany)}</button>
        </div>
      </div>
      <div id="kanban-pm-meta" class="pm-meta-card" style="display:none;"></div>
      <div id="kanban-project-summary" class="project-summary" style="display:none;"></div>
      <div id="kanban-stats-bar" class="kanban-stats-bar"></div>
      <div id="kanban-board-wrap">
        <div id="kanban-board" class="kanban-board"></div>
      </div>
      <div id="kanban-gantt-wrap" class="tile" style="display:none;">
        <div class="card-title">${escapeHtml(k.ganttTitle)}</div>
        <div id="kanban-gantt" class="list"></div>
      </div>
      <div id="kanban-graph-wrap" class="tile" style="display:none;">
        <div class="card-title">${escapeHtml(k.graphTitle)}</div>
        <div id="kanban-graph" class="list"></div>
      </div>
      <div id="kanban-detail-overlay" class="modal-overlay">
        <div id="kanban-detail-modal" class="panel"></div>
      </div>
      <div id="kanban-create-overlay" class="modal-overlay">
        <div class="panel">
          <button class="modal-close" id="kanban-create-close" type="button">&times;</button>
          <h2>${escapeHtml(k.newTaskH2)}</h2>
          <div class="field">
            <label>${escapeHtml(k.fieldTitle)}</label>
            <input id="kanban-create-title" />
          </div>
          <div class="field-row">
            <div class="field">
              <label>${escapeHtml(k.fieldProject)}</label>
              <input id="kanban-create-project" />
            </div>
            <div class="field">
              <label>${escapeHtml(k.fieldPriority)}</label>
              <select id="kanban-create-priority">
                <option>Critical</option><option>High</option><option selected>Medium</option><option>Low</option>
              </select>
            </div>
          </div>
          <div class="field-row">
            <div class="field">
              <label>${escapeHtml(k.fieldEffortHours)}</label>
              <input id="kanban-create-effort" type="number" min="0" step="0.5" />
            </div>
            <div class="field">
              <label>${escapeHtml(k.fieldAssignee)}</label>
              <input id="kanban-create-assignee" value="DomBot" />
            </div>
          </div>
          <div class="field">
            <label>${escapeHtml(k.fieldDescription)}</label>
            <textarea id="kanban-create-description"></textarea>
          </div>
          <div class="modal-actions">
            <button class="btn" id="kanban-create-submit" type="button">${escapeHtml(k.createBtn)}</button>
          </div>
        </div>
      </div>
      <div id="kanban-bulk-delete-overlay" class="modal-overlay">
        <div class="panel">
          <button class="modal-close" id="kanban-bulk-delete-close" type="button">&times;</button>
          <h2>${escapeHtml(k.deleteManyTitle)}</h2>
          <p class="desc" style="margin-top:0.5rem;">${escapeHtml(k.deleteManyIntro)}</p>
          <div class="field">
            <label>${escapeHtml(k.deleteManyScope)}</label>
            <select id="kanban-bulk-delete-scope"></select>
          </div>
          <div class="modal-actions">
            <button class="btn" id="kanban-bulk-delete-cancel" type="button">${escapeHtml(k.cancel)}</button>
            <button class="btn" id="kanban-bulk-delete-confirm" type="button" style="border-color:#ef4444;color:#ef4444;">${escapeHtml(k.delete)}</button>
          </div>
        </div>
      </div>
      <div id="kanban-archive-overlay" class="modal-overlay">
        <div class="panel">
          <button class="modal-close" id="kanban-archive-close" type="button">&times;</button>
          <h2>${escapeHtml(k.archiveH2)}</h2>
          <div id="kanban-archive-content" class="list"></div>
        </div>
      </div>
    </div>
  `;
}

function renderMemoryPage() {
  const fr = settingsLocale() === "fr";
  app.innerHTML = `
    <div class="container">
      ${subpageHeader("brain")}
      <div class="graph-toolbar" style="margin-top:10px;display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
        <button id="quartz-refresh" class="btn btn-primary" type="button">${fr ? "Actualiser" : "Refresh"}</button>
        <a class="btn" href="/memory/edit">${fr ? "Modifier le Brain" : "Edit Brain"}</a>
        <div style="flex:1;"></div>
        <span class="muted" style="font-size:13px;white-space:nowrap;">${fr ? "Mémoire" : "Memory"}</span>
        <span id="brain-memory-lock" style="display:inline-flex;align-items:center;gap:6px;"></span>
        <select id="brain-memory-select" style="min-width:140px;max-width:200px;"></select>
        <span id="brain-memory-path" class="muted" style="font-size:11px;opacity:.75;max-width:420px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"></span>
      </div>
      <div id="quartz-rebuild-loading" class="brain-rebuild-loading" hidden>
        <div class="brain-rebuild-loading-label">${fr ? "Reconstruction de la prévisualisation…" : "Rebuilding preview…"}</div>
        <div class="brain-rebuild-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100"></div>
      </div>
      <iframe id="quartz-frame" class="quartz-frame" title="Quartz preview"></iframe>
    </div>
  `;
}

function renderMemoryEditPage() {
  app.innerHTML = `
    <div class="container">
      ${subpageHeader("brainEdit")}
      <div class="brain-edit-notice">
        Pour les tâches, passe par le Kanban. Seuls les <strong>.md</strong> sous <code>memory/projects/</code> sont éditables via cette page (API). Logseq web demande souvent de <strong>choisir un dossier</strong> (API fichiers du navigateur) — page vide tant qu’aucun graphe n’est ouvert. La prévisualisation Quartz liste les <strong>.html</strong> exportés dans ce même dossier.
      </div>
      <p class="brain-source-hint" id="brain-source-hint"></p>
      <div class="graph-toolbar" style="margin-top:10px;">
        <a class="btn" href="/memory/">← Retour Brain</a>
        <a class="btn" id="edit-brain-link" href="http://localhost:3099" target="_blank" rel="noreferrer">Ouvrir Logseq</a>
      </div>
      <div style="display:grid;grid-template-columns:260px 1fr;gap:10px;margin-top:10px;">
        <div>
          <select id="memory-file-select" size="12" style="width:100%;height:360px;"></select>
        </div>
        <div style="display:flex;flex-direction:column;gap:8px;">
          <input id="memory-file-name" placeholder="example-project.md" />
          <textarea id="memory-content" rows="16" placeholder="# Project" style="flex:1;"></textarea>
          <div style="display:flex;gap:8px;">
            <button id="memory-save" class="btn btn-primary" type="button">Sauvegarder</button>
            <button id="memory-refresh" class="btn" type="button">Actualiser</button>
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderSettings() {
  const t = SETTINGS_TEXT[settingsLocale()];
  const isFr = settingsLocale() === "fr";
  app.innerHTML = `
    <div class="container">
      <header class="settings-page-header">
        <div class="title">
          <h1>${t.title} · <span>Clawvis</span></h1>
          <p>${t.subtitle}</p>
        </div>
        <div class="sub-page-header-actions">
          <a href="/" class="back-btn"><span class="icon">←</span><span>${t.back}</span></a>
          <div class="locale-menu">
            <button class="header-icon icon-button" type="button" id="locale-toggle" title="${escapeHtml(t.languageTitle)}" aria-label="${escapeHtml(t.languageTitle)}" aria-expanded="false" aria-haspopup="true">🌐</button>
            <div class="locale-dropdown" id="locale-dropdown" hidden role="menu">
              <button class="locale-option" data-locale="fr" type="button" role="menuitem" title="${escapeHtml(t.languageFr)}">FR</button>
              <button class="locale-option" data-locale="en" type="button" role="menuitem" title="${escapeHtml(t.languageEn)}">EN</button>
            </div>
          </div>
          <button class="header-icon icon-button" type="button" id="theme-toggle" title="${escapeHtml(t.appearanceTitle)}" aria-label="${escapeHtml(t.appearanceTitle)}">
            <span id="theme-toggle-icon">🌙</span>
          </button>
        </div>
      </header>

      <!-- Active instance info strip -->
      <div class="settings-instance-strip" id="settings-instance-strip">
        <span class="settings-instance-strip-label">${isFr ? "Instance active" : "Active instance"}</span>
        <code class="settings-instance-strip-path" id="settings-active-instance">—</code>
        <span class="settings-instance-strip-sep">·</span>
        <span class="settings-instance-strip-label">${isFr ? "Projets" : "Projects"}</span>
        <code class="settings-instance-strip-path" id="settings-active-projects-root">—</code>
      </div>

      <!-- Health banner centré -->
      <div class="settings-health-banner">
        <div class="settings-health-banner-title">${t.healthBannerTitle}</div>
        <div class="health-grid-banner">
          <div class="health-banner-item">
            <span class="health-banner-label">${t.runtimeHealth}</span>
            <span id="health-runtime" class="health-pill warn">${t.notConfigured}</span>
          </div>
          <div class="health-banner-item">
            <span class="health-banner-label">${t.workspaceHealth}</span>
            <span id="health-workspace" class="health-pill warn">${t.notConfigured}</span>
          </div>
          <div class="health-banner-item">
            <span class="health-banner-label">${t.instancesHealth}</span>
            <span id="health-instances" class="health-pill warn">0 ${t.linked}</span>
          </div>
        </div>
      </div>

      <div class="settings-sections">
        <section class="card settings-card settings-section settings-runtime-card">
          <div class="settings-card-header">
            <div class="settings-runtime-info">
              <div class="settings-heading-row">
                <h2 class="card-title settings-section-title">${t.runtimeTitle}</h2>
                <span id="settings-runtime-status" class="ai-runtime-status-badge warn">${t.notConfigured}</span>
                <span class="settings-info-hold" tabindex="0" aria-label="${escapeHtml(t.moreInfo)}">
                  <span class="settings-info-i" aria-hidden="true">i</span>
                </span>
                <div class="settings-info-popover" role="tooltip">${escapeHtml(t.runtimeInfo)}</div>
              </div>
              <div class="card-desc">${t.runtimeDesc}</div>
              <div id="settings-active-provider" class="settings-active-provider"></div>
            </div>
            <a href="/setup/runtime/" class="btn btn-primary">${t.configureRuntime}</a>
          </div>
          <span id="provider-save-feedback" class="test-result"></span>
        </section>

        <section class="card settings-card settings-section">
          <div class="settings-heading-row">
            <h2 class="card-title settings-section-title">${t.workspaceTitle}</h2>
            <span class="settings-info-hold" tabindex="0" aria-label="${escapeHtml(t.moreInfo)}">
              <span class="settings-info-i" aria-hidden="true">i</span>
            </span>
            <div class="settings-info-popover" role="tooltip">${escapeHtml(t.workspaceInfo)}</div>
          </div>
          <div class="card-desc">${t.workspaceDesc}</div>
          <div class="settings-field-group">
            <label for="projects-root">${t.projectsRoot}</label>
            <input id="projects-root" placeholder="/home/user/lab_perso/projects" />
            <label for="instances-external-root" style="margin-top:12px;">${t.externalInstances}</label>
            <input id="instances-external-root" placeholder="~/Lab/instances" />
          </div>
          <div class="settings-actions">
            <button id="save-settings" class="btn btn-primary" type="button">${t.saveWorkspace}</button>
            <span id="settings-save-feedback" class="test-result"></span>
          </div>
        </section>

        <section class="card settings-card settings-section">
          <div class="settings-heading-row">
            <h2 class="card-title settings-section-title">${t.instancesTitle}</h2>
            <span class="settings-info-hold" tabindex="0" aria-label="${escapeHtml(t.moreInfo)}">
              <span class="settings-info-i" aria-hidden="true">i</span>
            </span>
            <div class="settings-info-popover" role="tooltip">${escapeHtml(t.instancesInfo)}</div>
          </div>
          <div class="card-desc">${t.instancesDesc}</div>
          <div class="instances-toolbar">
            <button id="refresh-instances" class="btn" type="button">${t.refreshInstances}</button>
          </div>
          <div id="instances-list" class="instances-list" role="group" aria-label="${escapeHtml(t.instancesTitle)}"></div>
        </section>

        <section class="card settings-card settings-section" id="cron-section">
          <div class="settings-heading-row">
            <h2 class="card-title settings-section-title">${isFr ? "Cron OpenClaw" : "OpenClaw Cron"}</h2>
            <span id="cron-status" class="ai-runtime-status-badge warn">${isFr ? "Chargement…" : "Loading…"}</span>
            <button id="refresh-cron" class="btn" type="button" style="margin-left:auto">${isFr ? "Actualiser" : "Refresh"}</button>
          </div>
          <div class="card-desc">${isFr ? "Tâches planifiées OpenClaw — ~/.openclaw/cron/jobs.json" : "Scheduled OpenClaw jobs — ~/.openclaw/cron/jobs.json"}</div>
          <div id="cron-table-wrap"></div>
        </section>

      </div>
    </div>
  `;
}

function renderProjectPage(projectSlug) {
  const fr = settingsLocale() === "fr";
  app.innerHTML = `
    <div class="wrap project-page-wrap" data-project-slug="${escapeHtml(projectSlug || "")}">
      ${projectPageHeader(projectSlug || "")}
      <div class="project-toolbar project-toolbar-minimal">
        <button class="btn project-header-toggle" id="project-header-toggle" type="button" aria-expanded="true" aria-controls="project-header-collapsible">${fr ? "Masquer la fiche" : "Hide sheet"}</button>
        <button class="btn btn-primary" id="project-new-task" type="button">${fr ? "+ Tâche" : "+ New task"}</button>
        <span class="project-toolbar-spacer"></span>
        <button class="btn" id="project-preview-btn" type="button">${fr ? "Aperçu Brain" : "Brain preview"}</button>
        <a class="btn btn-launch" id="project-launch-btn" href="#" target="_blank" rel="noopener" hidden>${fr ? "▶ Lancer le projet" : "▶ Launch project"}</a>
        <button class="btn" id="archive-project-btn" type="button">${fr ? "Archiver le projet" : "Archive project"}</button>
        <button class="btn" id="delete-project-btn" type="button" style="border-color:#ef4444;color:#ef4444;">${fr ? "Supprimer le projet" : "Delete project"}</button>
      </div>
      <div id="project-endpoint-bar" class="project-endpoint-bar" hidden></div>
      <div class="project-header-block" id="project-header-block">
        <div class="project-header-collapsible" id="project-header-collapsible">
          <div class="project-sheet-card tile project-sheet-top">
            <div class="hero project-hero project-hero-simple project-hero-in-sheet">
              <div class="project-hero-avatar-wrap">
                <img id="project-logo-hero" class="project-logo-hero" alt="" hidden />
                <div id="project-avatar-fallback" class="project-avatar-fallback" hidden></div>
                <input type="file" id="project-logo-file" class="visually-hidden" accept="image/png,image/jpeg,image/gif,image/webp,image/svg+xml" />
                <button type="button" class="project-logo-edit-btn" id="project-logo-edit-btn" title="${fr ? "Changer le logo" : "Change logo"}" aria-label="${fr ? "Changer le logo" : "Change logo"}">✎</button>
                <button type="button" class="project-logo-remove-btn" id="project-logo-remove-btn" hidden title="${fr ? "Retirer le logo" : "Remove logo"}" aria-label="${fr ? "Retirer le logo" : "Remove logo"}">×</button>
              </div>
              <p class="muted project-sheet-hint" style="margin:0;flex:1;font-size:12px;line-height:1.45;">${fr ? "Logo tout de suite ; textes du formulaire via « Enregistrer dans la mémoire » → fichier .md du projet." : "Logo saves immediately; form text via « Save to memory » → the project .md file."}</p>
            </div>
            <div class="project-memory-form">
              <div class="field">
                <label for="pm-description">${fr ? "Description" : "Description"}</label>
                <textarea id="pm-description" rows="2" placeholder="${fr ? "Résumé du projet" : "Project summary"}"></textarea>
              </div>
              <div class="field">
                <label for="pm-strategy">${fr ? "Vision stratégique" : "Strategic vision"}</label>
                <textarea id="pm-strategy" rows="2" placeholder="${fr ? "Direction, ambition" : "Direction, ambition"}"></textarea>
              </div>
              <div class="field">
                <label for="pm-objectives">${fr ? "Objectifs" : "Objectives"}</label>
                <textarea id="pm-objectives" rows="2" placeholder="${fr ? "Objectifs macro, jalons" : "Macro goals, milestones"}"></textarea>
              </div>
              <div class="project-memory-form-actions">
                <button class="btn btn-primary" id="project-memory-save" type="button">${fr ? "Enregistrer dans la mémoire" : "Save to memory"}</button>
                <span class="muted" id="project-memory-save-status" style="font-size:12px;"></span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div id="project-brain-preview" class="tile project-brain-preview" hidden>
        <div class="title" style="font-size:14px;margin-bottom:8px;">${fr ? "Aperçu live (HTML)" : "Live preview (HTML)"}</div>
        <iframe id="project-brain-frame" class="quartz-frame" title="Brain preview"></iframe>
      </div>
      <div id="project-details" class="project-details-shell" hidden></div>
      <div id="project-kanban" class="kanban-board"></div>
      <div id="kanban-detail-overlay" class="modal-overlay">
        <div id="kanban-detail-modal" class="panel"></div>
      </div>
      <div id="kanban-create-overlay" class="modal-overlay">
        <div class="panel">
          <button class="modal-close" id="kanban-create-close" type="button">&times;</button>
          <h2>${fr ? "Nouvelle tâche" : "New Task"}</h2>
          <div class="field">
            <label>${fr ? "Titre" : "Title"}</label>
            <input id="kanban-create-title" />
          </div>
          <div class="field-row">
            <div class="field">
              <label>${fr ? "Projet" : "Project"}</label>
              <input id="kanban-create-project" />
            </div>
            <div class="field">
              <label>${fr ? "Priorité" : "Priority"}</label>
              <select id="kanban-create-priority">
                <option>Critical</option><option>High</option><option selected>Medium</option><option>Low</option>
              </select>
            </div>
          </div>
          <div class="field-row">
            <div class="field">
              <label>${fr ? "Effort (h)" : "Effort hours"}</label>
              <input id="kanban-create-effort" type="number" min="0" step="0.5" />
            </div>
            <div class="field">
              <label>${fr ? "Assigné" : "Assignee"}</label>
              <input id="kanban-create-assignee" value="DomBot" />
            </div>
          </div>
          <div class="field">
            <label>${fr ? "Description" : "Description"}</label>
            <textarea id="kanban-create-description"></textarea>
          </div>
          <div class="modal-actions">
            <button class="btn" id="kanban-create-submit" type="button">${fr ? "Créer" : "Create"}</button>
          </div>
        </div>
      </div>
    </div>
  `;
}

function projectDevRunCommand(template, repoPath) {
  const p = (repoPath || "").replace(/\\/g, "/");
  const safe = p.replace(/'/g, "'\\''");
  const cd = `cd '${safe}'`;
  const t = (template || "").toLowerCase();
  if (t === "nextjs") return `${cd} && npm install && npm run dev`;
  if (t === "vite") return `${cd} && npm install && npm run dev`;
  if (t === "python") return `${cd} && python3 main.py`;
  return `${cd} && # ${template || "template"}: install deps, then start (see README)`;
}

const STATUSES = [
  "Backlog",
  "To Start",
  "In Progress",
  "Blocked",
  "Review",
  "Done",
];

function kanbanUi() {
  const loc = settingsLocale();
  return KANBAN_UI[loc] || KANBAN_UI.en;
}

const KANBAN_UI = {
  fr: {
    codirTitle: "Comité de direction",
    viewBoard: "Tableau",
    viewGantt: "Gantt",
    viewGraph: "Graphe",
    allProjects: "Tous les projets",
    newTask: "+ Nouvelle tâche",
    archive: "Archives",
    deleteMany: "Supprimer…",
    deleteManyTitle: "Supprimer des tâches",
    deleteManyIntro:
      "Supprime les tâches actives (non archivées). Choisis un projet ou tous les projets.",
    deleteManyScope: "Portée",
    deleteManyAllOption: "Tous les projets",
    cancel: "Annuler",
    ganttTitle: "Gantt",
    graphTitle: "Graphe des dépendances",
    newTaskH2: "Nouvelle tâche",
    fieldTitle: "Titre",
    fieldProject: "Projet",
    fieldPriority: "Priorité",
    fieldEffortHours: "Effort (heures)",
    fieldAssignee: "Assigné à",
    fieldDescription: "Description",
    createBtn: "Créer",
    archiveH2: "Archives",
    statTotal: "Total",
    statEffortLeft: "Effort restant",
    statDone: "Terminé",
    codirProjectCount: "({n} projets)",
    effortLeftH: "h restantes",
    filterProjectTitle: "Filtrer {p}",
    emptyColToStart: "Ajoutez des tâches pour l'IA ici",
    emptyColOther: "Aucune tâche",
    detailStatus: "Statut",
    detailPriority: "Priorité",
    effortLabel: "Effort (heures)",
    timelineLabel: "Échéance",
    timelinePh: "ex. S23, T2 2025",
    assigneeLabel: "Assigné à",
    assigneePh: "DomBot",
    confidenceLabel: "Confiance",
    notes: "Notes",
    save: "Enregistrer",
    split: "Diviser",
    archiveVerb: "Archiver",
    delete: "Supprimer",
    badgeYou: "vous",
    alertUpdateFailed: "Mise à jour impossible",
    alertSaveFailed: "Enregistrement impossible",
    alertSplitFailed: "Division impossible",
    alertArchiveFailed: "Archivage impossible",
    alertDeleteFailed: "Suppression impossible",
    alertMoveFailed: "Déplacement impossible",
    promptSubtaskCount: "Nombre de sous-tâches",
    promptBaseTitle: "Titre de base (optionnel)",
    bulkConfirmTitle: "Confirmer la suppression",
    taskDeleteConfirmTitle: "Êtes-vous sûr ?",
    taskDeleteConfirmMessage:
      "Supprimer cette tâche définitivement ? Elle disparaîtra du Kanban et des dépendances.",
    bulkConfirmAll:
      "Supprimer définitivement toutes les tâches actives (tous les projets) ? Cette action est irréversible.",
    bulkConfirmProject:
      "Supprimer définitivement toutes les tâches actives du projet « {p} » ? Irréversible.",
    pmMetaTitle: "Méta PM",
    visionLabel: "Vision :",
    sumTotal: "Tâches totales",
    sumDone: "Terminées",
    sumRemaining: "Restantes",
    sumEffort: "Effort",
    ganttEmpty: "Aucune tâche pour la vue Gantt.",
    graphEmpty: "Aucune dépendance à afficher.",
    graphDepends: "Dépend de :",
    createFailed: "Création impossible",
    loadingArchive: "Chargement des archives…",
    restore: "Restaurer",
    noArchived: "Aucune tâche archivée.",
    restoreFailed: "Restauration impossible",
    bulkFailed: "Suppression groupée impossible",
  },
  en: {
    codirTitle: "Steering board",
    viewBoard: "Board",
    viewGantt: "Gantt",
    viewGraph: "Graph",
    allProjects: "All projects",
    newTask: "+ New task",
    archive: "Archive",
    deleteMany: "Delete…",
    deleteManyTitle: "Delete tasks",
    deleteManyIntro:
      "Deletes active (non-archived) tasks. Pick one project or all projects.",
    deleteManyScope: "Scope",
    deleteManyAllOption: "All projects",
    cancel: "Cancel",
    ganttTitle: "Gantt",
    graphTitle: "Dependency graph",
    newTaskH2: "New task",
    fieldTitle: "Title",
    fieldProject: "Project",
    fieldPriority: "Priority",
    fieldEffortHours: "Effort hours",
    fieldAssignee: "Assignee",
    fieldDescription: "Description",
    createBtn: "Create",
    archiveH2: "Archive",
    statTotal: "Total",
    statEffortLeft: "Effort left",
    statDone: "Done",
    codirProjectCount: "({n} projects)",
    effortLeftH: "h left",
    filterProjectTitle: "Filter {p}",
    emptyColToStart: "Add tasks here for AI",
    emptyColOther: "No tasks",
    detailStatus: "Status",
    detailPriority: "Priority",
    effortLabel: "Effort (hours)",
    timelineLabel: "Timeline",
    timelinePh: "e.g. S23, Q2 2025",
    assigneeLabel: "Assignee",
    assigneePh: "DomBot",
    confidenceLabel: "Confidence",
    notes: "Notes",
    save: "Save",
    split: "Split",
    archiveVerb: "Archive",
    delete: "Delete",
    badgeYou: "you",
    alertUpdateFailed: "Update failed",
    alertSaveFailed: "Save failed",
    alertSplitFailed: "Split failed",
    alertArchiveFailed: "Archive failed",
    alertDeleteFailed: "Delete failed",
    alertMoveFailed: "Move failed",
    promptSubtaskCount: "Number of subtasks",
    promptBaseTitle: "Base title (optional)",
    bulkConfirmTitle: "Confirm deletion",
    taskDeleteConfirmTitle: "Are you sure?",
    taskDeleteConfirmMessage:
      "Delete this task permanently? It will be removed from the board and dependencies.",
    bulkConfirmAll:
      "Permanently delete all active tasks across every project? This cannot be undone.",
    bulkConfirmProject:
      'Permanently delete all active tasks for project "{p}"? This cannot be undone.',
    pmMetaTitle: "PM meta",
    visionLabel: "Vision:",
    sumTotal: "Total tasks",
    sumDone: "Done",
    sumRemaining: "Remaining",
    sumEffort: "Effort",
    ganttEmpty: "No tasks for Gantt view.",
    graphEmpty: "No dependencies to display.",
    graphDepends: "Depends on:",
    createFailed: "Create failed",
    loadingArchive: "Loading archive…",
    restore: "Restore",
    noArchived: "No archived tasks.",
    restoreFailed: "Restore failed",
    bulkFailed: "Bulk delete failed",
  },
};

function updateKanbanOverview(tasks) {
  const k = kanbanUi();
  const total = tasks.length;
  const byStatus = {};
  let effortRemaining = 0;
  STATUSES.forEach((s) => (byStatus[s] = 0));
  tasks.forEach((t) => {
    if (byStatus[t.status] !== undefined) byStatus[t.status]++;
    if (t.status !== "Done") effortRemaining += Number(t.effort_hours || 0);
  });
  const done = byStatus["Done"] || 0;
  const pct = total ? Math.round((done / total) * 100) : 0;

  const bar = document.getElementById("kanban-stats-bar");
  if (bar) {
    bar.innerHTML = [
      `<span class="stat-item"><span>${escapeHtml(k.statTotal)}</span><span>${total}</span></span>`,
      ...STATUSES.map(
        (s) =>
          `<span class="stat-item"><span>${escapeHtml(s)}</span><span>${byStatus[s] || 0}</span></span>`,
      ),
      `<span class="stat-item"><span>${escapeHtml(k.statEffortLeft)}</span><span>${effortRemaining.toFixed(1)}h</span></span>`,
      `<span class="stat-item"><span>${escapeHtml(k.statDone)}</span><span>${pct}%</span></span>`,
    ].join("");
  }

  renderCoDirBoard(tasks);
}

let codirOpen = true;

function renderCoDirBoard(tasks) {
  const k = kanbanUi();
  const grid = document.getElementById("codir-grid");
  if (!grid) return;
  const allProjects = [
    ...new Set(tasks.map((t) => t.project).filter(Boolean)),
  ].sort();
  const countEl = document.getElementById("codir-proj-count");
  if (countEl)
    countEl.textContent = k.codirProjectCount.replace(
      "{n}",
      String(allProjects.length),
    );

  grid.innerHTML = "";
  allProjects.forEach((proj, idx) => {
    const projTasks = tasks.filter((t) => t.project === proj);
    const t = projTasks.length;
    const byS = {};
    let effort = 0,
      confSum = 0,
      confN = 0;
    projTasks.forEach((tk) => {
      byS[tk.status] = (byS[tk.status] || 0) + 1;
      effort += Number(tk.effort_hours || 0);
      if (tk.confidence != null) {
        confSum += tk.confidence;
        confN++;
      }
    });
    const d = byS["Done"] || 0,
      rv = byS["Review"] || 0,
      ip = byS["In Progress"] || 0;
    const bl = byS["Blocked"] || 0,
      ts = (byS["To Start"] || 0) + (byS["Backlog"] || 0);
    const pcDone = t ? Math.round((d / t) * 100) : 0;
    const pctColor =
      pcDone >= 75 ? "#22c55e" : pcDone >= 40 ? "#f59e0b" : "var(--muted)";
    const avgConf = confN ? (confSum / confN).toFixed(2) : null;
    const effortLeft = projTasks
      .filter((tk) => tk.status !== "Done")
      .reduce((s, tk) => s + Number(tk.effort_hours || 0), 0);

    const barParts = [
      { cls: "codir-bar-done", n: d },
      { cls: "codir-bar-review", n: rv },
      { cls: "codir-bar-progress", n: ip },
      { cls: "codir-bar-blocked", n: bl },
      { cls: "codir-bar-start", n: ts },
    ]
      .filter((x) => x.n > 0)
      .map((x) => `<div class="${x.cls}" style="flex:${x.n}"></div>`)
      .join("");

    const metaParts = [
      d ? `<span>✅ <strong>${d}</strong></span>` : "",
      ip ? `<span>🔨 <strong>${ip}</strong></span>` : "",
      rv ? `<span>👀 <strong>${rv}</strong></span>` : "",
      bl ? `<span>⛔ <strong>${bl}</strong></span>` : "",
      ts ? `<span>📥 <strong>${ts}</strong></span>` : "",
      `<span style="color:var(--muted)">/ ${t}</span>`,
      effortLeft
        ? `<span>⏱ ${effortLeft.toFixed(0)}${escapeHtml(k.effortLeftH)}</span>`
        : "",
      avgConf ? `<span>🎯 ${avgConf}</span>` : "",
    ]
      .filter(Boolean)
      .join("");

    grid.innerHTML += `
      <div class="codir-proj">
        <div class="codir-proj-header">
          <span class="codir-proj-num">#${idx + 1}</span>
          <span class="codir-proj-name" data-codir-proj="${escapeHtml(proj)}" title="${escapeHtml(k.filterProjectTitle.replace("{p}", proj))}">${escapeHtml(proj)}</span>
          <span class="codir-proj-pct" style="color:${pctColor}">${pcDone}%</span>
        </div>
        <div class="codir-bar">${barParts || '<div class="codir-bar-start" style="flex:1"></div>'}</div>
        <div class="codir-proj-meta">${metaParts}</div>
      </div>`;
  });
}

function createKanbanBoard(
  tasks,
  target,
  projectSlug = null,
  onChanged = null,
) {
  const k = kanbanUi();
  const colIcons = {
    Backlog: "📥",
    "To Start": "🤖",
    "In Progress": "🔨",
    Blocked: "⛔",
    Review: "👀",
    Done: "✅",
  };
  const byStatus = Object.fromEntries(STATUSES.map((s) => [s, []]));
  const byId = Object.fromEntries((tasks || []).map((t) => [t.id, t]));
  (tasks || []).forEach((task) => {
    if (byStatus[task.status]) byStatus[task.status].push(task);
  });
  target.innerHTML = "";
  STATUSES.forEach((status) => {
    const col = document.createElement("div");
    col.className = "kanban-column";
    col.dataset.status = status;
    const colTasks = byStatus[status] || [];
    col.innerHTML = `<div class="col-header"><h3>${colIcons[status] || ""} ${status}</h3><span class="col-count">${colTasks.length}</span></div>`;
    const cardsDiv = document.createElement("div");
    cardsDiv.className = "kanban-cards";
    if (!colTasks.length) {
      cardsDiv.innerHTML = `<div class="empty-col">${status === "To Start" ? escapeHtml(k.emptyColToStart) : escapeHtml(k.emptyColOther)}</div>`;
    }
    colTasks.forEach((task) => {
      const card = document.createElement("div");
      card.className = "kanban-card";
      card.draggable = true;
      card.dataset.taskId = task.id;
      let html = `<div class="kanban-card-title">${escapeHtml(task.title)}</div><div class="kanban-card-meta">`;
      if (task.project && projectSlug == null)
        html += `<span class="badge badge-project">${escapeHtml(task.project)}</span>`;
      html += `<span class="badge badge-${task.priority || "Medium"}">${escapeHtml(task.priority || "Medium")}</span>`;
      if (task.created_by === "user")
        html += `<span class="badge" style="background:rgba(99,102,241,0.1);color:var(--accent)">${escapeHtml(k.badgeYou)}</span>`;
      if (task.effort_hours)
        html += `<span class="card-effort">${task.effort_hours}h</span>`;
      html += `</div>`;
      card.innerHTML = html;
      cardsDiv.appendChild(card);
    });
    col.appendChild(cardsDiv);
    target.appendChild(col);
  });
  const overlay = document.getElementById("kanban-detail-overlay");
  const modal = document.getElementById("kanban-detail-modal");
  const PRIORITY_COLORS = {
    Critical: "var(--red)",
    High: "var(--amber)",
    Medium: "var(--blue)",
    Low: "var(--muted)",
  };
  const openDetail = (task) => {
    if (!overlay || !modal || !task) return;
    const score = Number(task.confidence ?? 0.5);
    const level = score >= 0.7 ? "high" : score >= 0.4 ? "mid" : "low";
    const priorities = ["Critical", "High", "Medium", "Low"];
    modal.innerHTML = `
      <button class="modal-close" id="kanban-detail-close" type="button">&times;</button>
      <h2>${escapeHtml(task.title || "Task")}</h2>
      <div class="detail-section-label">${escapeHtml(k.detailStatus)}</div>
      <div class="status-buttons">
        ${STATUSES.map((s) => `<button class="status-btn ${task.status === s ? "active" : ""}" data-task-id="${escapeHtml(task.id)}" data-next-status="${s}" type="button">${s}</button>`).join("")}
      </div>
      <div class="detail-section-label">${escapeHtml(k.detailPriority)}</div>
      <div class="priority-buttons">
        ${priorities.map((p) => `<button class="priority-btn ${task.priority === p ? "active" : ""}" data-priority="${p}" type="button" style="--pcolor:${PRIORITY_COLORS[p]}">${p}</button>`).join("")}
      </div>
      <div class="detail-fields-grid">
        <div class="field">
          <label>${escapeHtml(k.effortLabel)}</label>
          <input id="detail-effort" type="number" min="0" step="0.5" value="${escapeHtml(String(task.effort_hours ?? ""))}" placeholder="0.5" />
        </div>
        <div class="field">
          <label>${escapeHtml(k.timelineLabel)}</label>
          <input id="detail-timeline" type="text" value="${escapeHtml(task.timeline || "")}" placeholder="${escapeHtml(k.timelinePh)}" />
        </div>
        <div class="field">
          <label>${escapeHtml(k.assigneeLabel)}</label>
          <input id="detail-assignee" type="text" value="${escapeHtml(task.assignee || "")}" placeholder="${escapeHtml(k.assigneePh)}" />
        </div>
        <div class="field">
          <label>${escapeHtml(k.confidenceLabel)}</label>
          <span class="badge badge-conf-${level}">${score.toFixed(2)}</span>
          <span class="detail-meta-minor">${escapeHtml(task.project || "—")}</span>
        </div>
      </div>
      ${task.description ? `<div class="desc" style="margin-top:8px;">${escapeHtml(task.description)}</div>` : ""}
      <div class="field" style="margin-top:10px;">
        <label>${escapeHtml(k.notes)}</label>
        <textarea id="kanban-detail-notes">${escapeHtml(task.notes || "")}</textarea>
      </div>
      <div class="modal-actions">
        <button class="btn btn-primary" id="kanban-detail-save" type="button">${escapeHtml(k.save)}</button>
        <button class="btn" id="kanban-detail-split" type="button">${escapeHtml(k.split)}</button>
        ${task.status === "Done" ? `<button class="btn" id="kanban-detail-archive" type="button">${escapeHtml(k.archiveVerb)}</button>` : ""}
        <button class="btn" id="kanban-detail-delete" type="button" style="margin-left:auto;border-color:#ef4444;color:#ef4444;">${escapeHtml(k.delete)}</button>
      </div>
    `;
    overlay.classList.add("open");
    document
      .getElementById("kanban-detail-close")
      ?.addEventListener("click", () => overlay.classList.remove("open"));

    let selectedPriority = task.priority || "Medium";
    modal.querySelectorAll(".priority-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        selectedPriority = btn.dataset.priority;
        modal
          .querySelectorAll(".priority-btn")
          .forEach((b) =>
            b.classList.toggle(
              "active",
              b.dataset.priority === selectedPriority,
            ),
          );
      });
    });

    modal.querySelectorAll(".status-btn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const taskId = btn.dataset.taskId;
        const nextStatus = btn.dataset.nextStatus;
        const res = await fetch(
          `/api/hub/kanban/tasks/${encodeURIComponent(taskId)}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ status: nextStatus }),
          },
        );
        if (!res.ok) return alert(k.alertUpdateFailed);
        overlay.classList.remove("open");
        await reloadBoard();
      });
    });
    document
      .getElementById("kanban-detail-save")
      ?.addEventListener("click", async () => {
        const notes =
          document.getElementById("kanban-detail-notes")?.value || "";
        const effortRaw = document.getElementById("detail-effort")?.value;
        const effort_hours =
          effortRaw !== "" && effortRaw != null ? Number(effortRaw) : null;
        const timeline =
          document.getElementById("detail-timeline")?.value || null;
        const assignee =
          document.getElementById("detail-assignee")?.value || null;
        const body = { notes, priority: selectedPriority };
        if (effort_hours !== null) body.effort_hours = effort_hours;
        if (timeline) body.timeline = timeline;
        if (assignee) body.assignee = assignee;
        const res = await fetch(
          `/api/hub/kanban/tasks/${encodeURIComponent(task.id)}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          },
        );
        if (!res.ok) return alert(k.alertSaveFailed);
        overlay.classList.remove("open");
        await reloadBoard();
      });
    document
      .getElementById("kanban-detail-split")
      ?.addEventListener("click", async () => {
        const countRaw = prompt(k.promptSubtaskCount, "3");
        if (!countRaw) return;
        const count = Number(countRaw);
        if (!Number.isFinite(count) || count < 1) return;
        const base_title = prompt(k.promptBaseTitle, "") || null;
        const res = await fetch(
          `/api/hub/kanban/tasks/${encodeURIComponent(task.id)}/split`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ count, base_title }),
          },
        );
        if (!res.ok) return alert(k.alertSplitFailed);
        overlay.classList.remove("open");
        await reloadBoard();
      });
    document
      .getElementById("kanban-detail-archive")
      ?.addEventListener("click", async () => {
        const res = await fetch(
          `/api/hub/kanban/tasks/${encodeURIComponent(task.id)}/archive`,
          {
            method: "PUT",
          },
        );
        if (!res.ok) return alert(k.alertArchiveFailed);
        overlay.classList.remove("open");
        await reloadBoard();
      });
    document
      .getElementById("kanban-detail-delete")
      ?.addEventListener("click", async () => {
        const ok = await showConfirm({
          title: k.taskDeleteConfirmTitle,
          message: k.taskDeleteConfirmMessage,
          confirmLabel: k.delete,
          cancelLabel: k.cancel,
        });
        if (!ok) return;
        const res = await fetch(
          `/api/hub/kanban/tasks/${encodeURIComponent(task.id)}`,
          { method: "DELETE" },
        );
        if (!res.ok) return alert(k.alertDeleteFailed);
        overlay.classList.remove("open");
        await reloadBoard();
      });
  };
  overlay?.addEventListener("click", (e) => {
    if (e.target === overlay) overlay.classList.remove("open");
  });

  let draggedId = null;
  target.querySelectorAll(".kanban-card").forEach((card) => {
    card.addEventListener("dragstart", () => {
      draggedId = card.dataset.taskId;
      card.classList.add("dragging");
    });
    card.addEventListener("dragend", () => {
      card.classList.remove("dragging");
    });
    card.addEventListener("click", (e) => {
      if (e.target.closest(".mini-btn")) return;
      openDetail(byId[card.dataset.taskId]);
    });
  });
  target.querySelectorAll(".kanban-column").forEach((col) => {
    col.addEventListener("dragover", (e) => {
      e.preventDefault();
      col.classList.add("drag-over");
    });
    col.addEventListener("dragleave", () => col.classList.remove("drag-over"));
    col.addEventListener("drop", async (e) => {
      e.preventDefault();
      col.classList.remove("drag-over");
      if (!draggedId) return;
      const nextStatus = col.dataset.status;
      const res = await fetch(
        `/api/hub/kanban/tasks/${encodeURIComponent(draggedId)}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: nextStatus }),
        },
      );
      if (!res.ok) return alert(k.alertMoveFailed);
      draggedId = null;
      await reloadBoard();
    });
  });

  async function reloadBoard() {
    if (onChanged) {
      await onChanged();
      return;
    }
    if (projectSlug) {
      const refresh = await fetch(
        `/api/hub/kanban/tasks?project=${encodeURIComponent(projectSlug)}`,
      );
      const payload = refresh.ok ? await refresh.json() : { tasks: [] };
      createKanbanBoard(payload.tasks || [], target, projectSlug, onChanged);
      return;
    }
    const refresh = await fetch("/api/hub/kanban/tasks");
    const payload = refresh.ok ? await refresh.json() : { tasks: [] };
    const refreshedTasks = payload.tasks || [];
    updateKanbanOverview(refreshedTasks);
    createKanbanBoard(refreshedTasks, target, null, onChanged);
  }
}

async function loadProjects() {
  const grid = document.getElementById("projects-grid");
  const res = await fetch("/api/hub/kanban/hub/projects");
  if (!res.ok) {
    const fr = settingsLocale() === "fr";
    grid.insertAdjacentHTML(
      "beforeend",
      `<div class="onboarding-hint">${fr ? "Kanban API non disponible — lance <code>clawvis start</code>" : "Kanban API unavailable — run <code>clawvis start</code>"}</div>`,
    );
    return;
  }
  const data = await res.json();
  const v = Date.now();
  if (!(data.projects || []).length) {
    const fr = settingsLocale() === "fr";
    grid.insertAdjacentHTML(
      "beforeend",
      `<div class="onboarding-hint">${fr ? "Aucun projet — clique sur <strong>+</strong> pour créer le premier." : "No projects yet — click <strong>+</strong> to create your first one."}</div>`,
    );
  }
  (data.projects || []).forEach((project) => {
    const card = document.createElement("a");
    card.href = `/project/${encodeURIComponent(project.slug)}`;
    card.className = "card card-project";
    const hue = projectAvatarHue(project.slug);
    const logoBlock = project.has_logo
      ? `<div class="card-project-logo"><img src="/api/hub/kanban/hub/projects/${encodeURIComponent(project.slug)}/logo?v=${v}" alt="" loading="lazy" /></div>`
      : `<div class="card-project-logo" style="padding:0"><div class="card-project-logo-initials" style="--avatar-h:${hue}">${escapeHtml(projectInitials(project.name))}</div></div>`;
    const stage = project.stage || "PoC";
    const tmpl = (project.template || "").toLowerCase();
    const typeChip =
      tmpl && tmpl !== "empty"
        ? `<span class="card-project-type-chip">${escapeHtml(tmpl)}</span>`
        : "";
    const stageChip = `<span class="chip">${escapeHtml(stage)}</span>`;
    const userTags = (project.tags || [])
      .map((t) => `<span class="chip">${escapeHtml(t)}</span>`)
      .join("");
    const chipsRow = [typeChip, stageChip, userTags].filter(Boolean).join("");
    const main = `<div class="card-project-main"><div class="title">${escapeHtml(project.name)}</div><div class="desc">${escapeHtml(project.description || "")}</div><div class="chips" style="margin-top:6px">${chipsRow}</div></div>`;
    card.innerHTML = `<div class="card-project-row">${logoBlock}${main}</div>`;
    grid.appendChild(card);
  });
}

function wireProjectHeaderCollapse(slug) {
  const fr = settingsLocale() === "fr";
  const block = document.getElementById("project-header-block");
  const btn = document.getElementById("project-header-toggle");
  if (!block || !btn) return;
  const key = `clawvis-project-header-collapsed:${encodeURIComponent(slug)}`;
  const collapsed = localStorage.getItem(key) === "1";
  function apply(c) {
    block.classList.toggle("is-collapsed", c);
    btn.setAttribute("aria-expanded", c ? "false" : "true");
    btn.textContent = c
      ? fr
        ? "Afficher la fiche"
        : "Show sheet"
      : fr
        ? "Masquer la fiche"
        : "Hide sheet";
    localStorage.setItem(key, c ? "1" : "0");
  }
  apply(collapsed);
  btn.addEventListener("click", () =>
    apply(!block.classList.contains("is-collapsed")),
  );
}

async function wireProjectPage() {
  const slug = decodeURIComponent(
    path.replace("/project/", "").split("/")[0] || "",
  );
  if (!slug) return;
  wireProjectHeaderCollapse(slug);
  const fr = settingsLocale() === "fr";
  const [projectRes, taskRes] = await Promise.all([
    fetch(`/api/hub/kanban/hub/projects/${encodeURIComponent(slug)}`),
    fetch(`/api/hub/kanban/tasks?project=${encodeURIComponent(slug)}`),
  ]);
  const details = document.getElementById("project-details");
  if (!projectRes.ok) {
    if (details) {
      details.hidden = false;
      details.innerHTML = `<div class="title">${fr ? "Projet introuvable" : "Project not found"}</div>`;
    }
    return;
  }
  let payload = await projectRes.json();
  const tasks = taskRes.ok ? await taskRes.json() : { tasks: [] };
  let project = payload.project || {};
  if (details) {
    details.innerHTML = "";
    details.hidden = true;
  }
  document.getElementById("project-subtitle").textContent =
    project.name || slug;

  // Endpoint bar — show repo_path + run command
  // Check if project has a served app at /apps/<slug>/ and show launch button
  const launchBtn = document.getElementById("project-launch-btn");
  if (launchBtn) {
    launchBtn.href = `/apps/${encodeURIComponent(slug)}/`;
    try {
      const serveCheck = await fetch(`/apps/${encodeURIComponent(slug)}/`, {
        method: "HEAD",
        signal: AbortSignal.timeout(2000),
      });
      launchBtn.hidden = !serveCheck.ok;
    } catch (_) {
      launchBtn.hidden = true;
    }
  }

  const endpointBar = document.getElementById("project-endpoint-bar");
  if (endpointBar && project.repo_path) {
    const cmd = projectDevRunCommand(project.template, project.repo_path);
    endpointBar.hidden = false;
    endpointBar.innerHTML = `
      <span class="project-endpoint-label">${fr ? "Chemin" : "Path"}</span>
      <code class="project-endpoint-path">${escapeHtml(project.repo_path)}</code>
      <span class="project-endpoint-sep">·</span>
      <span class="project-endpoint-label">${fr ? "Lancer" : "Run"}</span>
      <code class="project-endpoint-cmd">${escapeHtml(cmd)}</code>
      <button class="btn project-endpoint-copy" type="button" title="${fr ? "Copier la commande" : "Copy run command"}" data-cmd="${escapeHtml(cmd)}">⎘</button>
    `;
    endpointBar
      .querySelector(".project-endpoint-copy")
      ?.addEventListener("click", (e) => {
        const c = e.currentTarget.dataset.cmd;
        navigator.clipboard?.writeText(c);
        e.currentTarget.textContent = "✓";
        setTimeout(() => {
          e.currentTarget.textContent = "⎘";
        }, 1500);
      });
  }
  const major = payload.major || {};
  const descEl = document.getElementById("pm-description");
  const stratEl = document.getElementById("pm-strategy");
  const objEl = document.getElementById("pm-objectives");
  if (descEl) descEl.value = major.description || "";
  if (stratEl) stratEl.value = major.strategy || "";
  if (objEl) objEl.value = major.macro_objectives || "";
  function syncProjectLogo() {
    const hero = document.getElementById("project-logo-hero");
    const fallback = document.getElementById("project-avatar-fallback");
    const removeBtn = document.getElementById("project-logo-remove-btn");
    const showImg = !!project.has_logo;
    const url = `/api/hub/kanban/hub/projects/${encodeURIComponent(slug)}/logo?t=${Date.now()}`;
    const displayName = project.name || slug;
    if (hero) {
      hero.hidden = !showImg;
      if (showImg) hero.src = url;
      else hero.removeAttribute("src");
    }
    if (fallback) {
      fallback.hidden = showImg;
      fallback.textContent = projectInitials(displayName);
      fallback.style.setProperty("--avatar-h", String(projectAvatarHue(slug)));
    }
    if (removeBtn) removeBtn.hidden = !showImg;
  }
  syncProjectLogo();
  createKanbanBoard(
    tasks.tasks || [],
    document.getElementById("project-kanban"),
    slug,
  );

  const createOverlay = document.getElementById("kanban-create-overlay");
  document.getElementById("project-new-task")?.addEventListener("click", () => {
    const projIn = document.getElementById("kanban-create-project");
    if (projIn) projIn.value = slug;
    const tIn = document.getElementById("kanban-create-title");
    if (tIn) tIn.value = "";
    createOverlay?.classList.add("open");
  });
  document
    .getElementById("kanban-create-close")
    ?.addEventListener("click", () => {
      createOverlay?.classList.remove("open");
    });
  createOverlay?.addEventListener("click", (e) => {
    if (e.target === createOverlay) createOverlay.classList.remove("open");
  });
  document
    .getElementById("kanban-create-submit")
    ?.addEventListener("click", async () => {
      const title = document
        .getElementById("kanban-create-title")
        ?.value?.trim();
      if (!title) return;
      const project =
        document.getElementById("kanban-create-project")?.value?.trim() || slug;
      const priority =
        document.getElementById("kanban-create-priority")?.value || "Medium";
      const effortRaw =
        document.getElementById("kanban-create-effort")?.value?.trim() || "";
      const assignee =
        document.getElementById("kanban-create-assignee")?.value?.trim() ||
        "DomBot";
      const description =
        document.getElementById("kanban-create-description")?.value?.trim() ||
        "";
      const effort_hours = effortRaw ? Number(effortRaw) : null;
      const res = await fetch("/api/hub/kanban/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          project,
          priority,
          effort_hours,
          assignee,
          description,
        }),
      });
      if (!res.ok) return alert(kanbanUi().createFailed);
      createOverlay?.classList.remove("open");
      const refresh = await fetch(
        `/api/hub/kanban/tasks?project=${encodeURIComponent(slug)}`,
      );
      const payload = refresh.ok ? await refresh.json() : { tasks: [] };
      createKanbanBoard(
        payload.tasks || [],
        document.getElementById("project-kanban"),
        slug,
      );
    });

  const logoInput = document.getElementById("project-logo-file");
  document
    .getElementById("project-logo-edit-btn")
    ?.addEventListener("click", () => logoInput?.click());

  async function uploadProjectLogo(file) {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch(
      `/api/hub/kanban/hub/projects/${encodeURIComponent(slug)}/logo`,
      { method: "PUT", body: fd },
    );
    if (!res.ok) {
      let msg = fr ? "Échec envoi du logo." : "Logo upload failed.";
      try {
        const j = await res.json();
        if (j.detail) msg = typeof j.detail === "string" ? j.detail : msg;
      } catch {
        /* ignore */
      }
      alert(msg);
      return;
    }
    project = { ...project, has_logo: true };
    syncProjectLogo();
  }

  logoInput?.addEventListener("change", async () => {
    const file = logoInput.files?.[0];
    if (file) {
      await uploadProjectLogo(file);
      logoInput.value = "";
    }
  });

  document
    .getElementById("project-logo-remove-btn")
    ?.addEventListener("click", async () => {
      if (
        !confirm(
          fr ? "Retirer le logo de ce projet ?" : "Remove this project logo?",
        )
      )
        return;
      const res = await fetch(
        `/api/hub/kanban/hub/projects/${encodeURIComponent(slug)}/logo`,
        { method: "DELETE" },
      );
      if (!res.ok) return alert(fr ? "Échec." : "Failed.");
      project = { ...project, has_logo: false };
      syncProjectLogo();
    });

  async function loadBrainPreviewHtml() {
    const frame = document.getElementById("project-brain-frame");
    if (!frame) return;
    const fn = `${slug}.html`;
    const res = await fetch(`/api/hub/memory/quartz/${encodeURIComponent(fn)}`);
    const emptyMsg = fr
      ? `Aucune page ${fn}. Ouvrez le Brain pour éditer memory/projects/${slug}.md.`
      : `No ${fn} yet. Open Brain to edit memory/projects/${slug}.md.`;
    if (res.ok) {
      const data = await res.json();
      let html = (data.content || "").trim();
      if (html && !/<!DOCTYPE/i.test(html) && !/<html[\s>]/i.test(html)) {
        html = `<!DOCTYPE html><html><head><meta charset="utf-8"><base target="_blank"></head><body>${html}</body></html>`;
      }
      if (html) {
        frame.srcdoc = html;
        return;
      }
    }
    const mdRes = await fetch(
      `/api/hub/memory/projects/${encodeURIComponent(`${slug}.md`)}`,
    );
    if (mdRes.ok) {
      const mdData = await mdRes.json();
      frame.srcdoc = markdownToBrainSrcdoc(mdData.content || "");
      return;
    }
    frame.srcdoc = `<div style="font-family:system-ui,sans-serif;padding:20px;color:#9aa6cf">${emptyMsg}</div>`;
  }

  document
    .getElementById("project-memory-save")
    ?.addEventListener("click", async () => {
      const status = document.getElementById("project-memory-save-status");
      const body = {
        description: document.getElementById("pm-description")?.value ?? "",
        strategy: document.getElementById("pm-strategy")?.value ?? "",
        macro_objectives: document.getElementById("pm-objectives")?.value ?? "",
      };
      const res = await fetch(
        `/api/hub/kanban/hub/projects/${encodeURIComponent(slug)}/memory-major`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
      );
      if (!res.ok) {
        if (status)
          status.textContent = fr ? "Échec enregistrement." : "Save failed.";
        return;
      }
      payload = await res.json();
      project = payload.project || project;
      const m = payload.major || {};
      if (descEl) descEl.value = m.description || "";
      if (stratEl) stratEl.value = m.strategy || "";
      if (objEl) objEl.value = m.macro_objectives || "";
      const subt = document.getElementById("project-subtitle");
      if (subt) subt.textContent = project.name || slug;
      syncProjectLogo();
      if (status)
        status.textContent = fr ? "Mémoire à jour." : "Memory updated.";
    });

  document
    .getElementById("project-preview-btn")
    .addEventListener("click", async () => {
      const wrap = document.getElementById("project-brain-preview");
      const hidden = !wrap.hidden;
      wrap.hidden = hidden;
      if (!hidden) await loadBrainPreviewHtml();
    });
  document
    .getElementById("project-dev-btn")
    .addEventListener("click", async () => {
      const devBtn = document.getElementById("project-dev-btn");
      const cmd = projectDevRunCommand(project.template, project.repo_path);
      const label =
        devBtn?.textContent ||
        (fr ? "Copier : lancer en local" : "Copy: run locally");
      try {
        await navigator.clipboard.writeText(cmd);
        if (devBtn) {
          devBtn.textContent = fr ? "Copié" : "Copied";
          setTimeout(() => {
            devBtn.textContent = label;
          }, 1600);
        }
      } catch {
        window.prompt(fr ? "Copier la commande :" : "Copy command:", cmd);
      }
    });
  document
    .getElementById("archive-project-btn")
    .addEventListener("click", async () => {
      if (
        !confirm(
          fr
            ? "Archiver ce projet ? Le dépôt ira dans archived/ et les tâches seront archivées."
            : "Archive this project? Repo will move to archived folder and tasks will be archived.",
        )
      )
        return;
      const res = await fetch(
        `/api/hub/kanban/hub/projects/${encodeURIComponent(slug)}/archive`,
        {
          method: "POST",
        },
      );
      if (!res.ok) return alert(fr ? "Échec archivage" : "Archive failed");
      window.location.href = "/";
    });
  document
    .getElementById("delete-project-btn")
    .addEventListener("click", async () => {
      const ok = await showConfirm({
        title: fr ? "Êtes-vous sûr ?" : "Are you sure?",
        message: fr
          ? "Supprimer définitivement ce projet ? Dépôt, mémoire et tâches seront effacés."
          : "Delete this project permanently? Repo, memory file and tasks will be removed.",
        confirmLabel: fr ? "Supprimer le projet" : "Delete project",
        cancelLabel: fr ? "Annuler" : "Cancel",
      });
      if (!ok) return;
      const res = await fetch(
        `/api/hub/kanban/hub/projects/${encodeURIComponent(slug)}`,
        {
          method: "DELETE",
        },
      );
      if (!res.ok) return alert(fr ? "Échec suppression" : "Delete failed");
      window.location.href = "/";
    });
}

function splitLogMessage(raw) {
  const s = (raw || "").trim();
  if (!s) return { primary: "", meta: "" };
  const sp = s.search(/\surl=/i);
  if (sp > 0)
    return { primary: s.slice(0, sp).trim(), meta: s.slice(sp).trim() };
  const cm = s.search(/,\s*url=/i);
  if (cm > 0)
    return { primary: s.slice(0, cm).trim(), meta: s.slice(cm + 1).trim() };
  return { primary: s, meta: "" };
}

function logLevelRowClass(level) {
  const L = (level || "INFO").toUpperCase();
  if (L === "ERROR" || L === "CRITICAL") return "level-error";
  if (L === "WARN" || L === "WARNING") return "level-warn";
  if (L === "DEBUG") return "level-debug";
  return "level-info";
}

function logEntryRawTimestamp(entry) {
  const v = entry?.timestamp ?? entry?.ts ?? entry?.time ?? "";
  return typeof v === "string" ? v.trim() : "";
}

function formatLogDisplayTs(raw) {
  if (!raw) return "—";
  const pad = (n) => String(n).padStart(2, "0");
  const normalized = raw.replace(/Z$/i, "");
  const d = new Date(normalized);
  if (!Number.isNaN(d.getTime())) {
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }
  let t = raw.includes("T") ? raw.replace("T", " ") : raw;
  t = t.replace(/\.\d{3,}/, "").trim();
  if (/^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}/.test(t)) return t.slice(0, 19);
  return t.length > 19 ? t.slice(0, 19) : t;
}

async function wireLogs() {
  let allLogs = [];
  let autoTimer = null;
  let autoOn = false;
  const LS = {
    search: "logs-filter-search",
    level: "logs-filter-level",
    process: "logs-filter-process",
    auto: "logs-filter-auto-refresh",
  };
  const searchEl = document.getElementById("log-search");
  const levelEl = document.getElementById("log-level-filter");
  const processEl = document.getElementById("log-process-filter");
  const autoBtn = document.getElementById("log-auto-toggle");

  if (searchEl) searchEl.value = localStorage.getItem(LS.search) || "";
  if (levelEl) levelEl.value = localStorage.getItem(LS.level) || "";
  autoOn = localStorage.getItem(LS.auto) === "1";

  function syncAutoUi() {
    if (!autoBtn) return;
    autoBtn.textContent = autoOn ? "Auto: ON" : "Auto: OFF";
    autoBtn.classList.toggle("active", autoOn);
  }

  function populateProcessSelect() {
    if (!processEl || processEl.tagName !== "SELECT") return;
    const saved = (localStorage.getItem(LS.process) || "").trim();
    const set = new Set();
    allLogs.forEach((e) => {
      const p = (e.process || e.agent || "").trim();
      if (p) set.add(p);
    });
    const sorted = [...set].sort();
    processEl.innerHTML =
      '<option value="">All Processes</option>' +
      sorted
        .map(
          (p) => `<option value="${escapeHtml(p)}">${escapeHtml(p)}</option>`,
        )
        .join("");
    if (saved && sorted.includes(saved)) processEl.value = saved;
  }

  function renderRows(logs) {
    const tbody = document.getElementById("logs-tbody");
    if (!tbody) return;
    if (!logs.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="muted-cell">No logs yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = logs
      .slice(0, 200)
      .map((entry) => {
        const level = (entry.level || "INFO").toUpperCase();
        const proc =
          (entry.process || entry.agent || "system").trim() || "system";
        const lvlCls = logLevelRowClass(level);
        const rawMsg = entry.message || entry.msg || "";
        const { primary, meta } = splitLogMessage(rawMsg);
        const msgHtml = meta
          ? `<div class="log-msg-primary">${escapeHtml(primary)}</div><div class="log-msg-meta">${escapeHtml(meta)}</div>`
          : `<div class="log-msg-primary">${escapeHtml(primary)}</div>`;
        const rawTs = logEntryRawTimestamp(entry);
        const showTs = formatLogDisplayTs(rawTs);
        return `<tr>
          <td class="col-mono log-ts" title="${escapeHtml(rawTs || "—")}">${escapeHtml(showTs)}</td>
          <td><span class="log-level ${lvlCls}">${escapeHtml(level)}</span></td>
          <td><span class="log-process-pill">${escapeHtml(proc)}</span></td>
          <td class="col-mono log-model">${escapeHtml(entry.model || "—")}</td>
          <td class="col-mono log-action">${escapeHtml(entry.action || "—")}</td>
          <td>${msgHtml}</td>
        </tr>`;
      })
      .join("");
  }

  function applyFilters() {
    const search = (searchEl?.value || "").trim().toLowerCase();
    const level = (levelEl?.value || "").trim();
    const process = (processEl?.value || "").trim();
    localStorage.setItem(LS.search, searchEl?.value || "");
    localStorage.setItem(LS.level, levelEl?.value || "");
    localStorage.setItem(LS.process, process || "");
    const filtered = allLogs.filter((entry) => {
      const eRaw = (entry.level || "INFO").toUpperCase();
      if (level) {
        if (level === "WARN" || level === "WARNING") {
          if (eRaw !== "WARN" && eRaw !== "WARNING") return false;
        } else if (level === "ERROR") {
          if (eRaw !== "ERROR" && eRaw !== "CRITICAL") return false;
        } else if (eRaw !== level) return false;
      }
      const eProc = (entry.process || entry.agent || "").trim();
      if (process && eProc !== process) return false;
      if (!search) return true;
      const rawTs = logEntryRawTimestamp(entry);
      const haystack = [
        entry.message || entry.msg || "",
        entry.action || "",
        entry.model || "",
        entry.process || "",
        entry.agent || "",
        rawTs,
        formatLogDisplayTs(rawTs),
      ]
        .join(" ")
        .toLowerCase();
      return haystack.includes(search);
    });
    document.getElementById("kpi-total").textContent = String(allLogs.length);
    document.getElementById("kpi-info").textContent = String(
      allLogs.filter((l) => (l.level || "INFO").toUpperCase() === "INFO")
        .length,
    );
    document.getElementById("kpi-warn").textContent = String(
      allLogs.filter((l) => {
        const x = (l.level || "INFO").toUpperCase();
        return x === "WARN" || x === "WARNING";
      }).length,
    );
    document.getElementById("kpi-error").textContent = String(
      allLogs.filter((l) => {
        const x = (l.level || "INFO").toUpperCase();
        return x === "ERROR" || x === "CRITICAL";
      }).length,
    );
    const kd = document.getElementById("kpi-debug");
    if (kd)
      kd.textContent = String(
        allLogs.filter((l) => (l.level || "INFO").toUpperCase() === "DEBUG")
          .length,
      );
    renderRows(filtered);
  }

  async function refreshLogs() {
    const url = "/api/hub/kanban/logs?limit=400";
    const res = await fetch(url);
    const data = res.ok ? await res.json() : { logs: [] };
    allLogs = data.logs || [];
    populateProcessSelect();
    applyFilters();
  }

  document.getElementById("log-refresh").addEventListener("click", refreshLogs);
  searchEl?.addEventListener("input", applyFilters);
  levelEl?.addEventListener("change", applyFilters);
  processEl?.addEventListener("change", applyFilters);

  const summaryEl = document.getElementById("logs-summary");
  summaryEl?.addEventListener("click", (e) => {
    const row = e.target.closest(".logs-kpi-filter");
    if (!row || !levelEl) return;
    levelEl.value = row.dataset.logLevel ?? "";
    applyFilters();
  });
  summaryEl?.addEventListener("keydown", (e) => {
    if (e.key !== "Enter" && e.key !== " ") return;
    const row = e.target.closest(".logs-kpi-filter");
    if (!row || !levelEl) return;
    e.preventDefault();
    levelEl.value = row.dataset.logLevel ?? "";
    applyFilters();
  });

  syncAutoUi();
  autoBtn?.addEventListener("click", () => {
    autoOn = !autoOn;
    localStorage.setItem(LS.auto, autoOn ? "1" : "0");
    syncAutoUi();
    if (autoTimer) {
      clearInterval(autoTimer);
      autoTimer = null;
    }
    if (autoOn) autoTimer = setInterval(refreshLogs, 10000);
  });
  if (autoOn) autoTimer = setInterval(refreshLogs, 10000);

  await refreshLogs();
}

async function wireKanbanPage() {
  let allTasks = [];
  let meta = {};
  let view = "board";
  let projectFilter = "";
  const boardWrap = document.getElementById("kanban-board-wrap");
  const ganttWrap = document.getElementById("kanban-gantt-wrap");
  const graphWrap = document.getElementById("kanban-graph-wrap");
  const boardTarget = document.getElementById("kanban-board");
  const ganttTarget = document.getElementById("kanban-gantt");
  const graphTarget = document.getElementById("kanban-graph");
  const filterSel = document.getElementById("kanban-project-filter");

  const createOverlay = document.getElementById("kanban-create-overlay");
  const archiveOverlay = document.getElementById("kanban-archive-overlay");
  const archiveContent = document.getElementById("kanban-archive-content");

  // CoDir toggle
  document.getElementById("codir-toggle")?.addEventListener("click", () => {
    codirOpen = !codirOpen;
    const body = document.getElementById("codir-body");
    const chevron = document.getElementById("codir-chevron");
    if (body) body.style.display = codirOpen ? "" : "none";
    if (chevron) chevron.textContent = codirOpen ? "▾" : "▸";
  });

  // CoDir project click → filter
  document.getElementById("codir-grid")?.addEventListener("click", (e) => {
    const projName = e.target.closest("[data-codir-proj]");
    if (!projName || !filterSel) return;
    const proj = projName.dataset.codirProj;
    filterSel.value = proj;
    projectFilter = proj;
    renderCurrent();
    boardTarget?.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  function filteredTasks() {
    return projectFilter
      ? allTasks.filter((t) => (t.project || "") === projectFilter)
      : allTasks;
  }

  function renderMetaCard() {
    const k = kanbanUi();
    const host = document.getElementById("kanban-pm-meta");
    if (!host) return;
    const hasDescription = !!(meta.description || "").trim();
    const hasVision = !!(meta.vision || "").trim();
    const hasLinks = Array.isArray(meta.pr_links) && meta.pr_links.length > 0;
    if (!hasDescription && !hasVision && !hasLinks) {
      host.style.display = "none";
      host.innerHTML = "";
      return;
    }
    host.style.display = "";
    host.innerHTML = `
      <div class="card-title">${escapeHtml(k.pmMetaTitle)}</div>
      <div class="desc">${escapeHtml(meta.description || "")}</div>
      ${meta.vision ? `<div class="desc" style="margin-top:6px;"><strong>${escapeHtml(k.visionLabel)}</strong> ${escapeHtml(meta.vision)}</div>` : ""}
      ${Array.isArray(meta.pr_links) && meta.pr_links.length ? `<div class="chips">${meta.pr_links.map((l) => `<a class="chip" href="${escapeHtml(l)}" target="_blank" rel="noreferrer">PR</a>`).join("")}</div>` : ""}
    `;
  }

  function renderProjectSummary(tasks) {
    const k = kanbanUi();
    const box = document.getElementById("kanban-project-summary");
    if (!box) return;
    if (!projectFilter || !tasks.length) {
      box.style.display = "none";
      box.innerHTML = "";
      return;
    }
    const total = tasks.length;
    const done = tasks.filter((t) => t.status === "Done").length;
    const remaining = total - done;
    const effort = tasks.reduce((s, t) => s + Number(t.effort_hours || 0), 0);
    box.style.display = "flex";
    box.innerHTML = `
      <div style="font-weight:600;font-size:0.9rem;">${escapeHtml(projectFilter)}</div>
      <div style="display:flex;flex-wrap:wrap;gap:0.75rem;font-size:0.78rem;">
        <span>${escapeHtml(k.sumTotal)}: <strong>${total}</strong></span>
        <span>${escapeHtml(k.sumDone)}: <strong>${done}</strong></span>
        <span>${escapeHtml(k.sumRemaining)}: <strong>${remaining}</strong></span>
        <span>${escapeHtml(k.sumEffort)}: <strong>${effort.toFixed(1)}h</strong></span>
      </div>
    `;
  }

  function syncViewButtons() {
    document
      .getElementById("view-board")
      ?.classList.toggle("active", view === "board");
    document
      .getElementById("view-gantt")
      ?.classList.toggle("active", view === "gantt");
    document
      .getElementById("view-graph")
      ?.classList.toggle("active", view === "graph");
    if (boardWrap) boardWrap.style.display = view === "board" ? "" : "none";
    if (ganttWrap) ganttWrap.style.display = view === "gantt" ? "" : "none";
    if (graphWrap) graphWrap.style.display = view === "graph" ? "" : "none";
  }

  function renderGantt(tasks) {
    const k = kanbanUi();
    if (!ganttTarget) return;
    const rows = tasks
      .map((t) => {
        const effort = Number(t.effort_hours || 0);
        const width = Math.max(8, Math.min(100, effort * 12));
        return `<div class="task">
          <div style="display:flex;justify-content:space-between;gap:8px;">
            <strong>${escapeHtml(t.title || t.id)}</strong>
            <span class="chip">${escapeHtml(t.status || "")}</span>
          </div>
          <div class="progress-bar" style="margin-top:6px;"><div class="progress-fill" style="width:${width}%"></div></div>
        </div>`;
      })
      .join("");
    ganttTarget.innerHTML =
      rows || `<div class="task">${escapeHtml(k.ganttEmpty)}</div>`;
  }

  function renderGraph(tasks) {
    const k = kanbanUi();
    if (!graphTarget) return;
    const rows = tasks
      .filter((t) => (t.dependencies || []).length)
      .map(
        (t) =>
          `<div class="task"><strong>${escapeHtml(t.title || t.id)}</strong><div class="desc">${escapeHtml(k.graphDepends)} ${escapeHtml((t.dependencies || []).join(", "))}</div></div>`,
      )
      .join("");
    graphTarget.innerHTML =
      rows || `<div class="task">${escapeHtml(k.graphEmpty)}</div>`;
  }

  async function renderCurrent() {
    const tasks = filteredTasks();
    updateKanbanOverview(allTasks);
    renderMetaCard();
    renderProjectSummary(tasks);
    syncViewButtons();
    if (view === "board" && boardTarget) {
      createKanbanBoard(tasks, boardTarget, null, refreshAll);
    } else if (view === "gantt") {
      renderGantt(tasks);
    } else {
      renderGraph(tasks);
    }
  }

  async function refreshAll() {
    const k = kanbanUi();
    const res = await fetch("/api/hub/kanban/tasks");
    const data = res.ok ? await res.json() : { tasks: [] };
    allTasks = data.tasks || [];
    const metaRes = await fetch("/api/hub/kanban/meta");
    meta = metaRes.ok ? await metaRes.json() : {};
    if (filterSel) {
      const current = filterSel.value;
      const projects = [
        ...new Set(allTasks.map((t) => t.project).filter(Boolean)),
      ].sort();
      filterSel.innerHTML = `<option value="">${escapeHtml(k.allProjects)}</option>${projects.map((p) => `<option value="${escapeHtml(p)}">${escapeHtml(p)}</option>`).join("")}`;
      if (current && projects.includes(current)) filterSel.value = current;
      projectFilter = filterSel.value;
    }
    await renderCurrent();
  }

  document.getElementById("view-board")?.addEventListener("click", async () => {
    view = "board";
    await renderCurrent();
  });
  document.getElementById("view-gantt")?.addEventListener("click", async () => {
    view = "gantt";
    await renderCurrent();
  });
  document.getElementById("view-graph")?.addEventListener("click", async () => {
    view = "graph";
    await renderCurrent();
  });
  filterSel?.addEventListener("change", async () => {
    projectFilter = filterSel.value || "";
    await renderCurrent();
  });

  document.getElementById("kanban-new-task")?.addEventListener("click", () => {
    createOverlay?.classList.add("open");
  });
  document
    .getElementById("kanban-create-close")
    ?.addEventListener("click", () => {
      createOverlay?.classList.remove("open");
    });
  createOverlay?.addEventListener("click", (e) => {
    if (e.target === createOverlay) createOverlay.classList.remove("open");
  });
  document
    .getElementById("kanban-create-submit")
    ?.addEventListener("click", async () => {
      const title = document
        .getElementById("kanban-create-title")
        ?.value?.trim();
      if (!title) return;
      const project =
        document.getElementById("kanban-create-project")?.value?.trim() || "";
      const priority =
        document.getElementById("kanban-create-priority")?.value || "Medium";
      const effortRaw =
        document.getElementById("kanban-create-effort")?.value?.trim() || "";
      const assignee =
        document.getElementById("kanban-create-assignee")?.value?.trim() ||
        "DomBot";
      const description =
        document.getElementById("kanban-create-description")?.value?.trim() ||
        "";
      const effort_hours = effortRaw ? Number(effortRaw) : null;
      const res = await fetch("/api/hub/kanban/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          project,
          priority,
          effort_hours,
          assignee,
          description,
        }),
      });
      if (!res.ok) return alert(kanbanUi().createFailed);
      createOverlay?.classList.remove("open");
      await refreshAll();
    });

  const bulkOverlay = document.getElementById("kanban-bulk-delete-overlay");
  const bulkScope = document.getElementById("kanban-bulk-delete-scope");
  function syncBulkDeleteScopeOptions() {
    if (!bulkScope) return;
    const k = kanbanUi();
    const projects = [
      ...new Set(allTasks.map((t) => t.project).filter(Boolean)),
    ].sort();
    bulkScope.innerHTML = `<option value="__all__">${escapeHtml(k.deleteManyAllOption)}</option>${projects.map((p) => `<option value="${escapeHtml(p)}">${escapeHtml(p)}</option>`).join("")}`;
  }
  document
    .getElementById("kanban-bulk-delete-open")
    ?.addEventListener("click", () => {
      syncBulkDeleteScopeOptions();
      bulkOverlay?.classList.add("open");
    });
  document
    .getElementById("kanban-bulk-delete-close")
    ?.addEventListener("click", () => bulkOverlay?.classList.remove("open"));
  document
    .getElementById("kanban-bulk-delete-cancel")
    ?.addEventListener("click", () => bulkOverlay?.classList.remove("open"));
  bulkOverlay?.addEventListener("click", (e) => {
    if (e.target === bulkOverlay) bulkOverlay.classList.remove("open");
  });
  document
    .getElementById("kanban-bulk-delete-confirm")
    ?.addEventListener("click", async () => {
      const k = kanbanUi();
      const v = bulkScope?.value;
      if (!v) return;
      const isAll = v === "__all__";
      const msg = isAll
        ? k.bulkConfirmAll
        : k.bulkConfirmProject.replace("{p}", v);
      const ok = await showConfirm({
        title: k.bulkConfirmTitle,
        message: msg,
        confirmLabel: k.delete,
        cancelLabel: k.cancel,
      });
      if (!ok) return;
      const url = isAll
        ? "/api/hub/kanban/tasks/bulk"
        : `/api/hub/kanban/tasks/bulk?project=${encodeURIComponent(v)}`;
      const res = await fetch(url, { method: "DELETE" });
      if (!res.ok) return alert(k.bulkFailed);
      bulkOverlay?.classList.remove("open");
      await refreshAll();
    });

  document
    .getElementById("kanban-open-archive")
    ?.addEventListener("click", async () => {
      const k = kanbanUi();
      archiveOverlay?.classList.add("open");
      if (!archiveContent) return;
      archiveContent.innerHTML = `<div class="task">${escapeHtml(k.loadingArchive)}</div>`;
      const res = await fetch("/api/hub/kanban/tasks/archive");
      const data = res.ok ? await res.json() : { tasks: [] };
      const archived = data.tasks || [];
      archiveContent.innerHTML =
        archived
          .map(
            (t) => `<div class="task">
            <div style="display:flex;justify-content:space-between;gap:8px;">
              <strong>${escapeHtml(t.title || t.id)}</strong>
              <button class="btn" data-restore-task="${escapeHtml(t.id)}" type="button">${escapeHtml(k.restore)}</button>
            </div>
            <div class="desc">${escapeHtml(t.project || "")}</div>
          </div>`,
          )
          .join("") || `<div class="task">${escapeHtml(k.noArchived)}</div>`;
      archiveContent.querySelectorAll("[data-restore-task]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const taskId = btn.dataset.restoreTask;
          const resp = await fetch(
            `/api/hub/kanban/tasks/${encodeURIComponent(taskId)}/restore`,
            {
              method: "PUT",
            },
          );
          if (!resp.ok) return alert(k.restoreFailed);
          await refreshAll();
          btn.closest(".task")?.remove();
        });
      });
    });
  document
    .getElementById("kanban-archive-close")
    ?.addEventListener("click", () => {
      archiveOverlay?.classList.remove("open");
    });
  archiveOverlay?.addEventListener("click", (e) => {
    if (e.target === archiveOverlay) archiveOverlay.classList.remove("open");
  });

  // Keyboard shortcut: 'n' to open new task
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      createOverlay?.classList.remove("open");
      archiveOverlay?.classList.remove("open");
      bulkOverlay?.classList.remove("open");
      document
        .getElementById("kanban-detail-overlay")
        ?.classList.remove("open");
    }
    if (
      e.key === "n" &&
      !e.ctrlKey &&
      !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement?.tagName)
    ) {
      createOverlay?.classList.add("open");
    }
  });

  await refreshAll();
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
      const res = await fetch("/api/hub/kanban/hub/projects", {
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
  const loc = settingsLocale();
  const t = SETTINGS_TEXT[loc];

  // AI Runtime banner — checks localStorage AND backend agent config
  async function refreshRuntimeBanner() {
    const statusEl = document.getElementById("ai-runtime-status");
    const labelEl = document.getElementById("ai-runtime-provider-label");
    const ctaEl = document.getElementById("ai-runtime-cta");
    if (!statusEl) return;
    const provider = localStorage.getItem("ai-provider") || "claude";
    const localConfigured =
      (provider === "claude" && !!localStorage.getItem("ai-claude-key")) ||
      (provider === "mistral" && !!localStorage.getItem("ai-mistral-key")) ||
      (provider === "openclaw" && !!localStorage.getItem("ai-openclaw-url"));

    // Also check if backend has a working provider (anthropic, mammouth, or openclaw)
    let backendConfigured = false;
    let backendProvider = null;
    try {
      const r = await fetch("/api/hub/agent/config", {
        signal: AbortSignal.timeout(3000),
      });
      if (r.ok) {
        const cfg = await r.json();
        if (cfg.anthropic_available) {
          backendConfigured = true;
          backendProvider = "claude";
        } else if (cfg.mammouth_available) {
          backendConfigured = true;
          backendProvider = "mistral";
        } else if (cfg.openclaw_available) {
          backendConfigured = true;
          backendProvider = "openclaw";
        }
      }
    } catch (_) {}

    const configured = localConfigured || backendConfigured;
    const activeProvider = localConfigured ? provider : backendProvider;
    const banner = document.getElementById("ai-runtime-banner");
    const chip = document.getElementById("ai-runtime-chip");
    const chipProvider = document.getElementById("ai-runtime-chip-provider");
    const chipPanelStatus = document.getElementById(
      "ai-runtime-chip-panel-status",
    );
    const labels = {
      claude: "Claude",
      mistral: "Mistral",
      openclaw: "OpenClaw",
    };
    if (configured) {
      // Hide full banner, show compact chip
      if (banner) banner.style.display = "none";
      if (chip) chip.style.display = "inline-flex";
      const providerLabel = labels[activeProvider] || activeProvider || "IA";
      if (chipProvider) chipProvider.textContent = providerLabel;
      if (chipPanelStatus)
        chipPanelStatus.textContent = `${t.runtimeBannerConfigured} · ${providerLabel}`;
    } else {
      // Show full banner, hide chip
      if (banner) banner.style.display = "";
      if (chip) chip.style.display = "none";
      statusEl.className = "ai-runtime-status-badge warn";
      statusEl.textContent = t.runtimeBannerNotConfigured;
      if (labelEl) labelEl.textContent = "";
      if (ctaEl) ctaEl.textContent = t.runtimeBannerCta;
    }
  }
  refreshRuntimeBanner();
  window.addEventListener("storage", refreshRuntimeBanner);

  // Wire chip toggle
  const chipBtn = document.getElementById("ai-runtime-chip-btn");
  const chipPanel = document.getElementById("ai-runtime-chip-panel");
  if (chipBtn && chipPanel) {
    function closChipPanel() {
      chipPanel.style.display = "none";
      chipBtn.setAttribute("aria-expanded", "false");
      chipBtn.querySelector(".ai-runtime-chip-arrow").textContent = "▾";
    }
    chipBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = chipPanel.style.display !== "none";
      if (isOpen) {
        closChipPanel();
      } else {
        chipPanel.style.display = "block";
        chipBtn.setAttribute("aria-expanded", "true");
        chipBtn.querySelector(".ai-runtime-chip-arrow").textContent = "▴";
      }
    });
    document.addEventListener("click", (e) => {
      if (!chipBtn.contains(e.target) && !chipPanel.contains(e.target)) {
        closChipPanel();
      }
    });
    closChipPanel(); // ensure closed on init
  }

  async function loadStats() {
    try {
      const response = await fetch("/api/system.json", { cache: "no-store" });
      if (response.ok) {
        const raw = await response.json();
        const stats = raw?.system_info || raw;
        const cpu = Number(stats?.cpu_percent);
        const ram = Number(stats?.ram_percent);
        const ramUsed = Number(stats?.ram_used_gb);
        const ramTotal = Number(stats?.ram_total_gb);
        const disk = Number(stats?.disk_percent);
        const diskUsed = Number(stats?.disk_used_gb);
        const diskTotal = Number(stats?.disk_total_gb);
        if (Number.isFinite(cpu) && Number.isFinite(ram)) {
          document.getElementById("cpu-percent").textContent = `${cpu}%`;
          document.getElementById("cpu-fill").style.width =
            `${Math.min(cpu, 100)}%`;

          document.getElementById("ram-percent").textContent = `${ram}%`;
          document.getElementById("ram-fill").style.width = `${ram}%`;
          document.getElementById("ram-detail").textContent =
            Number.isFinite(ramUsed) && Number.isFinite(ramTotal)
              ? `${ramUsed} / ${ramTotal} GB`
              : "N/A";

          if (Number.isFinite(disk)) {
            document.getElementById("disk-percent").textContent = `${disk}%`;
            document.getElementById("disk-fill").style.width = `${disk}%`;
            document.getElementById("disk-detail").textContent =
              Number.isFinite(diskUsed) && Number.isFinite(diskTotal)
                ? `${diskUsed} / ${diskTotal} GB`
                : "N/A";

            const fill = document.getElementById("disk-fill");
            if (disk > 90) fill.style.background = "#ef4444";
            else if (disk > 75) fill.style.background = "#f59e0b";
          }
        }
      }
    } catch (e) {}
  }

  async function loadBusinessKpis() {
    try {
      const [projRes, tasksRes, brainRes] = await Promise.allSettled([
        fetch("/api/hub/kanban/hub/projects", { cache: "no-store" }),
        fetch("/api/hub/kanban/tasks", { cache: "no-store" }),
        fetch("/api/hub/memory/projects", { cache: "no-store" }),
      ]);

      if (projRes.status === "fulfilled" && projRes.value.ok) {
        const data = await projRes.value.json();
        const count = (data.projects || []).length;
        const el = document.getElementById("kpi-projects");
        if (el) el.textContent = String(count);
      }

      if (tasksRes.status === "fulfilled" && tasksRes.value.ok) {
        const data = await tasksRes.value.json();
        const tasks = data.tasks || [];
        const active = tasks.filter(
          (t) => !["Done", "Archived"].includes(t.status),
        ).length;
        const done = tasks.filter((t) => t.status === "Done").length;
        const elActive = document.getElementById("kpi-tasks-active");
        const elDone = document.getElementById("kpi-tasks-done");
        if (elActive) elActive.textContent = String(active);
        if (elDone) elDone.textContent = String(done);
      }

      if (brainRes.status === "fulfilled" && brainRes.value.ok) {
        const data = await brainRes.value.json();
        const notes = (data.files || []).filter((f) =>
          f.endsWith(".md"),
        ).length;
        const el = document.getElementById("kpi-brain-notes");
        if (el) el.textContent = String(notes);
      }
    } catch (e) {}
  }

  loadStats();
  loadBusinessKpis();
  setInterval(loadStats, 30000);
  setInterval(loadBusinessKpis, 60000);
}

async function wireSettings() {
  const isFr = settingsLocale() === "fr";
  const t = SETTINGS_TEXT[settingsLocale()];
  const settingsFeedback = document.getElementById("settings-save-feedback");
  const providerFeedback = document.getElementById("provider-save-feedback");
  const runtimeHealth = document.getElementById("health-runtime");
  const workspaceHealth = document.getElementById("health-workspace");
  const instancesHealth = document.getElementById("health-instances");
  const setHealth = (el, ok, text) => {
    if (!el) return;
    el.className = `health-pill ${ok ? "ok" : "warn"}`;
    el.textContent = text;
  };
  const isRuntimeConfigured = () => {
    const provider = localStorage.getItem("ai-provider") || "claude";
    return (
      (provider === "claude" && !!localStorage.getItem("ai-claude-key")) ||
      (provider === "mistral" && !!localStorage.getItem("ai-mistral-key")) ||
      (provider === "openclaw" && !!localStorage.getItem("ai-openclaw-url"))
    );
  };
  const refreshRuntimeHealth = async () => {
    let ok = isRuntimeConfigured();
    let backendProvider = null;
    // Also check backend — same logic as refreshRuntimeBanner on home page.
    // Needed when localStorage is empty but .env has ANTHROPIC_API_KEY / openclaw configured.
    if (!ok) {
      try {
        const r = await fetch("/api/hub/agent/config", {
          signal: AbortSignal.timeout(2000),
        });
        if (r.ok) {
          const cfg = await r.json();
          if (cfg.anthropic_available || cfg.mammouth_available || cfg.openclaw_available) {
            ok = true;
            backendProvider =
              cfg.preferred_provider ||
              (cfg.openclaw_available ? "openclaw" : cfg.anthropic_available ? "claude" : "mistral");
          }
        }
      } catch (_) {}
    }
    setHealth(runtimeHealth, ok, ok ? t.configured : t.notConfigured);
    const statusBadge = document.getElementById("settings-runtime-status");
    if (statusBadge) {
      statusBadge.className = `ai-runtime-status-badge ${ok ? "ok" : "warn"}`;
      statusBadge.textContent = ok ? t.configured : t.notConfigured;
    }
    const providerLbl = document.getElementById("settings-active-provider");
    if (providerLbl) {
      if (ok) {
        const p = localStorage.getItem("ai-provider") || backendProvider || "claude";
        const labels = {
          claude: "Claude (Anthropic)",
          mistral: "Mistral AI",
          openclaw: "OpenClaw",
        };
        providerLbl.textContent = labels[p] || p;
        providerLbl.style.display = "";
      } else {
        providerLbl.textContent = "";
        providerLbl.style.display = "none";
      }
    }
  };

  const refreshWorkspaceHealth = () => {
    const root = document.getElementById("projects-root")?.value?.trim() || "";
    setHealth(workspaceHealth, !!root, !!root ? t.configured : t.notConfigured);
  };

  const res = await fetch("/api/hub/memory/settings");
  if (res.ok) {
    const data = await res.json();
    document.getElementById("projects-root").value = data.projects_root || "";
    document.getElementById("instances-external-root").value =
      data.instances_external_root || "";
    // Populate active instance strip
    const activeInstanceEl = document.getElementById(
      "settings-active-instance",
    );
    const activeProjectsEl = document.getElementById(
      "settings-active-projects-root",
    );
    if (activeInstanceEl)
      activeInstanceEl.textContent = data.active_brain_memory || "—";
    if (activeProjectsEl)
      activeProjectsEl.textContent = data.projects_root || "—";
    refreshWorkspaceHealth();
  }
  document
    .getElementById("save-settings")
    .addEventListener("click", async () => {
      const projects_root = document
        .getElementById("projects-root")
        .value.trim();
      const instances_external_root = document
        .getElementById("instances-external-root")
        .value.trim();
      const save = await fetch("/api/hub/memory/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ projects_root, instances_external_root }),
      });
      if (!save.ok) {
        if (settingsFeedback) {
          settingsFeedback.className = "test-result fail";
          settingsFeedback.textContent = t.saveFailed;
          settingsFeedback.style.display = "inline-block";
        }
        return;
      }
      if (settingsFeedback) {
        settingsFeedback.className = "test-result ok";
        settingsFeedback.textContent = t.workspaceSaved;
        settingsFeedback.style.display = "inline-block";
      }
      refreshWorkspaceHealth();
    });
  let activeProvider = localStorage.getItem("ai-provider") || "claude";

  async function loadInstances() {
    const list = document.getElementById("instances-list");
    if (!list) return;
    list.innerHTML = `<div class="instances-empty">${escapeHtml(t.loadingInstances)}</div>`;
    const r = await fetch("/api/hub/memory/instances");
    if (!r.ok) {
      list.innerHTML = `<div class="instances-empty">${escapeHtml(t.loadInstancesFailed)}</div>`;
      setHealth(instancesHealth, false, `0 ${t.linked}`);
      return;
    }
    const payload = await r.json();
    const instances = payload.instances || [];
    const linkedCount = instances.filter((it) => !!it.linked).length;
    setHealth(instancesHealth, linkedCount > 0, `${linkedCount} ${t.linked}`);
    if (!instances.length) {
      list.innerHTML = `<div class="instances-empty">${escapeHtml(t.noInstances)}</div>`;
      return;
    }
    list.innerHTML = instances
      .map((it) => {
        const path = it.path || "";
        const name = it.name || "instance";
        const source = it.source || "—";
        const status = it.linked ? t.linkedStatus : t.notLinkedStatus;
        const missing = it.missing
          ? `<span class="instance-badge missing">${escapeHtml(t.missingStatus)}</span>`
          : "";
        const escPath = escapeHtml(path);
        const actionBtn = it.linked
          ? `<button type="button" class="btn instance-row-btn" data-instance-action="unlink" data-instance-path="${escPath}">${escapeHtml(t.unlink)}</button>`
          : `<button type="button" class="btn instance-row-btn" data-instance-action="link" data-instance-path="${escPath}">${escapeHtml(t.link)}</button>`;
        return `
          <div class="instance-row ${it.linked ? "linked" : ""}" data-linked="${it.linked ? "1" : "0"}">
            <span class="instance-row-main">
              <span class="instance-row-name">${escapeHtml(name)}</span>
              <span class="instance-row-meta">${escapeHtml(source)} · ${escPath}</span>
            </span>
            <span class="instance-row-badges">
              <span class="instance-badge ${it.linked ? "linked" : "unlinked"}">${escapeHtml(status)}</span>
              ${missing}
            </span>
            ${actionBtn}
          </div>
        `;
      })
      .join("");
  }

  async function applyInstanceToggle(link, pathValue) {
    if (!pathValue) return;
    const url = link
      ? "/api/hub/memory/instances/link"
      : "/api/hub/memory/instances/unlink";
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: pathValue }),
    });
    if (!res.ok) alert(t.actionFailed);
    await loadInstances();
  }

  document.getElementById("instances-list")?.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-instance-action]");
    if (!btn) return;
    const pathValue = btn.getAttribute("data-instance-path");
    const action = btn.getAttribute("data-instance-action");
    if (!pathValue || (action !== "link" && action !== "unlink")) return;
    applyInstanceToggle(action === "link", pathValue);
  });

  document
    .getElementById("refresh-instances")
    .addEventListener("click", loadInstances);
  document
    .getElementById("projects-root")
    .addEventListener("input", refreshWorkspaceHealth);
  await refreshRuntimeHealth();
  refreshWorkspaceHealth();
  await loadInstances();

  // --- Cron section ---
  async function loadCronJobs() {
    const wrap = document.getElementById("cron-table-wrap");
    const status = document.getElementById("cron-status");
    if (!wrap) return;
    try {
      const r = await fetch("/api/hub/agent/cron", {
        signal: AbortSignal.timeout(5000),
      });
      if (!r.ok) {
        if (status) {
          status.className = "ai-runtime-status-badge warn";
          status.textContent = isFr ? "Indisponible" : "Unavailable";
        }
        wrap.innerHTML = `<p class="muted" style="font-size:12px">${isFr ? "Agent service inaccessible" : "Agent service unreachable"}</p>`;
        return;
      }
      const data = await r.json();
      const jobs = data.jobs || [];
      if (status) {
        status.className = `ai-runtime-status-badge ${jobs.length ? "ok" : "warn"}`;
        status.textContent = `${jobs.length} ${isFr ? "job(s)" : "job(s)"}`;
      }
      if (!jobs.length) {
        wrap.innerHTML = `<p class="muted" style="font-size:12px">${isFr ? "Aucune tâche planifiée" : "No scheduled jobs"} — <code>${escapeHtml(data.path || "")}</code></p>`;
        return;
      }
      const rows = jobs
        .map((j) => {
          const name = escapeHtml(j.name || j.id || "—");
          const schedule = escapeHtml(j.schedule || "—");
          const enabled = j.enabled !== false;
          const lastRun = j.lastRun
            ? escapeHtml(new Date(j.lastRun).toLocaleString())
            : "—";
          const errors = j.consecutiveErrors || 0;
          const errBadge =
            errors > 0
              ? `<span class="ai-runtime-status-badge warn">${errors} err</span>`
              : "";
          const statusBadge = enabled
            ? `<span class="ai-runtime-status-badge ok">${isFr ? "actif" : "active"}</span>`
            : `<span class="ai-runtime-status-badge warn">${isFr ? "désactivé" : "disabled"}</span>`;
          return `<tr>
            <td class="cron-td">${name}</td>
            <td class="cron-td"><code>${schedule}</code></td>
            <td class="cron-td">${statusBadge} ${errBadge}</td>
            <td class="cron-td cron-td-muted">${lastRun}</td>
          </tr>`;
        })
        .join("");
      wrap.innerHTML = `
        <table class="cron-table">
          <thead><tr>
            <th class="cron-th">${isFr ? "Nom" : "Name"}</th>
            <th class="cron-th">Schedule</th>
            <th class="cron-th">Status</th>
            <th class="cron-th">${isFr ? "Dernier run" : "Last run"}</th>
          </tr></thead>
          <tbody>${rows}</tbody>
        </table>`;
    } catch (_) {
      if (status) {
        status.className = "ai-runtime-status-badge warn";
        status.textContent = isFr ? "Erreur" : "Error";
      }
      wrap.innerHTML = `<p class="muted" style="font-size:12px">${isFr ? "Erreur de chargement" : "Load error"}</p>`;
    }
  }

  document
    .getElementById("refresh-cron")
    ?.addEventListener("click", loadCronJobs);
  await loadCronJobs();
}

async function refreshBrainSourceHint() {
  const select = document.getElementById("brain-memory-select");
  const lock = document.getElementById("brain-memory-lock");
  const pathEl = document.getElementById("brain-memory-path");
  if (!select) return;
  const fr = settingsLocale() === "fr";
  try {
    const [sr, ir] = await Promise.all([
      fetch("/api/hub/memory/settings"),
      fetch("/api/hub/memory/instances"),
    ]);
    const s = sr.ok ? await sr.json() : {};
    const i = ir.ok ? await ir.json() : {};
    const active = String(s.active_brain_memory || "").trim();
    const instances = Array.isArray(i.instances) ? i.instances : [];

    function labelForMemoryPath(p) {
      const parts = String(p || "")
        .replace(/\\/g, "/")
        .split("/")
        .filter(Boolean);
      const idx = parts.lastIndexOf("memory");
      if (idx > 0) return parts[idx - 1];
      return parts[parts.length - 1] || (fr ? "Mémoire" : "Memory");
    }

    const options = instances
      .filter((it) => it && it.linked && it.has_memory && !it.missing)
      .map((it) => ({
        label: `${it.name}`,
        value: `${it.path}/memory`,
        title: `${it.path}/memory`,
      }));
    if (!options.length && active) {
      options.push({
        label: labelForMemoryPath(active),
        value: active,
        title: active,
      });
    }
    select.innerHTML = options
      .map(
        (o) =>
          `<option value="${escapeHtml(o.value)}" title="${escapeHtml(o.title || o.value)}">${escapeHtml(o.label)}</option>`,
      )
      .join("");
    if (active) select.value = active;
    if (pathEl)
      pathEl.textContent =
        select.value || active ? `(${select.value || active})` : "";
    const locked = options.length <= 1;
    select.disabled = locked;
    if (lock) {
      lock.innerHTML = locked
        ? `<span title="${fr ? "Verrouillé" : "Locked"}" style="display:inline-flex;align-items:center;gap:6px;color:var(--muted,#9aa6cf);">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true" style="opacity:.9">
              <path d="M7 11V8a5 5 0 0 1 10 0v3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              <path d="M6 11h12v10H6V11Z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            </svg>
          </span>`
        : "";
    }

    select.onchange = () => {
      if (pathEl) pathEl.textContent = select.value ? `(${select.value})` : "";
    };
  } catch {
    if (lock) lock.textContent = "";
    if (pathEl) pathEl.textContent = "";
  }
}

async function wireMemoryEditor() {
  const fr = settingsLocale() === "fr";
  const quartzFrame = document.getElementById("quartz-frame");
  const quartzRefresh = document.getElementById("quartz-refresh");
  const quartzRebuildLoading = document.getElementById(
    "quartz-rebuild-loading",
  );
  if (!quartzFrame || !quartzRefresh) return;

  let brainPreviewKind = "html";

  await refreshBrainSourceHint();

  async function loadQuartzList() {
    const res = await fetch("/api/hub/memory/quartz");
    const payload = res.ok ? await res.json() : { files: [] };
    let files = payload.files || [];
    brainPreviewKind = "html";
    if (!files.length) {
      const mres = await fetch("/api/hub/memory/projects");
      const mp = mres.ok ? await mres.json() : { files: [] };
      files = (mp.files || []).filter((f) =>
        String(f).toLowerCase().endsWith(".md"),
      );
      brainPreviewKind = "md";
    }
    if (!files.length) {
      quartzFrame.srcdoc = fr
        ? '<div style="font-family:Inter,system-ui,sans-serif;padding:20px;color:#9aa6cf">Aucune page à afficher : pas de .html ni de .md dans <code>memory/projects/</code>.</div>'
        : '<div style="font-family:Inter,system-ui,sans-serif;padding:20px;color:#9aa6cf">Nothing to show: no .html or .md in <code>memory/projects/</code>.</div>';
      return;
    }
    // No page dropdown: show "home" if present, else first item.
    const names = files.map((f) => String(f));
    const lower = names.map((f) => f.toLowerCase());
    const preferred =
      names[lower.indexOf("home.html")] ||
      names[lower.indexOf("index.html")] ||
      names[lower.indexOf("clawvis.html")] ||
      names.find((f) => !f.toLowerCase().includes("project")) ||
      names[0];
    await loadQuartzPage(preferred);
  }

  async function loadQuartzPage(filename) {
    if (!filename) {
      quartzFrame.srcdoc = fr
        ? '<div style="font-family:system-ui,sans-serif;padding:20px;color:#9aa6cf">Aucune page à afficher.</div>'
        : '<div style="font-family:system-ui,sans-serif;padding:20px;color:#9aa6cf">No page to display.</div>';
      return;
    }
    if (brainPreviewKind === "md") {
      const res = await fetch(
        `/api/hub/memory/projects/${encodeURIComponent(filename)}`,
      );
      const payload = res.ok ? await res.json() : { content: "" };
      const text = (payload.content || "").trim();
      quartzFrame.srcdoc = markdownToBrainSrcdoc(text);
      return;
    }
    // Render real Quartz output via URL so CSS/JS/assets load correctly.
    quartzFrame.removeAttribute("srcdoc");
    quartzFrame.src = `/api/hub/memory/quartz-static/${encodeURIComponent(filename)}`;
  }

  quartzRefresh.addEventListener("click", async () => {
    if (quartzRebuildLoading) quartzRebuildLoading.hidden = false;
    quartzRefresh.disabled = true;
    quartzRefresh.setAttribute("aria-busy", "true");
    try {
      const res = await fetch("/api/hub/memory/brain/rebuild-static", {
        method: "POST",
      });
      let data = {};
      try {
        data = await res.json();
      } catch {
        /* ignore */
      }
      if (!res.ok || !data.ok) {
        const tail = (data.stderr || data.stdout || "").toString().slice(-600);
        const msg = data.error || data.detail || "Rebuild failed";
        alert(tail ? `${msg}\n${tail}` : msg);
        return;
      }
      await loadQuartzList();
    } finally {
      if (quartzRebuildLoading) quartzRebuildLoading.hidden = true;
      quartzRefresh.disabled = false;
      quartzRefresh.removeAttribute("aria-busy");
    }
  });
  await loadQuartzList();
}

async function wireMemoryEdit() {
  const editBrainLink = document.getElementById("edit-brain-link");
  const select = document.getElementById("memory-file-select");
  const name = document.getElementById("memory-file-name");
  const content = document.getElementById("memory-content");
  if (!editBrainLink || !select || !name || !content) return;

  editBrainLink.href = `${window.location.protocol}//${window.location.hostname}:3099`;

  await refreshBrainSourceHint();

  async function loadList() {
    const res = await fetch("/api/hub/memory/projects");
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
      `/api/hub/memory/projects/${encodeURIComponent(filename)}`,
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
    const res = await fetch("/api/hub/memory/projects", {
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

/** Parse streamed chat error tokens from agent-service (/api/hub/agent/chat) (i18n). */
function formatClawvisChatAssistantText(full, fr) {
  const t = full.trim();
  const authFr =
    "Clé API refusée ou invalide. Vérifie la variable dans .env, redémarre l’API Kanban ou Docker, puis réessaie.";
  const authEn =
    "API key rejected or invalid. Fix the key in .env, restart the Kanban API or Docker stack, then try again.";
  if (t === "[CLAWVIS:AUTH]" || t.startsWith("[CLAWVIS:AUTH]")) {
    return { text: fr ? authFr : authEn, authError: true };
  }
  const http = /^\[CLAWVIS:HTTP:(\d+)\]$/.exec(t);
  if (http) {
    return {
      text: fr
        ? `Le fournisseur a renvoyé une erreur HTTP ${http[1]}.`
        : `The provider returned HTTP ${http[1]}.`,
      authError: false,
    };
  }
  if (/^\[API error 401:/.test(t)) {
    return { text: fr ? authFr : authEn, authError: true };
  }
  return { text: full, authError: false };
}

function renderChatPage() {
  const fr = settingsLocale() === "fr";
  app.innerHTML = `
    <div class="container">
      ${subpageHeader("chat")}
      <div class="chat-shell">
        <div id="chat-status-bar" class="chat-status-bar"></div>
        <div id="chat-messages" class="chat-messages" aria-live="polite" aria-label="${fr ? "Conversation" : "Conversation"}"></div>
        <div class="chat-input-area">
          <textarea id="chat-input" class="chat-input" rows="3"
            placeholder="${fr ? "Posez une question à votre runtime IA…" : "Ask your AI runtime a question…"}"
            autocomplete="off"></textarea>
          <button id="chat-send" class="btn btn-primary chat-send-btn" type="button">
            ${fr ? "Envoyer" : "Send"}
          </button>
        </div>
        <p class="chat-hint">${fr ? "Entrée pour envoyer · Maj+Entrée pour un saut de ligne" : "Enter to send · Shift+Enter for new line"}</p>
      </div>
    </div>
  `;
}

async function wireChat() {
  const fr = settingsLocale() === "fr";
  const statusBar = document.getElementById("chat-status-bar");
  const messagesEl = document.getElementById("chat-messages");
  const input = document.getElementById("chat-input");
  const sendBtn = document.getElementById("chat-send");

  // Fetch agent config + status from backend
  try {
    const [statusRes, configRes] = await Promise.all([
      fetch("/api/hub/agent/status"),
      fetch("/api/hub/agent/config"),
    ]);
    if (statusRes.ok && configRes.ok) {
      const s = await statusRes.json();
      const cfg = await configRes.json();
      const configured = s.anthropic_configured || s.mammouth_configured;
      const providerLabels = {
        anthropic: "Claude (Anthropic)",
        mammouth: "Mammouth (Mistral)",
      };
      const modelLabel =
        s.provider === "anthropic"
          ? cfg.anthropic_model || "claude-haiku-4-5"
          : cfg.mammouth_model || "mistral-small-3.2-24b-instruct";
      const changeLink = `<a href="/settings" class="chat-setup-link">${fr ? "Changer →" : "Change →"}</a>`;
      if (statusBar) {
        statusBar.className = `chat-status-bar ${configured ? "ok" : "warn"}`;
        statusBar.innerHTML = configured
          ? `<span class="chat-status-dot ok"></span><strong>${providerLabels[s.provider] || s.provider}</strong> · <code>${modelLabel}</code> ${changeLink}`
          : `<span class="chat-status-dot warn"></span>${fr ? "Aucun provider configuré. " : "No provider configured. "}<a href="/settings" class="chat-setup-link">${fr ? "Configurer →" : "Configure →"}</a>`;
      }
    }
  } catch {
    if (statusBar)
      statusBar.innerHTML = `<span class="chat-status-dot warn"></span>${fr ? "API indisponible" : "API unavailable"}`;
  }

  const history = [];

  function addMessage(role, text, streaming = false) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble chat-bubble-${role}`;
    if (streaming) bubble.dataset.streaming = "1";
    const inner = document.createElement("div");
    inner.className = "chat-bubble-inner markdown-body";
    inner.innerHTML = marked.parse(text || "");
    bubble.appendChild(inner);
    messagesEl.appendChild(bubble);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return inner;
  }

  async function sendMessage() {
    const msg = input.value.trim();
    if (!msg) return;
    input.value = "";
    input.style.height = "";
    sendBtn.disabled = true;

    addMessage("user", msg);
    history.push({ role: "user", content: msg });

    const assistantEl = addMessage("assistant", fr ? "…" : "…", true);
    let full = "";

    try {
      const res = await fetch("/api/hub/agent/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, history: history.slice(0, -1) }),
      });
      if (!res.ok || !res.body) {
        assistantEl.textContent = fr
          ? "Erreur de communication avec l'API."
          : "Error communicating with API.";
        sendBtn.disabled = false;
        return;
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      assistantEl.textContent = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        full += chunk;
        assistantEl.innerHTML = marked.parse(full);
        messagesEl.scrollTop = messagesEl.scrollHeight;
      }
      const formatted = formatClawvisChatAssistantText(full, fr);
      assistantEl.innerHTML = marked.parse(formatted.text || "");
      history.push({ role: "assistant", content: formatted.text });
      if (formatted.authError && statusBar) {
        statusBar.className = "chat-status-bar err";
        statusBar.innerHTML = `<span class="chat-status-dot err"></span>${fr ? "Clé API refusée — vérifie .env et redémarre les services." : "API key rejected — check .env and restart services."}`;
      }
    } catch (e) {
      assistantEl.textContent = fr ? "Erreur réseau." : "Network error.";
    }
    sendBtn.disabled = false;
    input.focus();
  }

  sendBtn.addEventListener("click", sendMessage);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
  });
  input.focus();
}

const SETUP_RUNTIME_TEXT = {
  fr: {
    title: "Setup",
    subtitle: "Configure ton runtime IA en 4 étapes.",
    back: "Retour au hub",
    step1Title: "Choisir ton fournisseur",
    step1Desc:
      "Clawvis supporte plusieurs fournisseurs. Sélectionne celui que tu veux configurer.",
    step2Title: "Obtenir et entrer la clé",
    step2Desc:
      "Suis les instructions pour ton fournisseur, puis entre ta clé API.",
    step3Title: "Tester la connexion",
    step3Desc: "Vérifie que la connexion fonctionne avant de continuer.",
    step4Title: "Valide avec un message",
    step4Desc:
      "Envoie un message à ton runtime pour confirmer que tout fonctionne.",
    next: "Suivant →",
    back_btn: "← Retour",
    testBtn: "Lancer le test",
    testLoading: "Connexion en cours…",
    testOk: "Connexion réussie — ton runtime répond.",
    testErr: "Échec de connexion.",
    testErrHint: {
      claude: "Vérifie ta clé API.",
      mistral: "Vérifie ta clé API.",
      openclaw: "Vérifie l'URL et la clé.",
    },
    chatWelcome:
      "Bonjour ! Je suis ton runtime IA. Pose-moi une question pour vérifier que tout fonctionne.",
    chatPlaceholder: "Envoie un message…",
    chatSend: "Envoyer",
    finish: "Terminer →",
    providers: {
      claude: {
        name: "Claude",
        owner: "Anthropic",
        badge: "Cloud",
        desc: "Le modèle le plus capable d'Anthropic. Clé API sur console.anthropic.com.",
        link: "https://console.anthropic.com/settings/keys",
        linkLabel: "Obtenir une clé →",
        placeholder: "sk-ant-...",
      },
      mistral: {
        name: "Mistral",
        owner: "Mistral AI",
        badge: "Cloud",
        desc: "Modèle open-weight performant. Clé API sur console.mistral.ai.",
        link: "https://console.mistral.ai/api-keys",
        linkLabel: "Obtenir une clé →",
        placeholder: "...",
      },
      openclaw: {
        name: "OpenClaw",
        owner: "Auto-hébergé",
        badge: "Self-hosted",
        desc: "Instance compatible OpenAI. Renseigne l'URL de ton gateway OpenClaw (ex. http://localhost:18789). Note : le backend utilise le CLI — cette URL sert à l'identification de la session.",
        link: null,
        linkLabel: null,
        placeholder: "http://localhost:18789",
      },
    },
    securityNote:
      "La clé est stockée dans ton navigateur (localStorage). Elle n'est jamais envoyée à nos serveurs.",
  },
  en: {
    title: "Setup",
    subtitle: "Configure your AI runtime in 4 steps.",
    back: "Back to hub",
    step1Title: "Choose your provider",
    step1Desc:
      "Clawvis supports multiple providers. Select the one you want to configure.",
    step2Title: "Get and enter your key",
    step2Desc:
      "Follow the instructions for your provider, then enter your API key.",
    step3Title: "Test the connection",
    step3Desc: "Verify the connection works before continuing.",
    step4Title: "Validate with a message",
    step4Desc: "Send a message to your runtime to confirm everything works.",
    next: "Next →",
    back_btn: "← Back",
    testBtn: "Run test",
    testLoading: "Connecting…",
    testOk: "Connection successful — your runtime is responding.",
    testErr: "Connection failed.",
    testErrHint: {
      claude: "Check your API key.",
      mistral: "Check your API key.",
      openclaw: "Check the URL and key.",
    },
    chatWelcome:
      "Hello! I'm your AI runtime. Ask me a question to confirm everything is working.",
    chatPlaceholder: "Send a message…",
    chatSend: "Send",
    finish: "Finish →",
    providers: {
      claude: {
        name: "Claude",
        owner: "Anthropic",
        badge: "Cloud",
        desc: "Anthropic's most capable model. API key at console.anthropic.com.",
        link: "https://console.anthropic.com/settings/keys",
        linkLabel: "Get a key →",
        placeholder: "sk-ant-...",
      },
      mistral: {
        name: "Mistral",
        owner: "Mistral AI",
        badge: "Cloud",
        desc: "High-performance open-weight model. API key at console.mistral.ai.",
        link: "https://console.mistral.ai/api-keys",
        linkLabel: "Get a key →",
        placeholder: "...",
      },
      openclaw: {
        name: "OpenClaw",
        owner: "Self-hosted",
        badge: "Self-hosted",
        desc: "OpenAI-compatible self-hosted instance. Enter your OpenClaw gateway URL (e.g. http://localhost:18789). Note: the backend uses the CLI — this URL identifies your session.",
        link: null,
        linkLabel: null,
        placeholder: "http://localhost:18789",
      },
    },
    securityNote:
      "Your key is stored in your browser (localStorage). It is never sent to our servers.",
  },
};

function renderSetupRuntime() {
  const isFr = settingsLocale() === "fr";
  const t = SETUP_RUNTIME_TEXT[isFr ? "fr" : "en"];
  const themeLabel = SETTINGS_TEXT[settingsLocale()].appearanceTitle;
  app.innerHTML = `
    <div class="wrap">
      <header class="settings-page-header">
        <div class="title">
          <h1>${escapeHtml(t.title)} · <span>Clawvis</span></h1>
          <p>${escapeHtml(t.subtitle)}</p>
        </div>
        <div class="sub-page-header-actions">
          <a href="/" class="back-btn"><span class="icon">←</span><span>${escapeHtml(t.back)}</span></a>
          <button class="header-icon icon-button" type="button" id="theme-toggle" title="${escapeHtml(themeLabel)}" aria-label="${escapeHtml(themeLabel)}">
            <span id="theme-toggle-icon">🌙</span>
          </button>
        </div>
      </header>

      <!-- Stepper -->
      <div class="setup-stepper" id="setup-stepper" role="list" aria-label="${isFr ? "Étapes de configuration" : "Configuration steps"}">
        <div class="setup-step-circle active" id="step-circle-1" data-step="1" role="listitem" aria-label="${isFr ? "Étape 1 : Choisir ton fournisseur" : "Step 1: Choose your provider"}">1</div>
        <div class="setup-step-line" id="step-line-1" aria-hidden="true"></div>
        <div class="setup-step-circle" id="step-circle-2" data-step="2" role="listitem" aria-label="${isFr ? "Étape 2 : Entrer la clé" : "Step 2: Enter your key"}">2</div>
        <div class="setup-step-line" id="step-line-2" aria-hidden="true"></div>
        <div class="setup-step-circle" id="step-circle-3" data-step="3" role="listitem" aria-label="${isFr ? "Étape 3 : Tester la connexion" : "Step 3: Test connection"}">3</div>
        <div class="setup-step-line" id="step-line-3" aria-hidden="true"></div>
        <div class="setup-step-circle" id="step-circle-4" data-step="4" role="listitem" aria-label="${isFr ? "Étape 4 : Valider" : "Step 4: Validate"}">4</div>
      </div>

      <!-- Step 1: Choose provider -->
      <div class="setup-step" id="setup-step-1">
        <div class="setup-step-badge">1 / 4</div>
        <h2>${escapeHtml(t.step1Title)}</h2>
        <p class="setup-step-desc">${escapeHtml(t.step1Desc)}</p>
        <div class="setup-provider-cards">
          ${["claude", "mistral", "openclaw"]
            .map((pid) => {
              const p = t.providers[pid];
              return `<button class="setup-provider-card" data-provider="${pid}" type="button">
              <span class="setup-provider-icon">${pid === "claude" ? "🧠" : pid === "mistral" ? "✨" : "🐾"}</span>
              <strong>${escapeHtml(p.name)}</strong>
              <span>${escapeHtml(p.owner)}</span>
              <span class="setup-provider-badge">${escapeHtml(p.badge)}</span>
            </button>`;
            })
            .join("")}
        </div>
        <div class="setup-actions">
          <button class="btn btn-primary" id="setup-next-1" type="button" disabled>${escapeHtml(t.next)}</button>
        </div>
      </div>

      <!-- Step 2: Credentials -->
      <div class="setup-step" id="setup-step-2" style="display:none">
        <div class="setup-step-badge">2 / 4</div>
        <h2>${escapeHtml(t.step2Title)}</h2>
        <p class="setup-step-desc">${escapeHtml(t.step2Desc)}</p>
        <div id="setup-provider-detail" class="setup-provider-detail"></div>
        <p class="setup-security-note">${escapeHtml(t.securityNote)}</p>
        <div class="setup-actions">
          <button class="btn" id="setup-back-1" type="button">${escapeHtml(t.back_btn)}</button>
          <button class="btn btn-primary" id="setup-next-2" type="button" disabled>${escapeHtml(t.next)}</button>
        </div>
      </div>

      <!-- Step 3: Test -->
      <div class="setup-step" id="setup-step-3" style="display:none">
        <div class="setup-step-badge">3 / 4</div>
        <h2>${escapeHtml(t.step3Title)}</h2>
        <p class="setup-step-desc">${escapeHtml(t.step3Desc)}</p>
        <div class="setup-test-area">
          <button class="btn btn-primary" id="setup-test-btn" type="button">${escapeHtml(t.testBtn)}</button>
          <div id="setup-test-result" class="setup-test-result"></div>
        </div>
        <div class="setup-actions">
          <button class="btn" id="setup-back-2" type="button">${escapeHtml(t.back_btn)}</button>
          <button class="btn btn-primary" id="setup-next-3" type="button" disabled>${escapeHtml(t.next)}</button>
        </div>
      </div>

      <!-- Step 4: Mini-chat -->
      <div class="setup-step" id="setup-step-4" style="display:none">
        <div class="setup-step-badge">4 / 4</div>
        <h2>${escapeHtml(t.step4Title)}</h2>
        <p class="setup-step-desc">${escapeHtml(t.step4Desc)}</p>
        <div class="setup-mini-chat">
          <div class="setup-mini-chat-messages" id="setup-chat-messages">
            <div class="setup-chat-bubble assistant">${escapeHtml(t.chatWelcome)}</div>
          </div>
          <div class="setup-mini-chat-input-row">
            <textarea id="setup-chat-input" class="setup-mini-chat-input" rows="1"
              placeholder="${escapeHtml(t.chatPlaceholder)}"></textarea>
            <button class="btn" id="setup-chat-send" type="button">${escapeHtml(t.chatSend)}</button>
          </div>
        </div>
        <div class="setup-actions">
          <button class="btn" id="setup-back-3" type="button">${escapeHtml(t.back_btn)}</button>
          <button class="btn btn-primary" id="setup-finish" type="button">${escapeHtml(t.finish)}</button>
        </div>
      </div>
    </div>
  `;
}

async function wireSetupRuntime() {
  const isFr = settingsLocale() === "fr";
  const t = SETUP_RUNTIME_TEXT[isFr ? "fr" : "en"];

  // ── In-memory wizard state (not written to localStorage until "Terminer") ──
  let selectedProvider = localStorage.getItem("ai-provider") || "";
  let credKey = ""; // holds claude key or mistral key
  let credUrl = ""; // holds openclaw url

  // ── Stepper helpers ──
  const STEPS = [1, 2, 3, 4];
  function goToStep(n) {
    STEPS.forEach((s) => {
      const el = document.getElementById(`setup-step-${s}`);
      if (el) el.style.display = s === n ? "" : "none";
      const circle = document.getElementById(`step-circle-${s}`);
      if (!circle) return;
      circle.classList.remove("active", "done");
      if (s < n) circle.classList.add("done");
      else if (s === n) circle.classList.add("active");
      const line = document.getElementById(`step-line-${s}`);
      if (line) line.classList.toggle("done", s < n);
    });
    // Reset step 3 state when going back to 1 or 2
    if (n <= 2) resetStep3();
  }

  function resetStep3() {
    const result = document.getElementById("setup-test-result");
    if (result) {
      result.className = "setup-test-result";
      result.innerHTML = "";
    }
    const next3 = document.getElementById("setup-next-3");
    if (next3) next3.disabled = true;
  }

  // ── Pre-fill from localStorage if returning user ──
  // Only pre-select the provider card and enable "Next →". Do NOT touch stepper circle
  // classes here — goToStep() manages them when the user actually navigates.
  // The page always starts on step 1 (default from renderSetupRuntime).
  if (selectedProvider) {
    const card = document.querySelector(
      `[data-provider="${selectedProvider}"]`,
    );
    if (card) card.classList.add("selected");
    const next1 = document.getElementById("setup-next-1");
    if (next1) next1.disabled = false;
    // Pre-load cred values from localStorage into memory (shown in step 2 fields)
    credKey = localStorage.getItem(`ai-${selectedProvider}-key`) || "";
    credUrl = localStorage.getItem("ai-openclaw-url") || "";
  }

  // ── Stepper click-back (delegated — works for circles marked done after navigation) ──
  document.getElementById("setup-stepper").addEventListener("click", (e) => {
    const circle = e.target.closest(".setup-step-circle.done");
    if (!circle) return;
    const n = parseInt(circle.dataset.step, 10);
    if (n && n < 4) goToStep(n);
  });

  // ── Step 1: Provider selection ──
  document.querySelectorAll("[data-provider]").forEach((card) => {
    card.addEventListener("click", () => {
      document
        .querySelectorAll("[data-provider]")
        .forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");
      selectedProvider = card.dataset.provider;
      document.getElementById("setup-next-1").disabled = false;
    });
  });

  document.getElementById("setup-next-1").addEventListener("click", () => {
    renderStep2Detail();
    goToStep(2);
  });

  // ── Step 2: Render provider-specific detail and credentials ──
  function renderStep2Detail() {
    const p = t.providers[selectedProvider];
    const detail = document.getElementById("setup-provider-detail");
    if (!detail) return;

    if (selectedProvider === "openclaw") {
      detail.innerHTML = `
        <p>${escapeHtml(p.desc)}</p>
        <div class="setup-key-field">
          <input id="setup-cred-url" type="text" placeholder="${escapeHtml(p.placeholder)}"
            value="${escapeHtml(credUrl)}" autocomplete="off" />
        </div>
      `;
      const urlInput = document.getElementById("setup-cred-url");
      urlInput.addEventListener("input", () => {
        credUrl = urlInput.value.trim();
        document.getElementById("setup-next-2").disabled = !credUrl;
      });
      document.getElementById("setup-next-2").disabled = !credUrl;
    } else {
      const existingKey =
        localStorage.getItem(`ai-${selectedProvider}-key`) || credKey;
      detail.innerHTML = `
        <p>${escapeHtml(p.desc)}</p>
        ${p.link ? `<p><a href="${p.link}" target="_blank" rel="noopener">${escapeHtml(p.linkLabel)}</a></p>` : ""}
        <div class="setup-key-field">
          <input id="setup-cred-key" type="password" placeholder="${escapeHtml(p.placeholder)}"
            value="${escapeHtml(existingKey)}" autocomplete="off" />
          <button class="setup-key-toggle" id="setup-key-toggle" type="button">👁</button>
        </div>
      `;
      const keyInput = document.getElementById("setup-cred-key");
      document
        .getElementById("setup-key-toggle")
        .addEventListener("click", () => {
          keyInput.type = keyInput.type === "password" ? "text" : "password";
        });
      keyInput.addEventListener("input", () => {
        credKey = keyInput.value.trim();
        document.getElementById("setup-next-2").disabled = !credKey;
      });
      document.getElementById("setup-next-2").disabled =
        !existingKey && !credKey;
      if (existingKey) credKey = existingKey;
    }
  }

  document
    .getElementById("setup-back-1")
    .addEventListener("click", () => goToStep(1));

  document.getElementById("setup-next-2").addEventListener("click", () => {
    // Capture final credential values before advancing
    if (selectedProvider === "openclaw") {
      credUrl =
        (document.getElementById("setup-cred-url") || {}).value?.trim() ||
        credUrl;
    } else {
      credKey =
        (document.getElementById("setup-cred-key") || {}).value?.trim() ||
        credKey;
    }
    goToStep(3);
  });

  // ── Step 3: Connection test ──
  document
    .getElementById("setup-back-2")
    .addEventListener("click", () => goToStep(2));

  document
    .getElementById("setup-test-btn")
    .addEventListener("click", async () => {
      const result = document.getElementById("setup-test-result");
      const testBtn = document.getElementById("setup-test-btn");
      result.className = "setup-test-result";
      result.innerHTML = t.testLoading;
      testBtn.disabled = true;

      try {
        // ⚠️ KNOWN LIMITATION: this test validates the backend's configured key (from .env),
        // NOT the key the user just entered in the wizard. The agent service reads API keys
        // from environment only. A 200 confirms the stack is reachable with a working env key.
        // Future: pass the key in a header the agent service accepts for this request.
        const res = await fetch("/api/hub/agent/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: isFr ? "Réponds juste 'ok'." : "Just reply 'ok'.",
            history: [],
            system: "Reply with only the word 'ok'.",
          }),
        });
        if (res.ok) {
          const text = await res.text();
          const fmt = formatClawvisChatAssistantText(text, isFr);
          const trimmed = text.trim();
          if (fmt.authError || /^\[CLAWVIS:HTTP:\d+\]$/.test(trimmed)) {
            throw new Error(fmt.text);
          }
          result.className = "setup-test-result ok";
          result.innerHTML = `${escapeHtml(t.testOk)}
          <details class="setup-test-raw"><summary>${isFr ? "Réponse" : "Response"}</summary>${escapeHtml(text.slice(0, 200))}</details>`;
          document.getElementById("setup-next-3").disabled = false;
        } else {
          throw new Error(`HTTP ${res.status}`);
        }
      } catch (e) {
        result.className = "setup-test-result err";
        const hint = t.testErrHint[selectedProvider] || "";
        result.innerHTML = `${escapeHtml(t.testErr)} ${escapeHtml(hint)} <span style="opacity:.6">(${escapeHtml(String(e))})</span>`;
      }
      testBtn.disabled = false;
    });

  document
    .getElementById("setup-next-3")
    .addEventListener("click", () => goToStep(4));

  // ── Step 4: Mini-chat ──
  document
    .getElementById("setup-back-3")
    .addEventListener("click", () => goToStep(3));

  const chatMessages = document.getElementById("setup-chat-messages");
  const chatInput = document.getElementById("setup-chat-input");
  const chatSend = document.getElementById("setup-chat-send");
  const chatHistory = [];

  function addSetupBubble(role, text, streaming = false) {
    const div = document.createElement("div");
    div.className = `setup-chat-bubble ${role}`;
    div.textContent = text;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return div;
  }

  async function sendSetupMessage() {
    const msg = chatInput.value.trim();
    if (!msg) return;
    chatInput.value = "";
    chatSend.disabled = true;
    addSetupBubble("user", msg);
    chatHistory.push({ role: "user", content: msg });

    const el = addSetupBubble("assistant", "…", true);
    let full = "";
    try {
      const res = await fetch("/api/hub/agent/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: msg,
          history: chatHistory.slice(0, -1),
        }),
      });
      if (res.ok && res.body) {
        const reader = res.body.getReader();
        const dec = new TextDecoder();
        el.textContent = "";
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          full += dec.decode(value, { stream: true });
          el.textContent = full;
          chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        const sf = formatClawvisChatAssistantText(full, isFr);
        el.textContent = sf.text;
        chatHistory.push({ role: "assistant", content: sf.text });
      } else {
        el.textContent = isFr ? "Erreur." : "Error.";
      }
    } catch {
      el.textContent = isFr ? "Erreur réseau." : "Network error.";
    }
    chatSend.disabled = false;
    chatInput.focus();
  }

  chatSend.addEventListener("click", sendSetupMessage);
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendSetupMessage();
    }
  });

  // ── Finish: write to localStorage and redirect ──
  document.getElementById("setup-finish").addEventListener("click", () => {
    localStorage.setItem("ai-provider", selectedProvider);
    if (selectedProvider === "openclaw") {
      localStorage.setItem("ai-openclaw-url", credUrl);
    } else {
      localStorage.setItem(`ai-${selectedProvider}-key`, credKey);
    }
    window.location.href = "/";
  });

  // ── If returning user, land on step 1 (already pre-selected above) ──
  // (goToStep is not called here; step 1 is already visible from renderSetupRuntime)
}

async function boot() {
  if (path.startsWith("/setup/runtime")) renderSetupRuntime();
  else if (path.startsWith("/settings")) renderSettings();
  else if (path.startsWith("/logs")) renderLogs();
  else if (path.startsWith("/chat")) renderChatPage();
  else if (path.startsWith("/kanban")) renderKanbanPage();
  else if (path.startsWith("/memory/edit")) renderMemoryEditPage();
  else if (path.startsWith("/memory")) renderMemoryPage();
  else if (path.startsWith("/project/"))
    renderProjectPage(path.replace("/project/", ""));
  else renderHome();
  applyTheme(theme());
  wireActiveServicesCount();
  wireLocaleSwitcher();
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
  if (path.startsWith("/setup/runtime")) await wireSetupRuntime();
  else if (path.startsWith("/settings")) await wireSettings();
  else if (path.startsWith("/logs")) await wireLogs();
  else if (path.startsWith("/chat")) await wireChat();
  else if (path.startsWith("/kanban")) await wireKanbanPage();
  else if (path.startsWith("/memory/edit")) await wireMemoryEdit();
  else if (path.startsWith("/memory")) await wireMemoryEditor();
  else if (path.startsWith("/project/")) await wireProjectPage();
  else await wireHome();
}

function wireLocaleSwitcher() {
  const toggle = document.getElementById("locale-toggle");
  const dropdown = document.getElementById("locale-dropdown");
  if (!toggle || !dropdown) return;
  const current = settingsLocale();
  const setOpen = (open) => {
    dropdown.hidden = !open;
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
  };
  dropdown.querySelectorAll("[data-locale]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.locale === current);
    btn.addEventListener("click", (ev) => {
      ev.stopPropagation();
      const next = btn.dataset.locale;
      if (!next || next === current) {
        setOpen(false);
        return;
      }
      localStorage.setItem("clawvis-locale", next);
      window.location.reload();
    });
  });
  toggle.addEventListener("click", (e) => {
    e.stopPropagation();
    setOpen(dropdown.hidden);
  });
  document.addEventListener("click", () => {
    if (!dropdown.hidden) setOpen(false);
  });
}

boot();
