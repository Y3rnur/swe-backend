from app.api.routers.auth import router as auth_router
from app.api.routers.catalog import router as catalog_router
from app.api.routers.links import router as links_router
from app.api.routers.main import router as main_router
from app.api.routers.orders import router as orders_router
from app.api.routers.products import router as products_router
from app.api.routers.users import router as users_router

router = main_router

__all__ = [
    "auth_router",
    "catalog_router",
    "links_router",
    "main_router",
    "orders_router",
    "products_router",
    "router",
    "users_router",
]
