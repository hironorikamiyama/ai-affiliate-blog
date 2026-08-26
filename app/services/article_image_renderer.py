import html
import re

from sqlalchemy.orm import Session

from app.models.article_image import ArticleImage


# ========================================
# Article Image Renderer
# ========================================

ARTICLE_IMAGE_PATTERN = re.compile(
    r"\{\{ARTICLE_IMAGE:(\d+)\}\}"
)


def expand_article_images(
    *,
    body: str,
    article_id: int,
    db: Session,
) -> str:
    """
    記事本文内の画像プレースホルダーを
    HTMLへ展開する。

    Example:

        {{ARTICLE_IMAGE:4}}

    ↓

        <figure class="article-content-image">
            ...
        </figure>

    指定された画像が対象記事に属していない場合は
    プレースホルダーをそのまま残す。
    """

    image_ids = {
        int(match)
        for match in ARTICLE_IMAGE_PATTERN.findall(
            body
        )
    }

    if not image_ids:
        return body

    images = (
        db.query(ArticleImage)
        .filter(
            ArticleImage.article_id == article_id,
            ArticleImage.id.in_(image_ids),
        )
        .all()
    )

    image_map = {
        image.id: image
        for image in images
    }

    def replace_image(
        match: re.Match,
    ) -> str:
        image_id = int(
            match.group(1)
        )

        image = image_map.get(
            image_id
        )

        if image is None:
            return match.group(0)

        image_url = html.escape(
            image.image_url,
            quote=True,
        )

        alt_text = html.escape(
            image.alt_text or "",
            quote=True,
        )

        caption = (
            html.escape(
                image.caption
            )
            if image.caption
            else None
        )

        figure_html = [
            '<figure class="article-content-image">',
            (
                f'<img src="{image_url}" '
                f'alt="{alt_text}">'
            ),
        ]

        if caption:
            figure_html.append(
                (
                    '<figcaption>'
                    f'{caption}'
                    '</figcaption>'
                )
            )

        figure_html.append(
            '</figure>'
        )

        return "\n".join(
            figure_html
        )

    return ARTICLE_IMAGE_PATTERN.sub(
        replace_image,
        body,
    )