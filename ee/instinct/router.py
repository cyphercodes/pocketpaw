# ee/instinct/router.py — FastAPI router for the Instinct decision pipeline API.
# Created: 2026-03-28 — Propose, approve/reject, list pending, query audit.

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ee.instinct.models import (
    Action,
    ActionCategory,
    ActionPriority,
    ActionTrigger,
    AuditEntry,
)
from ee.instinct.store import InstinctStore

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Instinct"])

_DB_PATH = Path.home() / ".pocketpaw" / "instinct.db"


def _store() -> InstinctStore:
    return InstinctStore(_DB_PATH)


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ProposeRequest(BaseModel):
    pocket_id: str
    title: str
    description: str = ""
    recommendation: str = ""
    trigger: ActionTrigger
    category: ActionCategory = ActionCategory.WORKFLOW
    priority: ActionPriority = ActionPriority.MEDIUM
    parameters: dict[str, Any] = {}


class RejectRequest(BaseModel):
    reason: str = ""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/instinct/actions", response_model=Action, status_code=201)
async def propose_action(req: ProposeRequest):
    return await _store().propose(
        pocket_id=req.pocket_id, title=req.title,
        description=req.description, recommendation=req.recommendation,
        trigger=req.trigger, category=req.category,
        priority=req.priority, parameters=req.parameters,
    )


@router.get("/instinct/actions/pending", response_model=list[Action])
async def pending_actions(pocket_id: str | None = Query(None)):
    return await _store().pending(pocket_id=pocket_id)


@router.post("/instinct/actions/{action_id}/approve", response_model=Action)
async def approve_action(action_id: str):
    action = await _store().approve(action_id)
    if not action:
        raise HTTPException(404, "Action not found")
    return action


@router.post("/instinct/actions/{action_id}/reject", response_model=Action)
async def reject_action(action_id: str, req: RejectRequest | None = None):
    reason = req.reason if req else ""
    action = await _store().reject(action_id, reason=reason)
    if not action:
        raise HTTPException(404, "Action not found")
    return action


@router.get("/instinct/audit", response_model=list[AuditEntry])
async def query_audit(
    pocket_id: str | None = Query(None),
    category: str | None = Query(None),
    event: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
):
    return await _store().query_audit(
        pocket_id=pocket_id, category=category, event=event, limit=limit,
    )
