"""Modelos pydantic de los parámetros y las respuestas de `/v1/lotes` (api-contract.md)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.modelos import Lote, Pagina, ResumenLote

TipoPlantillaDTO = Literal["PREGRADO", "POSGRADO_CREDITOS", "POSGRADO_SMLV"]


class _Modelo(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ConsultaLotes(_Modelo):
    """`limit` de 1 a 100 (por defecto 20) y `offset` de 0 o más (BR-H01). Solo enteros escritos con dígitos."""

    limit: Annotated[int, Field(ge=1, le=100)] = 20
    offset: Annotated[int, Field(ge=0, le=10_000_000)] = 0


class ProcesadoDTO(_Modelo):
    fila: int
    codigo: str


class RechazoDTO(_Modelo):
    fila: int
    codigo: str | None
    motivo: str
    mensaje: str


class ResumenLoteDTO(_Modelo):
    id_lote: int
    tipo_plantilla: TipoPlantillaDTO
    total_filas: int
    procesados: tuple[ProcesadoDTO, ...]
    rechazados: tuple[RechazoDTO, ...]

    @classmethod
    def desde(cls, resumen: ResumenLote) -> ResumenLoteDTO:
        return cls(
            id_lote=resumen.id_lote,
            tipo_plantilla=resumen.tipo.name,  # type: ignore[arg-type]
            total_filas=resumen.total_filas,
            procesados=tuple(ProcesadoDTO(fila=p.fila, codigo=str(p.codigo)) for p in resumen.procesados),
            rechazados=tuple(
                RechazoDTO(fila=r.fila, codigo=r.codigo, motivo=r.motivo.value, mensaje=r.mensaje)
                for r in resumen.rechazados
            ),
        )


class LoteDTO(_Modelo):
    id: int
    usuario: str
    fecha: str  # ISO 8601 con la zona de Bogotá
    nombre_archivo: str
    ip: str

    @classmethod
    def desde(cls, lote: Lote) -> LoteDTO:
        return cls(
            id=lote.id,
            usuario=lote.documento_usuario,
            fecha=lote.fecha.isoformat(timespec="seconds"),
            nombre_archivo=lote.nombre_original,
            ip=lote.ip,
        )


class MetadataPagina(_Modelo):
    total: int
    limit: int
    offset: int

    @classmethod
    def desde(cls, pagina: Pagina[Lote]) -> MetadataPagina:
        return cls(total=pagina.total, limit=pagina.limite, offset=pagina.desplazamiento)
