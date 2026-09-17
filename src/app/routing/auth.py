from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from src.app.dependencies import get_auth_service
from src.app.schemas.user import LoginRequest, UserCreate, UserResponse
from src.app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user: UserCreate,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    try:
        new_user = await service.register(
            email=user.email,
            password=user.password,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error

    return UserResponse.model_validate(new_user)


@router.post("/login")
async def login(
    user: LoginRequest,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict[str, str]:
    try:
        authenticated_user = await service.authenticate(
            email=user.email,
            password=user.password,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error

    token = service.create_access_token(authenticated_user.id)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
    )

    return {"message": "Login successful"}
