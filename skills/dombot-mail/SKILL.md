---
name: dombot-mail
description: List folders and emails, read, send, reply, and archive mail via Infomaniak IMAP/SMTP using the dombot-mail CLI in skills/dombot-mail/core (needs uv). Requires DOMBOT_MAIL_USER and DOMBOT_MAIL_PASSWORD. Use when the user asks to check mail, send email, or process messages for operator@dombot.tech.
---

# dombot-mail

Racine dépôt : **`CLAWVIS_ROOT`** (répertoire contenant `hub-core/` et `skills/`). Sinon export explicite ou chemins fallback `~/lab/clawvis` / `~/Lab/clawvis`.

## ⚡ Exécution rapide

```bash
# Via script wrapper (recommandé — source skills/_clawvis_env.sh + .env)
${CLAWVIS_ROOT:-$HOME/lab/clawvis}/skills/dombot-mail/scripts/dombot-mail.sh <subcommand> [options]

# Exemples
${CLAWVIS_ROOT:-$HOME/lab/clawvis}/skills/dombot-mail/scripts/dombot-mail.sh list --folder INBOX --limit 10
${CLAWVIS_ROOT:-$HOME/lab/clawvis}/skills/dombot-mail/scripts/dombot-mail.sh folders
${CLAWVIS_ROOT:-$HOME/lab/clawvis}/skills/dombot-mail/scripts/dombot-mail.sh read --folder INBOX --uid 1234

# Ou directement via uv depuis core/
cd "${CLAWVIS_ROOT:-$HOME/lab/clawvis}/skills/dombot-mail/core" && uv run dombot-mail list --folder INBOX --limit 10
```

## 📢 Slack — Notifier après traitement mail

Pour notifier Ldom sur Slack lors du traitement automatique de mails importants :

```bash
# Notification simple (canal ops)
${CLAWVIS_ROOT:-$HOME/lab/clawvis}/skills/logger/scripts/slack-send.sh ops "📧 Nouveau mail important: <sujet> — <expéditeur>"

# Log structuré + Slack (traces sous ${CLAWVIS_ROOT}/logs/)
${CLAWVIS_ROOT:-$HOME/lab/clawvis}/skills/logger/scripts/dombot-log.sh INFO "cron:dombot-mail" system "mail:received" "Nouveau mail de X"
```

Voir le skill `logger` pour la configuration Slack (DOMBOT_SLACK_OPS).

Read and send email for DomBot via **Infomaniak** IMAP/SMTP using the address `operator@dombot.tech`. The agent runs the Python CLI in **`${CLAWVIS_ROOT}/skills/dombot-mail/core`** (see `core/README.md` for full reference).

**Capabilities:** list folders, list emails in a folder, read a message by UID, send email, reply to a thread, archive a message after processing.

---

## Environment

Configurer les variables ci-dessous dans **`${CLAWVIS_ROOT}/.env`**, dans `skills/dombot-mail/.env`, ou dans l’environnement du process (Compose / cron). Ordre de chargement côté Python : skill → core → racine repo (la racine prime pour les clés partagées avec l’agent).

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `DOMBOT_MAIL_IMAP_HOST` | yes | `imap.infomaniak.com` | IMAP host |
| `DOMBOT_MAIL_IMAP_PORT` | yes | `993` | IMAP port |
| `DOMBOT_MAIL_SMTP_HOST` | yes | `mail.infomaniak.com` | SMTP host |
| `DOMBOT_MAIL_SMTP_PORT` | yes | `465` or `587` | SMTP port |
| `DOMBOT_MAIL_USER` | yes | `operator@dombot.tech` | Account login |
| `DOMBOT_MAIL_PASSWORD` | yes | — | App/bridge password |

Optional:

- `DOMBOT_MAIL_IMAP_SENT_FOLDER` — e.g. `Sent` or `INBOX.Sent`
- `DOMBOT_MAIL_IMAP_ARCHIVE_FOLDER` — e.g. `Archives` (used by `archive`)

---

## Running the CLI

All commands are run from the skill’s **core** directory. Use the shell/exec tool:

```bash
cd "${CLAWVIS_ROOT:-$HOME/lab/clawvis}/skills/dombot-mail/core" && uv run dombot-mail <subcommand> [options...]
```

Every subcommand outputs **JSON** to stdout (no free-form text). Use `jq` if you need to parse it.

---

## Commands

### `folders` — List IMAP folders

Use to discover folder names (INBOX, Sent, Archives, etc.) before `list`/`read`/`archive`.

```bash
cd "${CLAWVIS_ROOT:-$HOME/lab/clawvis}/skills/dombot-mail/core" && uv run dombot-mail folders
```

Output: `{ "ok": true, "folders": [ "INBOX", "Sent", "Archives", ... ] }`

---

