from pydantic import EmailStr, Field, field_validator

from app.model.users import Role
from app.scheme.base import Schema


class UserAdd(Schema):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr = Field(max_length=254)
    role: Role
    dept: str = Field(min_length=2, max_length=60)
    manager_id: int | None = None

    @field_validator("email")
    @classmethod
    def lower_email(cls, value: str) -> str:
        return value.lower()


class UserUpdate(Schema):
    name: str = Field(None, min_length=2, max_length=80)
    role: Role = None
    dept: str = Field(None, min_length=2, max_length=60)
    manager_id: int | None = None
    active: bool = None


class UserShort(Schema):
    id: int
    name: str
    dept: str


class UserResponse(Schema):
    id: int
    name: str
    email: str
    role: Role
    dept: str
    manager_id: int | None
    active: bool


class TeamMemberResponse(UserResponse):
    open: int
    review: int
    done: int
