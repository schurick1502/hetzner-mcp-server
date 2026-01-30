"""CLI API Routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import importlib
import inspect
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../..'))

router = APIRouter()


class CommandRequest(BaseModel):
    command: str
    args: Dict[str, Any] = {}


def get_mcp_tools():
    """Alle MCP-Tools aus server.py extrahieren."""
    tools = []

    # Import MCP server module
    try:
        mcp_module = importlib.import_module('src.hetzner_mcp.server')
    except ImportError:
        return []

    # Finde alle Tool-Funktionen (die mit @mcp.tool() dekoriert sind)
    for name, obj in inspect.getmembers(mcp_module):
        if inspect.iscoroutinefunction(obj) and not name.startswith('_'):
            sig = inspect.signature(obj)
            params = []
            for param_name, param in sig.parameters.items():
                param_type = 'str'
                if param.annotation != inspect.Parameter.empty:
                    param_type = str(param.annotation).replace("<class '", "").replace("'>", "")

                params.append({
                    'name': param_name,
                    'type': param_type,
                    'required': param.default == inspect.Parameter.empty,
                    'default': str(param.default) if param.default != inspect.Parameter.empty else None
                })

            tools.append({
                'name': name,
                'description': obj.__doc__.strip() if obj.__doc__ else '',
                'parameters': params
            })

    return tools


@router.get("/tools")
async def list_tools():
    """Liste aller verfügbaren MCP-Tools."""
    return {"tools": get_mcp_tools()}


@router.post("/execute")
async def execute_command(request: CommandRequest):
    """Führt ein MCP-Tool aus."""
    import time

    start_time = time.time()

    # Import MCP server
    try:
        mcp_server = importlib.import_module('src.hetzner_mcp.server')
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"MCP Server konnte nicht geladen werden: {str(e)}"
        )

    # Finde Tool-Funktion
    if not hasattr(mcp_server, request.command):
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{request.command}' nicht gefunden"
        )

    tool_func = getattr(mcp_server, request.command)

    try:
        # Führe Tool aus
        result = await tool_func(**request.args)

        execution_time = (time.time() - start_time) * 1000

        return {
            "success": True,
            "output": result,
            "execution_time_ms": round(execution_time, 2)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "execution_time_ms": round((time.time() - start_time) * 1000, 2)
        }
