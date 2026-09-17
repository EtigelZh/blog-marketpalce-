from src.app.database.models.article import Article
from src.app.repositories.article import ArticleRepository
from src.app.services.category import CategoryService


class ArticleService:
    def __init__(
        self,
        repository: ArticleRepository,
        category_service: CategoryService,
    ) -> None:
        self.repository = repository
        self.category_service = category_service

    async def get_all(
        self,
        page_number: int,
        page_size: int,
        category_id: int | None = None,
        search: str | None = None,
    ) -> list[Article]:
        return await self.repository.get_all(
            page_number=page_number,
            page_size=page_size,
            category_id=category_id,
            search=search,
        )

    async def get_by_id(
        self,
        article_id: int,
    ) -> Article | None:
        return await self.repository.get_by_id(article_id)

    async def create(
        self,
        title: str,
        text: str,
        image: str,
        category_id: int,
        author_id: int,
    ) -> Article:
        category = await self.category_service.get_by_id(category_id)

        if category is None:
            raise ValueError("Category not found")

        return await self.repository.create(
            title=title,
            text=text,
            image=image,
            category_id=category_id,
            author_id=author_id,
        )

    async def update(
        self,
        article_id: int,
        user_id: int,
        title: str | None = None,
        text: str | None = None,
        image: str | None = None,
        category_id: int | None = None,
    ) -> Article | None:
        article = await self.repository.get_by_id(article_id)

        if article is None:
            return None

        if article.author_id != user_id:
            raise PermissionError("You cannot update this article")

        if category_id is not None:
            category = await self.category_service.get_by_id(category_id)

            if category is None:
                raise ValueError("Category not found")

        return await self.repository.update(
            article=article,
            title=title,
            text=text,
            image=image,
            category_id=category_id,
        )

    async def delete(
        self,
        article_id: int,
        user_id: int,
    ) -> bool:
        article = await self.repository.get_by_id(article_id)

        if article is None:
            return False

        if article.author_id != user_id:
            raise PermissionError("You cannot delete this article")

        await self.repository.delete(article)

        return True