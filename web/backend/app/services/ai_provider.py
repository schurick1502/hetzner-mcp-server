"""AI Provider Abstraction Layer."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncIterator
import os
import json


class AIProvider(ABC):
    """Base class für AI-Provider."""

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]]
    ) -> AsyncIterator[str]:
        """Streaming-Chat mit Tool-Support."""
        pass


class ClaudeProvider(AIProvider):
    """Anthropic Claude Provider."""

    def __init__(self):
        from anthropic import AsyncAnthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY nicht konfiguriert")
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = os.getenv("DEFAULT_AI_MODEL", "claude-3-5-sonnet-20241022")

    async def chat_stream(self, messages, tools):
        # Konvertiere tools zu Claude-Format
        claude_tools = [self._convert_tool(t) for t in tools]

        async with self.client.messages.stream(
            model=self.model,
            messages=messages,
            tools=claude_tools if tools else [],
            max_tokens=4096
        ) as stream:
            async for event in stream:
                if hasattr(event, 'type'):
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, "text"):
                            yield f"data: {json.dumps({'type': 'text', 'text': event.delta.text})}\n\n"
                    elif event.type == "content_block_start":
                        if hasattr(event, "content_block") and hasattr(event.content_block, "type"):
                            if event.content_block.type == "tool_use":
                                yield f"data: {json.dumps({'type': 'tool_use', 'tool': event.content_block.name})}\n\n"

    def _convert_tool(self, tool: Dict) -> Dict:
        """MCP-Tool zu Claude-Format."""
        properties = {}
        required = []

        for param_name, param_info in tool.get("parameters", {}).items():
            properties[param_name] = {
                "type": param_info.get("type", "string"),
                "description": param_info.get("description", "")
            }
            if param_info.get("required", False):
                required.append(param_name)

        return {
            "name": tool["name"],
            "description": tool.get("description", ""),
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }


class OpenAIProvider(AIProvider):
    """OpenAI Provider."""

    def __init__(self):
        from openai import AsyncOpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY nicht konfiguriert")
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4-turbo-preview"

    async def chat_stream(self, messages, tools):
        openai_tools = [self._convert_tool(t) for t in tools] if tools else None

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=openai_tools,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield f"data: {json.dumps({'type': 'text', 'text': chunk.choices[0].delta.content})}\n\n"
            elif chunk.choices[0].delta.tool_calls:
                for tool_call in chunk.choices[0].delta.tool_calls:
                    if tool_call.function and tool_call.function.name:
                        yield f"data: {json.dumps({'type': 'tool_use', 'tool': tool_call.function.name})}\n\n"

    def _convert_tool(self, tool: Dict) -> Dict:
        properties = {}
        for param_name, param_info in tool.get("parameters", {}).items():
            properties[param_name] = {
                "type": param_info.get("type", "string"),
                "description": param_info.get("description", "")
            }

        return {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": {
                    "type": "object",
                    "properties": properties
                }
            }
        }


class GeminiProvider(AIProvider):
    """Google Gemini Provider."""

    def __init__(self):
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY nicht konfiguriert")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    async def chat_stream(self, messages, tools):
        # Gemini-spezifische Implementierung (vereinfacht)
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])

        try:
            response = await self.model.generate_content_async(prompt, stream=True)
            async for chunk in response:
                if chunk.text:
                    yield f"data: {json.dumps({'type': 'text', 'text': chunk.text})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    def _convert_tool(self, tool: Dict) -> Dict:
        # Gemini tool format (vereinfacht)
        return tool


def get_provider(provider_name: str) -> AIProvider:
    """Factory für AI-Provider."""
    providers = {
        "claude": ClaudeProvider,
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
    }

    if provider_name not in providers:
        raise ValueError(f"Unknown provider: {provider_name}")

    try:
        return providers[provider_name]()
    except ValueError as e:
        raise ValueError(f"Provider {provider_name} nicht verfügbar: {e}")
