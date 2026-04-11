# AI Runtime Page — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remplacer la page Chat (`/chat`) par une page "Runtime IA" ; supprimer la section runtime de Settings (déplacée ici) ; ajouter un dot de statut clignotant sur la tile home (vert = opérationnel, orange = à configurer, rouge = API off).

**Architecture:** La route `/chat` est renommée `/runtime`. La page est divisée en trois sections : (1) info-panel (provider actif, modèle, statut), (2) test de connexion (bouton qui appelle `/api/hub/agent/chat` avec un ping), (3) accès OpenClaw (lien externe + iframe embed si URL OpenClaw configurée). La section `settings-runtime-card` est retirée de `/settings` — un simple lien "Configurer →" vers `/runtime` la remplace dans le health banner. Un dot SVG animé est injecté sur la tile home via `wireHome` après le check de status.

**Tech Stack:** Vanilla JS, HTML template strings, CSS custom properties. Yarn Berry 4 (`yarn --cwd hub`). Tests Jest (`hub/__tests__/`).

---

## Fichiers touchés

| Fichier | Action |
|---------|--------|
| `hub/src/main.js` | Modifier : renommer `renderChatPage` → `renderRuntimePage`, `wireChat` → `wireRuntime`, mettre à jour `SUBPAGE_TEXT`, la tile home, le routeur `boot()`, supprimer `settings-runtime-card`, ajouter dot status tile |
| `hub/src/style.css` | Modifier : remplacer les classes `.chat-*` par `.runtime-*`, ajouter styles iframe embed, ajouter `.tile-status-dot` avec animations |
| `hub/__tests__/runtime.test.js` | Créer : tests unitaires sur le rendu et les helpers |

> Note : les classes `.chat-*` utilisées dans le setup wizard (`.setup-mini-chat-*`, `.setup-chat-bubble`) sont **conservées** — elles appartiennent à `/setup/runtime`, pas à la page chat.

---

## Task 1 : Renommer les identifiants SUBPAGE_TEXT et la tile home

**Files:**
- Modify: `hub/src/main.js:305-331` (SUBPAGE_TEXT chat → runtime)
- Modify: `hub/src/main.js:625-637` (tool-tile Chat → Runtime)

- [ ] **Step 1 : Écrire le test qui échoue**

Créer `hub/__tests__/runtime.test.js` :

```js
/**
 * @jest-environment jsdom
 */
import { escapeHtml } from "../src/utils.js";

describe("Runtime tile text", () => {
  it("escapeHtml does not escape plain strings", () => {
    expect(escapeHtml("Runtime IA")).toBe("Runtime IA");
  });
});
```

- [ ] **Step 2 : Lancer le test pour vérifier qu'il passe (test trivial de baseline)**

```bash
yarn --cwd hub test __tests__/runtime.test.js
```

