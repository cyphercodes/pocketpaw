"""Soul Protocol API endpoints.

Updated: 2026-04-01 — Added GET /soul/dashboard endpoint that returns all soul
data in a single JSON response (identity, OCEAN, state, core memory, communication,
skills, bond, memory counts, evolution history, self-model).
Updated: 2026-03-29 — v0.2.8: Enriched /soul/status with did, focus, memory_count,
bond, core_memory. Added: GET/PATCH /soul/core-memory, POST /soul/remember,
POST /soul/recall, POST /soul/forget.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile

from pocketpaw.api.deps import require_scope

router = APIRouter(tags=["Soul"], dependencies=[Depends(require_scope("settings:read"))])


@router.get("/soul/status")
async def get_soul_status():
    """Return current soul state (mood, energy, personality, domains)."""
    from pocketpaw.soul.manager import get_soul_manager

    mgr = get_soul_manager()
    if mgr is None or mgr.soul is None:
        return {"enabled": False}

    soul = mgr.soul
    state = soul.state
    result: dict = {
        "enabled": True,
        "name": soul.name,
        "did": soul.did if hasattr(soul, "did") else None,
        "mood": getattr(state, "mood", None),
        "energy": getattr(state, "energy", None),
        "social_battery": getattr(state, "social_battery", None),
        "focus": getattr(state, "focus", None),
        "memory_count": soul.memory_count if hasattr(soul, "memory_count") else 0,
        "observe_count": mgr.observe_count,
    }

    # v0.2.8+: Include bond state
    if hasattr(soul, "bond") and soul.bond:
        try:
            result["bond"] = soul.bond.model_dump() if hasattr(soul.bond, "model_dump") else None
        except Exception:
            pass

    # v0.2.8+: Include core memory summary
    if hasattr(soul, "get_core_memory"):
        try:
            cm = soul.get_core_memory()
            result["core_memory"] = cm.model_dump() if hasattr(cm, "model_dump") else {}
        except Exception:
            pass

    if hasattr(soul, "self_model") and soul.self_model:
        try:
            images = soul.self_model.get_active_self_images(limit=5)
            result["domains"] = [
                {"domain": img.domain, "confidence": img.confidence} for img in images
            ]
        except Exception:
            pass

    return result


@router.get("/soul/dashboard")
async def get_soul_dashboard():
    """Return all soul data in a single JSON response for dashboard rendering."""
    from datetime import datetime

    from pocketpaw.soul.manager import get_soul_manager

    mgr = get_soul_manager()
    if mgr is None or mgr.soul is None:
        return {"enabled": False}

    soul = mgr.soul

    # ── Identity ──
    identity_data: dict = {
        "name": soul.name,
        "archetype": getattr(soul, "archetype", ""),
        "did": soul.did if hasattr(soul, "did") else None,
        "born": soul.born.isoformat() if hasattr(soul, "born") and soul.born else None,
        "age_days": (datetime.now() - soul.born).days if hasattr(soul, "born") and soul.born else 0,
        "lifecycle": soul.lifecycle.value if hasattr(soul, "lifecycle") else None,
        "values": (
            soul.identity.core_values
            if hasattr(soul, "identity") and hasattr(soul.identity, "core_values")
            else []
        ),
        "incarnation": (
            soul.identity.incarnation
            if hasattr(soul, "identity") and hasattr(soul.identity, "incarnation")
            else 1
        ),
    }

    # ── OCEAN personality ──
    ocean_data: dict = {}
    try:
        p = soul.dna.personality
        ocean_data = {
            "openness": p.openness,
            "conscientiousness": p.conscientiousness,
            "extraversion": p.extraversion,
            "agreeableness": p.agreeableness,
            "neuroticism": p.neuroticism,
        }
    except Exception:
        ocean_data = {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.5,
        }

    # ── State ──
    state = soul.state
    state_data: dict = {
        "mood": getattr(state, "mood", "neutral"),
        "energy": getattr(state, "energy", 100.0),
        "social_battery": getattr(state, "social_battery", 100.0),
        "focus": getattr(state, "focus", "medium"),
    }
    # Ensure mood is a string value, not an enum
    if hasattr(state_data["mood"], "value"):
        state_data["mood"] = state_data["mood"].value

    # ── Core memory ──
    core_memory_data: dict = {"persona": "", "human": ""}
    try:
        if hasattr(soul, "get_core_memory"):
            cm = soul.get_core_memory()
            core_memory_data = {
                "persona": getattr(cm, "persona", ""),
                "human": getattr(cm, "human", ""),
            }
    except Exception:
        pass

    # ── Communication style ──
    comm_data: dict = {
        "warmth": "moderate",
        "verbosity": "moderate",
        "humor_style": "none",
        "emoji_usage": "none",
    }
    try:
        comm = soul.dna.communication
        comm_data = {
            "warmth": getattr(comm, "warmth", "moderate"),
            "verbosity": getattr(comm, "verbosity", "moderate"),
            "humor_style": getattr(comm, "humor_style", "none"),
            "emoji_usage": getattr(comm, "emoji_usage", "none"),
        }
    except Exception:
        pass

    # ── Skills ──
    skills_data: list = []
    try:
        if hasattr(soul, "skills") and soul.skills:
            for skill in soul.skills.skills:
                skills_data.append({
                    "id": skill.id,
                    "name": skill.name,
                    "level": skill.level,
                    "xp": skill.xp,
                    "xp_to_next": skill.xp_to_next,
                })
    except Exception:
        pass

    # ── Bond ──
    bond_data: dict | None = None
    try:
        if hasattr(soul, "bond") and soul.bond:
            bond = soul.bond
            bond_data = {
                "bonded_to": getattr(bond, "bonded_to", None) or None,
                "strength": getattr(bond, "bond_strength", 50.0),
                "interaction_count": getattr(bond, "interaction_count", 0),
                "bonded_at": (
                    bond.bonded_at.isoformat()
                    if hasattr(bond, "bonded_at") and bond.bonded_at
                    else None
                ),
            }
    except Exception:
        pass

    # ── Memory counts ──
    memory_data: dict = {
        "episodic": 0,
        "semantic": 0,
        "procedural": 0,
        "graph_nodes": 0,
        "total": soul.memory_count if hasattr(soul, "memory_count") else 0,
    }
    try:
        mem = soul._memory
        memory_data["episodic"] = len(mem._episodic.entries())
        memory_data["semantic"] = len(mem._semantic.facts())
        memory_data["procedural"] = len(mem._procedural.entries())
        memory_data["graph_nodes"] = len(mem._graph.entities())
    except Exception:
        pass

    # ── Evolution history (last 20) ──
    evolution_data: list = []
    try:
        history = []
        if hasattr(soul, "evolution_history"):
            history = soul.evolution_history
        elif hasattr(soul, "_evolution") and hasattr(soul._evolution, "history"):
            history = soul._evolution.history
        for mut in history[-20:]:
            evolution_data.append({
                "id": getattr(mut, "id", ""),
                "trait": getattr(mut, "trait", ""),
                "old_value": getattr(mut, "old_value", ""),
                "new_value": getattr(mut, "new_value", ""),
                "reason": getattr(mut, "reason", ""),
                "approved": getattr(mut, "approved", None),
                "proposed_at": (
                    mut.proposed_at.isoformat()
                    if hasattr(mut, "proposed_at") and mut.proposed_at
                    else None
                ),
            })
    except Exception:
        pass

    # ── Self-model ──
    self_model_data: list = []
    try:
        if hasattr(soul, "self_model") and soul.self_model:
            images = soul.self_model.get_active_self_images()
            for img in images:
                self_model_data.append({
                    "domain": img.domain,
                    "confidence": img.confidence,
                    "evidence_count": img.evidence_count,
                })
    except Exception:
        pass

    return {
        "enabled": True,
        "identity": identity_data,
        "ocean": ocean_data,
        "state": state_data,
        "core_memory": core_memory_data,
        "communication": comm_data,
        "skills": skills_data,
        "bond": bond_data,
        "memory": memory_data,
        "evolution": evolution_data,
        "self_model": self_model_data,
    }


@router.get("/soul/core-memory")
async def get_core_memory():
    """Return the soul's core memory (persona and human description)."""
    from pocketpaw.soul.manager import get_soul_manager
    mgr = get_soul_manager()
    if mgr is None or mgr.soul is None:
        return {"error": "Soul not available"}
    if not hasattr(mgr.soul, "get_core_memory"):
        return {"error": "Requires soul-protocol >= 0.2.8."}
    try:
        cm = mgr.soul.get_core_memory()
        return cm.model_dump() if hasattr(cm, "model_dump") else {}
    except Exception as exc:
        return {"error": f"Failed: {exc}"}


