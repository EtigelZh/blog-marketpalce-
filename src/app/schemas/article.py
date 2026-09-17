from datetime import datetime

from pydantic import BaseModel


class ArticleCreate(BaseModel):
    title: str
    text: str
    image: str
    category_id: int


class ArticleUpdate(BaseModel):
    title: str | None = None
    text: str | None = None
    image: str | None = None
    category_id: int | None = None


class ArticleResponse(BaseModel):
    id: int
    title: str
    text: str
    image: str
    category_id: int
    author_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }
