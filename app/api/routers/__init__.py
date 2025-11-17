from app.api.routers.auth import router as auth_router
from app.api.routers.main import router as main_router
from app.api.routers.users import router as users_router

router = main_router

__all__ = ["auth_router", "main_router", "router", "users_router"]
