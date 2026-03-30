# Connector registry — discovers and manages available connectors.
# Created: 2026-03-27 — Scans connectors/ dir for YAML definitions.
# Updated: 2026-03-30 — Native adapter support for database connectors.
# Updated: 2026-03-30 — Persist connector state to disk; shared singleton.

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from pocketpaw.connectors.protocol import (
    ActionResult,
    ActionSchema,
    ConnectionResult,
    ConnectorStatus,
    SyncResult,
)
from pocketpaw.connectors.yaml_engine import ConnectorDef, DirectRESTAdapter, parse_connector_yaml

logger = logging.getLogger(__name__)


@runtime_checkable
class AnyAdapter(Protocol):
    """Union type for all adapter kinds."""

    @property
    def name(self) -> str: ...
    @property
    def display_name(self) -> str: ...
    async def connect(self, pocket_id: str, config: dict[str, Any]) -> ConnectionResult: ...
    async def disconnect(self, pocket_id: str) -> bool: ...
    async def actions(self) -> list[ActionSchema]: ...
    async def execute(self, action: str, params: dict[str, Any]) -> ActionResult: ...


# Connectors handled by native Python adapters instead of YAML/REST.
# SQL databases use DatabaseAdapter, MongoDB uses MongoDBAdapter.
_SQL_CONNECTORS: set[str] = {"postgresql", "mysql", "mssql", "sqlite"}
_NOSQL_CONNECTORS: set[str] = {"mongodb"}


def _create_native_adapter(connector_name: str) -> AnyAdapter | None:
    """Create a native adapter for database connectors."""
    if connector_name in _SQL_CONNECTORS:
        try:
            from pocketpaw.connectors.db_adapter import DatabaseAdapter
            return DatabaseAdapter(connector_name)
        except Exception:
            return None
    if connector_name in _NOSQL_CONNECTORS:
        try:
            from pocketpaw.connectors.mongo_adapter import MongoDBAdapter
            return MongoDBAdapter()
        except Exception:
            return None
    return None


def _state_path() -> Path:
    """Path to the persisted connector state file."""
    from pocketpaw.config import get_config_dir
    return get_config_dir() / "connector_state.enc"


