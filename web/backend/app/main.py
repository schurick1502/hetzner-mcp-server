"""FastAPI Backend für Hetzner Cloud MCP Web UI."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .api.routes import servers, firewalls, volumes, networks, load_balancers, misc, cli, ai, docker_monitoring, settings, security_audit, costs, health_checks, topology, bulk, snapshot_scheduler, alerting, dns, ssh_terminal

# Load environment
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Hetzner Cloud MCP API",
    description="REST API für Hetzner Cloud Management",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware - allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(servers.router, prefix="/api/servers", tags=["Servers"])
app.include_router(firewalls.router, prefix="/api/firewalls", tags=["Firewalls"])
app.include_router(volumes.router, prefix="/api/volumes", tags=["Volumes"])
app.include_router(networks.router, prefix="/api/networks", tags=["Networks"])
app.include_router(load_balancers.router, prefix="/api/load-balancers", tags=["Load Balancers"])
app.include_router(misc.router, prefix="/api", tags=["Misc"])
app.include_router(cli.router, prefix="/api/cli", tags=["CLI"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(docker_monitoring.router, prefix="/api/docker", tags=["Docker Monitoring"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(security_audit.router, prefix="/api/security", tags=["Security"])
app.include_router(costs.router, prefix="/api/costs", tags=["Costs"])
app.include_router(health_checks.router, prefix="/api/health-checks", tags=["Health Checks"])
app.include_router(topology.router, prefix="/api/topology", tags=["Topology"])
app.include_router(bulk.router, prefix="/api/servers/bulk", tags=["Bulk Operations"])
app.include_router(snapshot_scheduler.router, prefix="/api/snapshots/schedules", tags=["Snapshot Scheduler"])
app.include_router(alerting.router, prefix="/api/alerting", tags=["Alerting"])
app.include_router(dns.router, prefix="/api/dns", tags=["DNS"])
app.include_router(ssh_terminal.router, prefix="/api/ssh", tags=["SSH Terminal"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "Hetzner Cloud MCP API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "healthy"}
