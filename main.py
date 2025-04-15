import logging
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from src.conf.config import settings
from src.routes import internal
from src.routes.v1 import contacts, auth, users

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG if settings.ENV == "dev" else logging.INFO)

app = FastAPI(
    title="Users Contacts Organizer", version="1.3", description="GoIT Home Work 10"
)
logger.debug(
    "Starting FastAPI app '%s' v%s in environment '%s'",
    app.title,
    app.version,
    settings.ENV,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.LIMIT_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(auth.router)
v1_router.include_router(users.router)
v1_router.include_router(contacts.router)

app.include_router(v1_router)
app.include_router(internal.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.BIND_HOST,
        port=settings.BIND_PORT,
        reload=True if settings.ENV == "dev" else False,
    )
