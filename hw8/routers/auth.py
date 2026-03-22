from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from services.auth import AuthService
from dependencies import get_auth_service

router = APIRouter()


class LoginInDto(BaseModel):
    login: str
    password: str


@router.post("/login")
async def login(
    dto: LoginInDto,
    auth_service: AuthService = Depends(get_auth_service),
):
    account = await auth_service.authenticate_user(dto.login, dto.password)
    if not account:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = auth_service.create_access_token(account.id)
    response = JSONResponse(content={"message": "Login successful"})
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=1800, samesite="lax")
    return response