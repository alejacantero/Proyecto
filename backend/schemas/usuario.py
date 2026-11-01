from typing import Literal
from pydantic import BaseModel, Field, EmailStr


class UsuarioCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UsuarioActualizar(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    rol: Literal["admin", "cliente"]