class ConnectorRegistry:
    """Discovers available connectors and manages instances per pocket."""

    def __init__(self, connectors_dir: Path | None = None) -> None:
        self._connectors_dir = connectors_dir or Path("connectors")
        self._definitions: dict[str, ConnectorDef] = {}
        self._instances: dict[str, AnyAdapter] = {}  # key = "{pocket_id}:{connector_name}"
        self._configs: dict[str, dict[str, Any]] = {}  # key → config used to connect
        self._scan()

    def _scan(self) -> None:
        """Scan connectors directory for YAML definitions."""
        if not self._connectors_dir.exists():
            return
        for path in sorted(self._connectors_dir.glob("*.yaml")):
            try:
                defn = parse_connector_yaml(path)
                self._definitions[defn.name] = defn
            except Exception:
                pass  # Skip malformed YAMLs

    # ── Persistence ─────────────────────────────────────────────────────────

    def _save_state(self) -> None:
        """Persist connected connector configs to encrypted storage."""
        try:
            from pocketpaw.credentials import CredentialStore
            store = CredentialStore()
            # Build state: list of {pocket_id, connector_name, config}
            entries = []
            for key, config in self._configs.items():
                pocket_id, connector_name = key.split(":", 1)
                entries.append({
                    "pocket_id": pocket_id,
                    "connector_name": connector_name,
                    "config": config,
                })
            store.set("_connector_state", json.dumps(entries))
            logger.debug("Saved %d connector state(s)", len(entries))
        except Exception:
            logger.warning("Failed to save connector state", exc_info=True)

    def _load_state(self) -> list[dict[str, Any]]:
        """Load persisted connector state from encrypted storage."""
        try:
            from pocketpaw.credentials import CredentialStore
            store = CredentialStore()
            raw = store.get("_connector_state")
            if raw:
                return json.loads(raw)
        except Exception:
            logger.warning("Failed to load connector state", exc_info=True)
        return []

    async def restore(self) -> int:
        """Reconnect connectors from persisted state. Returns count restored."""
        entries = self._load_state()
        restored = 0
        for entry in entries:
            pocket_id = entry.get("pocket_id", "default")
            connector_name = entry.get("connector_name", "")
            config = entry.get("config", {})
            if not connector_name:
                continue
            key = f"{pocket_id}:{connector_name}"
            if key in self._instances:
                continue  # Already connected
            try:
                result = await self.connect(pocket_id, connector_name, config)
                if result and result.success:
                    restored += 1
                    logger.info("Restored connector: %s (pocket=%s)", connector_name, pocket_id)
                else:
                    msg = result.message if result else "unknown"
                    logger.warning("Failed to restore %s: %s", connector_name, msg)
            except Exception:
                logger.warning("Error restoring connector %s", connector_name, exc_info=True)
        return restored

    # ── Public API ──────────────────────────────────────────────────────────

    @property
    def available(self) -> list[dict[str, str]]:
        """List all available connector definitions."""
        return [
            {
                "name": d.name,
                "display_name": d.display_name,
                "type": d.type,
                "icon": d.icon,
            }
            for d in self._definitions.values()
        ]

    def get_definition(self, name: str) -> ConnectorDef | None:
        """Get a connector definition by name."""
        return self._definitions.get(name)

    def get_adapter(self, pocket_id: str, connector_name: str) -> AnyAdapter | None:
        """Get an active adapter instance for a pocket+connector."""
        key = f"{pocket_id}:{connector_name}"
        return self._instances.get(key)

    async def connect(self, pocket_id: str, connector_name: str, config: dict[str, Any]) -> Any:
        """Create and connect a connector adapter for a pocket."""
        defn = self._definitions.get(connector_name)
        if not defn:
            return None

        # Use native adapter if available, otherwise fall back to YAML/REST.
        adapter: AnyAdapter
        native = _create_native_adapter(connector_name)
        if native is not None:
            adapter = native
        else:
            adapter = DirectRESTAdapter(defn)

        result = await adapter.connect(pocket_id, config)

        if result.success:
            key = f"{pocket_id}:{connector_name}"
            self._instances[key] = adapter
            self._configs[key] = config
            self._save_state()

        return result

    async def disconnect(self, pocket_id: str, connector_name: str) -> bool:
        """Disconnect a connector from a pocket."""
        key = f"{pocket_id}:{connector_name}"
        adapter = self._instances.get(key)
        if not adapter:
            return False
        await adapter.disconnect(pocket_id)
        del self._instances[key]
        self._configs.pop(key, None)
        self._save_state()
        return True

    def status(self, pocket_id: str) -> list[dict[str, Any]]:
        """Get connection status for all connectors in a pocket."""
        results = []
        for name, defn in self._definitions.items():
            key = f"{pocket_id}:{name}"
            adapter = self._instances.get(key)
            results.append({
                "name": name,
                "display_name": defn.display_name,
                "icon": defn.icon,
                "status": ConnectorStatus.CONNECTED if adapter else ConnectorStatus.DISCONNECTED,
            })
        return results

    def reload(self) -> None:
        """Re-scan the connectors directory."""
        self._definitions.clear()
        self._scan()


# ── Shared singleton ────────────────────────────────────────────────────────

_shared_registry: ConnectorRegistry | None = None


def get_connector_registry(connectors_dir: Path | None = None) -> ConnectorRegistry:
    """Get the shared ConnectorRegistry singleton."""
    global _shared_registry
    if _shared_registry is None:
        _shared_registry = ConnectorRegistry(connectors_dir or Path("connectors"))
    return _shared_registry
