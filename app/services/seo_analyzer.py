import logging
import re
from typing import Any

from app.config import settings


logger = logging.getLogger(__name__)


# ========================================
# SEO Analyzer
# ========================================

def analyze_seo(
    *,
    title: str,
    keyword: str,
    meta_description: str | None,
    body: str,
) -> dict[str, Any]:
    """
    記事のSEO分析を実行する。

    SEO_PROVIDER によって
    mock / openai を切り替える。

    SEOスコアは検索順位を保証するものではなく、
    CMS内部で使用する品質チェック指標。
    """

    provider = getattr(
        settings,
        "seo_provider",
        "mock",
    ).lower()

    if provider == "mock":
        return _analyze_with_mock(
            title=title,
            keyword=keyword,
            meta_description=meta_description,
            body=body,
        )

    if provider == "openai":
        return _analyze_with_openai(
            title=title,
            keyword=keyword,
            meta_description=meta_description,
            body=body,
        )

    raise ValueError(
        f"Unsupported SEO provider: {provider}"
    )


# ========================================
# Mock SEO Analyzer
# ========================================

def _analyze_with_mock(
    *,
    title: str,
    keyword: str,
    meta_description: str | None,
    body: str,
) -> dict[str, Any]:

    score = 100

    warnings: list[str] = []
    improvements: list[str] = []
    missing_topics: list[str] = []

    # ------------------------------------
    # Title
    # ------------------------------------

    title_length = len(title)

    if title_length < 20:
        score -= 10

        warnings.append(
            "タイトルが短い可能性があります。"
        )

    elif title_length > 60:
        score -= 10

        warnings.append(
            "タイトルが長い可能性があります。"
        )

    if keyword not in title:
        score -= 15

        improvements.append(
            "タイトルに主要キーワードを"
            "自然な形で含めることを検討してください。"
        )

    # ------------------------------------
    # Meta Description
    # ------------------------------------

    if not meta_description:
        score -= 15

        warnings.append(
            "Meta Descriptionが設定されていません。"
        )

    else:
        meta_length = len(
            meta_description
        )

        if meta_length < 50:
            score -= 5

            improvements.append(
                "Meta Descriptionに"
                "記事内容をもう少し具体的に"
                "記載することを検討してください。"
            )

        elif meta_length > 160:
            score -= 5

            warnings.append(
                "Meta Descriptionが"
                "長い可能性があります。"
            )

    # ------------------------------------
    # Body length
    # ------------------------------------

    body_length = len(body)

    if body_length < 500:
        score -= 20

        warnings.append(
            "本文の情報量が少ない可能性があります。"
        )

    elif body_length < 1000:
        score -= 10

        improvements.append(
            "必要に応じて具体例や"
            "実体験などを追加してください。"
        )

    # ------------------------------------
    # Heading analysis
    # Markdown想定
    # ------------------------------------

    h2_count = len(
        re.findall(
            r"^##\s+.+$",
            body,
            flags=re.MULTILINE,
        )
    )

    h3_count = len(
        re.findall(
            r"^###\s+.+$",
            body,
            flags=re.MULTILINE,
        )
    )

    if h2_count == 0:
        score -= 10

        warnings.append(
            "H2相当の見出しがありません。"
        )

    # ------------------------------------
    # Keyword usage
    # ------------------------------------

    keyword_count = body.count(
        keyword
    )

    if keyword_count == 0:
        score -= 10

        improvements.append(
            "本文に主要キーワードを"
            "自然な形で含めることを"
            "検討してください。"
        )

    # ------------------------------------
    # Affiliate placeholder
    # ------------------------------------

    affiliate_links = re.findall(
        r"\{\{AFFILIATE_LINK:(\d+)\}\}",
        body,
    )

    if not affiliate_links:
        improvements.append(
            "収益化対象の記事であれば"
            "アフィリエイトリンクの配置を"
            "検討してください。"
        )

    # ------------------------------------
    # Example topic analysis
    # 後でLLMに置き換える部分
    # ------------------------------------

    body_lower = body.lower()

    topic_candidates = {
        "アクセス": [
            "アクセス",
            "行き方",
            "交通",
        ],
        "費用": [
            "費用",
            "料金",
            "交通費",
        ],
        "注意点": [
            "注意",
            "注意点",
        ],
        "具体例・体験": [
            "実際",
            "体験",
            "実釣",
        ],
    }

    for topic, words in (
        topic_candidates.items()
    ):
        if not any(
            word.lower() in body_lower
            for word in words
        ):
            missing_topics.append(
                topic
            )

    # ------------------------------------
    # Score normalization
    # ------------------------------------

    score = max(
        0,
        min(
            score,
            100,
        ),
    )

    # ------------------------------------
    # Suggestions
    # ------------------------------------

    title_suggestion = title

    if keyword not in title:
        title_suggestion = (
            f"{keyword}｜{title}"
        )

    meta_description_suggestion = (
        meta_description
        or (
            f"{keyword}について、"
            "具体的なポイントや"
            "注意点をわかりやすく解説します。"
        )
    )

    return {
        "provider": "mock",

        "score": score,

        "search_intent": (
            f"「{keyword}」について"
            "具体的な情報を探しているユーザー"
        ),

        "title_suggestion": (
            title_suggestion
        ),

        "meta_description_suggestion": (
            meta_description_suggestion
        ),

        "warnings": warnings,

        "improvements": improvements,

        "missing_topics": missing_topics,

        "metrics": {
            "title_length": title_length,
            "meta_description_length": (
                len(meta_description)
                if meta_description
                else 0
            ),
            "body_length": body_length,
            "keyword_count": keyword_count,
            "h2_count": h2_count,
            "h3_count": h3_count,
            "affiliate_link_count": len(
                affiliate_links
            ),
        },
    }


# ========================================
# OpenAI SEO Analyzer
# ========================================

def _analyze_with_openai(
    *,
    title: str,
    keyword: str,
    meta_description: str | None,
    body: str,
) -> dict[str, Any]:
    """
    OpenAI API接続用。

    現在はAPI利用開始前なので、
    実装箇所だけ分離しておく。
    """

    raise NotImplementedError(
        "OpenAI SEO analyzer is not enabled yet."
    )