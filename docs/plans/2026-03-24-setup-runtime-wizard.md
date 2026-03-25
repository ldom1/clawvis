# Setup Runtime Wizard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the buried 3-step modal wizard in `/settings/` with a dedicated 4-step full-page wizard at `/setup/runtime/`, and migrate all `/api/kanban/` frontend calls to `/api/hub/kanban/` (and `/api/hub/chat/` for chat).

**Architecture:** Vite proxy is the only routing layer changed — backend routes stay identical. The new page is added to `hub/src/main.js` following the existing render/wire pattern. Credentials are held in memory during the wizard and written to localStorage only on final confirmation.

**Tech Stack:** Vanilla JS (ES modules), Vite 5, FastAPI (backend unchanged), `localStorage` for credential storage, `fetch` streaming for mini-chat.

**Spec:** `docs/specs/2026-03-24-agent-config-setup-runtime-design.md`

---

## File Map

| File | Action | What changes |
|------|--------|-------------|
| `hub/vite.config.js` | Modify | Replace single `/api/kanban` proxy with two entries: `/api/hub/chat` and `/api/hub/kanban` |
| `hub/src/main.js` | Modify | (1) Rename 48 fetch calls, (2) add `renderSetupRuntime` + `wireSetupRuntime`, (3) update router, (4) update home banner CTA, (5) remove settings modal, (6) update chat warn link |
| `hub/src/style.css` | Modify | Add stepper, provider-detail, live test result, inline mini-chat styles |
| `clawvis-cli/cli.mjs` | Modify | Line 466: `doneSettings` URL → `/setup/runtime/` |
| `docs/playwright-persona.md` | Modify | Rewrite Persona 1 steps 2–5, fix Persona 5 step 3, fix Persona 6 step 1 |

---

## Task 1: Migrate API proxy — `/api/kanban` → `/api/hub/kanban` + `/api/hub/chat`

**Files:**
- Modify: `hub/vite.config.js`
- Modify: `hub/src/main.js` (48 fetch call renames)

The backend routes are unchanged. Only the Vite dev proxy and the frontend fetch strings change.

- [ ] **Step 1: Verify current state**

```bash
grep -c "api/kanban" hub/src/main.js
```
Expected output: `48`

- [ ] **Step 2: Update Vite proxy config**

In `hub/vite.config.js`, replace the `proxy` block (lines 20–24):

```js
// OLD:
proxy: {
  "/api/kanban": {
    target: `http://127.0.0.1:${kanbanPort}`,
    rewrite: (p) => p.replace(/^\/api\/kanban/, ""),
  },
},

// NEW:
proxy: {
  "/api/hub/chat": {
    target: `http://127.0.0.1:${kanbanPort}`,
    rewrite: (p) => p.replace(/^\/api\/hub\/chat/, "/hub/chat"),
  },
  "/api/hub/kanban": {
    target: `http://127.0.0.1:${kanbanPort}`,
    rewrite: (p) => p.replace(/^\/api\/hub\/kanban/, ""),
  },
},
```

- [ ] **Step 3: Rename chat-specific fetch calls in main.js (2 occurrences)**

These two calls must become `/api/hub/chat`, not `/api/hub/kanban/hub/chat`:

```
/api/kanban/hub/chat/status  →  /api/hub/chat/status   (line 3247)
/api/kanban/hub/chat         →  /api/hub/chat           (line 3300)
```

Use find-and-replace to rename `/api/kanban/hub/chat` → `/api/hub/chat`.
This must be done BEFORE the bulk rename in step 4.

- [ ] **Step 4: Rename all remaining `/api/kanban/` → `/api/hub/kanban/` in main.js**

After step 3, there should be 46 remaining occurrences of `/api/kanban/`.
Replace all `/api/kanban/` → `/api/hub/kanban/`.

> **Important — preserved `hub/` segment:** routes like `/api/kanban/hub/projects` become `/api/hub/kanban/hub/projects`. This is correct: the Vite proxy strips `/api/hub/kanban`, leaving `/hub/projects` which matches the backend route. Do NOT remove the inner `hub/` segment.

- [ ] **Step 5: Verify counts**

```bash
grep -c "api/kanban" hub/src/main.js
# Expected: 0

grep -c "api/hub/chat" hub/src/main.js
# Expected: 2

