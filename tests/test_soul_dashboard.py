# tests/test_soul_dashboard.py — Unit tests for GET /api/v1/soul/dashboard endpoint.
# Created: 2026-04-01 — Covers all 16 test cases for get_soul_dashboard(), using
# unittest.mock to isolate the endpoint from SoulManager and Soul entirely.

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

# Import the endpoint function under test directly — no test server needed.
from pocketpaw.api.v1.soul import get_soul_dashboard


# ---------------------------------------------------------------------------
# Helpers — build a fully-populated mock Soul for reuse across tests
# ---------------------------------------------------------------------------

def _make_lifecycle(value: str = "awakened") -> MagicMock:
    lc = MagicMock()
    lc.value = value
    return lc


def _make_personality(
    openness: float = 0.8,
    conscientiousness: float = 0.7,
    extraversion: float = 0.6,
    agreeableness: float = 0.9,
    neuroticism: float = 0.3,
) -> MagicMock:
    p = MagicMock()
    p.openness = openness
    p.conscientiousness = conscientiousness
    p.extraversion = extraversion
    p.agreeableness = agreeableness
    p.neuroticism = neuroticism
    return p


def _make_communication(
    warmth: str = "high",
    verbosity: str = "concise",
    humor_style: str = "dry",
    emoji_usage: str = "rare",
) -> MagicMock:
    c = MagicMock()
    c.warmth = warmth
    c.verbosity = verbosity
    c.humor_style = humor_style
    c.emoji_usage = emoji_usage
    return c


def _make_dna(personality=None, communication=None) -> MagicMock:
    dna = MagicMock()
    dna.personality = personality or _make_personality()
    dna.communication = communication or _make_communication()
    return dna


def _make_state(
    mood: str = "content",
    energy: float = 85.0,
    social_battery: float = 72.0,
    focus: str = "high",
) -> MagicMock:
    s = MagicMock()
    s.mood = mood
    s.energy = energy
    s.social_battery = social_battery
    s.focus = focus
    return s


def _make_core_memory(persona: str = "I am PocketPaw.", human: str = "Prakash") -> MagicMock:
    cm = MagicMock()
    cm.persona = persona
    cm.human = human
    return cm


def _make_skill(
    skill_id: str = "sk_001",
    name: str = "Python",
    level: int = 3,
    xp: int = 250,
    xp_to_next: int = 500,
) -> MagicMock:
    sk = MagicMock()
    sk.id = skill_id
    sk.name = name
    sk.level = level
    sk.xp = xp
    sk.xp_to_next = xp_to_next
    return sk


def _make_bond(
    bonded_to: str = "Prakash",
    bond_strength: float = 78.5,
    interaction_count: int = 42,
    bonded_at: datetime | None = None,
) -> MagicMock:
    b = MagicMock()
    b.bonded_to = bonded_to
    b.bond_strength = bond_strength
    b.interaction_count = interaction_count
    b.bonded_at = bonded_at or datetime(2026, 1, 1, 12, 0, 0)
    return b


def _make_memory_store(
    episodic_count: int = 10,
    semantic_count: int = 5,
    procedural_count: int = 3,
    graph_count: int = 7,
) -> MagicMock:
    mem = MagicMock()
    mem._episodic.entries.return_value = ["e"] * episodic_count
    mem._semantic.facts.return_value = ["s"] * semantic_count
    mem._procedural.entries.return_value = ["p"] * procedural_count
    mem._graph.entities.return_value = ["g"] * graph_count
    return mem


def _make_evolution_entry(
    mut_id: str = "mut_001",
    trait: str = "openness",
    old_value: str = "0.6",
    new_value: str = "0.7",
    reason: str = "Grew through exploration",
    approved: bool = True,
    proposed_at: datetime | None = None,
) -> MagicMock:
    m = MagicMock()
    m.id = mut_id
    m.trait = trait
    m.old_value = old_value
    m.new_value = new_value
    m.reason = reason
    m.approved = approved
    m.proposed_at = proposed_at or datetime(2026, 3, 1, 10, 0, 0)
    return m


def _make_self_image(
    domain: str = "coding",
    confidence: float = 0.85,
    evidence_count: int = 12,
) -> MagicMock:
    img = MagicMock()
    img.domain = domain
    img.confidence = confidence
    img.evidence_count = evidence_count
    return img


def _make_soul_identity(
    core_values: list | None = None,
    incarnation: int = 2,
) -> MagicMock:
    identity = MagicMock()
    identity.core_values = core_values or ["sovereignty", "curiosity"]
    identity.incarnation = incarnation
    return identity


def _make_skills_container(skills: list | None = None) -> MagicMock:
    container = MagicMock()
    # Use sentinel to distinguish "not provided" from "empty list"
    container.skills = [_make_skill()] if skills is None else skills
    return container


def _make_self_model(images: list | None = None) -> MagicMock:
    sm = MagicMock()
    # Use sentinel to distinguish "not provided" from "empty list"
    sm.get_active_self_images.return_value = [_make_self_image()] if images is None else images
    return sm


def _make_full_soul(
    name: str = "PocketPaw",
    archetype: str = "Sage",
    did: str = "did:soul:pocketpaw-405c4f",
    born: datetime | None = None,
    memory_count: int = 25,
    skills: list | None = None,
    bond=None,
    evolution_history: list | None = None,
    self_model_images: list | None = None,
    episodic_count: int = 10,
    semantic_count: int = 5,
    procedural_count: int = 3,
    graph_count: int = 7,
) -> MagicMock:
    """Build a comprehensive mock Soul with all attributes needed by get_soul_dashboard.

    Pass an explicit empty list [] for skills/evolution_history/self_model_images
    to get a soul with no entries.  Passing None (default) gives one default entry.
    """
    soul = MagicMock()
    soul.name = name
    soul.archetype = archetype
    soul.did = did
    soul.born = born or datetime(2025, 6, 1, 0, 0, 0)
    soul.lifecycle = _make_lifecycle()
    soul.identity = _make_soul_identity()
    soul.dna = _make_dna()
    soul.state = _make_state()
    soul.get_core_memory.return_value = _make_core_memory()
    soul.skills = _make_skills_container(skills)
    soul.bond = bond  # None means no bond
    soul.memory_count = memory_count
    soul._memory = _make_memory_store(episodic_count, semantic_count, procedural_count, graph_count)
    # Distinguish None (use default) from [] (empty)
    soul.evolution_history = [_make_evolution_entry()] if evolution_history is None else evolution_history
    soul.self_model = _make_self_model(self_model_images)
    return soul


def _make_manager(soul=None) -> MagicMock:
    mgr = MagicMock()
    mgr.soul = soul
    return mgr


# ---------------------------------------------------------------------------
# Tests — disabled soul / no soul loaded
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_soul_disabled():
    """When get_soul_manager() returns None, response is {"enabled": false}."""
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=None):
        result = await get_soul_dashboard()

    assert result == {"enabled": False}


@pytest.mark.asyncio
async def test_dashboard_soul_not_loaded():
    """When manager exists but soul is None, response is {"enabled": false}."""
    mgr = _make_manager(soul=None)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    assert result == {"enabled": False}


# ---------------------------------------------------------------------------
# Tests — identity section
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_returns_identity():
    """Identity section contains all expected fields with correct values."""
    born = datetime(2025, 6, 1, 0, 0, 0)
    soul = _make_full_soul(
        name="Aria",
        archetype="Explorer",
        did="did:soul:aria-abc123",
        born=born,
    )
    soul.identity.core_values = ["curiosity", "honesty"]
    soul.identity.incarnation = 3
    soul.lifecycle.value = "awakened"

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    identity = result["identity"]
    assert identity["name"] == "Aria"
    assert identity["archetype"] == "Explorer"
    assert identity["did"] == "did:soul:aria-abc123"
    assert identity["born"] == born.isoformat()
    assert identity["age_days"] >= 0
    assert identity["lifecycle"] == "awakened"
    assert identity["values"] == ["curiosity", "honesty"]
    assert identity["incarnation"] == 3


# ---------------------------------------------------------------------------
# Tests — OCEAN personality section
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_returns_ocean():
    """OCEAN section returns all five traits as floats between 0 and 1."""
    soul = _make_full_soul()
    soul.dna.personality.openness = 0.8
    soul.dna.personality.conscientiousness = 0.7
    soul.dna.personality.extraversion = 0.6
    soul.dna.personality.agreeableness = 0.9
    soul.dna.personality.neuroticism = 0.3

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    ocean = result["ocean"]
    assert ocean["openness"] == 0.8
    assert ocean["conscientiousness"] == 0.7
    assert ocean["extraversion"] == 0.6
    assert ocean["agreeableness"] == 0.9
    assert ocean["neuroticism"] == 0.3
    # All values should be floats in valid range
    for val in ocean.values():
        assert isinstance(val, float)
        assert 0.0 <= val <= 1.0


