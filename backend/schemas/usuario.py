
from pydantic import BaseModel, Field, EmailStr


class UsuarioCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    email: EmailStr

