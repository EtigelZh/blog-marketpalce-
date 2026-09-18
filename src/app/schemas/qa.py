from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class ArticleSource(BaseModel):
    id: int
    title: str


class AskResponse(BaseModel):
    answer: str
    sources: list[ArticleSource]
