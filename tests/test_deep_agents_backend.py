"""Tests for Deep Agents backend -- mocked (no real SDK needed)."""

from unittest.mock import MagicMock, patch

import pytest

from pocketpaw.agents.backend import Capability
from pocketpaw.config import Settings


class TestDeepAgentsBackendInfo:
    """Tests for static backend metadata."""

    def test_info_name(self):
        from pocketpaw.agents.deep_agents import DeepAgentsBackend

        info = DeepAgentsBackend.info()
        assert info.name == "deep_agents"

    def test_info_display_name(self):
        from pocketpaw.agents.deep_agents import DeepAgentsBackend

        info = DeepAgentsBackend.info()
        assert info.display_name == "Deep Agents (LangChain)"

    def test_info_capabilities(self):
        from pocketpaw.agents.deep_agents import DeepAgentsBackend

        info = DeepAgentsBackend.info()
        assert Capability.STREAMING in info.capabilities
        assert Capability.TOOLS in info.capabilities
        assert Capability.MULTI_TURN in info.capabilities
        assert Capability.CUSTOM_SYSTEM_PROMPT in info.capabilities

    def test_info_beta(self):
        from pocketpaw.agents.deep_agents import DeepAgentsBackend

        info = DeepAgentsBackend.info()
        assert info.beta is True

    def test_info_install_hint(self):
        from pocketpaw.agents.deep_agents import DeepAgentsBackend

        info = DeepAgentsBackend.info()
        assert info.install_hint["pip_spec"] == "pocketpaw[deep-agents]"
        assert info.install_hint["verify_import"] == "deepagents"


class TestDeepAgentsBackendInit:
    """Tests for backend initialization."""

    def test_custom_tools_cached(self):
        """_build_custom_tools caches the result."""
        from pocketpaw.agents.deep_agents import DeepAgentsBackend

        backend = DeepAgentsBackend(Settings())
        mock_tools = [MagicMock(), MagicMock()]

        with patch(
            "pocketpaw.agents.tool_bridge.build_deep_agents_tools",
            return_value=mock_tools,
        ):
            backend._custom_tools = None
            result1 = backend._build_custom_tools()
            result2 = backend._build_custom_tools()
            assert result1 is result2

    def test_custom_tools_graceful_degradation(self):
        """Returns empty list when tool_bridge is unavailable."""
        from pocketpaw.agents.deep_agents import DeepAgentsBackend

        backend = DeepAgentsBackend(Settings())
        with patch.dict("sys.modules", {"pocketpaw.agents.tool_bridge": None}):
            backend._custom_tools = None
            result = backend._build_custom_tools()
            assert result == []

    def test_build_model_default(self):
        """Default model string is returned."""
        from pocketpaw.agents.deep_agents import DeepAgentsBackend

        backend = DeepAgentsBackend(Settings())
        assert backend._build_model() == "anthropic:claude-sonnet-4-6"

    def test_build_model_custom(self):
        """Custom model from settings is returned."""
        from pocketpaw.agents.deep_agents import DeepAgentsBackend

        settings = Settings(deep_agents_model="openai:gpt-4o")
        backend = DeepAgentsBackend(settings)
        assert backend._build_model() == "openai:gpt-4o"


class TestDeepAgentsBackendRun:
    """Tests for the run() async generator."""

    @pytest.mark.asyncio
    async def test_run_sdk_unavailable_yields_error(self):
        """When SDK is missing, run() yields an error event."""
        from pocketpaw.agents.deep_agents import DeepAgentsBackend

        backend = DeepAgentsBackend(Settings())
        backend._sdk_available = False

        events = []
        async for event in backend.run("hello"):
            events.append(event)

        assert len(events) == 1
        assert events[0].type == "error"
        assert "not installed" in events[0].content.lower()

    @pytest.mark.asyncio
    async def test_stop_sets_flag(self):
        from pocketpaw.agents.deep_agents import DeepAgentsBackend

        backend = DeepAgentsBackend(Settings())
        assert backend._stop_flag is False
        await backend.stop()
        assert backend._stop_flag is True

    @pytest.mark.asyncio
    async def test_get_status(self):
        from pocketpaw.agents.deep_agents import DeepAgentsBackend

        backend = DeepAgentsBackend(Settings())
        status = await backend.get_status()
        assert status["backend"] == "deep_agents"
        assert "available" in status
        assert "running" in status
        assert "model" in status


class TestDeepAgentsRegistry:
    """Tests for registry integration."""

    def test_backend_in_registry(self):
        from pocketpaw.agents.registry import list_backends

        assert "deep_agents" in list_backends()

    def test_backend_class_loadable(self):
        from pocketpaw.agents.registry import get_backend_class

        cls = get_backend_class("deep_agents")
        # May be None if deepagents not installed, but should not raise
        if cls is not None:
            info = cls.info()
            assert info.name == "deep_agents"
