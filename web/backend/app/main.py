"""FastAPI Backend für Hetzner Cloud MCP Web UI."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .api.routes import servers, firewalls, volumes, networks, load_balancers, misc

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

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
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
