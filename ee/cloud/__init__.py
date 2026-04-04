"""PocketPaw Enterprise Cloud — domain-driven architecture.

Domains: auth, workspace, chat, pockets, sessions, agents.
Each has router.py (thin), service.py (logic), schemas.py (validation).
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ee.cloud.shared.errors import CloudError


def mount_cloud(app: FastAPI) -> None:
    """Mount all cloud domain routers and the error handler."""

    # Global error handler
    @app.exception_handler(CloudError)
    async def cloud_error_handler(request: Request, exc: CloudError):
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

    # Import and mount domain routers
    from ee.cloud.auth.router import router as auth_router
    from ee.cloud.workspace.router import router as workspace_router
    from ee.cloud.agents.router import router as agents_router
    from ee.cloud.chat.router import router as chat_router
    from ee.cloud.pockets.router import router as pockets_router
    from ee.cloud.sessions.router import router as sessions_router
    from ee.cloud.license import get_license_info

    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(workspace_router, prefix="/api/v1")
    app.include_router(agents_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(pockets_router, prefix="/api/v1")
    app.include_router(sessions_router, prefix="/api/v1")

    # License endpoint (no auth)
    @app.get("/api/v1/license", tags=["License"])
    async def license_info():
        return get_license_info()

    # Register cross-domain event handlers
    from ee.cloud.shared.event_handlers import register_event_handlers
    register_event_handlers()
