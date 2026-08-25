import json
import re
import unicodedata
from uuid import uuid4

from openai import OpenAI

from app.config import settings
from app.models.affiliate import AffiliateProgram


def get_client() -> OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured"
        )

    return OpenAI(
        api_key=settings.openai_api_key
    )


def generate_slug(
    title: str,
    keyword: str,
) -> str:
    source = f"{title}-{keyword}"

    source = unicodedata.normalize(
        "NFKC",
        source,
    ).lower()

    # 英数字部分だけをslug候補として取得
    ascii_part = re.sub(
        r"[^a-z0-9]+",
        "-",
        source,
    )

    ascii_part = ascii_part.strip("-")

    # 日本語中心で英数字がほぼ無い場合
    if len(ascii_part) < 3:
        ascii_part = "article"

    # 長すぎるslugを防止
    ascii_part = ascii_part[:100].rstrip("-")

    # 衝突防止用のランダムID
    suffix = uuid4().hex[:8]

    return f"{ascii_part}-{suffix}"

def generate_mock_article(
    program: AffiliateProgram,
    keyword: str,
) -> dict:
    title = f"{program.name}を解説｜{keyword}"

    meta_description = (
        f"{program.name}について、"
        f"{keyword}をテーマに紹介する記事です。"
    )

    body = f"""# {title}

これはMock AIによって生成された開発用の記事です。

## {program.name}とは

{program.name}について紹介します。

ASP: {program.asp_name}

カテゴリ: {program.category}

## 特徴

キーワード「{keyword}」をもとに、
記事生成フローを確認するためのテスト本文です。

## どんな人に向いているか

{program.name}について情報を調べている人を想定しています。

## 選ぶ際の注意点

実際に公開する際は、
商品情報やサービス内容を確認して本文を編集してください。

## まとめ

この記事はMock AIによって生成されています。

{{{{AFFILIATE_LINK:{program.id}}}}}
"""

    slug = generate_slug(
        title=title,
        keyword=keyword,
    )

    return {
        "title": title,
        "slug": slug,
        "meta_description": meta_description,
        "body": body,
    }


def generate_openai_article(
    program: AffiliateProgram,
    keyword: str,
) -> dict:
    prompt = f"""
あなたは日本語のWeb記事編集者です。

以下の情報だけを事実情報として使用して、
アフィリエイト記事の下書きを作成してください。

商品名:
{program.name}

ASP:
{program.asp_name}

カテゴリ:
{program.category}

キーワード:
{keyword}

条件:
- 入力されていない料金・性能・実績などを推測しない
- 誇大表現を避ける
- 日本語で書く
- Markdown形式で本文を書く
- titleは300文字以内
- meta_descriptionは500文字以内
- 本文には以下の構成を含める

## {program.name}とは
## 特徴
## どんな人に向いているか
## 選ぶ際の注意点
## まとめ

本文の最後に必ず以下をそのまま入れてください。

{{{{AFFILIATE_LINK:{program.id}}}}}

必ず次のJSON形式だけで返してください。

{{
  "title": "記事タイトル",
  "meta_description": "記事概要",
  "body": "Markdown本文"
}}
"""

    client = get_client()

    response = client.responses.create(
        model=settings.llm_model,
        input=prompt,
    )

    raw_text = response.output_text.strip()

    try:
        generated = json.loads(raw_text)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "AI response is not valid JSON"
        ) from exc

    title = generated.get("title")
    meta_description = generated.get(
        "meta_description"
    )
    body = generated.get("body")

    if not title:
        raise ValueError(
            "AI response does not contain title"
        )

    if not body:
        raise ValueError(
            "AI response does not contain body"
        )

    slug = generate_slug(
        title=title,
        keyword=keyword,
    )

    return {
        "title": title,
        "slug": slug,
        "meta_description": meta_description,
        "body": body,
    }


def generate_article(
    program: AffiliateProgram,
    keyword: str,
) -> dict:
    if settings.use_mock_ai:
        return generate_mock_article(
            program=program,
            keyword=keyword,
        )

    return generate_openai_article(
        program=program,
        keyword=keyword,
    )
