---
name: morning-briefing
description: "Use when generating and sending the daily morning briefing to Ldom via Telegram. Triggered at 08:00 each day. Fetches real data from Wikipedia On This Day, Brave Search (tech headlines + top story), and local system.json metrics. Never invents data — missing sources are skipped."
metadata:
---

# Morning Briefing

## 🚀 EXÉCUTION OBLIGATOIRE — SCRIPT D'ABORD

**AVANT toute autre action**, exécuter ce script Python :

```bash
python3 ~/Lab/clawvis/skills/morning-briefing/morning-briefing.py
```

- Ce script construit le briefing à partir de sources réelles (curiosity files, Wikipedia API, system.json).
- Il envoie le résultat à Telegram via `openclaw message send`.
- **Répondre uniquement** : `Morning briefing envoyé ✅` (ou afficher le briefing généré).
- **NE PAS générer de contenu manuellement** si le script fonctionne.

Si le script échoue (ImportError, fichier manquant), suivre les étapes manuelles ci-dessous **avec sources réelles uniquement**.

---

Generate and deliver the daily morning briefing to Ldom via Telegram (ID: `5689694685`).

## 🚨 CARDINAL RULE: NO INVENTED DATA

**This is non-negotiable.** If you cannot source the data from a real API, file, or Brave search → **omit the section entirely**.

**What counts as "invented data":**
- Placeholder text like "[HEADLINE TITLE]" or "[domain.com]"
- Making up news that isn't from a real source
- Guessing system metrics when system.json is unavailable
- Assuming "3 headlines" exist when only 1 is available

**What to do instead:**
- Source missing → skip section silently
- Fewer than 3 tech headlines available? Show 1-2
- System metrics unavailable? Omit the entire System Audit section
- No Wikipedia event for today? Skip Moment Before

**Implementation:** See `~/Lab/clawvis/skills/morning-briefing/morning-briefing.py` for reference implementation with strict source validation.

## Quick Reference

| Section | Source | If Unavailable |
|---------|--------|----------------|
| Moment Before | Wikipedia On This Day API | Skip section |
| Tech Summary (3) | `web_search` — Brave API | Skip section |
| News of the Day | `web_search` — Brave API | Skip section |
| System Audit | `~/Lab/hub/public/api/system.json` | Skip section |
| Hub Remote URL | `https://lab.dombot.tech` | Fixe — toujours disponible |

---

## Data Validation Checklist (Before Building)

Before assembling ANY section, validate sources:

| Section | Source(s) | Validation | If Missing |
|---------|-----------|-----------|------------|
| **Moment Before** | Wikipedia API | `wikipedia_on_this_day.fetch_on_this_day()` returns an event | ✅ Skip silently |
| **Tech Headlines** | `memory/resources/curiosity/YYYY-MM-DD-{tech_news,tech}.md` | File exists + markdown parses | Try Brave, then skip |
| **News of Day** | `memory/resources/curiosity/YYYY-MM-DD-latest.md` | File exists + first numbered `##` block | Try Brave, then skip |
| **System Audit** | `~/Lab/hub/public/api/system.json` | File exists + has `cpu_percent`, `ram_percent`, `disk_percent`, `timestamp` | ✅ Skip silently |
| **Remote URL** | `https://lab.dombot.tech` | Fixe — toujours inclure | Fixe — ne peut pas manquer |

**Golden Rule:** Missing data = missing section. Never fill gaps with placeholders or guesses.

---

## Step 1 — Moment Before (Wikipedia)

**Implémentation repo :** `skills/morning-briefing/wikipedia_on_this_day.py` (stdlib + User-Agent) ; le script appelle `format_wikipedia_moment()` dans `morning-briefing.py`.

- Langue : variable d’environnement `WIKIPEDIA_ON_THIS_DAY_LANG` (défaut `en`). Endpoint Wikimedia :  
  `GET https://api.wikimedia.org/feed/v1/wikipedia/{lang}/onthisday/events/{month}/{day}`
- Si l’API échoue ou aucun événement exploitable → **ne pas inventer** ; section omise.

---

## Step 2 — Tech Summary (Curiosity → Brave fallback)

**Primary source (local, via `knowledge_consolidator`):**

1. Look for the most recent files in `$BRAIN_PATH/resources/knowledge/curiosity/`:
   - `YYYY-MM-DD-tech_news.md`
   - `YYYY-MM-DD-tech.md`