@pytest.mark.asyncio
async def test_dashboard_ocean_falls_back_to_defaults_on_exception():
    """When soul.dna.personality raises AttributeError, OCEAN defaults to 0.5 for all traits."""
    soul = _make_full_soul()
    # MagicMock(spec=[]) has no allowed attributes, so any attr access raises AttributeError.
    # Assigning it to soul.dna causes `soul.dna.personality` to raise, hitting the except branch.
    import unittest.mock as _mock
    soul.dna = _mock.MagicMock(spec=[])

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    ocean = result["ocean"]
    for trait in ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"):
        assert ocean[trait] == 0.5


# ---------------------------------------------------------------------------
# Tests — state section
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_returns_state():
    """State section contains mood, energy, social_battery, and focus."""
    soul = _make_full_soul()
    soul.state.mood = "joyful"
    soul.state.energy = 92.0
    soul.state.social_battery = 60.0
    soul.state.focus = "deep"

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    state = result["state"]
    assert state["mood"] == "joyful"
    assert state["energy"] == 92.0
    assert state["social_battery"] == 60.0
    assert state["focus"] == "deep"


@pytest.mark.asyncio
async def test_dashboard_state_mood_enum_unwrapped():
    """When mood is an enum-like object with .value, the string value is returned."""
    soul = _make_full_soul()
    mood_enum = MagicMock()
    mood_enum.value = "melancholy"
    soul.state.mood = mood_enum

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    assert result["state"]["mood"] == "melancholy"


# ---------------------------------------------------------------------------
# Tests — core_memory section
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_returns_core_memory():
    """Core memory section contains persona and human strings."""
    soul = _make_full_soul()
    soul.get_core_memory.return_value = _make_core_memory(
        persona="I am PocketPaw, a sovereign AI.",
        human="Prakash — builder, captain.",
    )

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    cm = result["core_memory"]
    assert cm["persona"] == "I am PocketPaw, a sovereign AI."
    assert cm["human"] == "Prakash — builder, captain."


@pytest.mark.asyncio
async def test_dashboard_core_memory_defaults_on_exception():
    """When get_core_memory() raises, core_memory defaults to empty strings."""
    soul = _make_full_soul()
    soul.get_core_memory.side_effect = RuntimeError("core memory unavailable")

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    cm = result["core_memory"]
    assert cm["persona"] == ""
    assert cm["human"] == ""


# ---------------------------------------------------------------------------
# Tests — communication section
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_returns_communication():
    """Communication section returns warmth, verbosity, humor_style, emoji_usage."""
    soul = _make_full_soul()
    soul.dna.communication.warmth = "high"
    soul.dna.communication.verbosity = "concise"
    soul.dna.communication.humor_style = "dry"
    soul.dna.communication.emoji_usage = "rare"

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    comm = result["communication"]
    assert comm["warmth"] == "high"
    assert comm["verbosity"] == "concise"
    assert comm["humor_style"] == "dry"
    assert comm["emoji_usage"] == "rare"


# ---------------------------------------------------------------------------
# Tests — skills section
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_returns_skills():
    """Skills list contains id, name, level, xp, xp_to_next for each skill."""
    skill1 = _make_skill("sk_001", "Python", 5, 900, 1000)
    skill2 = _make_skill("sk_002", "Writing", 2, 100, 300)
    soul = _make_full_soul(skills=[skill1, skill2])

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    skills = result["skills"]
    assert len(skills) == 2
    assert skills[0] == {"id": "sk_001", "name": "Python", "level": 5, "xp": 900, "xp_to_next": 1000}
    assert skills[1] == {"id": "sk_002", "name": "Writing", "level": 2, "xp": 100, "xp_to_next": 300}


@pytest.mark.asyncio
async def test_dashboard_returns_empty_skills():
    """When no skills exist, skills returns an empty list."""
    soul = _make_full_soul(skills=[])

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    assert result["skills"] == []


# ---------------------------------------------------------------------------
# Tests — bond section
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_returns_bond():
    """Bond section contains bonded_to, strength, interaction_count, bonded_at."""
    bonded_at = datetime(2026, 1, 15, 9, 30, 0)
    bond = _make_bond("Prakash", 82.0, 100, bonded_at)
    soul = _make_full_soul(bond=bond)

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    b = result["bond"]
    assert b is not None
    assert b["bonded_to"] == "Prakash"
    assert b["strength"] == 82.0
    assert b["interaction_count"] == 100
    assert b["bonded_at"] == bonded_at.isoformat()


@pytest.mark.asyncio
async def test_dashboard_returns_bond_null():
    """When no bond exists on the soul, bond should be null."""
    soul = _make_full_soul(bond=None)
    # Ensure soul.bond is explicitly falsy
    soul.bond = None

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    assert result["bond"] is None


