from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=64)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(UserBase):
    id: int


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
