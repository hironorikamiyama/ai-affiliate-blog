from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def build_article_text(article) -> str:
    return " ".join(
        [
            article.title or "",
            article.keyword or "",
            article.body or "",
        ]
    )


def get_similar_articles(
    target_article,
    articles,
    limit: int = 5,
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

    vectorizer = TfidfVectorizer()

    try:
        tfidf_matrix = vectorizer.fit_transform(
            documents
        )
    except ValueError:
        return []

    target_vector = tfidf_matrix[0:1]
    candidate_vectors = tfidf_matrix[1:]

    similarities = cosine_similarity(
        target_vector,
        candidate_vectors,
    )[0]

    results = []

    for article, similarity in zip(
        candidates,
        similarities,
    ):
        results.append(
            {
                "article_id": article.id,
                "title": article.title,
                "slug": article.slug,
                "similarity": float(similarity),
            }
        )

    results.sort(
        key=lambda item: item["similarity"],
        reverse=True,
    )

    return results[:limit]