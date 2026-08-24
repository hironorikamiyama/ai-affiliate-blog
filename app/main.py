from fastapi import FastAPI

from app.db.database import Base, engine
from app.models.affiliate import AffiliateProgram
from app.models.article import Article
from app.models.article_image import ArticleImage

from app.routers.affiliate import router as affiliate_router
from app.routers.article import router as article_router
from app.routers import article_image
from fastapi.staticfiles import StaticFiles

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Affiliate Blog API",
    version="0.1.0",
)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads",
)

app.include_router(affiliate_router)
app.include_router(article_router)
app.include_router(article_image.router)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "AI Affiliate Blog API is running",
    }