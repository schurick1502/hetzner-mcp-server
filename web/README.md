# Hetzner Cloud Web UI

Moderne Web-UI für Hetzner Cloud Management mit FastAPI Backend und React Frontend.

## 🚀 Features

- **Dashboard**: Übersicht aller Ressourcen
- **Server-Management**: Erstellen, Starten, Stoppen, Löschen
- **Firewall-Management**: Regeln konfigurieren und anwenden
- **Volume-Management**: Volumes erstellen und an Server anhängen
- **Network-Management**: Private Netzwerke verwalten
- **Responsive Design**: Funktioniert auf Desktop und Mobile
- **Docker-basiert**: Einfaches Deployment

## 📋 Voraussetzungen

- Docker & Docker Compose
- Hetzner Cloud API Token

## 🛠️ Installation

### Development

1. **Repository klonen & in web/ wechseln**
   ```bash
   cd web
   ```

2. **Environment konfigurieren**
   ```bash
   cp .env.example .env
   # Bearbeite .env und füge deinen HCLOUD_TOKEN ein
   ```

3. **Docker Compose starten**
   ```bash
   cd ..
   docker-compose up -d
   ```

4. **Öffne im Browser**
   - Frontend: http://localhost:5173
   - Backend API Docs: http://localhost:8000/api/docs

### Production

1. **Environment konfigurieren**
   ```bash
   cp web/.env.example web/.env
   # HCLOUD_TOKEN setzen
   ```

2. **Production Build starten**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Öffne im Browser**
   - Web-UI: http://localhost

## 🏗️ Architektur

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Browser   │─────▶│    Nginx     │─────▶│  FastAPI Backend│
│  (React)    │      │ (Reverse Proxy)      │   (Python)      │
└─────────────┘      └──────────────┘      └─────────────────┘
                                                     │
                                                     ▼
                                            ┌─────────────────┐
                                            │  Hetzner Cloud  │
                                            │      API        │
                                            └─────────────────┘
```

### Backend (FastAPI)
- **Framework**: FastAPI + Uvicorn
- **API**: RESTful Endpoints
- **Tools**: Nutzt hetzner_mcp.tools direkt
- **Docs**: Auto-generierte Swagger UI unter /api/docs

### Frontend (React + TypeScript)
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS
- **State**: TanStack Query (React Query)
- **Routing**: React Router v6
- **Icons**: Lucide React

## 📁 Struktur

```
web/
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py              # FastAPI App
│       └── api/
│           └── routes/          # API Endpoints
│               ├── servers.py
│               ├── firewalls.py
│               ├── volumes.py
│               └── ...
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf               # Nginx Config
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── src/
│       ├── App.tsx              # Main App
│       ├── pages/               # React Pages
│       │   ├── DashboardPage.tsx
│       │   ├── ServersPage.tsx
│       │   └── ...
│       └── services/
│           └── api.ts           # API Client
│
└── docker-compose.yml           # Development
└── docker-compose.prod.yml      # Production
```

## 🔧 Development

### Backend entwickeln
```bash
cd web/backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend entwickeln
```bash
cd web/frontend
npm install
npm run dev
```

### Mit Docker entwickeln
```bash
# Hot-reload für beide Services
docker-compose up

# Logs anzeigen
docker-compose logs -f

# Einzelner Service neu starten
docker-compose restart backend
docker-compose restart frontend
```

## 📝 API Endpoints

### Servers
- `GET /api/servers` - Liste aller Server
- `POST /api/servers` - Server erstellen
- `DELETE /api/servers/{id}` - Server löschen
- `POST /api/servers/{id}/power` - Power-Aktion
- `POST /api/servers/{id}/backup/enable` - Backup aktivieren

### Firewalls
- `GET /api/firewalls` - Liste aller Firewalls
- `POST /api/firewalls` - Firewall erstellen
- `POST /api/firewalls/{id}/rules` - Regel hinzufügen

### Volumes
- `GET /api/volumes` - Liste aller Volumes
- `POST /api/volumes` - Volume erstellen
- `POST /api/volumes/{vol}/attach/{server}` - Volume anhängen

Vollständige API-Dokumentation: http://localhost:8000/api/docs

## 🎨 UI Screenshots

### Dashboard
- Übersicht aller Ressourcen
- Schnellzugriff auf letzte Server
- Statistiken

### Server-Management
- Tabellarische Übersicht
- Power-Buttons (Start, Stop, Reboot)
- Schnelles Löschen
- Server erstellen mit Formular

## 🐳 Docker Commands

```bash
# Starten
docker-compose up -d

# Stoppen
docker-compose down

# Neu builden
docker-compose build

# Logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Container betreten
docker-compose exec backend sh
docker-compose exec frontend sh
```

## 🔒 Sicherheit

- CORS ist konfiguriert
- API-Token wird nur im Backend gespeichert
- Nginx Security Headers gesetzt
- Force-Delete für destruktive Aktionen

## 🚀 Deployment

### Mit Docker Swarm
```bash
docker stack deploy -c docker-compose.prod.yml hetzner
```

### Mit Kubernetes
Siehe `kubernetes/` Verzeichnis für Manifests (TODO)

## 📦 Updates

```bash
# Code pullen
git pull

# Container neu builden und starten
docker-compose down
docker-compose build
docker-compose up -d
```

## 🐛 Troubleshooting

### Backend startet nicht
```bash
# Logs prüfen
docker-compose logs backend

# Environment-Variablen prüfen
docker-compose exec backend env | grep HCLOUD
```

### Frontend verbindet nicht zum Backend
- Prüfe CORS_ORIGINS in .env
- Prüfe ob Backend läuft: http://localhost:8000/health

### Ports bereits belegt
```bash
# Andere Ports in docker-compose.yml setzen
ports:
  - "8001:8000"  # Backend
  - "3000:80"    # Frontend
```

## 📚 Weitere Informationen

- [FastAPI Dokumentation](https://fastapi.tiangolo.com/)
- [React Dokumentation](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## 🤝 Contributing

PRs willkommen! Siehe CONTRIBUTING.md

## 📄 Lizenz

MIT
