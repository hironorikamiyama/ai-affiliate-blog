from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


MODEL_NAME = (
    "sentence-transformers/"
    "paraphrase-multilingual-MiniLM-L12-v2"
)

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model

    if _model is None:
        _model = SentenceTransformer(
            MODEL_NAME
        )

    return _model


def build_article_text(article) -> str:
    return " ".join(
        [
            article.title or "",
            article.keyword or "",
            article.body or "",
        ]
    )


def get_embedding_similar_articles(
    target_article,
    articles,
    limit: int = 5,
    min_similarity: float = 0.0,
):
    candidates = [
        article
        for article in articles
        if article.id != target_article.id
    ]

    if not candidates:
        return []

    all_articles = [
        target_article,
        *candidates,
    ]

    documents = [
        build_article_text(article)
        for article in all_articles
    ]

    model = get_model()

    embeddings = model.encode(
        documents,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    target_vector = embeddings[0:1]
    candidate_vectors = embeddings[1:]

    similarities = cosine_similarity(
        target_vector,
        candidate_vectors,
    )[0]

    results = []

    for article, similarity in zip(
        candidates,
        similarities,
    ):
        similarity_value = float(similarity)

        if similarity_value < min_similarity:
            continue

        results.append(
            {
                "article_id": article.id,
                "title": article.title,
                "slug": article.slug,
                "similarity": similarity_value,
            }
        )

    results.sort(
        key=lambda item: item["similarity"],
        reverse=True,
    )

    return results[:limit]
