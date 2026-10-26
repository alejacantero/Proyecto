from pydantic import BaseModel, Field


class PedidoCrear(BaseModel):
    usuario_id: str = Field(min_length=1)
    producto_id: str = Field(min_length=1)
    cantidad: int = Field(gt=0)