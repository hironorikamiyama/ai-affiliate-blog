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


def calculate_similarities(articles):
    if len(articles) < 2:
        return []

    documents = [
        build_article_text(article)
        for article in articles
    ]

    vectorizer = TfidfVectorizer()

    tfidf_matrix = vectorizer.fit_transform(
        documents
    )

    similarity_matrix = cosine_similarity(
        tfidf_matrix
    )

    results = []

    for i, article in enumerate(articles):
        similarities = []

        for j, other_article in enumerate(articles):
            if i == j:
                continue

            similarities.append(
                {
                    "article_id": other_article.id,
                    "title": other_article.title,
                    "similarity": float(
                        similarity_matrix[i][j]
                    ),
                }
            )

        similarities.sort(
            key=lambda x: x["similarity"],
            reverse=True,
        )

        results.append(
            {
                "article_id": article.id,
                "title": article.title,
                "similar_articles": similarities,
            }
        )

    return results
