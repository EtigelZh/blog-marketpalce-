from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.database.models.category import Category


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self) -> list[Category]:
        result = await self.session.execute(select(Category).order_by(Category.id))
        return list(result.scalars().all())

    async def create(self, name: str) -> Category:
        category = Category(name=name)

        self.session.add(category)

        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise

        await self.session.refresh(category)

        return category

    async def get_by_id(self, category_id: int) -> Category | None:
        result = await self.session.execute(select(Category).where(Category.id == category_id))

        return result.scalar_one_or_none()