@router.patch("/soul/core-memory")
async def edit_core_memory(body: dict):
    """Edit core memory. Body: {"persona": "...", "human": "..."}"""
    from pocketpaw.soul.manager import get_soul_manager
    mgr = get_soul_manager()
    if mgr is None or mgr.soul is None:
        return {"error": "Soul not available"}
    try:
        kwargs = {k: v for k, v in body.items() if k in ("persona", "human") and v}
        if not kwargs:
            return {"error": "Provide 'persona' or 'human'."}
        await mgr.soul.edit_core_memory(**kwargs)
        mgr._dirty = True
        return {"ok": True, "updated": list(kwargs.keys())}
    except Exception as exc:
        return {"error": f"Failed: {exc}"}


@router.post("/soul/remember")
async def soul_remember(body: dict):
    """Store a memory. Body: {"content": "...", "importance": 5}"""
    from pocketpaw.soul.manager import get_soul_manager
    mgr = get_soul_manager()
    if mgr is None or mgr.soul is None:
        return {"error": "Soul not available"}
    content = body.get("content", "")
    if not content:
        return {"error": "Missing 'content'"}
    try:
        importance = max(1, min(10, body.get("importance", 5)))
        mid = await mgr.soul.remember(content, importance=importance)
        mgr._dirty = True
        return {"ok": True, "memory_id": mid}
    except Exception as exc:
        return {"error": f"Failed: {exc}"}


