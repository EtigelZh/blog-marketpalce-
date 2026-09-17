from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.database.models.article import Article


class ArticleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(
        self,
        page_number: int,
        page_size: int,
        category_id: int | None = None,
        search: str | None = None,
    ) -> list[Article]:
        offset = (page_number - 1) * page_size

        query = select(Article).where(
            Article.is_deleted.is_(False),
        )

        if category_id is not None:
            query = query.where(Article.category_id == category_id)

        if search:
            search_vector = func.to_tsvector(
                "russian",
                Article.title + " " + Article.text,
            )

            search_query = func.plainto_tsquery(
                "russian",
                search,
            )

            query = query.where(
                search_vector.op("@@")(search_query),
            )

        query = query.order_by(Article.id.desc()).offset(offset).limit(page_size)

        result = await self.session.execute(query)

        return list(result.scalars().all())

    async def get_by_id(self, article_id: int) -> Article | None:
        result = await self.session.execute(
            select(Article).where(
                Article.id == article_id,
                Article.is_deleted.is_(False),
            )
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        title: str,
        text: str,
        image: str,
        category_id: int,
        author_id: int,
    ) -> Article:
        article = Article(
            title=title,
            text=text,
            image=image,
            category_id=category_id,
            author_id=author_id,
        )

        self.session.add(article)

        await self.session.commit()
        await self.session.refresh(article)

        return article

    async def update(
        self,
        article: Article,
        title: str | None = None,
        text: str | None = None,
        image: str | None = None,
        category_id: int | None = None,
    ) -> Article:
        if title is not None:
            article.title = title

        if text is not None:
            article.text = text

        if image is not None:
            article.image = image

        if category_id is not None:
            article.category_id = category_id

        await self.session.commit()
        await self.session.refresh(article)

        return article

    async def delete(self, article: Article) -> None:
        article.is_deleted = True

        await self.session.commit()
