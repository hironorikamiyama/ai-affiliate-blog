import logging
import re
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
# Helpers
# ========================================

def _get_markdown_headings(
    body: str,
) -> list[str]:
    """
    MarkdownのH2見出しを取得する。

    ## 見出し
    の形式を対象とする。
    """

    headings = re.findall(
        r"^##\s+(.+?)\s*$",
        body,
        flags=re.MULTILINE,
    )

    return [
        heading.strip()
        for heading in headings
    ]


def _has_similar_heading(
    *,
    headings: list[str],
    candidates: list[str],
) -> bool:
    """
    既存見出しに候補文字列が含まれているか確認する。
    """

    normalized_headings = [
        heading.lower()
        for heading in headings
    ]

    for heading in normalized_headings:
        for candidate in candidates:
            if candidate.lower() in heading:
                return True

    return False


def _split_affiliate_links(
    body: str,
) -> tuple[str, list[str]]:
    """
    本文内のアフィリエイトプレースホルダーを一旦分離する。

    SEO追加セクションをリンクより後ろへ
    無制限に追加しないために使用する。
    """

    pattern = r"\{\{AFFILIATE_LINK:\d+\}\}"

    links = re.findall(
        pattern,
        body,
    )

    body_without_links = re.sub(
        pattern,
        "",
        body,
    )

    return (
        body_without_links.rstrip(),
        links,
    )


def _append_section(
    *,
    body: str,
    section: str,
) -> str:
    """
    本文末尾へMarkdownセクションを追加する。
    """

    return (
        body.rstrip()
        + "\n\n"
        + section.strip()
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
    APIを使わずにSEO改善版本文を生成する。

    方針:
    - 元本文を大きく書き換えない
    - 不足トピックのみ追加
    - 既存見出しとの重複を避ける
    - 「まとめ」を重複生成しない
    - アフィリエイトリンクを維持する
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

    # ------------------------------------
    # No rewrite required
    # ------------------------------------

    if (
        not missing_topics
        and keyword_count > 0
    ):
        return {
            "provider": "mock",

            "original_body": body,

            "rewritten_body": body,

            "added_topics": [],

            "skipped_topics": [],

            "original_length": len(
                body
            ),

            "rewritten_length": len(
                body
            ),

            "seo_score_before": (
                seo_result["score"]
            ),

            "seo_score_after": (
                seo_result["score"]
            ),

            "score_difference": 0,

            "metrics_before": (
                seo_result.get(
                    "metrics",
                    {},
                )
            ),

            "metrics_after": (
                seo_result.get(
                    "metrics",
                    {},
                )
            ),
        }

    existing_headings = (
        _get_markdown_headings(
            body
        )
    )

    # ------------------------------------
    # Affiliate placeholders
    # ------------------------------------

    (
        working_body,
        affiliate_links,
    ) = _split_affiliate_links(
        body
    )

    added_topics: list[str] = []

    skipped_topics: list[str] = []

    # ------------------------------------
    # Topic definitions
    # ------------------------------------

    topic_definitions = {
        "アクセス": {
            "heading_candidates": [
                "アクセス",
                "行き方",
                "交通",
            ],
            "section": (
                "## アクセス情報\n\n"
                "公共交通を利用する場合は、"
                "最寄り駅やバス停から目的地までの"
                "移動経路を事前に確認しておきましょう。"
                "所要時間や徒歩区間も整理しておくと、"
                "当日の移動をスムーズに進めやすくなります。"
            ),
        },

        "費用": {
            "heading_candidates": [
                "費用",
                "料金",
                "交通費",
                "予算",
            ],
            "section": (
                "## 費用の目安\n\n"
                "移動に必要な交通費や、"
                "現地で発生する可能性のある費用を"
                "事前に確認しておくことが重要です。"
                "往復交通費だけでなく、"
                "飲食費やその他の必要経費も含めて"
                "予算を考えておくと安心です。"
            ),
        },

        "注意点": {
            "heading_candidates": [
                "注意",
                "注意点",
                "ルール",
            ],
            "section": (
                "## 利用時の注意点\n\n"
                "現地のルールや利用条件を確認し、"
                "周囲の利用者に配慮して行動しましょう。"
                "天候や交通状況なども"
                "事前に確認しておくことをおすすめします。"
            ),
        },

        "具体例・体験": {
            "heading_candidates": [
                "実際",
                "体験",
                "実釣",
                "利用例",
            ],
            "section": (
                "## 実際に利用する際のポイント\n\n"
                "実際に利用する場合は、"
                "移動経路や必要な準備を事前に整理し、"
                "余裕を持ったスケジュールを組むことが重要です。"
                "現地で確認できた情報や気付いた点を"
                "記録しておくと、"
                "次回以降の計画にも役立ちます。"
            ),
        },
    }

    # ------------------------------------
    # Add missing topic sections
    # ------------------------------------

    for topic in missing_topics:
        definition = (
            topic_definitions.get(
                topic
            )
        )

        if definition is None:
            continue

        heading_candidates = (
            definition[
                "heading_candidates"
            ]
        )

        if _has_similar_heading(
            headings=existing_headings,
            candidates=heading_candidates,
        ):
            skipped_topics.append(
                topic
            )
            continue

        working_body = _append_section(
            body=working_body,
            section=definition[
                "section"
            ],
        )

        added_topics.append(
            topic
        )

        new_heading = (
            _get_markdown_headings(
                definition[
                    "section"
                ]
            )
        )

        existing_headings.extend(
            new_heading
        )


    if keyword_count == 0:
        # 「まとめ」が既にある場合は
        # まとめ見出しを重複させない
        if _has_similar_heading(
            headings=existing_headings,
            candidates=[
                "まとめ",
                "総括",
            ],
        ):
            keyword_section = (
                f"「{keyword}」について検討する際は、"
                "記事内の情報を参考にしつつ、"
                "最新情報も確認してください。"
            )

            working_body = (
                working_body.rstrip()
                + "\n\n"
                + keyword_section
            )

        else:
            keyword_section = (
                "## まとめ\n\n"
                f"この記事では「{keyword}」について"
                "紹介しました。"
                "実際に利用・実践する際は、"
                "最新情報を確認しながら"
                "計画を立ててください。"
            )

            working_body = _append_section(
                body=working_body,
                section=keyword_section,
            )

    # ------------------------------------
    # Restore affiliate links
    # ------------------------------------

    rewritten_body = (
        working_body.rstrip()
    )

    if affiliate_links:
        rewritten_body += "\n\n"

        rewritten_body += "\n\n".join(
            affiliate_links
        )

    # ------------------------------------
    # Analyze after rewrite
    # ------------------------------------

    seo_result_after = analyze_seo(
        title=title,
        keyword=keyword,
        meta_description=meta_description,
        body=rewritten_body,
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

        "skipped_topics": (
            skipped_topics
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

        "seo_score_after": (
            seo_result_after["score"]
        ),

        "score_difference": (
            seo_result_after["score"]
            - seo_result["score"]
        ),

        "metrics_before": (
            seo_result.get(
                "metrics",
                {},
            )
        ),

        "metrics_after": (
            seo_result_after.get(
                "metrics",
                {},
            )
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

    将来的には以下を考慮する。

    - 検索意図
    - 不足トピック
    - 記事構造
    - 自然なキーワード配置
    - 既存内容の保持
    - 事実の捏造防止
    """

    raise NotImplementedError(
        "OpenAI SEO rewriter is not enabled yet."
    )