### `list` — List latest messages in a folder

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--folder` | yes | — | IMAP folder (e.g. `INBOX`) |
| `--limit` | no | `10` | Max number of messages |

```bash
cd "${CLAWVIS_ROOT:-$HOME/lab/clawvis}/skills/dombot-mail/core" && uv run dombot-mail list --folder INBOX --limit 20
```

Output: `{ "ok": true, "folder": "<folder>", "messages": [ { "uid", "subject", "sender", "to", "date", "snippet", "message_id" }, ... ] }`

---

### `read` — Read a message by UID

| Option | Required | Description |
|--------|----------|-------------|
| `--folder` | yes | Folder containing the message |
| `--uid` | yes | Message UID |

```bash
cd "${CLAWVIS_ROOT:-$HOME/lab/clawvis}/skills/dombot-mail/core" && uv run dombot-mail read --folder INBOX --uid 1234
```

Output: `{ "ok": true, "message": { "uid", "subject", "sender", "to", "cc", "date", "snippet", "message_id", "text", "html" } }`. Prefer the `text` field for summarising, replying, or extracting tasks.

---

### `send` — Send an email

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--to` | yes | — | Recipient(s) |
| `--cc` | no | `""` | CC |
| `--bcc` | no | `""` | BCC |
| `--subject` | no | `""` | Subject |
| `--text` | no | `""` | Plain-text body |
| `--html` | no | — | HTML body (optional) |

```bash
cd "${CLAWVIS_ROOT:-$HOME/lab/clawvis}/skills/dombot-mail/core" && uv run dombot-mail send --to "dest@example.com" --subject "Subject" --text "Body."
```

Output: `{ "ok": true }`

---

### `reply` — Reply to a message (keeps thread: Re:, In-Reply-To, References)

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `--folder` | yes | — | Folder of the message |
| `--uid` | yes | — | UID to reply to |
| `--to` | no | `""` | Override recipient (else From/Reply-To) |
| `--cc`, `--bcc` | no | `""` | CC/BCC |
| `--text` | no | `""` | Plain-text body |
| `--html` | no | — | HTML body (optional) |

```bash
cd "${CLAWVIS_ROOT:-$HOME/lab/clawvis}/skills/dombot-mail/core" && uv run dombot-mail reply --folder INBOX --uid 1234 --text "My reply."
```

Output: `{ "ok": true }`

---

### `archive` — Archive a message (copy to archive folder, then delete from source)

Use after processing a message (e.g. read + reply). Destination is `DOMBOT_MAIL_IMAP_ARCHIVE_FOLDER`; use `folders` to confirm exact name.

| Option | Required | Description |
|--------|----------|-------------|
| `--folder` | yes | Source folder (e.g. `INBOX`) |
| `--uid` | yes | UID to archive |

```bash
cd "${CLAWVIS_ROOT:-$HOME/lab/clawvis}/skills/dombot-mail/core" && uv run dombot-mail archive --folder INBOX --uid 1234
```

Output: `{ "ok": true }`

---

## Usage rules

- **No fabricated addresses:** Use addresses from existing messages or from explicit user instructions.
- **Confirm before sending:** Before `send` or `reply`, draft the text, show it to the user, and send only after explicit approval (e.g. “Yes, send” / “OK to send”).
- **Language:** Use the user’s language unless they ask otherwise.
- **Long bodies:** Prefer summarising or quoting when the user only wants an overview.

---

## Example workflows

- **Browse and read:** Run `folders` → `list --folder INBOX --limit N` → `read --folder INBOX --uid <uid>`; summarise or act on `message.text`.
- **Reply then archive:** `read` → propose reply → after user approval run `reply` → then `archive` for that UID.
- **New email:** Draft with `send` params, get approval, then run `send`.
- **Process and archive:** After handling a message (reply or ignore), run `archive --folder <folder> --uid <uid>` so it is moved to the archive folder.

---

## Quick pattern for "lis mes mails + tableau"

If user asks to read inbox and return interesting messages in a table:

1. `list --folder INBOX --limit <N>`
2. `read` only selected UIDs (high-signal subject/sender/snippet)
3. Return a **Markdown table** with: `UID | Date | Sender | Subject | Why interesting | Action`
4. If requested, append knowledge notes to `memory/resources/curiosity/` and archive handled emails with `archive`.

---

## Quick pattern — "Write / send an email"

When the user asks to write or send an email:

1. Clarify **recipient(s)** (required), **subject**, and **body** (full text or bullet points).
2. Draft the message (subject + body in plain text) and show it to the user.
3. After explicit approval ("send", "OK"): run `send --to "<address>" --subject "..." --text "..."`.
4. Confirm send and note that the email is sent from `operator@dombot.tech`.

---

## Quick pattern — "Archive an email"

When the user asks to archive an email (or "move to archive"):

1. Identify the message: by UID if known, or run `list --folder INBOX --limit N` and ask which to archive (or use the last one read).
2. Run: `archive --folder INBOX --uid <uid>` (or the source folder if not INBOX).
3. Confirm: "Email UID &lt;uid&gt; archived to &lt;DOMBOT_MAIL_IMAP_ARCHIVE_FOLDER&gt;."

---

## Quick pattern — "Read mail and if interesting, add to your brain"

When the user asks to read mail(s) and, if interesting, add interesting content to brain:

1. **List:** `list --folder INBOX --limit N` to get recent messages.
2. **Read:** For each candidate, `read --folder INBOX --uid <uid>` to get full `message.text`.
3. **Process:** Decide if the content is worth keeping (facts, insights, tasks, references). Extract a short note (title + 1–3 sentences or bullets).
4. **Add to memory:** Append to `memory/resources/curiosity/YYYY-MM-DD-mail.md` (or create it) with: date, sender, subject, and the extracted note. Optionally link from relevant `memory/projects/*.md` if it relates to a project.
5. **Archive:** Run `archive --folder INBOX --uid <uid>` for each processed message so it is moved out of INBOX.
6. **Confirm:** Tell the user how many mails were read, how many were added to knowledge, and that they were archived.