@router.post("/soul/recall")
async def soul_recall(body: dict):
    """Search memories. Body: {"query": "...", "limit": 10}"""
    from pocketpaw.soul.manager import get_soul_manager
    mgr = get_soul_manager()
    if mgr is None or mgr.soul is None:
        return {"error": "Soul not available"}
    try:
        memories = await mgr.soul.recall(body.get("query", ""), limit=body.get("limit", 10))
        return [m.model_dump() if hasattr(m, "model_dump") else {"content": str(m)} for m in memories]
    except Exception as exc:
        return {"error": f"Failed: {exc}"}


@router.post("/soul/forget")
async def soul_forget(body: dict):
    """Forget memories matching query. Body: {"query": "..."}"""
    from pocketpaw.soul.manager import get_soul_manager
    mgr = get_soul_manager()
    if mgr is None or mgr.soul is None:
        return {"error": "Soul not available"}
    if not body.get("query"):
        return {"error": "Missing 'query'"}
    result = await mgr.forget(body["query"])
    return result


@router.post("/soul/export")
async def export_soul():
    """Save the current soul to its .soul file."""
    from pocketpaw.soul.manager import get_soul_manager

    mgr = get_soul_manager()
    if mgr is None or mgr.soul is None:
        return {"error": "Soul not enabled"}

    await mgr.save()
    return {"path": str(mgr.soul_file), "status": "exported"}


@router.post("/soul/reload")
async def reload_soul():
    """Reload the soul from its .soul file on disk (v0.2.4+).

    Useful when the file was modified by another client.
    """
    from pocketpaw.soul.manager import get_soul_manager

    mgr = get_soul_manager()
    if mgr is None or mgr.soul is None:
        return {"error": "Soul not enabled"}

    success = await mgr.reload()
    if success:
        return {"status": "reloaded", "name": mgr.soul.name}
    return {"error": "Reload failed. Check if the .soul file exists and is valid."}


