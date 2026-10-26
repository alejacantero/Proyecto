
from pydantic import BaseModel, Field


class ProductoCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    descripcion: str = Field(min_length=1, max_length=500)
    precio: float = Field(gt=0)
    stock: int = Field(ge=0)
    categoria: str = Field(min_length=2, max_length=50)
