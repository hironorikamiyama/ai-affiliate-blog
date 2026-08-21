from pydantic import BaseModel


class ArticleGenerateRequest(BaseModel):
    affiliate_program_id: int
    keyword: str


class ArticleResponse(BaseModel):
    id: int
    affiliate_program_id: int
    title: str
    keyword: str
    body: str
    status: str

    model_config = {
        "from_attributes": True
    }