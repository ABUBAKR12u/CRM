import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from app.database.Base import MyDb
from app.model.users import Role, User
from app.utils.config import settings

ALGORITHM = "HS256"

password_hasher = PasswordHash.recommended()
DUMMY_HASH = password_hasher.hash("dummy-password-for-timing")

bearer = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed: str | None) -> bool:
    matches = password_hasher.verify(password, hashed or DUMMY_HASH)
    return matches and hashed is not None


def create_token(payload: dict, minutes: int) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=minutes)
    return jwt.encode({**payload, "exp": expire}, settings.SECRET_KEY.get_secret_value(), algorithm=ALGORITHM)


def decode_token(token: str, token_type: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY.get_secret_value(), algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    return payload if payload.get("type") == token_type else None


def create_access_token(user: User) -> str:
    return create_token({"sub": str(user.id), "type": "access"}, settings.ACCESS_TOKEN_MINUTES)


def password_fingerprint(user: User) -> str:
    return hashlib.sha256((user.password_hash or "").encode()).hexdigest()[:16]


def create_reset_token(user: User) -> str:
    payload = {"sub": str(user.id), "type": "reset", "pwd": password_fingerprint(user)}
    return create_token(payload, settings.RESET_TOKEN_MINUTES)


async def get_reset_user(db: MyDb, token: str) -> User | None:
    payload = decode_token(token, "reset")
    user = await db.get(User, int(payload["sub"])) if payload else None
    if not user or not user.active or not hmac.compare_digest(payload["pwd"], password_fingerprint(user)):
        return None
    return user


async def get_current_user(db: MyDb, token: Annotated[str, Depends(bearer)]) -> User:
    payload = decode_token(token, "access")
    user = await db.get(User, int(payload["sub"])) if payload else None
    if not user or not user.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "unauthorized", headers={"WWW-Authenticate": "Bearer"})
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: Role):
    async def checker(current_user: CurrentUser) -> User:
        if current_user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "forbidden")
        return current_user

    return checker
