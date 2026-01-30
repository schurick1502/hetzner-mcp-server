"""MCP Tools Registry."""
import importlib
import inspect
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))


def get_all_mcp_tools() -> List[Dict[str, Any]]:
    """Alle MCP-Tools mit Schemas extrahieren."""
    tools = []

    # Import MCP server
    try:
        mcp_module = importlib.import_module('src.hetzner_mcp.server')
    except ImportError:
        return []

    for name, obj in inspect.getmembers(mcp_module):
        if inspect.iscoroutinefunction(obj) and not name.startswith('_'):
            sig = inspect.signature(obj)

            params = {}
            for param_name, param in sig.parameters.items():
                param_type = 'string'
                if param.annotation != inspect.Parameter.empty:
                    annotation_str = str(param.annotation).replace("<class '", "").replace("'>", "")
                    if 'int' in annotation_str:
                        param_type = 'integer'
                    elif 'bool' in annotation_str:
                        param_type = 'boolean'
                    elif 'float' in annotation_str:
                        param_type = 'number'

                params[param_name] = {
                    "type": param_type,
                    "required": param.default == inspect.Parameter.empty,
                    "description": f"Parameter {param_name}"
                }

            tools.append({
                "name": name,
                "description": (obj.__doc__ or "").strip() or f"Execute {name}",
                "parameters": params
            })

    return tools


async def execute_mcp_tool(tool_name: str, args: Dict[str, Any]) -> Any:
    """MCP-Tool dynamisch ausführen."""
    try:
        mcp_module = importlib.import_module('src.hetzner_mcp.server')
    except ImportError as e:
        raise ValueError(f"MCP Server konnte nicht geladen werden: {str(e)}")

    if not hasattr(mcp_module, tool_name):
        raise ValueError(f"Tool {tool_name} nicht gefunden")

    tool_func = getattr(mcp_module, tool_name)
    return await tool_func(**args)