grep -c "api/hub/kanban" hub/src/main.js
# Expected: 46
```

- [ ] **Step 6: Verify backend tests are unaffected**

```bash
cd kanban && uv run pytest tests/ -q
```
Expected: all tests pass (backend routes unchanged, tests use TestClient with raw paths).

- [ ] **Step 7: Verify hub build compiles**

```bash
rtk yarn --cwd hub build 2>&1 | tail -5
```
Expected: build succeeds, no JS errors.

- [ ] **Step 8: Commit**

```bash
rtk git add hub/vite.config.js hub/src/main.js
rtk git commit -m "feat(api): migrate /api/kanban to /api/hub/kanban and /api/hub/chat"
```

---

## Task 2: Add stepper and setup page CSS

**Files:**
- Modify: `hub/src/style.css` (append to end)

- [ ] **Step 1: Add styles**

Append to `hub/src/style.css`:

```css
/* ============================================================
   Setup Runtime Wizard — /setup/runtime/
   ============================================================ */

/* Stepper */
.setup-stepper {
  display: flex;
  align-items: center;
  gap: 0;
  margin: 2rem 0 2.5rem;
  padding: 0 1rem;
}
.setup-step-circle {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
  flex-shrink: 0;
  cursor: default;
  border: 2px solid var(--border);
  background: transparent;
  color: var(--text-muted);
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.setup-step-circle.active {
  border-color: var(--accent);
  background: var(--accent);
  color: #fff;
}
.setup-step-circle.done {
  border-color: #22c55e;
  background: #22c55e;
  color: #fff;
  cursor: pointer;
}
.setup-step-line {
  flex: 1;
  height: 2px;
  background: var(--border);
  margin: 0 0.25rem;
}
.setup-step-line.done {
  background: #22c55e;
}

/* Step container */
.setup-step {
  max-width: 560px;
  margin: 0 auto;
}
.setup-step-badge {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.setup-step h2 {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0 0 0.5rem;
}
.setup-step-desc {
  color: var(--text-muted);
  margin: 0 0 1.5rem;
  font-size: 0.95rem;
}

/* Provider cards */
.setup-provider-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}
.setup-provider-card {
  border: 2px solid var(--border);
  border-radius: 10px;
  padding: 1rem 0.75rem;
  background: transparent;
  cursor: pointer;
  text-align: center;
  transition: border-color 0.15s, background 0.15s;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  align-items: center;
}
.setup-provider-card:hover { border-color: var(--accent); }
.setup-provider-card.selected {
  border-color: var(--accent);
  background: color-mix(in srgb, var(--accent) 10%, transparent);
}
.setup-provider-icon { font-size: 1.75rem; }
.setup-provider-card strong { font-size: 0.95rem; }
.setup-provider-card span { font-size: 0.8rem; color: var(--text-muted); }
.setup-provider-badge {
  font-size: 0.7rem;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--bg-secondary);
  color: var(--text-muted);
  margin-top: 0.2rem;
}

/* Provider detail block (step 2) */
.setup-provider-detail {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1rem 1.25rem;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}
.setup-provider-detail a { color: var(--accent); }
.setup-provider-detail p { margin: 0 0 0.5rem; }
.setup-key-field { position: relative; margin-bottom: 0.5rem; }
.setup-key-field input {
  width: 100%;
  padding: 0.6rem 2.5rem 0.6rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text);
  font-size: 0.9rem;
  box-sizing: border-box;
}
.setup-key-toggle {
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 0.8rem;
}
.setup-security-note {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-top: 0.5rem;
}

