from sqlalchemy.exc import IntegrityError

from src.app.database.models.category import Category
from src.app.repositories.category import CategoryRepository


class CategoryService:
    def __init__(self, repository: CategoryRepository) -> None:
        self.repository = repository

    async def get_all(self) -> list[Category]:
        return await self.repository.get_all()

    async def create(self, name: str) -> Category:
        try:
            return await self.repository.create(name)
        except IntegrityError as error:
            raise ValueError("Category already exists") from error

    async def get_by_id(self, category_id: int) -> Category | None:
        return await self.repository.get_by_id(category_id)
