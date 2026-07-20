from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.gateway.routes.chat import router as chat_router
from services.gateway.routes.children import router as children_router
from services.gateway.routes.profile import router as profile_router
from services.gateway.routes.story import router as story_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from services.bootstrap import bootstrap
    await bootstrap()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Children Growth OS", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(children_router, prefix="/api/v1")
    app.include_router(profile_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(story_router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
