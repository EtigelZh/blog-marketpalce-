import asyncio
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from src.app.database.models.user import User
from src.app.dependencies import (
    get_article_service,
    get_category_service,
    get_current_user,
    get_qa_service,
    get_storage_service,
)
from src.app.routing.auth import router as auth_router
from src.app.schemas.article import ArticleResponse, ArticleUpdate
from src.app.schemas.category import CategoryCreate, CategoryResponse
from src.app.schemas.qa import ArticleSource, AskRequest, AskResponse
from src.app.services.article import ArticleService
from src.app.services.category import CategoryService
from src.app.services.qa import QaService
from src.app.services.storage import StorageService

router = APIRouter()

router.include_router(auth_router)


@router.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


@router.get(
    "/articles",
    response_model=list[ArticleResponse],
)
async def get_articles(
    service: Annotated[
        ArticleService,
        Depends(get_article_service),
    ],
    page_number: Annotated[
        int,
        Query(ge=1),
    ] = 1,
    page_size: Annotated[
        int,
        Query(ge=1, le=50),
    ] = 10,
    category_id: Annotated[
        int | None,
        Query(ge=1),
    ] = None,
    search: Annotated[
        str | None,
        Query(max_length=255),
    ] = None,
) -> list[ArticleResponse]:
    articles = await service.get_all(
        page_number=page_number,
        page_size=page_size,
        category_id=category_id,
        search=search,
    )

    return [
        ArticleResponse.model_validate(article)
        for article in articles
    ]


@router.post(
    "/articles",
    response_model=ArticleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_article(
    title: Annotated[
        str,
        Form(min_length=1, max_length=255),
    ],
    text: Annotated[
        str,
        Form(min_length=1),
    ],
    category_id: Annotated[
        int,
        Form(ge=1),
    ],
    image: Annotated[
        UploadFile,
        File(),
    ],
    service: Annotated[
        ArticleService,
        Depends(get_article_service),
    ],
    storage: Annotated[
        StorageService,
        Depends(get_storage_service),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> ArticleResponse:
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    content = await image.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image cannot be empty",
        )

    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Image size must not exceed 10 MB",
        )

    image_url = await asyncio.to_thread(
        storage.upload_image,
        content=content,
        filename=image.filename or "image",
        content_type=image.content_type,
    )

    try:
        new_article = await service.create(
            title=title,
            text=text,
            image=image_url,
            category_id=category_id,
            author_id=current_user.id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return ArticleResponse.model_validate(new_article)


@router.get(
    "/articles/{article_id}",
    response_model=ArticleResponse,
)
async def get_article(
    article_id: int,
    service: Annotated[
        ArticleService,
        Depends(get_article_service),
    ],
) -> ArticleResponse:
    article = await service.get_by_id(article_id)

    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    return ArticleResponse.model_validate(article)


@router.patch(
    "/articles/{article_id}",
    response_model=ArticleResponse,
)
async def update_article(
    article_id: int,
    article: ArticleUpdate,
    service: Annotated[
        ArticleService,
        Depends(get_article_service),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> ArticleResponse:
    try:
        updated_article = await service.update(
            article_id=article_id,
            user_id=current_user.id,
            title=article.title,
            text=article.text,
            image=article.image,
            category_id=article.category_id,
        )
    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    if updated_article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    return ArticleResponse.model_validate(updated_article)


@router.delete(
    "/articles/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_article(
    article_id: int,
    service: Annotated[
        ArticleService,
        Depends(get_article_service),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> None:
    try:
        deleted = await service.delete(
            article_id=article_id,
            user_id=current_user.id,
        )
    except PermissionError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        ) from error

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )


@router.get(
    "/categories",
    response_model=list[CategoryResponse],
)
async def get_categories(
    service: Annotated[
        CategoryService,
        Depends(get_category_service),
    ],
) -> list[CategoryResponse]:
    categories = await service.get_all()

    return [
        CategoryResponse.model_validate(category)
        for category in categories
    ]


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    category: CategoryCreate,
    service: Annotated[
        CategoryService,
        Depends(get_category_service),
    ],
) -> CategoryResponse:
    try:
        new_category = await service.create(category.name)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return CategoryResponse.model_validate(new_category)


@router.post(
    "/qa/ask",
    response_model=AskResponse,
)
async def ask_question(
    request: AskRequest,
    service: Annotated[
        QaService,
        Depends(get_qa_service),
    ],
) -> AskResponse:
    answer, sources = await service.ask(request.question)

    return AskResponse(
        answer=answer,
        sources=[
            ArticleSource(id=article.id, title=article.title)
            for article in sources
        ],
    )
