# dombot-mail (core)

CLI client to read and send email for DomBot via IMAP/SMTP (Infomaniak), using `operator@dombot.tech`.

From the repo, the wrapper **`../scripts/dombot-mail.sh`** sources **`skills/_clawvis_env.sh`**, loads `.env` (skill → core → `${CLAWVIS_ROOT}/.env`), then runs this package.

## Prerequisites

- Python and `uv` installed
- Environment variables `DOMBOT_MAIL_*` set (see `../SKILL.md` for details)
- Infomaniak account: https://www.infomaniak.com

From this directory (`core/`), all commands use the same pattern:

```bash
uv run dombot-mail <subcommand> [options...]
```

## Philosophy

- **Scriptable CLI** : every command outputs **JSON** to stdout (no free-form text), for piping (`jq`), scripts, or other tools.
- **Read then archive** : the intended flow is « list → read a message by UID → handle (e.g. reply or ignore) → archive ». The `read` command does not modify anything; `archive` copies the message to the configured folder (`DOMBOT_MAIL_IMAP_ARCHIVE_FOLDER`) and removes it from the source folder.
- **Single account** : configuration (IMAP/SMTP, credentials, Sent/Archive folders) is read once at startup from environment variables; no `--config` or multi-account support in the CLI.
- **Pydantic models** : responses are typed objects (ListResult, ReadResult, SimpleResult, FoldersResult) serialized as JSON; business logic lives in `dombot_mail.service` and models in `dombot_mail.models`.

---

## Command reference

### `list` — List the latest messages in a folder

| Option     | Required | Default | Description                          |
|------------|----------|---------|--------------------------------------|
| `--folder` | yes      | —       | IMAP folder name (e.g. `INBOX`)      |
| `--limit`  | no       | `10`    | Max number of messages (most recent) |

**JSON output** : `{ "ok": true, "folder": "<folder>", "messages": [ { "uid", "subject", "sender", "to", "date", "snippet", "message_id" }, ... ] }`

```bash
uv run dombot-mail list --folder INBOX --limit 10
```

---

### `read` — Read a message by UID

| Option     | Required | Description                |
|------------|----------|----------------------------|
| `--folder` | yes      | IMAP folder containing the message |
| `--uid`    | yes      | Message UID                |

**JSON output** : `{ "ok": true, "message": { "uid", "subject", "sender", "to", "cc", "date", "snippet", "message_id", "text", "html" } }`

```bash
uv run dombot-mail read --folder INBOX --uid 1234
```

---

### `send` — Send an email

| Option      | Required | Default | Description                    |
|-------------|----------|---------|--------------------------------|
| `--to`      | yes      | —       | Recipient address(es)         |
| `--cc`      | no       | `""`    | Carbon copy                   |
| `--bcc`     | no       | `""`    | Blind carbon copy             |
| `--subject` | no       | `""`    | Subject                       |
| `--text`    | no       | `""`    | Plain-text body               |
| `--html`    | no       | —       | HTML body (optional)          |

**JSON output** : `{ "ok": true }`

```bash
uv run dombot-mail send --to "dest@example.com" --subject "Subject" --text "Body."
uv run dombot-mail send --to "a@b.com" --cc "c@d.com" --html "<p>HTML</p>"
```

---

### `reply` — Reply to a message (Re: subject, In-Reply-To; recipient inferred from From/Reply-To if `--to` is empty)

| Option     | Required | Default | Description                          |
|------------|----------|---------|--------------------------------------|
| `--folder` | yes      | —       | Folder containing the message        |
| `--uid`    | yes      | —       | UID of the message to reply to       |
| `--to`     | no       | `""`    | Recipient (otherwise From/Reply-To)  |
| `--cc`     | no       | `""`    | Carbon copy                          |
| `--bcc`    | no       | `""`    | Blind carbon copy                    |
| `--text`   | no       | `""`    | Plain-text body                      |
| `--html`   | no       | —       | HTML body (optional)                 |

**JSON output** : `{ "ok": true }`

```bash
uv run dombot-mail reply --folder INBOX --uid 1234 --text "My reply."
```

---

### `archive` — Archive a message (copy to Archive folder then delete from source folder)

| Option     | Required | Description                          |
|------------|----------|--------------------------------------|
| `--folder` | yes      | Source folder (e.g. `INBOX`)         |
| `--uid`    | yes      | UID of the message to archive        |

Destination folder is set by `DOMBOT_MAIL_IMAP_ARCHIVE_FOLDER` (e.g. `Archives`). Use `folders` to check exact names.

**JSON output** : `{ "ok": true }`

```bash
uv run dombot-mail archive --folder INBOX --uid 1234
```

---

### `folders` — List IMAP folders

No options. Prints the list of mailboxes (INBOX, Sent, Archives, etc.) to check exact names (case, accents) before using `--folder` or archive config.

**JSON output** : `{ "ok": true, "folders": [ "INBOX", "Sent", "Archives", ... ] }`

```bash
uv run dombot-mail folders
```

---

## Example flows

- Read then archive a processed message:

```bash
uv run dombot-mail read --folder INBOX --uid 2
uv run dombot-mail archive --folder INBOX --uid 2
```

- Send an email with both plain-text and HTML:

```bash
uv run dombot-mail send \
  --to "dest@example.com" \
  --cc "cc@example.com" \
  --subject "Subject" \
  --text "Plain text" \
  --html "<p>Version <strong>HTML</strong></p>"
```