/* Test result (step 3) */
.setup-test-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  margin: 1.5rem 0;
}
.setup-test-result {
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  display: none;
}
.setup-test-result.ok {
  display: block;
  background: color-mix(in srgb, #22c55e 12%, transparent);
  border: 1px solid #22c55e;
  color: #22c55e;
}
.setup-test-result.err {
  display: block;
  background: color-mix(in srgb, #ef4444 12%, transparent);
  border: 1px solid #ef4444;
  color: #ef4444;
}
.setup-test-raw {
  font-family: monospace;
  font-size: 0.8rem;
  color: var(--text-muted);
  max-height: 80px;
  overflow: auto;
  margin-top: 0.4rem;
}

/* Mini-chat (step 4) */
.setup-mini-chat {
  border: 1px solid var(--border);
  border-radius: 8px;
  height: 300px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-bottom: 1rem;
}
.setup-mini-chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.setup-chat-bubble {
  max-width: 85%;
  padding: 0.5rem 0.75rem;
  border-radius: 10px;
  font-size: 0.88rem;
  line-height: 1.4;
}
.setup-chat-bubble.assistant {
  align-self: flex-start;
  background: var(--bg-secondary);
  color: var(--text);
}
.setup-chat-bubble.user {
  align-self: flex-end;
  background: var(--accent);
  color: #fff;
}
.setup-mini-chat-input-row {
  display: flex;
  border-top: 1px solid var(--border);
  padding: 0.5rem;
  gap: 0.5rem;
}
.setup-mini-chat-input {
  flex: 1;
  padding: 0.4rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text);
  font-size: 0.88rem;
  resize: none;
}

/* Step actions */
.setup-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-top: 1.5rem;
}
```

- [ ] **Step 2: Verify build still passes**

```bash
rtk yarn --cwd hub build 2>&1 | tail -3
```

- [ ] **Step 3: Commit**

```bash
rtk git add hub/src/style.css
rtk git commit -m "feat(setup): add /setup/runtime/ page CSS — stepper, provider cards, mini-chat"
```

---

## Task 3: Add `renderSetupRuntime()` + router entry

**Files:**
- Modify: `hub/src/main.js`

Add the render function and wire it into the `boot()` router. No wiring logic yet.

- [ ] **Step 1: Add i18n text block and `renderSetupRuntime()`**

Insert before the `boot()` function (around line 3345). Add this block:

```js
const SETUP_RUNTIME_TEXT = {
  fr: {
    title: "Setup",
    subtitle: "Configure ton runtime IA en 4 étapes.",
    back: "Retour au hub",
    step1Title: "Choisir ton fournisseur",
    step1Desc: "Clawvis supporte plusieurs fournisseurs. Sélectionne celui que tu veux configurer.",
    step2Title: "Obtenir et entrer la clé",
    step2Desc: "Suis les instructions pour ton fournisseur, puis entre ta clé API.",
    step3Title: "Tester la connexion",
    step3Desc: "Vérifie que la connexion fonctionne avant de continuer.",
    step4Title: "Valide avec un message",
    step4Desc: "Envoie un message à ton runtime pour confirmer que tout fonctionne.",
    next: "Suivant →",
    back_btn: "← Retour",
    testBtn: "Lancer le test",
    testLoading: "Connexion en cours…",
    testOk: "Connexion réussie — ton runtime répond.",
    testErr: "Échec de connexion.",
    testErrHint: { claude: "Vérifie ta clé API.", mistral: "Vérifie ta clé API.", openclaw: "Vérifie l'URL et la clé." },
    chatWelcome: "Bonjour ! Je suis ton runtime IA. Pose-moi une question pour vérifier que tout fonctionne.",
    chatPlaceholder: "Envoie un message…",
    chatSend: "Envoyer",
    finish: "Terminer →",
    providers: {
      claude: { name: "Claude", owner: "Anthropic", badge: "Cloud", desc: "Le modèle le plus capable d'Anthropic. Clé API sur console.anthropic.com.", link: "https://console.anthropic.com/settings/keys", linkLabel: "Obtenir une clé →", placeholder: "sk-ant-..." },
      mistral: { name: "Mistral", owner: "Mistral AI", badge: "Cloud", desc: "Modèle open-weight performant. Clé API sur console.mistral.ai.", link: "https://console.mistral.ai/api-keys", linkLabel: "Obtenir une clé →", placeholder: "..." },
      openclaw: { name: "OpenClaw", owner: "Auto-hébergé", badge: "Self-hosted", desc: "Instance compatible OpenAI. Renseigne l'URL de ton serveur.", link: null, linkLabel: null, placeholder: "http://host:port" },
    },
    securityNote: "La clé est stockée dans ton navigateur (localStorage). Elle n'est jamais envoyée à nos serveurs.",
  },
  en: {
    title: "Setup",
    subtitle: "Configure your AI runtime in 4 steps.",
    back: "Back to hub",
    step1Title: "Choose your provider",
    step1Desc: "Clawvis supports multiple providers. Select the one you want to configure.",
    step2Title: "Get and enter your key",
    step2Desc: "Follow the instructions for your provider, then enter your API key.",
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
    testErrHint: { claude: "Check your API key.", mistral: "Check your API key.", openclaw: "Check the URL and key." },
    chatWelcome: "Hello! I'm your AI runtime. Ask me a question to confirm everything is working.",
    chatPlaceholder: "Send a message…",
    chatSend: "Send",
    finish: "Finish →",
    providers: {
      claude: { name: "Claude", owner: "Anthropic", badge: "Cloud", desc: "Anthropic's most capable model. API key at console.anthropic.com.", link: "https://console.anthropic.com/settings/keys", linkLabel: "Get a key →", placeholder: "sk-ant-..." },
      mistral: { name: "Mistral", owner: "Mistral AI", badge: "Cloud", desc: "High-performance open-weight model. API key at console.mistral.ai.", link: "https://console.mistral.ai/api-keys", linkLabel: "Get a key →", placeholder: "..." },
      openclaw: { name: "OpenClaw", owner: "Self-hosted", badge: "Self-hosted", desc: "OpenAI-compatible self-hosted instance. Enter your server URL.", link: null, linkLabel: null, placeholder: "http://host:port" },
    },
    securityNote: "Your key is stored in your browser (localStorage). It is never sent to our servers.",
  },
};

