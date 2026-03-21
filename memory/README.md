# Vault (Obsidian)

This folder contains the default Clawvis Obsidian vault using the PARA approach:

- Projects — active outcomes you are working on.
- Areas — ongoing responsibilities you need to maintain.
- Resources — reference material you might reuse.
- Archives — inactive items from the three other categories.

The vault root is mounted into the `obsidian` service in `docker-compose.yml`:

```yaml
obsidian:
  volumes:
    - ./memory/vault:/config/vault
```

Start it with:

```bash
docker compose up -d obsidian
```

Then open Obsidian in your browser at:

- http://localhost:3099 (remote / reverse-proxy port)
- http://localhost:3100 (local browser port)
