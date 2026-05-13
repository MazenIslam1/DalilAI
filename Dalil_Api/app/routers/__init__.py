from app.routers.health import router as health_router
from app.routers.files import router as files_router
from app.routers.chat import router as chat_router
from app.routers.datasets import router as datasets_router

__all__ = ["health_router", "files_router", "chat_router", "datasets_router"]