function renderSetupRuntime() {
  const isFr = settingsLocale() === "fr";
  const t = SETUP_RUNTIME_TEXT[isFr ? "fr" : "en"];
  app.innerHTML = `
    <div class="wrap">
      <header class="settings-page-header">
        <div class="title">
          <h1>${escapeHtml(t.title)} · <span>Clawvis</span></h1>
          <p>${escapeHtml(t.subtitle)}</p>
        </div>
        <a href="/" class="back-btn"><span class="icon">←</span><span>${escapeHtml(t.back)}</span></a>
        <button id="theme-toggle" class="icon-btn" aria-label="Toggle theme" type="button">
          <span id="theme-toggle-icon">🌙</span>
        </button>
      </header>

      <!-- Stepper -->
      <div class="setup-stepper" id="setup-stepper" role="list" aria-label="${isFr ? 'Étapes de configuration' : 'Configuration steps'}">
        <div class="setup-step-circle active" id="step-circle-1" data-step="1" role="listitem" aria-label="${isFr ? 'Étape 1 : Choisir ton fournisseur' : 'Step 1: Choose your provider'}">1</div>
        <div class="setup-step-line" id="step-line-1" aria-hidden="true"></div>
        <div class="setup-step-circle" id="step-circle-2" data-step="2" role="listitem" aria-label="${isFr ? 'Étape 2 : Entrer la clé' : 'Step 2: Enter your key'}">2</div>
        <div class="setup-step-line" id="step-line-2" aria-hidden="true"></div>
        <div class="setup-step-circle" id="step-circle-3" data-step="3" role="listitem" aria-label="${isFr ? 'Étape 3 : Tester la connexion' : 'Step 3: Test connection'}">3</div>
        <div class="setup-step-line" id="step-line-3" aria-hidden="true"></div>
        <div class="setup-step-circle" id="step-circle-4" data-step="4" role="listitem" aria-label="${isFr ? 'Étape 4 : Valider' : 'Step 4: Validate'}">4</div>
      </div>

      <!-- Step 1: Choose provider -->
      <div class="setup-step" id="setup-step-1">
        <div class="setup-step-badge">1 / 4</div>
        <h2>${escapeHtml(t.step1Title)}</h2>
        <p class="setup-step-desc">${escapeHtml(t.step1Desc)}</p>
        <div class="setup-provider-cards">
          ${["claude", "mistral", "openclaw"].map((pid) => {
            const p = t.providers[pid];
            return `<button class="setup-provider-card" data-provider="${pid}" type="button">
              <span class="setup-provider-icon">${pid === "claude" ? "🧠" : pid === "mistral" ? "✨" : "🐾"}</span>
              <strong>${escapeHtml(p.name)}</strong>
              <span>${escapeHtml(p.owner)}</span>
              <span class="setup-provider-badge">${escapeHtml(p.badge)}</span>
            </button>`;
          }).join("")}
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
```

- [ ] **Step 2: Wire into the `boot()` router**

In the `boot()` function, add before the `/settings` branch:

```js
// In the render block:
if (path.startsWith("/setup/runtime")) renderSetupRuntime();
else if (path.startsWith("/settings")) renderSettings();
// ...rest unchanged

// In the wire block:
if (path.startsWith("/setup/runtime")) await wireSetupRuntime();
else if (path.startsWith("/settings")) await wireSettings();
// ...rest unchanged
```

Add a stub so the file compiles:

```js
async function wireSetupRuntime() {
  // wired in Task 4
}
```

- [ ] **Step 3: Verify page renders at `/setup/runtime/`**

```bash
# Start dev server if not running
rtk yarn --cwd hub dev &
# Navigate to http://localhost:8088/setup/runtime/ and verify:
# - Header "Setup · Clawvis" visible
# - Stepper with 4 circles visible
# - Step 1 provider cards visible
# - Steps 2, 3, 4 hidden
```

- [ ] **Step 4: Commit**

```bash
rtk git add hub/src/main.js
rtk git commit -m "feat(setup): add renderSetupRuntime() with 4-step HTML skeleton"
```

---

## Task 4: Implement `wireSetupRuntime()` — full step logic

**Files:**
- Modify: `hub/src/main.js` (replace the stub `wireSetupRuntime`)

This is the core logic: step state machine, credentials in-memory, test call, mini-chat, localStorage save on finish.

- [ ] **Step 1: Replace the stub with the full implementation**

Replace `async function wireSetupRuntime() { // wired in Task 4 }` with:

```js
async function wireSetupRuntime() {
  const isFr = settingsLocale() === "fr";
  const t = SETUP_RUNTIME_TEXT[isFr ? "fr" : "en"];

  // ── In-memory wizard state (not written to localStorage until "Terminer") ──
  let selectedProvider = localStorage.getItem("ai-provider") || "";
  let credKey = "";   // holds claude key or mistral key
  let credUrl = "";   // holds openclaw url

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
    if (result) { result.className = "setup-test-result"; result.innerHTML = ""; }
    const next3 = document.getElementById("setup-next-3");
    if (next3) next3.disabled = true;
  }

  // ── Pre-fill from localStorage if returning user ──
  // Only pre-select the provider card and enable "Next →". Do NOT touch stepper circle
  // classes here — goToStep() manages them when the user actually navigates.
  // The page always starts on step 1 (default from renderSetupRuntime).
  if (selectedProvider) {
    const card = document.querySelector(`[data-provider="${selectedProvider}"]`);
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
      document.querySelectorAll("[data-provider]").forEach((c) => c.classList.remove("selected"));
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
      const existingKey = localStorage.getItem(`ai-${selectedProvider}-key`) || credKey;
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
      document.getElementById("setup-key-toggle").addEventListener("click", () => {
        keyInput.type = keyInput.type === "password" ? "text" : "password";
      });
      keyInput.addEventListener("input", () => {
        credKey = keyInput.value.trim();
        document.getElementById("setup-next-2").disabled = !credKey;
      });
      document.getElementById("setup-next-2").disabled = !existingKey && !credKey;
      if (existingKey) credKey = existingKey;
    }
  }

  document.getElementById("setup-back-1").addEventListener("click", () => goToStep(1));

  document.getElementById("setup-next-2").addEventListener("click", () => {
    // Capture final credential values before advancing
    if (selectedProvider === "openclaw") {
      credUrl = (document.getElementById("setup-cred-url") || {}).value?.trim() || credUrl;
    } else {
      credKey = (document.getElementById("setup-cred-key") || {}).value?.trim() || credKey;
    }
    goToStep(3);
  });

  // ── Step 3: Connection test ──
  document.getElementById("setup-back-2").addEventListener("click", () => goToStep(2));

  document.getElementById("setup-test-btn").addEventListener("click", async () => {
    const result = document.getElementById("setup-test-result");
    const testBtn = document.getElementById("setup-test-btn");
    result.className = "setup-test-result";
    result.innerHTML = t.testLoading;
    testBtn.disabled = true;

    try {
      // ⚠️ KNOWN LIMITATION: this test validates the backend's configured key (from .env),
      // NOT the key the user just entered in the wizard. hub_core.chat_runtime reads API
      // keys from environment variables only. A 200 response confirms the backend is
      // reachable and its env has a working key — it does not validate the wizard-entered key.
      // Future improvement: pass the key in a request header that chat_runtime reads
      // preferentially over the env.
      const res = await fetch("/api/hub/chat", {
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

  document.getElementById("setup-next-3").addEventListener("click", () => goToStep(4));

  // ── Step 4: Mini-chat ──
  document.getElementById("setup-back-3").addEventListener("click", () => goToStep(3));

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
      const res = await fetch("/api/hub/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, history: chatHistory.slice(0, -1) }),
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
        chatHistory.push({ role: "assistant", content: full });
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
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendSetupMessage(); }
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
```

- [ ] **Step 2: Verify step navigation manually**

Start the dev server and test:
- Step 1: click a provider → "Next →" enables → click → step 2 appears
- Step 2: fill a key → "Next →" enables → click → step 3 appears
- Step 3: click "Run test" → spinner → result shown; if failed: "Next →" stays disabled
- Step 4: pre-filled assistant bubble present; send a message
- "Terminer →" → values written to localStorage → redirected to `/`

- [ ] **Step 3: Verify back-navigation resets step 3**

- From step 3, click ← Back → step 2 shown, step 3 test result cleared
- From step 2, click ← Back → step 1 shown, step 3 test result cleared

- [ ] **Step 4: Verify returning user pre-fill**

- Configure a provider (finish wizard once)
- Navigate to `/setup/runtime/` again
- Assert: step 1 visible, correct provider card pre-selected, "Next →" enabled

- [ ] **Step 5: Commit**

```bash
rtk git add hub/src/main.js
rtk git commit -m "feat(setup): implement wireSetupRuntime() — 4-step wizard with test + mini-chat"
```

---

## Task 5: Update all entry points

**Files:**
- Modify: `hub/src/main.js` (home banner CTA, settings modal removal, chat warn link)
- Modify: `clawvis-cli/cli.mjs` (doneSettings URL)

- [ ] **Step 1: Update home banner CTA (`renderHome`, line ~415)**

Change:
```js
<a href="/settings/" id="ai-runtime-cta" class="btn btn-primary ai-runtime-cta">${escapeHtml(t.runtimeBannerCta)}</a>
```
To:
```js
<a href="/setup/runtime/" id="ai-runtime-cta" class="btn btn-primary ai-runtime-cta">${escapeHtml(t.runtimeBannerCta)}</a>
```

The `#ai-runtime-cta` href in `wireHome()` is not set dynamically — the static change in `renderHome()` above is the only change needed here.

- [ ] **Step 2: Update chat page warn link (`wireChat`, line ~3263)**

Change:
```js
<a href="/settings/" class="chat-setup-link">
```
To:
```js
<a href="/setup/runtime/" class="chat-setup-link">
```

- [ ] **Step 3: Update settings page — remove wizard modal, add link**

In `renderSettings()`:
1. Remove the entire `<!-- Wizard IA Modal -->` block (from `<div id="ai-wizard-overlay"` to its closing `</div>`, lines ~912–965).
2. Replace the `<button id="open-ai-wizard" ...>` button with a link:
```js
// OLD:
<button id="open-ai-wizard" class="btn btn-primary" type="button">${t.configureRuntime}</button>

// NEW:
<a href="/setup/runtime/" class="btn btn-primary">${t.configureRuntime}</a>
```

In `wireSettings()`, remove the following dead code entirely (variables + inner functions + event listeners):
- Variables: `wizardOverlay`, `wizardProvider`
- Functions: `wizardBuildStep2Fields`, `wizardShowStep`, `wizardRunTest`, `wizardSaveFromStep2`
- Event listeners attached to: `open-ai-wizard`, `ai-wizard-close`, `ai-wizard-overlay` (click-outside), `wizard-back-1`, `wizard-back-2`, `wizard-next-2`, `wizard-save-btn`, `wizard-test-btn`, all `.wizard-provider-card` click handlers

- [ ] **Step 4: Update all `/settings/` references in `clawvis-cli/cli.mjs`**

Three locations:

**Line ~300 (FR `providerNote`):**
```js
// OLD: "→ Connecter votre runtime IA se fait depuis le Hub (/settings/) ou via le CLI..."
// NEW: "→ Connecter votre runtime IA se fait depuis le Hub (/setup/runtime/) ou via le CLI..."
```

**Line ~334 (EN `providerNote`):**
```js
// OLD: "→ Connect your AI runtime from the Hub (/settings/) or via the clawvis CLI..."
// NEW: "→ Connect your AI runtime from the Hub (/setup/runtime/) or via the clawvis CLI..."
```

**Line ~466 (`doneSettings`):**
```js
// OLD:
chalk.yellow(`${t("doneSettings")}: http://localhost:${hubPort}/settings/`),
// NEW:
chalk.yellow(`${t("doneSettings")}: http://localhost:${hubPort}/setup/runtime/`),
```

**Line ~706 (`setup provider --status` output):**
```js
// OLD: reference to http://localhost:.../settings/ → section "AI Runtime"
// NEW: reference to http://localhost:.../setup/runtime/
```

- [ ] **Step 5: Run CI**

```bash
bash tests/ci-all.sh
```
Expected: 0 failures.

- [ ] **Step 6: Commit**

```bash
rtk git add hub/src/main.js clawvis-cli/cli.mjs
rtk git commit -m "feat(setup): update all entry points to /setup/runtime/, remove settings modal"
```

---

## Task 6: Update `docs/playwright-persona.md`

**Files:**
- Modify: `docs/playwright-persona.md`

Apply the changes defined in the spec's playwright section.

- [ ] **Step 1: Rewrite Persona 1 steps 2–5**

Replace the current steps 2–5 of Persona 1 with:

```markdown
2. **Navigate to Setup Runtime** via AI runtime banner CTA
   - Assert URL is `/setup/runtime/`
   - Assert page header contains "Setup · Clawvis" or "Setup · Clawvis"
   - Assert stepper is visible with 4 step circles

3. **Step 1 — Choose provider**
   - Assert 3 provider cards visible: Claude, Mistral, OpenClaw
   - Assert "Next →" button is disabled
   - Click "Claude" card
   - Assert "Next →" button is now enabled

4. **Step 2 — Credentials**
   - Click "Next →"
   - Assert stepper advances to step 2 (circle 2 is active)
   - Assert API key input is visible (`type=password`, placeholder `sk-ant-...`)
   - Assert "Next →" is disabled
   - Type `sk-ant-test-key-00000000`
   - Assert "Next →" is now enabled
   - Click "Next →"

5. **Step 3 — Test gate**
   - Assert stepper is on step 3
   - Assert "Next →" is disabled (no test run yet)
   - Click "Run test" / "Lancer le test"
   - Assert test result is shown (error expected — key is fake)
   - Assert "Next →" remains **disabled** (failed test must not unlock step 4)
   - *(Journey ends here — step 4 mini-chat not tested with fake key)*
```

- [ ] **Step 2: Fix Persona 5 step 3**

Replace current step 3 of Persona 5 with:

```markdown
3. **AI Runtime section (no modal)**
   - Assert a link with text matching "Configurer le runtime" / "Configure runtime" is visible
   - Assert the link's `href` attribute is `/setup/runtime/`
   - Assert **no modal overlay is present** (`#ai-wizard-overlay` must not exist in the DOM)
```

- [ ] **Step 3: Fix Persona 6 step 1 warn assertion**

Replace the "not configured" sub-assertion in step 1:

```markdown
   - If runtime not configured: assert warn status bar contains a link with `href="/setup/runtime/"` and visible text matching "Configurer le runtime" / "Setup runtime"
```

- [ ] **Step 4: Commit**

```bash
rtk git add docs/playwright-persona.md
rtk git commit -m "docs(playwright): update Persona 1/5/6 for /setup/runtime/ wizard"
```

> **Note — coverage gap:** The home banner "Connected" state (green, "Connecté · Claude") is no longer tested by any persona after this change. Persona 1 ends on step 3 with a fake key. This is intentional for now. Add a dedicated `setup-runtime-happy-path.spec.ts` persona when a mock/stub API key becomes available in CI.

---

## Verification Checklist

After all 6 tasks, run:

```bash
# 1. CI passes
bash tests/ci-all.sh

# 2. Hub builds
rtk yarn --cwd hub build 2>&1 | tail -3

# 3. No stale /api/kanban references in frontend
grep -c "api/kanban" hub/src/main.js   # Expected: 0

# 4. No wizard modal in settings
grep "ai-wizard-overlay" hub/src/main.js   # Expected: no match

# 5. All entry points updated
grep -n "ai-runtime-cta\|chat-setup-link\|doneSettings" hub/src/main.js clawvis-cli/cli.mjs
# All should reference /setup/runtime/
```
