# AI Affiliate Blog

AIを活用した記事生成・コンテンツ管理・アフィリエイト運用を行うためのWebアプリケーションです。

FastAPIを中心に、記事生成、記事管理、公開ブログ、アフィリエイト案件管理などを一つのシステムとして構築しています。

現在はMVP開発中です。

---

## Concept

単純にAIで記事を生成するだけではなく、

- 記事生成
- 人間による編集・レビュー
- SEO分析
- アフィリエイト案件管理
- 広告リンク管理
- コンテンツ公開
- 公開後の運用管理

までを一つのCMS上で扱える「AI Content Management Platform」を目指しています。

AIによる完全自動化ではなく、AIによる生成・分析と人間による確認・判断を組み合わせることを基本方針としています。

---

## Current Features

### Article Management

- 記事一覧表示
- 記事生成
- 記事編集
- Draft / Published管理
- 管理画面からの記事公開
- 公開記事を下書きへ戻す機能
- Slug管理
- Meta Description管理
- カテゴリ管理
- タグ管理

### AI Article Generation

記事生成処理はProviderを切り替えられる構成を採用しています。

現在はAPIコストなしで開発・テストを継続できるよう、Mock Providerを利用できます。

将来的にはOpenAI APIなどのLLM Providerを利用した記事生成に対応予定です。

### Public Blog

- 公開記事一覧
- Slugによる記事詳細表示
- MarkdownからHTMLへの変換
- Published記事のみ公開
- カテゴリ・タグ表示
- Meta Description出力

### Affiliate Program Management

管理画面からアフィリエイト案件を管理できます。

- Create
- Read
- Update
- Delete
- ASP名管理
- アフィリエイトURL管理
- 報酬情報管理
- Active / Inactive管理
- 記事から参照中の案件に対する削除防止

### Dynamic Affiliate Link Rendering

記事本文には直接URLを埋め込まず、以下のようなPlaceholderを保存できます。

    {{AFFILIATE_LINK:1}}

公開時にAffiliate Program IDを参照し、登録されているアフィリエイトURLへ動的に展開します。

これにより、リンク変更時に記事本文を直接修正せず、案件管理側からURLを管理できる構成としています。

---

## Architecture

    Admin UI
       |
       +-- Article Management
       |
       +-- Affiliate Program Management
       |
       +-- Article Generation
                |
                v
           AI Provider
          /           \
       Mock           LLM
                |
                v
             Article
                |
                v
       Affiliate Link Renderer
                |
                v
           Public Blog

---

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- Alembic
- SQLite
- Jinja2
- Markdown
- Docker
- Git / GitHub

---

# Roadmap

## SEO Analyzer

記事生成とは独立したSEO分析機能を実装予定です。

Pythonによる定量的なチェックと、LLMによる意味的な分析を組み合わせる構成を想定しています。

### Static Analysis

- タイトル文字数
- Meta Description
- 本文文字数
- 見出し構造
- キーワード出現状況
- アフィリエイトリンク数

### LLM Analysis

- 検索意図分析
- 検索意図との一致度
- 不足トピック検出
- タイトル改善案
- Meta Description改善案
- 見出し構成改善案
- コンテンツ品質評価

SEOスコアは検索順位を保証する指標ではなく、CMS内部の品質チェック指標として利用する予定です。

---

## PDF Content Import

PDFコンテンツをWebコンテンツへ変換する機能を検討しています。

    PDF
     |
     v
    Content Parser
     |
     v
    Article
     |
     +-- SEO Analyzer
     |
     +-- Affiliate Matcher
     |
     v
    Human Review
     |
     v
    Publish

想定機能:

- PDFアップロード
- PDFからテキスト抽出
- 見出し構造解析
- Web記事への変換
- SEO分析
- 関連アフィリエイト案件の推薦
- アフィリエイトリンク挿入候補の提示

自作または利用許諾を得たコンテンツを対象とすることを前提としています。

---

## Affiliate Recommendation

記事内容と登録済みアフィリエイト案件を分析し、関連性の高い案件を推薦する機能を検討しています。

    Article
       |
       v
    Content Analysis
       |
       v
    Affiliate Matcher
       |
       v
    Recommended Programs
       |
       v
    Human Approval

AIが自動的に広告を確定するのではなく、候補を提示して人間が採用する方式を想定しています。

---

## Affiliate Expiration Management

アフィリエイト案件の掲載期限・キャンペーン期限を管理する機能を検討しています。

想定項目:

- 掲載開始日時
- 掲載終了日時
- アラート開始日
- 案件ステータス

想定機能:

- 掲載期限前アラート
- 期限切れ案件の検出
- 期限切れ案件を使用している記事の検出
- 対象記事一覧表示
- 案件Inactive化候補の提示
- 公開記事上の期限切れリンク対策

将来的にはメールや外部通知サービスへの通知も検討しています。

---

## Content Optimization

公開済みコンテンツの継続的な改善を支援する機能を検討しています。

- 類似記事検出
- 内部リンク候補推薦
- 重複コンテンツ検出
- SEO再分析
- 記事更新候補提示

将来的にはSearch Console等の実データと組み合わせ、

    LLM Analysis
          +
    Search Performance
          |
          v
    Content Improvement

という改善サイクルを構築することを想定しています。

---

## Multi LLM Provider

特定のAI Providerへ強く依存しない構成を目指しています。

将来的な候補:

- OpenAI
- その他のLLM API
- Local LLM

記事生成・SEO分析などの機能ごとにProviderを切り替えられる構成を検討しています。

---

# Future Vision

最終的には、

    Content Input
         |
         v
    AI Generation
         |
         v
    SEO Analysis
         |
         +----------------+
         |                |
         v                v
    Affiliate        Internal Link
    Recommendation   Recommendation
         |                |
         +-------+--------+
                 |
                 v
            Human Review
                 |
                 v
              Publish
                 |
                 v
         Performance Data
                 |
                 v
          AI Re-Analysis
                 |
                 v
        Content Improvement

という循環型のコンテンツ管理基盤を目指します。

AIにすべてを任せるのではなく、

**AIが生成・分析・提案し、人間が判断して公開する**

ことを基本思想とします。

---

## Status

Under active development.
