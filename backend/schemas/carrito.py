from pydantic import BaseModel, Field


class ItemCarrito(BaseModel):
    producto_id: str = Field(min_length=1)
    cantidad: int = Field(gt=0, le=100)


class CantidadItem(BaseModel):
    cantidad: int = Field(gt=0, le=100)