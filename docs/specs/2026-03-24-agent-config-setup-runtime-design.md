# Design Spec — Page `/setup/runtime/` (Agent Configuration Wizard)

**Date:** 2026-03-24
**Status:** Approved

---

## Problem

The current AI runtime configuration flow is buried:
- Home shows a small banner → links to `/settings/`
- Settings opens a **modal** with a 3-step wizard (no tutorial, no pédagogie)
- No explanation of what each provider is, how to get a key, or how to validate the setup
- After install, the CLI points to `/settings/` — not obvious for a new user

Result: users who skip the banner have no clear path to configure their agent, and the Chat tool silently fails.

---

## Goal

A **dedicated page** at `/setup/runtime/` that is the single, canonical entry point for agent configuration. It must:
- Be the target of all "configure runtime" CTAs in the hub
- Walk the user through 4 clear steps with inline explanation
- Include a live connection test and a mini-chat validation at the end
- Be non-blocking (user can still navigate the hub freely)

---

## Architecture

### New route

In `hub/src/main.js`:
- `renderSetupRuntime()` — HTML for the full page
- `wireSetupRuntime()` — step state machine, test call, mini-chat
- Dispatched in the existing router: `path.startsWith("/setup/runtime")`

Step state is managed by a local `let step = 1` variable (1–4). No URL change between steps — everything stays at `/setup/runtime/`.

### API endpoints (correct paths)

| Purpose | Endpoint |
|---------|----------|
| Test connection (step 3) | `GET /api/hub/chat/status` |
| Live test ping (step 3) | `POST /api/hub/chat` |
| Mini-chat (step 4) | `POST /api/hub/chat` |

No new backend endpoints needed. The existing chat endpoints are reused.

### Storage

Credentials stay in `localStorage` (unchanged from current behavior):
- `ai-provider`
- `ai-claude-key`
- `ai-mistral-key`
- `ai-openclaw-url`

---

## The 4 Steps

### Step 1 — Choose your provider

Three provider cards (Claude / Mistral / OpenClaw), reusing existing `.wizard-provider-card` CSS.

Each card shows:
- Icon + name + owner label
- 2-line description (e.g. "Most capable for complex tasks — cloud API")
- Badge: `Cloud` or `Self-hosted`

**Claude:** "Le modèle le plus capable d'Anthropic pour les tâches complexes. Clé API sur console.anthropic.com."
**Mistral:** "Modèle open-weight performant. Clé API sur console.mistral.ai."
**OpenClaw:** "Instance auto-hébergée compatible OpenAI. Renseigne l'URL de ton serveur."

Selected card gets an accent outline. "Next →" is enabled immediately after selecting.

### Step 2 — Get & enter credentials

Context-aware block based on selected provider:

**Claude / Mistral:**
- Link to provider console (opens in new tab)
- Short instruction: "Crée un compte, génère une clé API, colle-la ici."
- `<input type="password">` + show/hide toggle
- Placeholder: `sk-ant-...` (Claude) or `...` (Mistral)

**OpenClaw:**
- URL field: `http://host:port` hint
- Optional API key field (secondary)

Security note (subtle, below the field):
> "La clé est stockée dans ton navigateur (localStorage). Elle n'est jamais envoyée à nos serveurs."

"Next →" enabled when field is non-empty.

### Step 3 — Test the connection

Single prominent "Lancer le test" button, centered.

States:
- Idle: button visible
- Loading: spinner + "Connexion en cours…"
- Success: green banner "Connexion réussie — ton runtime répond." + collapsible raw response
- Error: red banner with readable error message (no stack trace) + suggestion ("Vérifie ta clé", "Vérifie l'URL")

"Next →" is **only enabled after a successful test**.

### Step 4 — Mini-chat validation

Minimal inline chat (height ~300px, scroll interne):
- Pre-filled assistant bubble: "Bonjour ! Je suis ton runtime IA. Pose-moi une question pour vérifier que tout fonctionne."
- Input at the bottom + Send button
- No history persistence (session only)

"Terminer →" button:
- Saves all values to `localStorage`
- Redirects to `/`

---

## Visual Structure

### Page header

Same template as other sub-pages (`settings-page-header`):
- Title: `Setup · Clawvis` (accent span on "Clawvis")
- Subtitle: "Configure ton runtime IA en 4 étapes." (i18n FR/EN)
- Back link ←
- Theme toggle

### Stepper

Horizontal bar, fixed below the header:
- 4 numbered circles connected by a line
- Active = accent color
- Completed = green check
- Future = grey
- Completed steps are clickable (to go back); future steps are not

---

## Changes to Existing Entry Points

| Location | Current | New |
|----------|---------|-----|
| Home `ai-runtime-banner` CTA | `/settings/` | `/setup/runtime/` |
| Chat page warn link | `/settings/` | `/setup/runtime/` |
| Settings page runtime section | Opens modal | Link to `/setup/runtime/` |
| CLI `doneSettings` message | `/settings/` | `/setup/runtime/` |

### Home banner states

**Not configured:**
- Background: amber/warn
- Text: "Runtime IA non configuré"
- CTA: "Configurer →" → `/setup/runtime/`

**Configured:**
- Background: green/ok
- Text: "Connecté · Claude" (or Mistral / OpenClaw)
- CTA: "Modifier" → `/setup/runtime/` (fields pre-filled from localStorage)

---

## What Is Removed

- The `#ai-wizard-overlay` modal and all its HTML from `renderSettings()`
- Event listeners: `open-ai-wizard`, `wizard-step-*`, `wizard-back-*`, `wizard-next-2`, `wizard-save-btn`, `wizard-test-btn` from `wireSettings()`

---

## Files Modified

| File | Change |
|------|--------|
| `hub/src/main.js` | + `renderSetupRuntime()`, `wireSetupRuntime()`, router entry. Update `renderHome()` banner CTA. Update `renderSettings()` (remove modal, replace button with link). Update `renderChatPage()` warn link. |
| `hub/src/style.css` | + stepper styles, provider-detail block, live test result, inline mini-chat |
| `clawvis-cli/cli.mjs` | `doneSettings` URL → `/setup/runtime/` |
| `docs/playwright-persona.md` | Rewrite Persona 1 (4-step full page wizard). Fix Persona 5 (no modal in settings). Fix Persona 6 (warn link → `/setup/runtime/`). |

---

## Out of Scope

- Backend key storage (keys stay in localStorage)
- New API endpoints (reuses `/api/hub/chat`)
- `clawvis setup provider` CLI command (separate future task)
- Additional `/setup/workspace/` steps (stepper is extensible but not implemented here)