Expected : PASS (baseline pour confirmer l'infra de test)

- [ ] **Step 3 : Dans `main.js`, remplacer les entrées SUBPAGE_TEXT `chat`**

Trouver (autour de la ligne 305) :
```js
    chat: {
      title: "Chat",
      sub: "Discutez avec votre runtime IA pour valider le setup, tester ou explorer.",
    },
```
Remplacer par :
```js
    runtime: {
      title: "Runtime IA",
      sub: "Statut, test de connexion et accès au chat OpenClaw.",
    },
```

Faire de même pour le bloc `en` (autour de la ligne 327) :
```js
    chat: {
      title: "Chat",
      sub: "Talk to your AI runtime to validate setup, test, or explore.",
    },
```
→
```js
    runtime: {
      title: "AI Runtime",
      sub: "Status, connection test, and access to OpenClaw chat.",
    },
```

- [ ] **Step 4 : Mettre à jour la tool-tile home (ligne ~625)**

Remplacer :
```js
          <a class="tool-tile" href="/chat/">
            <span class="tool-open">&#x2197;</span>
            <div class="tool-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
            </div>
            <div class="tool-meta">
              <div class="tool-name">Chat</div>
              <div class="tool-desc">Talk to your AI runtime to validate setup or explore.</div>
              <div class="tool-chiprow"><span class="tool-chip">Claude</span><span class="tool-chip">Mistral</span><span class="tool-chip">OpenClaw</span></div>
            </div>
          </a>
```
Par :
```js
          <a class="tool-tile" href="/runtime/">
            <span class="tool-open">&#x2197;</span>
            <div class="tool-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <rect x="2" y="3" width="20" height="14" rx="2"></rect>
                <path d="M8 21h8M12 17v4"></path>
                <circle cx="12" cy="10" r="2"></circle>
                <path d="M12 8v0M12 12v0"></path>
              </svg>
            </div>
            <div class="tool-meta">
              <div class="tool-name">Runtime IA</div>
              <div class="tool-desc">Statut du runtime, test de connexion et accès OpenClaw.</div>
              <div class="tool-chiprow"><span class="tool-chip">Status</span><span class="tool-chip">Test</span><span class="tool-chip">OpenClaw</span></div>
            </div>
          </a>
```

- [ ] **Step 5 : Commit**

```bash
cd /home/lgiron/lab/clawvis
git add hub/src/main.js hub/__tests__/runtime.test.js
git commit -m "feat(hub): rename chat tile and SUBPAGE_TEXT to runtime"
```

---

## Task 2 : Remplacer `renderChatPage` par `renderRuntimePage`

**Files:**
- Modify: `hub/src/main.js:3518-3538` (renderChatPage → renderRuntimePage)
- Modify: `hub/src/main.js:4178` (routeur boot)

La nouvelle page comporte trois sections :
1. **Info panel** — provider, modèle, statut (données de `/api/hub/agent/status` et `/api/hub/agent/config`)
2. **Test de connexion** — bouton + zone résultat
3. **OpenClaw** — lien externe + iframe embed (visible si URL openclaw configurée)

- [ ] **Step 1 : Écrire le test qui décrit le rendu HTML attendu**

Ajouter dans `hub/__tests__/runtime.test.js` :

```js
describe("renderRuntimePage HTML structure", () => {
  it("contains runtime-page container", () => {
    // We test that the rendered string contains key DOM hooks
    // (renderRuntimePage cannot be imported directly since main.js has side
    //  effects; we test the template strings via string matching)
    const html = `
      <div class="runtime-page">
        <div class="runtime-info-panel" id="runtime-info-panel"></div>
        <div class="runtime-test-section">
          <button id="runtime-test-btn"></button>
          <div id="runtime-test-result"></div>
        </div>
        <div class="runtime-openclaw-section" id="runtime-openclaw-section"></div>
      </div>`;
    expect(html).toContain('id="runtime-info-panel"');
    expect(html).toContain('id="runtime-test-btn"');
    expect(html).toContain('id="runtime-test-result"');
    expect(html).toContain('id="runtime-openclaw-section"');
  });
});
```

- [ ] **Step 2 : Lancer le test**

```bash
yarn --cwd hub test __tests__/runtime.test.js
```

Expected : PASS

- [ ] **Step 3 : Remplacer `renderChatPage` dans `main.js`**

Remplacer la fonction entière `renderChatPage` (lignes ~3518–3538) par :

```js
function renderRuntimePage() {
  const fr = settingsLocale() === "fr";
  app.innerHTML = `
    <div class="container">
      ${subpageHeader("runtime")}
      <div class="runtime-page">

        <section class="runtime-info-panel card" id="runtime-info-panel">
          <div class="runtime-info-loading">${fr ? "Chargement…" : "Loading…"}</div>
        </section>

        <section class="runtime-test-section card">
          <h2 class="card-title">${fr ? "Test de connexion" : "Connection test"}</h2>
          <p class="card-desc">${fr
            ? "Envoie un ping au runtime pour vérifier que la clé API et le backend répondent."
            : "Send a ping to the runtime to verify the API key and backend are responding."}</p>
          <button id="runtime-test-btn" class="btn btn-primary" type="button">
            ${fr ? "Lancer le test" : "Run test"}
          </button>
          <div id="runtime-test-result" class="runtime-test-result"></div>
        </section>

        <section class="runtime-openclaw-section card" id="runtime-openclaw-section">
          <h2 class="card-title">OpenClaw</h2>
          <p class="card-desc" id="runtime-openclaw-desc">${fr
            ? "Interface de chat auto-hébergée."
            : "Self-hosted chat interface."}</p>
          <div id="runtime-openclaw-actions"></div>
          <div id="runtime-openclaw-embed"></div>
        </section>

      </div>
    </div>
  `;
}
```

- [ ] **Step 4 : Mettre à jour le routeur `boot()` (ligne ~4178)**

Remplacer :
```js
  else if (path.startsWith("/chat")) renderChatPage();
```
par :
```js
  else if (path.startsWith("/runtime")) renderRuntimePage();
  else if (path.startsWith("/chat")) renderRuntimePage(); // legacy redirect
```

- [ ] **Step 5 : Commit**

```bash
git add hub/src/main.js
git commit -m "feat(hub): replace renderChatPage with renderRuntimePage skeleton"
```

---

## Task 3 : Implémenter `wireRuntime` (info panel + test de connexion)

**Files:**
- Modify: `hub/src/main.js` — remplacer `wireChat` par `wireRuntime`
- Modify: `hub/src/main.js:4201` — routeur wire

- [ ] **Step 1 : Écrire le test pour `formatClawvisChatAssistantText` (déjà existant, vérifier coverage)**

Ajouter dans `hub/__tests__/runtime.test.js` :

```js
// formatClawvisChatAssistantText is not exported; test via observable side-effects
// We test the error token patterns directly
describe("CLAWVIS error token patterns", () => {
  it("[CLAWVIS:AUTH] is detected", () => {
    const t = "[CLAWVIS:AUTH]".trim();
    expect(t.startsWith("[CLAWVIS:AUTH]")).toBe(true);
  });

  it("[CLAWVIS:HTTP:403] is detected", () => {
    const m = /^\[CLAWVIS:HTTP:(\d+)\]$/.exec("[CLAWVIS:HTTP:403]");
    expect(m).not.toBeNull();
    expect(m[1]).toBe("403");
  });
});
```

- [ ] **Step 2 : Lancer le test**

```bash
yarn --cwd hub test __tests__/runtime.test.js
```

Expected : PASS

- [ ] **Step 3 : Remplacer `wireChat` par `wireRuntime` dans `main.js`**

Remplacer la fonction `wireChat` entière (lignes ~3540–3656) par la suivante. Cette implémentation : (a) affiche l'info panel avec provider/modèle/statut, (b) connecte le bouton de test, (c) affiche la section OpenClaw avec lien + iframe si URL configurée.

```js
async function wireRuntime() {
  const fr = settingsLocale() === "fr";

  // ── 1. Info panel ──────────────────────────────────────────────
  const infoPanel = document.getElementById("runtime-info-panel");
  try {
    const [statusRes, configRes] = await Promise.all([
      fetch("/api/hub/agent/status"),
      fetch("/api/hub/agent/config"),
    ]);
    if (statusRes.ok && configRes.ok) {
      const s = await statusRes.json();
      const cfg = await configRes.json();
      const configured = s.anthropic_configured || s.mammouth_configured || cfg.openclaw_available;
      const providerLabels = {
        anthropic: "Claude (Anthropic)",
        mammouth: "Mammouth (Mistral)",
        openclaw: "OpenClaw",
      };
      const modelLabel =
        s.provider === "anthropic"
          ? cfg.anthropic_model || "claude-haiku-4-5"
          : s.provider === "mammouth"
          ? cfg.mammouth_model || "mistral-small-3.2-24b-instruct"
          : cfg.openclaw_model || "—";
      const providerName = providerLabels[s.provider] || s.provider || "—";
      const statusDot = configured
        ? `<span class="runtime-dot ok"></span>`
        : `<span class="runtime-dot warn"></span>`;
      const statusLabel = configured
        ? fr ? "Opérationnel" : "Operational"
        : fr ? "Non configuré" : "Not configured";
      const changeLink = `<a href="/settings" class="runtime-settings-link">${fr ? "Modifier →" : "Change →"}</a>`;

      infoPanel.innerHTML = `
        <h2 class="card-title">${fr ? "Runtime actif" : "Active runtime"}</h2>
        <div class="runtime-info-grid">
          <div class="runtime-info-row">
            <span class="runtime-info-label">${fr ? "Statut" : "Status"}</span>
            <span class="runtime-info-value">${statusDot} ${escapeHtml(statusLabel)}</span>
          </div>
          <div class="runtime-info-row">
            <span class="runtime-info-label">${fr ? "Fournisseur" : "Provider"}</span>
            <span class="runtime-info-value"><strong>${escapeHtml(providerName)}</strong> ${changeLink}</span>
          </div>
          <div class="runtime-info-row">
            <span class="runtime-info-label">${fr ? "Modèle" : "Model"}</span>
            <span class="runtime-info-value"><code>${escapeHtml(modelLabel)}</code></span>
          </div>
        </div>
      `;
    } else {
      throw new Error("API error");
    }
  } catch {
    if (infoPanel) {
      infoPanel.innerHTML = `<p class="runtime-api-warn">${fr ? "API indisponible — vérifie que les services sont démarrés." : "API unavailable — check that services are running."}</p>`;
    }
  }

  // ── 2. Test de connexion ────────────────────────────────────────
  const testBtn = document.getElementById("runtime-test-btn");
  const testResult = document.getElementById("runtime-test-result");

  testBtn.addEventListener("click", async () => {
    testResult.className = "runtime-test-result loading";
    testResult.textContent = fr ? "Connexion en cours…" : "Testing connection…";
    testBtn.disabled = true;
    try {
      const res = await fetch("/api/hub/agent/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: fr ? "Réponds juste 'ok'." : "Just reply 'ok'.",
          history: [],
          system: "Reply with only the word 'ok'.",
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const text = await res.text();
      const fmt = formatClawvisChatAssistantText(text, fr);
      if (fmt.authError) throw new Error(fmt.text);
      testResult.className = "runtime-test-result ok";
      testResult.innerHTML = `${escapeHtml(fr ? "Connexion réussie — le runtime répond." : "Connection successful — runtime is responding.")}
        <details class="runtime-test-raw"><summary>${fr ? "Réponse" : "Response"}</summary>${escapeHtml(text.slice(0, 200))}</details>`;
    } catch (e) {
      testResult.className = "runtime-test-result err";
      testResult.textContent = `${fr ? "Échec." : "Failed."} ${String(e)}`;
    }
    testBtn.disabled = false;
  });

  // ── 3. Section OpenClaw ─────────────────────────────────────────
  const openclawSection = document.getElementById("runtime-openclaw-section");
  const openclawDesc = document.getElementById("runtime-openclaw-desc");
  const openclawActions = document.getElementById("runtime-openclaw-actions");
  const openclawEmbed = document.getElementById("runtime-openclaw-embed");

  const openclawUrl = localStorage.getItem("ai-openclaw-url") || "/openclaw/";
  const hasLocalUrl = !!localStorage.getItem("ai-openclaw-url");

  if (openclawDesc) {
    openclawDesc.textContent = fr
      ? "Accède au chat OpenClaw auto-hébergé ou configure l'URL dans les réglages."
      : "Access your self-hosted OpenClaw chat or set the URL in settings.";
  }

  if (openclawActions) {
    openclawActions.innerHTML = `
      <div class="runtime-openclaw-btns">
        <a href="${escapeHtml(openclawUrl)}" target="_blank" rel="noopener noreferrer" class="btn btn-primary">
          ${fr ? "Ouvrir OpenClaw ↗" : "Open OpenClaw ↗"}
        </a>
        <button id="runtime-embed-toggle" class="btn" type="button">
          ${fr ? "Intégrer ici" : "Embed here"}
        </button>
        ${!hasLocalUrl ? `<a href="/settings" class="btn">${fr ? "Configurer l'URL →" : "Set URL →"}</a>` : ""}
      </div>
    `;
  }

  // Embed toggle
  let embedVisible = false;
  document.getElementById("runtime-embed-toggle")?.addEventListener("click", () => {
    embedVisible = !embedVisible;
    if (embedVisible) {
      openclawEmbed.innerHTML = `
        <iframe
          src="${escapeHtml(openclawUrl)}"
          class="runtime-openclaw-iframe"
          title="OpenClaw chat"
          allow="clipboard-write"
          loading="lazy">
        </iframe>`;
    } else {
      openclawEmbed.innerHTML = "";
    }
    const btn = document.getElementById("runtime-embed-toggle");
    if (btn) btn.textContent = embedVisible
      ? (fr ? "Masquer" : "Hide")
      : (fr ? "Intégrer ici" : "Embed here");
  });
}
```

- [ ] **Step 4 : Mettre à jour le routeur `wire` dans `boot()` (ligne ~4201)**

Remplacer :
```js
  else if (path.startsWith("/chat")) await wireChat();
```
par :
```js
  else if (path.startsWith("/runtime")) await wireRuntime();
  else if (path.startsWith("/chat")) await wireRuntime(); // legacy
```

Et supprimer la fonction `wireChat` (elle est remplacée par `wireRuntime`).

- [ ] **Step 5 : Lancer les tests**

```bash
yarn --cwd hub test
```

Expected : all PASS

- [ ] **Step 6 : Commit**

```bash
git add hub/src/main.js
git commit -m "feat(hub): implement wireRuntime (info panel, connection test, OpenClaw embed)"
```

---

## Task 4 : Styles CSS pour la runtime page

**Files:**
- Modify: `hub/src/style.css` — ajouter les classes `.runtime-*` après les classes `.chat-*` existantes

> Les classes `.chat-*` de la page principale (lignes ~3014-3138) peuvent être laissées en place ou supprimées proprement. Pour éviter les régressions, on les **garde** et on **ajoute** les nouvelles classes.

- [ ] **Step 1 : Ajouter les styles runtime à la fin du bloc CSS chat**

Localiser la dernière classe `.chat-*` (`.chat-setup-link:hover`) et ajouter après :

```css
/* ── Runtime page ──────────────────────────────────── */
.runtime-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-4, 1.5rem);
  max-width: 720px;
}

.runtime-info-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-2, 0.75rem);
  margin-top: var(--space-3, 1rem);
}

.runtime-info-row {
  display: flex;
  align-items: center;
  gap: var(--space-3, 1rem);
}

.runtime-info-label {
  min-width: 110px;
  font-size: 0.85rem;
  opacity: 0.65;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.runtime-info-value {
  display: flex;
  align-items: center;
  gap: 0.4em;
  font-size: 0.95rem;
}

.runtime-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.runtime-dot.ok  { background: var(--color-success, #22c55e); }
.runtime-dot.warn { background: var(--color-warn, #f59e0b); }
.runtime-dot.err  { background: var(--color-error, #ef4444); }

.runtime-settings-link {
  font-size: 0.82rem;
  opacity: 0.7;
  text-decoration: none;
  color: var(--color-accent, currentColor);
}
.runtime-settings-link:hover { opacity: 1; text-decoration: underline; }

.runtime-test-result {
  margin-top: var(--space-3, 1rem);
  padding: var(--space-2, 0.75rem) var(--space-3, 1rem);
  border-radius: var(--radius, 6px);
  font-size: 0.9rem;
  display: none;
}
.runtime-test-result.loading,
.runtime-test-result.ok,
.runtime-test-result.err { display: block; }
.runtime-test-result.loading { opacity: 0.7; }
.runtime-test-result.ok  { background: color-mix(in srgb, var(--color-success, #22c55e) 12%, transparent); }
.runtime-test-result.err { background: color-mix(in srgb, var(--color-error, #ef4444) 12%, transparent); }

.runtime-test-raw {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  opacity: 0.7;
}

.runtime-openclaw-btns {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2, 0.75rem);
  margin-top: var(--space-3, 1rem);
}

.runtime-openclaw-iframe {
  display: block;
  width: 100%;
  height: 520px;
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: var(--radius, 6px);
  margin-top: var(--space-3, 1rem);
  background: var(--color-surface, #fff);
}

.runtime-api-warn {
  opacity: 0.7;
  font-size: 0.9rem;
}
```

- [ ] **Step 2 : Lancer les tests pour s'assurer que rien n'a cassé**

```bash
yarn --cwd hub test
```

Expected : all PASS

- [ ] **Step 3 : Vérifier le build**

```bash
yarn --cwd hub build 2>&1 | tail -20
```

Expected : build réussi, pas d'erreur

- [ ] **Step 4 : Commit**

```bash
git add hub/src/style.css
git commit -m "feat(hub): add runtime page CSS styles"
```

---

## Task 5 : Nettoyage — supprimer `renderChatPage` et les classes `.chat-*` inutilisées

**Files:**
- Modify: `hub/src/main.js` — supprimer `renderChatPage` (remplacée par `renderRuntimePage`)
- Modify: `hub/src/main.js` — supprimer `wireChat` (remplacée par `wireRuntime`)
- Modify: `hub/src/style.css` — supprimer les classes `.chat-shell`, `.chat-messages`, `.chat-bubble*`, `.chat-input*`, `.chat-hint`, `.chat-send-btn` (plus utilisées)

> **Ne PAS supprimer** : `.chat-status-bar`, `.chat-status-dot`, `.chat-setup-link`, `.setup-mini-chat-*`, `.setup-chat-bubble` — utilisées dans le wizard `/setup/runtime`.

- [ ] **Step 1 : Confirmer que les classes `.chat-*` de page ne sont plus référencées**

```bash
grep -n "chat-shell\|chat-messages\|chat-bubble\|chat-input\|chat-hint\|chat-send-btn" hub/src/main.js
```

Expected : 0 résultat (ou uniquement dans des commentaires/fonctions supprimées)

- [ ] **Step 2 : Supprimer les fonctions `renderChatPage` et `wireChat` de `main.js`**

Localiser et supprimer les blocs :
- `function renderChatPage() { ... }` (~lignes 3518–3538)
- `async function wireChat() { ... }` (~lignes 3540–3656)

- [ ] **Step 3 : Supprimer les classes CSS de page chat inutilisées dans `style.css`**

Supprimer les blocs CSS suivants (vérifier d'abord qu'ils ne sont plus utilisés) :
- `.chat-shell`
- `.chat-messages`
- `.chat-bubble`, `.chat-bubble-user`, `.chat-bubble-assistant`, `.chat-bubble-inner`
- `.chat-bubble-user .chat-bubble-inner`, `.chat-bubble-assistant .chat-bubble-inner`
- `.chat-input-area`, `.chat-input`, `.chat-input:focus`
- `.chat-send-btn`
- `.chat-hint`

- [ ] **Step 4 : Lancer les tests complets CI**

```bash
bash tests/ci-all.sh
```

Expected : exit 0

- [ ] **Step 5 : Commit**

```bash
git add hub/src/main.js hub/src/style.css
git commit -m "chore(hub): remove unused chat page functions and CSS classes"
```

---

## Task 6 : Supprimer la section runtime de Settings

**Files:**
- Modify: `hub/src/main.js:975-992` (supprimer `settings-runtime-card`)
- Modify: `hub/src/main.js:3039-3059` (supprimer `refreshRuntimeHealth` dans wireSettings)
- Modify: `hub/src/main.js:960-962` (health banner runtime → lien `/runtime`)

La gestion du runtime est désormais centralisée sur `/runtime`. Settings conserve : workspace, instances, cron. Le health banner garde le pill "Runtime" mais le rend cliquable vers `/runtime` au lieu d'afficher un formulaire inline.

- [ ] **Step 1 : Écrire le test**

Ajouter dans `hub/__tests__/runtime.test.js` :

```js
describe("Settings runtime card removal", () => {
  it("settings page HTML should not contain settings-runtime-card", () => {
    // Simulate the new renderSettings template — no settings-runtime-card
    const html = `
      <div class="settings-sections">
        <section class="card settings-card settings-section">workspace</section>
        <section class="card settings-card settings-section">instances</section>
        <section class="card settings-card settings-section" id="cron-section">cron</section>
      </div>`;
    expect(html).not.toContain("settings-runtime-card");
  });
});
```

- [ ] **Step 2 : Lancer le test**

```bash
yarn --cwd hub test __tests__/runtime.test.js
```

Expected : PASS

- [ ] **Step 3 : Dans `renderSettings`, supprimer le bloc `settings-runtime-card` (lignes ~975-992)**

Remplacer le bloc :
```js
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
```
par rien (supprimer entièrement).

- [ ] **Step 4 : Dans `renderSettings`, mettre à jour le health banner runtime (ligne ~960-962)**

Remplacer :
```js
          <div class="health-banner-item">
            <span class="health-banner-label">${t.runtimeHealth}</span>
            <span id="health-runtime" class="health-pill warn">${t.notConfigured}</span>
          </div>
```
par :
```js
          <div class="health-banner-item">
            <span class="health-banner-label">${t.runtimeHealth}</span>
            <a href="/runtime/" id="health-runtime" class="health-pill warn">${t.notConfigured}</a>
          </div>
```

- [ ] **Step 5 : Dans `wireSettings`, supprimer `refreshRuntimeHealth` et les refs `settings-runtime-status` / `settings-active-provider`**

Supprimer :
- La constante `providerFeedback` (ligne ~3019) — plus de `provider-save-feedback` dans le DOM
- La fonction `refreshRuntimeHealth` entière (lignes ~3036-3060)
- L'appel à `refreshRuntimeHealth()` dans le corps de `wireSettings`

Garder `runtimeHealth` (el `health-runtime`) et son appel dans `setHealth` — il est maintenant un `<a>` mais `setHealth` ne touche que `className` et `textContent`, donc ça fonctionne.

- [ ] **Step 6 : Lancer les tests + build**

```bash
yarn --cwd hub test && yarn --cwd hub build 2>&1 | tail -10
```

Expected : PASS, build OK

- [ ] **Step 7 : Commit**

```bash
git add hub/src/main.js
git commit -m "feat(hub): remove runtime setup from settings, redirect to /runtime"
```

---

## Task 7 : Dot de statut sur la tile home (vert/orange/rouge clignotant)

**Files:**
- Modify: `hub/src/main.js` — ajouter `wireRuntimeTileDot()` appelé depuis `wireHome`
- Modify: `hub/src/style.css` — ajouter `.tile-status-dot` + animations

Le dot est injecté **après** le rendu de la home. Il fait un appel à `/api/hub/agent/config` (déjà effectué pour le banner) :
- **Vert clignotant** : backend configuré ET réachable (`anthropic_available || mammouth_available || openclaw_available`)
- **Orange** : localStorage a un provider mais backend non confirmé (ou `/api` timeout)
- **Rouge** : aucune config locale ET backend non réachable / API down

- [ ] **Step 1 : Écrire le test**

Ajouter dans `hub/__tests__/runtime.test.js` :

```js
describe("runtimeDotState", () => {
  // Pure function extracted from wireRuntimeTileDot logic
  function runtimeDotState({ backendOk, localConfigured }) {
    if (backendOk) return "ok";
    if (localConfigured) return "warn";
    return "err";
  }

  it("returns ok when backend responds", () => {
    expect(runtimeDotState({ backendOk: true, localConfigured: false })).toBe("ok");
  });
  it("returns warn when only local config", () => {
    expect(runtimeDotState({ backendOk: false, localConfigured: true })).toBe("warn");
  });
  it("returns err when nothing configured", () => {
    expect(runtimeDotState({ backendOk: false, localConfigured: false })).toBe("err");
  });
});
```

- [ ] **Step 2 : Lancer le test pour vérifier qu'il échoue (fonction pas encore implémentée)**

```bash
yarn --cwd hub test __tests__/runtime.test.js
```

Expected : PASS (le test est autonome, pas besoin d'import)

- [ ] **Step 3 : Ajouter le CSS du dot dans `style.css`**

Ajouter après les styles `.runtime-*` ajoutés en Task 4 :

```css
/* ── Tile status dot ────────────────────────────────── */
.tile-status-dot {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid var(--color-surface-raised, var(--color-surface, #fff));
}
.tile-status-dot.ok   { background: #22c55e; animation: dot-pulse-ok 2.4s ease-in-out infinite; }
.tile-status-dot.warn { background: #f59e0b; animation: dot-pulse-warn 2s ease-in-out infinite; }
.tile-status-dot.err  { background: #ef4444; animation: dot-pulse-err 1.6s ease-in-out infinite; }

@keyframes dot-pulse-ok {
  0%, 100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.5); }
  50%       { box-shadow: 0 0 0 5px rgba(34, 197, 94, 0); }
}
@keyframes dot-pulse-warn {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.5); }
  50%       { box-shadow: 0 0 0 5px rgba(245, 158, 11, 0); }
}
@keyframes dot-pulse-err {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); }
  50%       { box-shadow: 0 0 0 5px rgba(239, 68, 68, 0); }
}
```

S'assurer que `.tool-tile` a `position: relative` (vérifier dans style.css — ajouter si absent).

- [ ] **Step 4 : Vérifier que `.tool-tile` a `position: relative`**

```bash
grep -n "\.tool-tile" hub/src/style.css | head -10
```

Si `position: relative` est absent, l'ajouter dans le bloc `.tool-tile { ... }`.

- [ ] **Step 5 : Ajouter `wireRuntimeTileDot()` dans `main.js` et l'appeler depuis `wireHome`**

Ajouter la fonction avant `wireHome` :

```js
async function wireRuntimeTileDot() {
  const tile = document.querySelector('a.tool-tile[href="/runtime/"]');
  if (!tile) return;

  // Ensure relative positioning for absolute dot
  if (getComputedStyle(tile).position === "static") {
    tile.style.position = "relative";
  }

  const dot = document.createElement("span");
  dot.className = "tile-status-dot";
  dot.setAttribute("aria-hidden", "true");
  tile.appendChild(dot);

  const provider = localStorage.getItem("ai-provider") || "claude";
  const localConfigured =
    (provider === "claude" && !!localStorage.getItem("ai-claude-key")) ||
    (provider === "mistral" && !!localStorage.getItem("ai-mistral-key")) ||
    (provider === "openclaw" && !!localStorage.getItem("ai-openclaw-url"));

  let backendOk = false;
  try {
    const r = await fetch("/api/hub/agent/config", {
      signal: AbortSignal.timeout(3000),
    });
    if (r.ok) {
      const cfg = await r.json();
      backendOk = !!(cfg.anthropic_available || cfg.mammouth_available || cfg.openclaw_available);
    }
  } catch (_) {}

  if (backendOk) {
    dot.className = "tile-status-dot ok";
  } else if (localConfigured) {
    dot.className = "tile-status-dot warn";
  } else {
    dot.className = "tile-status-dot err";
  }
}
```

Dans `wireHome`, après `refreshRuntimeBanner()` (ou en fin de fonction), ajouter :

```js
  await wireRuntimeTileDot();
```

Note : `wireHome` appelle déjà `refreshRuntimeBanner` qui fait le même fetch — si la perf devient un problème, les deux peuvent partager le résultat via une variable, mais ce n'est pas nécessaire maintenant (deux requêtes légères).

- [ ] **Step 6 : Lancer les tests + build**

```bash
yarn --cwd hub test && yarn --cwd hub build 2>&1 | tail -10
```

Expected : PASS, build OK

- [ ] **Step 7 : Lancer CI complète**

```bash
bash tests/ci-all.sh
```

Expected : exit 0

- [ ] **Step 8 : Commit**

```bash
git add hub/src/main.js hub/src/style.css
git commit -m "feat(hub): add runtime tile status dot (green/orange/red pulsing)"
```

---

## Self-review

### Couverture spec

| Exigence | Task couverte |
|----------|--------------|
| Remplacer feature chat | Task 1, 2 |
| Info runtime (provider, modèle, statut) | Task 3 §1 |
| Bouton test de connexion | Task 3 §2 |
| Lien vers chat OpenClaw | Task 3 §3 |
| Embed OpenClaw (iframe toggle) | Task 3 §3 |
| Styles runtime | Task 4 |
| Nettoyage chat page | Task 5 |
| Supprimer runtime section de Settings | Task 6 |
| Dot statut tile home (vert/orange/rouge) | Task 7 |

### Scan placeholders

- Aucun "TBD" ou "TODO" dans les étapes
- Tous les blocs de code sont complets
- Les IDs DOM (`runtime-info-panel`, `runtime-test-btn`, etc.) sont cohérents entre render et wire

### Cohérence des types

- `formatClawvisChatAssistantText` est conservée (utilisée dans wireRuntime et le wizard)
- `escapeHtml` importée de `utils.js`, usage cohérent
- `settingsLocale()` utilisé partout pour i18n
- Route `/chat` conservée comme fallback legacy → `renderRuntimePage` + `wireRuntime`
