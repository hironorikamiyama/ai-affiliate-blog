from openai import OpenAI

from app.config import settings
from app.models.affiliate import AffiliateProgram


client = OpenAI(
    api_key=settings.openai_api_key
)


def generate_article(
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
- Markdown形式
- 以下の構成を基本とする

# タイトル

## {program.name}とは

## 特徴

## どんな人に向いているか

## 選ぶ際の注意点

## まとめ

最後に必ず以下をそのまま入れてください。

{{{{AFFILIATE_LINK:{program.id}}}}}
"""

    response = client.responses.create(
        model=settings.llm_model,
        input=prompt,
    )

    body = response.output_text

    title = f"{program.name}を解説｜{keyword}"

    return {
        "title": title,
        "body": body,
    }