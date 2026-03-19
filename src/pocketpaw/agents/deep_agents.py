"""LangChain Deep Agents backend for PocketPaw.

Uses the Deep Agents SDK (pip install deepagents) which provides:
- create_deep_agent() with built-in planning, filesystem, and subagent tools
- LangGraph runtime with durable execution and streaming
- Multi-provider LLM support via langchain init_chat_model
- Pluggable virtual filesystem backends

Requires: pip install deepagents
"""

import logging
from collections.abc import AsyncIterator
from typing import Any

from pocketpaw.agents.backend import _DEFAULT_IDENTITY, BackendInfo, Capability
from pocketpaw.agents.protocol import AgentEvent
from pocketpaw.config import Settings

logger = logging.getLogger(__name__)


class DeepAgentsBackend:
    """Deep Agents backend -- LangChain/LangGraph agent framework."""

    @staticmethod
    def info() -> BackendInfo:
        return BackendInfo(
            name="deep_agents",
            display_name="Deep Agents (LangChain)",
            capabilities=(
                Capability.STREAMING
                | Capability.TOOLS
                | Capability.MULTI_TURN
                | Capability.CUSTOM_SYSTEM_PROMPT
            ),
            builtin_tools=["write_todos", "read_todos", "task", "ls", "read_file", "write_file"],
            tool_policy_map={
                "write_file": "write_file",
                "read_file": "read_file",
                "task": "shell",
                "ls": "read_file",
            },
            required_keys=[],
            supported_providers=[
                "anthropic",
                "openai",
                "google",
                "ollama",
                "openrouter",
                "openai_compatible",
                "litellm",
            ],
            install_hint={
                "pip_package": "deepagents",
                "pip_spec": "pocketpaw[deep-agents]",
                "verify_import": "deepagents",
            },
            beta=True,
        )

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._stop_flag = False
        self._sdk_available = False
        self._custom_tools: list | None = None
        self._initialize()

    def _initialize(self) -> None:
        try:
            import deepagents  # noqa: F401

            self._sdk_available = True
            logger.info("Deep Agents SDK ready")
        except ImportError:
            logger.warning("Deep Agents SDK not installed -- pip install 'pocketpaw[deep-agents]'")

    def _build_custom_tools(self) -> list:
        """Lazily build and cache PocketPaw tools as LangChain StructuredTool wrappers."""
        if self._custom_tools is not None:
            return self._custom_tools
        try:
            from pocketpaw.agents.tool_bridge import build_deep_agents_tools

            self._custom_tools = build_deep_agents_tools(self.settings, backend="deep_agents")
        except Exception as exc:
            logger.debug("Could not build custom tools: %s", exc)
            self._custom_tools = []
        return self._custom_tools

    def _build_model(self) -> str:
        """Return the provider:model string for init_chat_model."""
        model_str = self.settings.deep_agents_model
        if model_str:
            return model_str
        return "anthropic:claude-sonnet-4-6"

    async def run(
        self,
        message: str,
        *,
        system_prompt: str | None = None,
        history: list[dict] | None = None,
        session_key: str | None = None,
    ) -> AsyncIterator[AgentEvent]:
        if not self._sdk_available:
            yield AgentEvent(
                type="error",
                content=(
                    "Deep Agents SDK not installed.\n\n"
                    "Install with: pip install 'pocketpaw[deep-agents]'"
                ),
            )
            return

        self._stop_flag = False

        try:
            from deepagents import create_deep_agent
            from langchain.chat_models import init_chat_model

            model_str = self._build_model()
            model = init_chat_model(model_str)
            instructions = system_prompt or _DEFAULT_IDENTITY

            custom_tools = self._build_custom_tools()

            # Build messages list: history + current message
            messages: list[dict[str, str]] = []
            if history:
                for msg in history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if content:
                        messages.append({"role": role, "content": content})
            messages.append({"role": "user", "content": message})

            agent = create_deep_agent(
                model=model,
                tools=custom_tools if custom_tools else [],
                system_prompt=instructions,
            )

            # Stream using LangGraph's async streaming
            async for chunk in agent.astream(
                {"messages": messages},
                stream_mode=["updates", "messages"],
                version="v2",
            ):
                if self._stop_flag:
                    break

                chunk_type = chunk.get("type", "")

                if chunk_type == "messages":
                    data = chunk.get("data")
                    if data is None:
                        continue
                    # AIMessageChunk contains streamed tokens
                    content = getattr(data, "content", "")
                    if content and isinstance(content, str):
                        yield AgentEvent(type="message", content=content)

                elif chunk_type == "updates":
                    data = chunk.get("data", {})
                    if not isinstance(data, dict):
                        continue
                    # Check for tool calls in updates
                    for _node_name, node_data in data.items():
                        if not isinstance(node_data, dict):
                            continue
                        node_messages = node_data.get("messages", [])
                        for msg in node_messages:
                            # Tool call messages
                            tool_calls = getattr(msg, "tool_calls", None)
                            if tool_calls:
                                for tc in tool_calls:
                                    name = tc.get("name", "Tool")
                                    yield AgentEvent(
                                        type="tool_use",
                                        content=f"Using {name}...",
                                        metadata={
                                            "name": name,
                                            "input": tc.get("args", {}),
                                        },
                                    )
                            # Tool response messages
                            if getattr(msg, "type", "") == "tool":
                                tool_name = getattr(msg, "name", "tool")
                                tool_content = getattr(msg, "content", "")
                                if isinstance(tool_content, str):
                                    yield AgentEvent(
                                        type="tool_result",
                                        content=tool_content[:200],
                                        metadata={"name": tool_name},
                                    )

            yield AgentEvent(type="done", content="")

        except Exception as e:
            logger.error("Deep Agents error: %s", e)
            yield AgentEvent(type="error", content=f"Deep Agents error: {e}")

    async def stop(self) -> None:
        self._stop_flag = True

    async def get_status(self) -> dict[str, Any]:
        return {
            "backend": "deep_agents",
            "available": self._sdk_available,
            "running": not self._stop_flag,
            "model": self.settings.deep_agents_model,
        }
