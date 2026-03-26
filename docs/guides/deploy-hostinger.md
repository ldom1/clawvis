# Déploiement Clawvis sur Hostinger VPS

> Pour les non-techniques. Aucune ligne de commande requise après la première connexion.

---

## Prérequis

- Un VPS Hostinger avec **Docker** pré-installé (template "Docker" dans hPanel)
- OpenClaw déjà déployé sur le même VPS (ou accessible via URL externe)
- Le dépôt Clawvis est **public** sur GitHub

---

## Méthode recommandée — Docker Manager dans hPanel

Hostinger fournit un **Docker Manager visuel** dans hPanel. Pas de terminal requis.

### Étape 1 — Accéder au Docker Manager

1. Connectez-vous à [hPanel](https://hpanel.hostinger.com)
2. Sélectionnez votre VPS → **Docker**
3. Cliquez **New project**
4. Choisissez **Compose from URL**

### Étape 2 — Pointer sur le docker-compose Clawvis

Dans le champ URL, collez :

```
https://raw.githubusercontent.com/YOUR_USERNAME/clawvis/main/docker-compose.yml
```

> Remplacez `YOUR_USERNAME` par votre nom d'utilisateur GitHub.

### Étape 3 — Configurer les variables d'environnement

Dans l'interface Docker Manager, ajoutez ces variables :

| Variable | Valeur | Description |
|----------|--------|-------------|
| `INSTANCE_NAME` | `mon-instance` | Nom de votre instance (sans espaces) |
| `OPENCLAW_BASE_URL` | `http://host.docker.internal:3333` | URL d'OpenClaw sur le même VPS |
| `OPENCLAW_API_KEY` | _(votre clé)_ | Clé API OpenClaw (si configurée) |
| `PRIMARY_AI_PROVIDER` | `openclaw` | Active OpenClaw comme provider |
| `HOST_UID` | `1000` | UID de l'utilisateur VPS |
| `HOST_GID` | `1000` | GID de l'utilisateur VPS |

> **OpenClaw sur le même VPS :** utilisez `http://host.docker.internal:3333`.
> Ce nom est résolu automatiquement par Docker vers la machine hôte.
>
> **OpenClaw sur un autre serveur :** utilisez l'URL complète, ex. `https://openclaw.mondomaine.com`.

### Étape 4 — Démarrer le projet

Cliquez **Deploy**. Le Docker Manager télécharge les images et démarre les conteneurs.

Accédez au Hub via : `http://<IP-de-votre-VPS>:8088`

---

## Méthode avancée — GitHub Actions (déploiement automatique)

Pour que chaque `git push` déclenche un redéploiement automatique.

### Prérequis supplémentaires

- Un compte Hostinger avec accès API
- Votre **VM ID** Hostinger (visible dans hPanel → VPS → API)
- Votre **clé API Hostinger** (hPanel → Profile → API Keys)

### Configuration

Ajoutez ces secrets dans votre dépôt GitHub (**Settings → Secrets → Actions**) :

| Secret | Valeur |
|--------|--------|
| `HOSTINGER_API_KEY` | Votre clé API Hostinger |
| `HOSTINGER_VM_ID` | L'ID de votre VPS |

Le workflow `.github/workflows/deploy-hostinger.yml` est déjà inclus dans Clawvis. Il se déclenche automatiquement sur chaque push vers `main`.

---

## Architecture sur le VPS

```
Internet
    │
    ▼
[VPS Hostinger]
    ├── Port 8088 (ou 80 avec reverse proxy)
    │       └── Hub nginx ─────────────────────────────┐
    │              ├── /api/hub/kanban/*  → kanban-api  │
    │              ├── /api/hub/memory/*  → memory-api  │
    │              └── /api/hub/chat/*    → kanban-api  │
    │                                          │        │
    │                                          ▼        │
    │                                      OpenClaw     │
    │                                    (port 3333)    │
    │                                                   │
    └── Port 3333 — OpenClaw (interne, non exposé)  ◄──┘
```

Le port OpenClaw **n'est pas exposé** à l'extérieur — seul le Hub (port 8088/80) est accessible.

---

## Ajouter un nom de domaine

Pour accéder à `https://clawvis.mondomaine.com` au lieu d'une IP :

1. Dans hPanel → **Domaines** → pointez un sous-domaine vers l'IP du VPS
2. Installez nginx en reverse proxy sur le VPS :

```bash
# Connexion SSH au VPS
ssh root@<IP-VPS>

# Installer nginx
apt install nginx -y

# Créer la config (remplacez clawvis.mondomaine.com)
cat > /etc/nginx/sites-available/clawvis <<'CONF'
server {
    listen 80;
    server_name clawvis.mondomaine.com;
    location / {
        proxy_pass http://127.0.0.1:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
CONF

ln -s /etc/nginx/sites-available/clawvis /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# SSL (Let's Encrypt)
apt install certbot python3-certbot-nginx -y
certbot --nginx -d clawvis.mondomaine.com
```

---

## Vérification du déploiement

Après démarrage, vérifiez que tout fonctionne :

```bash
# Depuis votre machine locale (remplacez l'IP)
curl http://<IP-VPS>:8088/api/hub/chat/status
# Attendu: {"provider":"openclaw","openclaw_configured":true,...}

curl http://<IP-VPS>:8088/api/hub/kanban/hub/projects
# Attendu: {"projects":[...]}

curl http://<IP-VPS>:8088/api/hub/memory/settings
# Attendu: {"projects_root":...}
```

---

## Mise à jour

Pour mettre à jour Clawvis vers une nouvelle version :

**Via Docker Manager :** Ouvrez le projet → **Update** → le manager repull et redémarre.

**Via GitHub Actions :** faites un push sur `main` — le redéploiement est automatique.

---

## Dépannage

| Symptôme | Cause probable | Solution |
|----------|----------------|----------|
| Chat ne répond pas | OpenClaw injoignable | Vérifier `OPENCLAW_BASE_URL`, tester `curl http://host.docker.internal:3333/v1/models` depuis le conteneur |
| Kanban vide | `INSTANCE_NAME` pas défini | Vérifier la variable dans hPanel Docker Manager |
| Brain ne charge pas | Quartz non buildé | `docker exec <hub-memory-api> bash scripts/build-quartz.sh` |
| Port 8088 inaccessible | Pare-feu VPS | hPanel → VPS → Firewall → autoriser port 8088 |
