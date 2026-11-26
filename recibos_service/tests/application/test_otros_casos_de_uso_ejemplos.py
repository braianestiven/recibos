"""Pruebas de ejemplo de UC-02, UC-03, `Plazo` y los errores de aplicación (US-01, US-13)."""

from __future__ import annotations

from datetime import datetime

import pytest

from app.application import errores
from app.application.autorizar_usuario import AutorizarUsuario
from app.application.consultar_lotes import ConsultarLotes
from app.application.presupuesto import Plazo, PlazoVencido
from app.domain.fechas import ZONA_BOGOTA
from app.domain.modelos import NuevoLote, Usuario
from tests.application import dobles


class TestConsultarLotes:
    def test_del_mas_reciente_al_mas_antiguo(self) -> None:
        repositorio = dobles.RepositorioEnMemoria()
        fecha = datetime(2027, 1, 4, 8, tzinfo=ZONA_BOGOTA)
        for nombre in ("a.xls", "b.xls", "c.xls"):
            repositorio.registrar_lote(NuevoLote("79", nombre, "lotes/x.xls", "10.0.0.1", fecha))
        pagina = ConsultarLotes(repositorio).ejecutar(limite=2, desplazamiento=0)
        assert [lote.nombre_original for lote in pagina.elementos] == ["c.xls", "b.xls"]
        assert (pagina.total, pagina.limite, pagina.desplazamiento) == (3, 2, 0)

    def test_sin_lotes(self) -> None:
        pagina = ConsultarLotes(dobles.RepositorioEnMemoria()).ejecutar(limite=20, desplazamiento=0)
        assert pagina.elementos == ()
        assert pagina.total == 0

    def test_mysql_no_responde(self) -> None:
        repositorio = dobles.RepositorioEnMemoria()
        repositorio.error_listado = True
        with pytest.raises(errores.DependenciaNoDisponible):
            ConsultarLotes(repositorio).ejecutar(limite=20, desplazamiento=0)


class TestAutorizarUsuario:
    def test_usuario_de_arc(self) -> None:
        AutorizarUsuario("ARC").ejecutar(Usuario("79", "sub", frozenset({"ARC", "Internal/everyone"})))

    @pytest.mark.parametrize(
        "usuario",
        [Usuario("79", "sub", frozenset({"OTRO"})), Usuario("  ", "sub", frozenset({"ARC"}))],
    )
    def test_sin_rol_o_sin_documento(self, usuario: Usuario) -> None:
        with pytest.raises(errores.AccesoDenegado):
            AutorizarUsuario(" ARC ").ejecutar(usuario)

    def test_rol_configurado_vacio(self) -> None:
        with pytest.raises(ValueError, match="rol"):
            AutorizarUsuario("  ")


class TestPlazo:
    def test_restante_y_vigente(self) -> None:
        reloj = dobles.RelojDePrueba(inicio=100.0)
        plazo = Plazo(130.0, reloj.segundos)
        assert plazo.restante() == 30.0
        assert plazo.vigente()
        assert plazo.para(5.0) == 5.0
        assert plazo.para(60.0) == 30.0
        plazo.exigir(29.0)
        with pytest.raises(PlazoVencido):
            plazo.exigir(30.0)

    def test_vencido(self) -> None:
        reloj = dobles.RelojDePrueba(inicio=200.0)
        plazo = Plazo(130.0, reloj.segundos)
        assert plazo.restante() == 0.0
        assert not plazo.vigente()
        with pytest.raises(PlazoVencido):
            plazo.para(5.0)

    def test_el_que_vence_primero(self) -> None:
        reloj = dobles.RelojDePrueba()
        corto, largo = Plazo(10.0, reloj.segundos), Plazo(20.0, reloj.segundos)
        assert corto.hasta(largo) is corto
        assert largo.hasta(corto) is corto


def test_errores_de_aplicacion_y_sus_codigos() -> None:
    assert errores.ArchivoNoPermitido(415, "m").status == 415
    formato = errores.FormatoPlantillaInvalido(3, "m", {"id_lote": 3})
    assert (formato.status, formato.id_lote, formato.auditoria) == (422, 3, {"id_lote": 3})
    assert errores.FormatoPlantillaInvalido(4, "m").auditoria == {}
    dependencia = errores.DependenciaNoDisponible("s3")
    assert (dependencia.status, dependencia.dependencia) == (503, "s3")
    assert dependencia.mensaje == errores.MENSAJE_DEPENDENCIA
    assert errores.RespuestaInvalida("m").status == 502
    assert errores.NoAutenticado().status == 401
    assert errores.AccesoDenegado().mensaje == "Prohibido"
    assert errores.ParametrosConsultaInvalidos("m").status == 400
    assert errores.ArchivoNoLegible("m").status == 422
    assert issubclass(errores.ErrorConexionBD, errores.ErrorPersistencia)
    assert issubclass(errores.BloqueoNoObtenido, errores.ErrorPersistencia)
