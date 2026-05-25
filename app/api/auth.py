from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.schemas import UserRegister, UserLogin, Token, UserResponse
from app.services.auth_service import AuthService
from app.core.security import get_current_active_user
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    注册新用户

    - **username**: 用户名（3-128个字符）
    - **email**: 邮箱地址（可选）
    - **password**: 密码（至少6位）
    """
    return await AuthService.register(db, user_data)


@router.post("/login", response_model=Token, summary="用户登录")
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    用户登录，返回 JWT Token

    - **username**: 用户名
    - **password**: 密码

    成功后返回 access_token，后续请求需要在 Header 中携带：
    Authorization: Bearer <token>
    """
    result = await AuthService.login(db, login_data.username, login_data.password)
    return Token(access_token=result["access_token"], token_type=result["token_type"])


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_active_user)):
    """
    获取当前登录用户的信息

    需要在请求头中携带有效的 Token：
    Authorization: Bearer <token>
    """
    return current_user


@router.post("/logout", summary="用户登出")
async def logout(current_user: User = Depends(get_current_active_user)):
    """
    用户登出（客户端删除 Token 即可）

    由于使用 JWT，服务端无需额外操作，客户端删除 Token 即完成登出
    """
    return {"message": "登出成功"}
