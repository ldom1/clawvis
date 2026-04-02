# OpenClaw — Telegram / Discord et transcription vocale (Clawvis)

Ce guide relie **les canaux messagers** (Telegram, Discord) gérés par **OpenClaw** à la transcription audio, en s’appuyant sur **Faster Whisper** déjà intégré dans `hub-core` (sans clé API).

Référence upstream : [Audio and Voice Notes](https://docs.openclaw.ai/audio).

---

## Vue d’ensemble

| Couche | Rôle |
|--------|------|
| **OpenClaw** | Reçoit les vocal sur Telegram/Discord, télécharge le média, appelle `tools.media.audio` |
| **`tools.media.audio`** | Chaîne de modèles (API ou CLI) ; le transcript remplace le corps du message pour l’agent |
| **Clawvis `hub_core transcribe`** | CLI locale : Faster Whisper via `uv run` dans `hub-core/` |

Même configuration **`tools.media.audio`** pour **tous** les canaux : une fois activée, les notes vocales Telegram **et** Discord (selon ce qu’OpenClaw supporte pour Discord dans ta version) passent par la même pipeline.

---

## 1. Prérequis locaux

```bash
cd /chemin/vers/clawvis/hub-core
uv sync
uv pip install faster-whisper
```

Test manuel :

```bash
uv run python -m hub_core transcribe /chemin/vers/note.ogg -l fr -m base
```

Le texte doit s’afficher sur stdout.

---

## 2. Brancher Telegram ou Discord (OpenClaw)

La connexion des **bots** et **tokens** se fait dans la config OpenClaw (souvent `~/.openclaw/openclaw.json` + secrets / profils d’auth). Suit la doc OpenClaw pour :

- créer le bot Telegram / application Discord ;
- renseigner `channels.telegram` / `channels.discord` (noms exacts selon ta version d’OpenClaw) ;
- redémarrer la gateway : `openclaw gateway restart`.

Sans canaux configurés, aucune transcription ne sera déclenchée côté messager.

---

## 3. Activer la transcription (automatique ou manuelle)

### Option A — Script Clawvis (recommandé)

Depuis la racine du dépôt Clawvis :

```bash
# Fragment JSON + instructions (un seul script)
bash scripts/transcribe-audio.sh --config

# Backup openclaw.json puis fusion (si absent, même entrée CLI)
bash scripts/transcribe-audio.sh --config --apply
```

Le script ne fait qu’appeler **`uv run python -m hub_core openclaw-audio-config`** dans `hub-core/` ; toute la fusion JSON est dans le module [`hub_core/openclaw_audio_config.py`](../../hub-core/hub_core/openclaw_audio_config.py).

Variable optionnelle : `OPENCLAW_JSON=/chemin/vers/openclaw.json`.

Puis :

```bash
openclaw gateway restart
```

Le script unique est [`scripts/transcribe-audio.sh`](../../scripts/transcribe-audio.sh) : en usage normal il appelle `uv run python -m hub_core transcribe` avec le fichier OpenClaw (`{{MediaPath}}`) ; `--config` sert à générer / fusionner `tools.media.audio`.

Variables d’environnement optionnelles pour le **process** lancé par OpenClaw (si tu les exportes avant `gateway start` ou via ton unit systemd) :

| Variable | Défaut | Rôle |
|----------|--------|------|
| `TRANSCRIBE_LANG` | `fr` | Langue Whisper |
| `TRANSCRIBE_MODEL` | `base` | `tiny`, `base`, `small`, etc. |

### Option B — Fournisseur cloud (sans Whisper local)

Tu peux à la place (ou en complément, avant/après le CLI) utiliser OpenAI, Deepgram, Mistral Voxtral, etc., comme décrit dans la [doc audio OpenClaw](https://docs.openclaw.ai/audio). Configure alors `models` avec `provider` + clés API selon la doc.

### Option C — Manually merge

Si tu préfères éditer à la main, ajoute sous `tools.media` un bloc `audio` avec un modèle `"type": "cli"` pointant vers le **chemin absolu** de `transcribe-audio.sh` et `"args": ["{{MediaPath}}"]`.

---

## 4. Groupes Telegram et mentions

Pour les **groupes** avec `requireMention: true`, OpenClaw peut faire une **transcription préalable** pour détecter la mention dans le vocal. Voir la section *Mention Detection in Groups* sur [docs.openclaw.ai/audio](https://docs.openclaw.ai/audio).

---

## 5. Intégration côté skills Clawvis

Le skill **project-init** attend un texte ; pour un vocal Telegram, le flux typique est : **OpenClaw transcrit** → le corps du message vu par l’agent contient le transcript → le skill peut enchaîner (voir [`skills/project-init/SKILL.md`](../../skills/project-init/SKILL.md)).

En mode manuel hors OpenClaw : `uv run python -m hub_core transcribe <fichier>`.

---

## 6. Dépannage rapide

| Symptôme | Piste |
|----------|--------|
| Pas de transcript | Vérifier `tools.media.audio.enabled`, logs gateway `--verbose`, présence de `faster-whisper` |
| Timeout | Augmenter `timeoutSeconds` (Whisper CPU sur gros fichiers) |
| Permission / PATH | Utiliser un **chemin absolu** pour `command` du modèle CLI |
| Discord seulement | Confirmer dans la doc OpenClaw de ta version que les pièces audio Discord passent par la même pipeline `tools.media.audio` |

---

## Voir aussi

- [`scripts/transcribe-audio.sh`](../../scripts/transcribe-audio.sh) — transcription + `--config` / `--config --apply`  
- [`hub-core/hub_core/transcribe/`](../../hub-core/hub_core/transcribe/) — implémentation Faster Whisper
