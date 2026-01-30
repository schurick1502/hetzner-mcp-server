"""AI Assistant API Routes."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Literal, Optional
import json
import os

from ...services.ai_provider import get_provider
from ...services.mcp_tools_registry import get_all_mcp_tools, execute_mcp_tool

router = APIRouter()


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    provider: Literal["claude", "openai", "gemini"]
    messages: List[Message]
    model: Optional[str] = None


@router.get("/providers")
async def list_providers():
    """Verfügbare AI-Provider mit Status."""
    providers = []

    for name in ["claude", "openai", "gemini"]:
        env_key = f"{name.upper()}_API_KEY" if name != "claude" else "ANTHROPIC_API_KEY"
        available = bool(os.getenv(env_key))

        providers.append({
            "name": name,
            "available": available,
            "error": None if available else f"{env_key} nicht konfiguriert"
        })

    return {"providers": providers}


@router.post("/chat")
async def chat(request: ChatRequest):
    """AI-Chat mit Streaming und Tool-Calling."""

    try:
        provider = get_provider(request.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Hole alle MCP-Tools
    tools = get_all_mcp_tools()

    # Konvertiere Messages
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    async def stream_generator():
        """SSE Stream Generator mit Tool-Calling."""

        try:
            # AI-Streaming
            tool_calls = []
            async for event in provider.chat_stream(messages, tools):
                yield event

                # Parse tool calls (vereinfacht - sammelt Tool-Namen)
                if '"type": "tool_use"' in event:
                    try:
                        data_str = event.split("data: ")[1] if "data: " in event else event
                        data = json.loads(data_str)
                        if data.get("type") == "tool_use":
                            tool_name = data.get("tool")
                            if tool_name:
                                tool_calls.append(tool_name)
                    except:
                        pass

            # Führe Tool-Calls aus (vereinfachte Version - ohne Args-Parsing)
            for tool_name in tool_calls:
                try:
                    yield f"data: {json.dumps({'type': 'tool_executing', 'tool': tool_name})}\n\n"

                    # Führe Tool aus
                    result = await execute_mcp_tool(tool_name, {})

                    yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name, 'result': result})}\n\n"

                    # Zweite AI-Runde mit Tool-Ergebnissen
                    messages.append({
                        "role": "assistant",
                        "content": f"Tool {tool_name} executed successfully."
                    })
                    messages.append({
                        "role": "user",
                        "content": f"Here is the result: {json.dumps(result)}"
                    })

                    # Stream AI response mit Tool-Ergebnis
                    async for event in provider.chat_stream(messages, tools):
                        yield event

                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

            yield "data: {\"type\": \"done\"}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
            yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(
        stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
