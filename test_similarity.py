from app.db.database import SessionLocal

from app.models.affiliate import AffiliateProgram
from app.models.article import Article
from app.models.article_image import ArticleImage

from app.services.article_similarity import (
    calculate_similarities,
)
db = SessionLocal()

try:
    articles = (
        db.query(Article)
        .order_by(Article.id.asc())
        .all()
    )

    results = calculate_similarities(
        articles
    )

    for result in results:
        print()
        print(
            f"ARTICLE: "
            f"{result['article_id']} "
            f"{result['title']}"
        )

        for similar in result["similar_articles"][:3]:
            print(
                f"  -> "
                f"{similar['article_id']} "
                f"{similar['title']} "
                f"{similar['similarity']:.4f}"
            )

finally:
    db.close()