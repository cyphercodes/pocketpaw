"""Tests for SoulManager lifecycle."""

import asyncio

import pytest


def _has_soul_protocol() -> bool:
    try:
        import soul_protocol  # noqa: F401

        return True
    except ImportError:
        return False


pytestmark = pytest.mark.skipif(not _has_soul_protocol(), reason="soul-protocol not installed")


@pytest.fixture(autouse=True)
def _reset_soul():
    from pocketpaw.soul.manager import _reset_manager

    _reset_manager()
    yield
    _reset_manager()


@pytest.fixture
def soul_settings(tmp_path):
    from pocketpaw.config import Settings

    return Settings(
        soul_enabled=True,
        soul_name="TestSoul",
        soul_archetype="The Test Helper",
        soul_path=str(tmp_path / "test.soul"),
        soul_auto_save_interval=0,
    )


class TestSoulManager:
    async def test_initialize_births_new_soul(self, soul_settings):
        from pocketpaw.soul.manager import SoulManager

        mgr = SoulManager(soul_settings)
        await mgr.initialize()
        assert mgr.soul is not None
        assert mgr.soul.name == "TestSoul"
        assert mgr.bridge is not None
        assert mgr.bootstrap_provider is not None

    async def test_save_and_reawaken(self, soul_settings, tmp_path):
        from pocketpaw.soul.manager import SoulManager, _reset_manager

        mgr = SoulManager(soul_settings)
        await mgr.initialize()
        await mgr.save()
        assert (tmp_path / "test.soul").exists()

        _reset_manager()
        mgr2 = SoulManager(soul_settings)
        await mgr2.initialize()
        assert mgr2.soul.name == "TestSoul"

    async def test_observe_does_not_raise(self, soul_settings):
        from pocketpaw.soul.manager import SoulManager

        mgr = SoulManager(soul_settings)
        await mgr.initialize()
        await mgr.observe("Hello", "Hi there!")

    async def test_get_tools_returns_four(self, soul_settings):
        from pocketpaw.soul.manager import SoulManager

        mgr = SoulManager(soul_settings)
        await mgr.initialize()
        tools = mgr.get_tools()
        assert len(tools) == 4
        names = {t.name for t in tools}
        assert names == {"soul_remember", "soul_recall", "soul_edit_core", "soul_status"}

    async def test_corrupt_soul_file_falls_back_to_birth(self, soul_settings, tmp_path):
        from pocketpaw.soul.manager import SoulManager

        soul_file = tmp_path / "test.soul"
        soul_file.write_text("this is not a valid soul file")

        mgr = SoulManager(soul_settings)
        await mgr.initialize()
        assert mgr.soul is not None
        assert mgr.soul.name == "TestSoul"
        backup = tmp_path / "test.soul.corrupt"
        assert backup.exists()

    async def test_concurrent_observe_is_serialized(self, soul_settings):
        from pocketpaw.soul.manager import SoulManager

        mgr = SoulManager(soul_settings)
        await mgr.initialize()

        tasks = [mgr.observe(f"msg {i}", f"reply {i}") for i in range(10)]
        await asyncio.gather(*tasks)

    async def test_shutdown_saves_and_stops_autosave(self, tmp_path):
        from pocketpaw.config import Settings
        from pocketpaw.soul.manager import SoulManager

        settings = Settings(
            soul_enabled=True,
            soul_name="ShutdownTest",
            soul_path=str(tmp_path / "shutdown.soul"),
            soul_auto_save_interval=1,
        )
        mgr = SoulManager(settings)
        await mgr.initialize()
        mgr.start_auto_save()

        await mgr.observe("test", "test reply")
        await mgr.shutdown()

        assert (tmp_path / "shutdown.soul").exists()
        assert mgr._auto_save_task is None or mgr._auto_save_task.done()
