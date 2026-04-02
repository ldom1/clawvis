# Memory (Logseq + PARA)

This folder contains the default Clawvis memory tree using PARA:

- Projects — active outcomes you are working on.
- Resources — reference material you might reuse.
- Daily — daily notes and execution traces.
- Archive — inactive items.
- Todo — planning and backlog notes.

Brain : les données vivent dans `instances/<instance_name>/memory`.
Pour la stack Docker Clawvis (Hub + APIs) :

```bash
docker compose up -d hub kanban-api hub-memory-api
```

Pour ouvrir l’UI « Brain » (port configuré dans `.env`, souvent 3099), sers Quartz selon ton setup instance — il n’y a pas de service compose nommé `memory`.
Cf. `scripts/setup-quartz.sh` et la doc instance.

Puis ouvre typiquement :

- http://localhost:3099

Notes:

- The canonical runtime data is instance-scoped (`instances/<instance_name>/memory`).
- Clawvis APIs and Hub pages read/write markdown in that memory root.
