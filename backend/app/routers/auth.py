from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.database.Base import MyDb
from app.model.notifications import NotificationKey
from app.model.users import User
from app.scheme.auth import ForgotPassword, ForgotPasswordResponse, ResetPassword, TokenResponse
from app.scheme.users import UserResponse
from app.utils.config import Environment, settings
from app.utils.email import send_reset_email
from app.utils.notifications import admin_ids, notify
from app.utils.rate_limiting import (
    client_ip,
    ensure_not_limited,
    forgot_limiter,
    login_account_limiter,
    login_ip_limiter,
    reset_limiter,
)
from app.utils.security import (
    CurrentUser,
    create_access_token,
    create_reset_token,
    get_reset_user,
    hash_password,
    verify_password,
)

router = APIRouter(tags=["Auth"], prefix="/auth")


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, db: MyDb, form: OAuth2PasswordRequestForm = Depends()):
    email = form.username.strip().lower()
    ip_key = client_ip(request)
    await ensure_not_limited((login_ip_limiter, ip_key), (login_account_limiter, email))

    user = await db.scalar(select(User).where(User.email == email))
    if not await run_in_threadpool(verify_password, form.password, user.password_hash if user else None):
        await login_ip_limiter.hit(ip_key)
        await login_account_limiter.hit(email)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid")
    if not user.active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "blocked")

    await login_account_limiter.reset(email)
    return {"access_token": create_access_token(user), "user": user}


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser):
    return current_user


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(data: ForgotPassword, request: Request, db: MyDb, background: BackgroundTasks):
    ip_key = client_ip(request)
    await ensure_not_limited((forgot_limiter, ip_key))
    await forgot_limiter.hit(ip_key)

    user = await db.scalar(select(User).where(User.email == data.email, User.active))
    response = {"msg": "If the account exists, a reset link has been sent"}
    if not user:
        return response

    token = create_reset_token(user)
    if settings.SMTP_HOST:
        background.add_task(send_reset_email, user, token, data.locale)
    if settings.ENVIRONMENT is not Environment.PRODUCTION:
        response["reset_token"] = token
    return response


@router.post("/reset-password")
async def reset_password(data: ResetPassword, request: Request, db: MyDb):
    ip_key = client_ip(request)
    await ensure_not_limited((reset_limiter, ip_key))
    await reset_limiter.hit(ip_key)

    user = await get_reset_user(db, data.token)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalid_token")
    user.password_hash = await run_in_threadpool(hash_password, data.password)
    notify(db, user, await admin_ids(db), NotificationKey.PASSWORD_RESET, name=user.name)
    await db.commit()
    return {"msg": "Password updated successfully"}
