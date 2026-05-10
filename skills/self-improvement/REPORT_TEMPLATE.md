# Template du rapport final — Self-Improvement Review (cron)

Quand le cron **Self-Improvement Review** est exécuté, le rapport doit être **SPÉCIFIQUE ET DÉTAILLÉ**, avec des vraies listes (pas de placeholders).

---

## Structure du rapport (à respecter)

### Titre
**Self-Improvement Review —** [date et heure, ex. 15 mars 2026 08:58]

### What's Working (Keep Doing It)
Liste 2-3 choses qui fonctionnent bien. **SOYEZ SPÉCIFIQUE** — pas de généralités.

Examples:
- ✅ 100% uptime for Curiosity Skill (autonomous execution via crons)
- ✅ High-frequency discovery logging (60+ in 22h)
- ✅ Error-free state (no critical issues detected)

### What Needs Fixing (Priority Order)
Liste 2-3 vrais problèmes / améliorations. **SOYEZ SPÉCIFIQUE** avec contexte.

Examples:
- [ ] Optimize QMD indexing (currently slow on large knowledge base)
- [ ] Fix OpenRouter / LLM upstream errors (auth, quotas)
- [ ] Review token usage in morning-briefing (could be more efficient)

### Innovation To Try
**UNE SEULE** idée concrète à essayer dans les 24h.

Examples:
- 🔮 Test parallel agent execution for multi-task workflows (Ruflo + proactive-innovation)
- 🔮 Add automated backup for .learnings/ directory
- 🔮 Implement sliding window for Curiosity retention (keep last 7 days only)

---

## Règles Strictes

1. **PAS de placeholders** (pas de "[(Details in full log)]")
2. **SPÉCIFIQUE** — chaque item doit être actionnable ou descriptif
3. **COURT** — 1-2 lignes par item
4. **LOGUÉ** — analyses détaillées : fichiers `logs/self-improvement-*.log` sous la racine Clawvis + canal Telegram selon config
5. **PAS d'écriture en MEMORY.md** — réservé aux mises à jour manuelles

---

## Format de sortie attendu

```
🔍 Self-Improvement Review — 15 mars 2026 08:58

**What's Working (Keep Doing It)**
- ✅ 100% uptime for Curiosity Skill
- ✅ High-frequency discovery logging
- ✅ Error-free state

**What Needs Fixing (Priority Order)**
- [ ] Optimize QMD indexing
- [ ] Fix OpenRouter / LLM upstream errors
- [ ] Review token usage

**Innovation To Try**
- 🔮 Test parallel agent execution
```
