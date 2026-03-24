# Memory (Logseq + PARA)

This folder contains the default Clawvis memory tree using PARA:

- Projects — active outcomes you are working on.
- Resources — reference material you might reuse.
- Daily — daily notes and execution traces.
- Archive — inactive items.
- Todo — planning and backlog notes.

Start the Brain runtime (Logseq web app):

```bash
docker compose up -d memory
```

Then open:

- http://localhost:3099

Notes:

- The canonical runtime data is instance-scoped (`instances/<instance_name>/memory`).
- Clawvis APIs and Hub pages read/write markdown in that memory root.
