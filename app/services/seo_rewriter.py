import logging
from typing import Any

from app.config import settings
from app.services.seo_analyzer import analyze_seo


logger = logging.getLogger(__name__)


# ========================================
# SEO Rewriter
# ========================================

def rewrite_article_for_seo(
    *,
    title: str,
    keyword: str,
    meta_description: str | None,
    body: str,
) -> dict[str, Any]:
    """
    SEO分析結果をもとに本文の改善版を生成する。

    seo_rewriter_provider によって
    mock / openai を切り替える。

    この関数ではDB更新を行わない。
    改善版本文を生成して返すだけとする。
    """

    provider = getattr(
        settings,
        "seo_rewriter_provider",
        "mock",
    ).lower()

    if provider == "mock":
        return _rewrite_with_mock(
            title=title,
            keyword=keyword,
            meta_description=meta_description,
            body=body,
        )

    if provider == "openai":
        return _rewrite_with_openai(
            title=title,
            keyword=keyword,
            meta_description=meta_description,
            body=body,
        )

    raise ValueError(
        f"Unsupported SEO rewriter provider: {provider}"
    )


# ========================================
# Mock SEO Rewriter
# ========================================

def _rewrite_with_mock(
    *,
    title: str,
    keyword: str,
    meta_description: str | None,
    body: str,
) -> dict[str, Any]:
    """
    APIを使わず、SEO Analyzerの結果を利用して
    改善版本文を生成する。

    Mock版では既存本文を破壊せず、
    不足しているトピックのセクションを
    本文末尾へ追加する。
    """

    seo_result = analyze_seo(
        title=title,
        keyword=keyword,
        meta_description=meta_description,
        body=body,
    )

    missing_topics = (
        seo_result.get(
            "missing_topics",
            [],
        )
    )

    rewritten_body = body.rstrip()

    added_topics: list[str] = []

    # ------------------------------------
    # Missing topic sections
    # ------------------------------------

    topic_templates = {
        "アクセス": (
            "## アクセス情報\n\n"
            "公共交通を利用する場合は、"
            "最寄り駅やバス停から目的地までの"
            "移動経路を事前に確認しておきましょう。"
            "所要時間や徒歩区間も確認しておくと、"
            "当日の移動がスムーズです。"
        ),

        "費用": (
            "## 費用の目安\n\n"
            "交通費や現地で必要になる費用を"
            "事前に確認しておくことが重要です。"
            "往復の交通費だけでなく、"
            "必要に応じて飲食費や"
            "その他の費用も考慮しましょう。"
        ),

        "注意点": (
            "## 注意点\n\n"
            "現地のルールや利用条件を確認し、"
            "周囲の利用者に配慮して行動しましょう。"
            "天候や交通状況なども"
            "事前に確認することをおすすめします。"
        ),

        "具体例・体験": (
            "## 実際に利用する際のポイント\n\n"
            "実際に利用する場合は、"
            "事前に移動経路や必要な準備を整理し、"
            "余裕を持ったスケジュールを"
            "組むことがポイントです。"
            "現地で得た情報も記録しておくと、"
            "次回以降の計画に役立ちます。"
        ),
    }

    for topic in missing_topics:
        section = topic_templates.get(
            topic
        )

        if section is None:
            continue

        rewritten_body += (
            "\n\n"
            + section
        )

        added_topics.append(
            topic
        )

    # ------------------------------------
    # Keyword section
    # ------------------------------------

    keyword_count = (
        seo_result
        .get(
            "metrics",
            {},
        )
        .get(
            "keyword_count",
            0,
        )
    )

    if keyword_count == 0:
        rewritten_body += (
            "\n\n"
            "## まとめ\n\n"
            f"この記事では「{keyword}」について"
            "紹介しました。"
            "実際に利用・実践する際は、"
            "最新情報を確認しながら"
            "計画を立ててください。"
        )

    # ------------------------------------
    # Result
    # ------------------------------------

    return {
        "provider": "mock",

        "original_body": body,

        "rewritten_body": (
            rewritten_body
        ),

        "added_topics": (
            added_topics
        ),

        "original_length": len(
            body
        ),

        "rewritten_length": len(
            rewritten_body
        ),

        "seo_score_before": (
            seo_result["score"]
        ),
    }


# ========================================
# OpenAI SEO Rewriter
# ========================================

def _rewrite_with_openai(
    *,
    title: str,
    keyword: str,
    meta_description: str | None,
    body: str,
) -> dict[str, Any]:
    """
    OpenAI APIによるSEOリライト用。

    API利用開始後に実装する。

    将来的には、
    ・検索意図
    ・不足トピック
    ・記事構造
    ・自然なキーワード配置
    ・既存内容の保持
    を考慮した改善版本文を生成する。
    """

    raise NotImplementedError(
        "OpenAI SEO rewriter is not enabled yet."
    )