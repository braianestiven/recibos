"""UC-02: historial paginado de lotes (BR-H01 a BR-H03)."""

from __future__ import annotations

from app.application.errores import DependenciaNoDisponible, ErrorPersistencia
from app.application.puertos import RepositorioSolicitudes
from app.domain.modelos import Lote, Pagina


class ConsultarLotes:
    def __init__(self, repositorio: RepositorioSolicitudes) -> None:
        self._repositorio = repositorio

    def ejecutar(self, limite: int, desplazamiento: int) -> Pagina[Lote]:
        """Del más reciente al más antiguo. Los límites de `limite` y `desplazamiento` los valida la API."""
        try:
            return self._repositorio.listar_lotes(limite, desplazamiento)
        except ErrorPersistencia:
            raise DependenciaNoDisponible("mysql") from None