# ---------------------------------------------------------------------------
# Tests — memory breakdown section
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_returns_memory_breakdown():
    """Memory section reports correct counts for all memory tiers."""
    soul = _make_full_soul(
        memory_count=50,
        episodic_count=20,
        semantic_count=15,
        procedural_count=8,
        graph_count=7,
    )

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    mem = result["memory"]
    assert mem["episodic"] == 20
    assert mem["semantic"] == 15
    assert mem["procedural"] == 8
    assert mem["graph_nodes"] == 7
    assert mem["total"] == 50


@pytest.mark.asyncio
async def test_dashboard_memory_counts_default_to_zero_on_exception():
    """When accessing _memory sub-stores raises, per-tier counts default to 0."""
    soul = _make_full_soul(memory_count=50)
    # Make _episodic.entries() raise — this exercises the except branch in the memory block
    soul._memory._episodic.entries.side_effect = AttributeError("no entries")

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    mem = result["memory"]
    assert mem["episodic"] == 0
    assert mem["semantic"] == 0
    assert mem["procedural"] == 0
    assert mem["graph_nodes"] == 0
    assert mem["total"] == 50


# ---------------------------------------------------------------------------
# Tests — evolution section
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_returns_evolution():
    """Evolution history entries contain all expected fields."""
    proposed = datetime(2026, 2, 10, 8, 0, 0)
    mut = _make_evolution_entry(
        mut_id="mut_xyz",
        trait="conscientiousness",
        old_value="0.6",
        new_value="0.75",
        reason="Completed a long project",
        approved=True,
        proposed_at=proposed,
    )
    soul = _make_full_soul(evolution_history=[mut])

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    evo = result["evolution"]
    assert len(evo) == 1
    entry = evo[0]
    assert entry["id"] == "mut_xyz"
    assert entry["trait"] == "conscientiousness"
    assert entry["old_value"] == "0.6"
    assert entry["new_value"] == "0.75"
    assert entry["reason"] == "Completed a long project"
    assert entry["approved"] is True
    assert entry["proposed_at"] == proposed.isoformat()


@pytest.mark.asyncio
async def test_dashboard_returns_empty_evolution():
    """Empty evolution history returns an empty list."""
    soul = _make_full_soul(evolution_history=[])

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    assert result["evolution"] == []


@pytest.mark.asyncio
async def test_dashboard_evolution_capped_at_20_entries():
    """Evolution history is capped at the last 20 entries."""
    mutations = [
        _make_evolution_entry(mut_id=f"mut_{i:03d}", trait=f"trait_{i}")
        for i in range(25)
    ]
    soul = _make_full_soul(evolution_history=mutations)

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    # Endpoint does history[-20:] so we get the last 20
    assert len(result["evolution"]) == 20
    # Last entry should be from the end of the list (index 24 = mut_024)
    assert result["evolution"][-1]["id"] == "mut_024"


# ---------------------------------------------------------------------------
# Tests — self_model section
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_returns_self_model():
    """Self-model entries contain domain, confidence, and evidence_count."""
    images = [
        _make_self_image("coding", 0.9, 20),
        _make_self_image("writing", 0.6, 8),
    ]
    soul = _make_full_soul(self_model_images=images)

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    sm = result["self_model"]
    assert len(sm) == 2
    assert sm[0] == {"domain": "coding", "confidence": 0.9, "evidence_count": 20}
    assert sm[1] == {"domain": "writing", "confidence": 0.6, "evidence_count": 8}


@pytest.mark.asyncio
async def test_dashboard_returns_empty_self_model():
    """Empty self-model returns an empty list."""
    soul = _make_full_soul(self_model_images=[])

    mgr = _make_manager(soul=soul)
    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    assert result["self_model"] == []


# ---------------------------------------------------------------------------
# Tests — complete response shape
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dashboard_all_fields_present():
    """The complete response includes all expected top-level keys."""
    soul = _make_full_soul()
    mgr = _make_manager(soul=soul)

    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    expected_keys = {
        "enabled",
        "identity",
        "ocean",
        "state",
        "core_memory",
        "communication",
        "skills",
        "bond",
        "memory",
        "evolution",
        "self_model",
    }
    assert set(result.keys()) == expected_keys
    assert result["enabled"] is True


@pytest.mark.asyncio
async def test_dashboard_enabled_true_when_soul_loaded():
    """enabled field is True when manager and soul are both present."""
    soul = _make_full_soul()
    mgr = _make_manager(soul=soul)

    with patch("pocketpaw.soul.manager.get_soul_manager", return_value=mgr):
        result = await get_soul_dashboard()

    assert result["enabled"] is True
