from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.config import settings

from app.routers import affiliate
from app.routers import article
from app.routers import article_image
from app.routers import category
from app.routers import tag
from app.routers import public_article
from app.routers import admin
from app.routers import web

from starlette.middleware.sessions import SessionMiddleware



app = FastAPI(
    title="AI Affiliate Blog API",
)


@app.middleware("http")
async def protect_admin_routes(
    request: Request,
    call_next,
):
    path = request.url.path

    # 管理画面以外はそのまま通す
    if not path.startswith("/admin"):
        return await call_next(request)

    # ログイン画面は未認証でも利用可能
    public_admin_paths = {
        "/admin/login",
    }

    if path in public_admin_paths:
        return await call_next(request)

    user_id = request.session.get(
        "user_id"
    )

    role = request.session.get(
        "role"
    )

    # ------------------------------------
    # 未ログイン
    # ------------------------------------

    if user_id is None:
        request.session.clear()

        return RedirectResponse(
            url="/admin/login",
            status_code=303,
        )

    # ------------------------------------
    # Role validation
    # ------------------------------------

    if role not in {
        "admin",
        "editor",
    }:
        request.session.clear()

        return RedirectResponse(
            url="/admin/login",
            status_code=303,
        )

    # ------------------------------------
    # User management
    #
    # admin のみ許可
    # ------------------------------------

    if (
        path.startswith("/admin/users")
        and role != "admin"
    ):
        return RedirectResponse(
            url="/admin/articles",
            status_code=303,
        )

    return await call_next(request)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key,
    session_cookie="ai_blog_session",
    max_age=60 * 60 * 8,
    same_site="lax",
    https_only=settings.session_https_only,
)

# ========================================
# Upload directory
# ========================================

upload_dir = Path(settings.upload_dir)

upload_dir.mkdir(
    parents=True,
    exist_ok=True,
)


# ========================================
# Static files
# ========================================

app.mount(
    "/uploads",
    StaticFiles(
        directory=str(upload_dir),
    ),
    name="uploads",
)


# ========================================
# Routers
# ========================================

app.include_router(
    affiliate.router
)

app.include_router(
    article.router
)

app.include_router(
    article_image.router
)

app.include_router(
    category.router
)

app.include_router(
    tag.router
)

app.include_router(
    public_article.router
)

app.include_router(
    admin.router
)

app.include_router(
    web.router
)
