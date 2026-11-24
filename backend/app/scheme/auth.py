import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.scheme.base import Schema
from app.scheme.users import UserResponse


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ForgotPassword(Schema):
    email: EmailStr = Field(max_length=254)
    locale: Literal["uz", "ru", "en"] = "uz"

    @field_validator("email")
    @classmethod
    def lower_email(cls, value: str) -> str:
        return value.lower()


class ForgotPasswordResponse(Schema):
    msg: str
    reset_token: str | None = None


class ResetPassword(Schema):
    model_config = ConfigDict(str_strip_whitespace=False)

    token: str = Field(min_length=10, max_length=2048)
    password: str = Field(min_length=8, max_length=128)
    confirm: str

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        if not all(re.search(pattern, value) for pattern in ("[a-z]", "[A-Z]", r"\d")):
            raise ValueError("passwordWeak")
        return value

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm:
            raise ValueError("passwordMismatch")
        return self
