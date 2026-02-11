# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP (Model Context Protocol) Server for Hetzner Cloud API with **117 tools** and a Web-UI. Enables Claude Desktop/Code to manage Hetzner Cloud resources directly.

## Commands

```bash
# MCP Server Development
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/Mac
pip install -e ".[dev]"

# Run MCP Server
python -m hetzner_mcp.server

# Run Tests
pytest
pytest --cov=hetzner_mcp

# Web-UI Development (Docker)
docker-compose up -d           # Start dev environment
docker-compose down            # Stop
docker-compose logs -f         # View logs
docker-compose build           # Rebuild images

# Web-UI Development (Local)
cd web/backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd web/frontend && npm install && npm run dev
```

## Architecture

### Data Flow
```
Claude Desktop/Code  →  MCP Protocol  →  hetzner_mcp.server  →  hcloud Library  →  Hetzner Cloud API
Browser (React)      →  Nginx         →  FastAPI Backend     →  hetzner_mcp.tools →  Hetzner Cloud API
```

### Key Components

| Path | Purpose |
|------|---------|
| `src/hetzner_mcp/server.py` | FastMCP server with 117 tool registrations |
| `src/hetzner_mcp/config.py` | Configuration & hcloud API client singleton |
| `src/hetzner_mcp/tools/` | Tool implementations by resource type |
| `web/backend/` | FastAPI backend serving the same tools via REST |
| `web/frontend/` | React + TypeScript + Tailwind CSS dashboard |

### Tool Modules (`src/hetzner_mcp/tools/`)

- `servers.py` - Server lifecycle, rescue, metrics, snapshots (18 tools)
- `load_balancers.py` - LB services, targets, algorithms (9 tools)
- `firewalls.py` - Rules, server application (8 tools)
- `volumes.py` - Attach, detach, resize (8 tools)
- `networks.py` - Subnets, routes, server connections (12 tools)
- `certificates.py` - SSL/TLS, Let's Encrypt managed (6 tools)
- `misc.py` - Floating IPs, Primary IPs, SSH keys, Images (25+ tools)
- `isos.py` - ISO management (2 tools)
- `placement_groups.py` - Anti-affinity groups (4 tools)

## Tool Development Pattern

### Adding New Tools

1. Implement in appropriate `tools/*.py`:
```python
async def hcloud_resource_action(identifier: str, force: bool = False) -> dict:
    """Description for Claude."""
    try:
        client = get_client()
        # ... implementation
        return {"success": True, "message": "...", "data": {...}}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

2. Register in `server.py`:
```python
@mcp.tool()
async def resource_action(identifier: str, force: bool = False) -> dict:
    """Description shown to Claude."""
    return await hcloud_resource_action(identifier, force)
```

### Response Format

All tools must return consistent dict format:
- Success: `{"success": True, "message": "...", "data": {...}}`
- Error: `{"success": False, "error": "description"}`

### Destructive Actions

All delete/rebuild operations require `force: bool = False` parameter:
```python
if not force:
    return {"success": False, "error": "Zum Löschen muss force=True gesetzt werden"}
```

## Configuration

- `HCLOUD_TOKEN` - Required: Hetzner Cloud API token
- `CORS_ORIGINS` - Web-UI allowed origins
- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY` - Optional AI providers for Web-UI

## Claude Desktop Integration

Add to `%APPDATA%\Claude\claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "hetzner": {
      "command": "C:\\projekte\\hetzner-mcp-server\\venv\\Scripts\\python.exe",
      "args": ["-m", "hetzner_mcp.server"],
      "env": {"HCLOUD_TOKEN": "your_token"}
    }
  }
}
```

## Ports

- `5173` - Frontend dev server (Vite)
- `8001` - Backend API (FastAPI)
- `8000/api/docs` - Swagger UI (when backend running)