2. Découper les blocs avec des titres du type `## 1.`, `## 1)`, `##1.` (regex tolérante). Extraire `Title`, `Source` (ligne `**Source :**` / variantes), `Lien`, `Résumé`.
3. Use up to **3** items as the Tech Summary.

**Fallback (external, via `web_search` + Brave) — only if no local curiosity files found:**

- Run `web_search` with these queries until you have up to 3 fresh results:
  1. `"AI news"` or `"artificial intelligence today"`
  2. `"tech news today"` or `"software development news"`
  3. `"science technology news"`
- For each result, extract: `title`, `domain` (source), `url`, `snippet` (TLDR).

**Rules:**
- Max 3 results
- Prefer **local curiosity markdown**; Brave is a pure fallback
- If neither source available → **skip this section**

---

## Step 3 — News of the Day (Curiosity → Brave fallback)

**Primary source (local, via `knowledge_consolidator`):**

1. Look for the most recent `$BRAIN_PATH/resources/knowledge/curiosity/YYYY-MM-DD-latest.md`.
2. Prendre le **premier** bloc numéroté (`## 1.` / `## 1)` / etc.) + `Source`, `Lien`, `Résumé`.

**Fallback (external, via `web_search` + Brave) — only if no local curiosity file found:**

- Run `web_search` for the single most impactful story of the past 24h:
  - Query: `"breaking news today"` or `"top story [YYYY-MM-DD]"`
  - Keep: `title`, `domain`, `url`, `snippet` (2-sentence context max)

If no source (curiosity or Brave) → **skip this section**.

---

## Step 4 — System Audit (défectueux uniquement)

Inclure dans le briefing **uniquement les éléments défectueux** : exécuter `~/Lab/hub/system_audit.sh` (ou lire `~/Lab/hub/public/api/system.json` + healthcheck) et ne rapporter que ce qui est anormal (disk > 90 %, RAM > 85 %, service down, unités systemd en failed, ports ouverts suspects, mises à jour sécurité en attente). Si tout est nominal : une courte phrase du type « Système : rien à signaler » ou omettre la section.

---

## Step 5 — Hub Access URL

Le lab est accessible à l'URL fixe `https://lab.dombot.tech` — toujours inclure ce lien dans le briefing.

---

## Step 6 — Assemble Briefing

Use the template at `${CLAWVIS_ROOT}/skills/morning-briefing/BRIEFING_TEMPLATE.md`.

Replace placeholders:
- `{{DATE}}` → today's date (`YYYY-MM-DD`)
- `HH:MM` → current time
- Only render sections that have real data

**Forme du message :**
- **Phrases complètes** : rédiger en phrases (pas seulement des listes de titres).
- **Liens** : chaque info (headline, news, tech) doit avoir un lien cliquable vers la source (URL réelle).

**Iron Rules:**
1. **Never invent data.** API fails → skip section silently.
2. **No placeholders.** Empty section = omitted section.
3. **Source-traceable.** Every value comes from a named source; include link for each headline/news.
4. **Timestamps.** System audit (when shown) must show its `last updated` time.

---

## Step 7 — Send via Telegram

**Il est primordial** de respecter le format défini dans **`REPORT_TEMPLATE.md`** (à la racine du skill) pour le message envoyé à Ldom.

Send the assembled briefing using the `message` tool:

```
action: send
target: 5689694685
message: [assembled briefing]
```

---

## Output Shape (all sections present)

```
═══════════════════════════════════════════
🌅 DAILY BRIEFING — YYYY-MM-DD

🧠 HUB ACCESS
[Lab](https://lab.dombot.tech)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏳ MOMENT BEFORE — Wikipedia "On This Day"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YYYY: [historical event]
📖 [Read on Wikipedia](https://...)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 TECH SUMMARY — 3 Headlines (Brave Search API)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. **[Headline]** — *(Source: domain.com)*
   TLDR: [one-liner]
   [Read](https://...)

2. **[Headline]** — *(Source: domain.com)*
   TLDR: [one-liner]
   [Read](https://...)

3. **[Headline]** — *(Source: domain.com)*
   TLDR: [one-liner]
   [Read](https://...)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📰 NEWS OF THE DAY — Most Trending Story (Brave Search API)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**[Story Title]** — *(Source: domain.com)*

**Context:** [1-2 sentences why this matters]

[Full story](https://...)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ SYSTEM AUDIT — Alertes uniquement
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

N'afficher que les éléments défectueux (disk > 90 %, service down, failed units, etc.). Si tout est nominal : « Système : rien à signaler » ou omettre.

[Full metrics](https://lab.dombot.tech/api/system.json)

═══════════════════════════════════════════
```