@router.post("/soul/evaluate")
async def evaluate_soul(body: dict):
    """Run rubric-based self-evaluation on a response (v0.2.4+).

    Body: {"user_input": "...", "agent_output": "..."}
    Returns heuristic scores for 7 criteria.
    """
    from pocketpaw.soul.manager import get_soul_manager

    mgr = get_soul_manager()
    if mgr is None or mgr.soul is None:
        return {"error": "Soul not enabled"}

    user_input = body.get("user_input", "")
    agent_output = body.get("agent_output", "")
    if not user_input or not agent_output:
        return {"error": "Both 'user_input' and 'agent_output' are required"}

    result = await mgr.evaluate(user_input, agent_output)
    if result is None:
        return {"error": "Self-evaluation not available. Requires soul-protocol >= 0.2.4."}
    return {"status": "evaluated", "scores": result}


_ALLOWED_IMPORT_SUFFIXES = frozenset({".soul", ".yaml", ".yml", ".json"})


@router.post("/soul/import")
async def import_soul(file: UploadFile):
    """Import a soul from an uploaded .soul, .yaml, .yml, or .json file.

    Replaces the currently active soul with the imported one.
    Requires soul to be enabled in settings.
    """
    from pocketpaw.soul.manager import get_soul_manager

    mgr = get_soul_manager()
    if mgr is None:
        return {"error": "Soul not enabled. Enable it in Settings > Soul first."}

    # Validate file extension
    filename = file.filename or "upload"
    suffix = Path(filename).suffix.lower()
    if suffix not in _ALLOWED_IMPORT_SUFFIXES:
        return {
            "error": f"Unsupported file type: {suffix}. "
            f"Accepted: {', '.join(sorted(_ALLOWED_IMPORT_SUFFIXES))}"
        }

    # Save upload to a temp file in the soul directory
    from pocketpaw.config import get_config_dir

    import_dir = get_config_dir() / "soul" / "imports"
    import_dir.mkdir(parents=True, exist_ok=True)
    temp_path = import_dir / f"import{suffix}"

    try:
        content = await file.read()
        temp_path.write_bytes(content)

        name = await mgr.import_from_file(temp_path)
        return {"status": "imported", "name": name, "path": str(mgr.soul_file)}
    except (ValueError, FileNotFoundError) as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"Import failed: {exc}"}
    finally:
        temp_path.unlink(missing_ok=True)


@router.post("/soul/import-path")
async def import_soul_from_path(body: dict):
    """Import a soul from a file path on the server's filesystem.

    Body: {"path": "/path/to/file.soul"} or {"path": "/path/to/config.yaml"}
    """
    from pocketpaw.soul.manager import get_soul_manager

    mgr = get_soul_manager()
    if mgr is None:
        return {"error": "Soul not enabled. Enable it in Settings > Soul first."}

    file_path = body.get("path", "")
    if not file_path:
        return {"error": "Missing 'path' field"}

    path = Path(file_path)

    # Sandbox: only allow paths within ~/.pocketpaw/soul/
    from pocketpaw.config import get_config_dir

    allowed_base = get_config_dir() / "soul"
    try:
        path.resolve().relative_to(allowed_base.resolve())
    except ValueError:
        return {"error": f"Path must be within {allowed_base}"}

    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    suffix = path.suffix.lower()
    if suffix not in _ALLOWED_IMPORT_SUFFIXES:
        return {
            "error": f"Unsupported file type: {suffix}. "
            f"Accepted: {', '.join(sorted(_ALLOWED_IMPORT_SUFFIXES))}"
        }

    try:
        name = await mgr.import_from_file(path)
        return {"status": "imported", "name": name, "path": str(mgr.soul_file)}
    except (ValueError, FileNotFoundError) as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": f"Import failed: {exc}"}
