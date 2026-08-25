import logging
import re

from sqlalchemy.orm import Session

from app.models.affiliate import AffiliateProgram


logger = logging.getLogger(__name__)


AFFILIATE_LINK_PATTERN = re.compile(
    r"\{\{AFFILIATE_LINK:(\d+)\}\}"
)


def expand_affiliate_links(
    body: str,
    db: Session,
) -> str:
    """
    {{AFFILIATE_LINK:1}}
    のようなプレースホルダーを
    AffiliateProgram.affiliate_url に置換する。
    """

    if not body:
        return body

    matches = AFFILIATE_LINK_PATTERN.findall(body)

    if not matches:
        return body

    program_ids = {
        int(program_id)
        for program_id in matches
    }

    programs = (
        db.query(AffiliateProgram)
        .filter(
            AffiliateProgram.id.in_(program_ids)
        )
        .all()
    )

    url_map = {
        program.id: program.affiliate_url
        for program in programs
    }

    def replace(match: re.Match) -> str:
        program_id = int(match.group(1))

        affiliate_url = url_map.get(program_id)

        if affiliate_url is None:
            logger.warning(
                "Affiliate program not found for placeholder: %s",
                program_id,
            )

            # 公開記事に壊れたプレースホルダーを
            # そのまま表示しない
            return ""

        return affiliate_url

    return AFFILIATE_LINK_PATTERN.sub(
        replace,
        body,
    )