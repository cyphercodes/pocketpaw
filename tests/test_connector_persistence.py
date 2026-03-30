# Tests for connector persistence — verify state survives registry recreation.
# Created: 2026-03-30

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pocketpaw.connectors.protocol import ConnectorStatus
from pocketpaw.connectors.registry import ConnectorRegistry


CONNECTORS_DIR = Path(__file__).parent.parent / "connectors"


class FakeCredentialStore:
    """In-memory credential store for testing (no disk, no encryption)."""

    def __init__(self):
        self._data: dict[str, str] = {}

    def get(self, name: str) -> str | None:
        return self._data.get(name)

    def set(self, name: str, value: str) -> None:
        self._data[name] = value

    def delete(self, name: str) -> None:
        self._data.pop(name, None)


@pytest.fixture
def fake_store():
    """Patch CredentialStore so persistence uses in-memory dict."""
    store = FakeCredentialStore()
    with patch("pocketpaw.credentials.CredentialStore", return_value=store):
        yield store


class TestConnectorPersistence:
    """Verify connectors persist across registry instances."""

    @pytest.mark.asyncio
    async def test_connect_saves_state(self, fake_store: FakeCredentialStore) -> None:
        """Connecting a connector should persist its config."""
        reg = ConnectorRegistry(CONNECTORS_DIR)
        result = await reg.connect("pocket-1", "stripe", {"STRIPE_API_KEY": "sk_test_123"})
        assert result.success is True

        # Verify state was saved
        raw = fake_store.get("_connector_state")
        assert raw is not None
        entries = json.loads(raw)
        assert len(entries) == 1
        assert entries[0]["pocket_id"] == "pocket-1"
        assert entries[0]["connector_name"] == "stripe"
        assert entries[0]["config"]["STRIPE_API_KEY"] == "sk_test_123"

    @pytest.mark.asyncio
    async def test_disconnect_removes_from_state(self, fake_store: FakeCredentialStore) -> None:
        """Disconnecting should remove the connector from persisted state."""
        reg = ConnectorRegistry(CONNECTORS_DIR)
        await reg.connect("pocket-1", "stripe", {"STRIPE_API_KEY": "sk_test_123"})
        await reg.disconnect("pocket-1", "stripe")

        raw = fake_store.get("_connector_state")
        entries = json.loads(raw)
        assert len(entries) == 0

    @pytest.mark.asyncio
    async def test_restore_reconnects(self, fake_store: FakeCredentialStore) -> None:
        """A new registry should restore connections from persisted state."""
        # Connect with first registry
        reg1 = ConnectorRegistry(CONNECTORS_DIR)
        await reg1.connect("pocket-1", "stripe", {"STRIPE_API_KEY": "sk_test_456"})

        # Create a new registry (simulates restart)
        reg2 = ConnectorRegistry(CONNECTORS_DIR)

        # Before restore — not connected
        adapter = reg2.get_adapter("pocket-1", "stripe")
        assert adapter is None

        # After restore — connected
        restored = await reg2.restore()
        assert restored == 1

        adapter = reg2.get_adapter("pocket-1", "stripe")
        assert adapter is not None

        status = reg2.status("pocket-1")
        stripe_status = next(s for s in status if s["name"] == "stripe")
        assert stripe_status["status"] == ConnectorStatus.CONNECTED

    @pytest.mark.asyncio
    async def test_restore_multiple_connectors(self, fake_store: FakeCredentialStore) -> None:
        """Multiple connectors should all be restored."""
        reg1 = ConnectorRegistry(CONNECTORS_DIR)
        await reg1.connect("pocket-1", "stripe", {"STRIPE_API_KEY": "sk_test"})
        await reg1.connect("pocket-1", "csv", {})

        reg2 = ConnectorRegistry(CONNECTORS_DIR)
        restored = await reg2.restore()
        assert restored == 2
        assert reg2.get_adapter("pocket-1", "stripe") is not None
        assert reg2.get_adapter("pocket-1", "csv") is not None

    @pytest.mark.asyncio
    async def test_restore_skips_already_connected(self, fake_store: FakeCredentialStore) -> None:
        """Restore should not re-connect connectors that are already active."""
        reg = ConnectorRegistry(CONNECTORS_DIR)
        await reg.connect("pocket-1", "stripe", {"STRIPE_API_KEY": "sk_test"})

        # Restore on same registry (already connected)
        restored = await reg.restore()
        assert restored == 0

    @pytest.mark.asyncio
    async def test_restore_with_no_saved_state(self, fake_store: FakeCredentialStore) -> None:
        """Restore with empty store should do nothing."""
        reg = ConnectorRegistry(CONNECTORS_DIR)
        restored = await reg.restore()
        assert restored == 0

    @pytest.mark.asyncio
    async def test_restore_handles_bad_connector_name(self, fake_store: FakeCredentialStore) -> None:
        """Restore should skip unknown connectors gracefully."""
        fake_store.set("_connector_state", json.dumps([
            {"pocket_id": "p1", "connector_name": "nonexistent_service", "config": {}},
        ]))
        reg = ConnectorRegistry(CONNECTORS_DIR)
        restored = await reg.restore()
        assert restored == 0

    @pytest.mark.asyncio
    async def test_singleton_shares_state(self, fake_store: FakeCredentialStore) -> None:
        """get_connector_registry should return the same instance."""
        from pocketpaw.connectors.registry import get_connector_registry

        # Reset the singleton for this test
        import pocketpaw.connectors.registry as reg_mod
        reg_mod._shared_registry = None

        try:
            r1 = get_connector_registry(CONNECTORS_DIR)
            r2 = get_connector_registry()
            assert r1 is r2

            # Connect via r1, visible via r2
            await r1.connect("pocket-1", "stripe", {"STRIPE_API_KEY": "sk_test"})
            assert r2.get_adapter("pocket-1", "stripe") is not None
        finally:
            reg_mod._shared_registry = None
