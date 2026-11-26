"""Propiedades de la capa HTTP: ida y vuelta de los esquemas (PBT-02), límites del historial e IP (AD-29)."""

from __future__ import annotations

import json
from datetime import datetime

from hypothesis import given
from hypothesis import strategies as st

from app.domain.fechas import ZONA_BOGOTA
from app.domain.modelos import Lote, MotivoRechazo, Procesado, Rechazo, ResumenLote, TipoPlantilla
from app.interfaces.schemas.lotes import LoteDTO, ResumenLoteDTO
from tests.interfaces import dobles
from tests.interfaces.dobles import archivo, autorizacion, cliente, servicios

REMOTA = "10.9.9.9"


@st.composite
def resumenes(draw: st.DrawFn) -> ResumenLote:
    filas = draw(st.lists(st.integers(1, 65_535), unique=True, max_size=30))
    procesados: list[Procesado] = []
    rechazados: list[Rechazo] = []
    for fila in filas:
        if draw(st.booleans()):
            procesados.append(Procesado(fila, draw(st.integers(0, 10**15 - 1))))
        else:
            codigo = draw(st.none() | st.text(max_size=30))
            mensaje = draw(st.text(min_size=1, max_size=200))
            rechazados.append(Rechazo(fila, codigo, draw(st.sampled_from(list(MotivoRechazo))), mensaje))
    tipo = draw(st.sampled_from(list(TipoPlantilla)))
    return ResumenLote(draw(st.integers(1, 2**31)), tipo, tuple(procesados), tuple(rechazados))


@given(resumenes())
def test_ida_y_vuelta_del_resumen(resumen: ResumenLote) -> None:
    dto = ResumenLoteDTO.desde(resumen)
    texto = json.dumps(dto.model_dump(mode="json"), ensure_ascii=False)
    assert ResumenLoteDTO.model_validate_json(texto) == dto
    assert TipoPlantilla[dto.tipo_plantilla] is resumen.tipo
    assert [(p.fila, int(p.codigo)) for p in dto.procesados] == [(p.fila, p.codigo) for p in resumen.procesados]
    assert [(r.fila, r.codigo, MotivoRechazo(r.motivo), r.mensaje) for r in dto.rechazados] == [
        (r.fila, r.codigo, r.motivo, r.mensaje) for r in resumen.rechazados
    ]
    assert dto.total_filas == len(dto.procesados) + len(dto.rechazados)


@given(
    st.integers(1, 2**31),
    st.text(min_size=1, max_size=20),
    st.text(min_size=1, max_size=255),
    st.ip_addresses().map(str),
    st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2100, 1, 1), timezones=st.just(ZONA_BOGOTA)),
)
def test_ida_y_vuelta_del_lote(id_lote: int, usuario: str, nombre: str, ip: str, momento: datetime) -> None:
    lote = Lote(id_lote, usuario, nombre, ip, momento.replace(microsecond=0))
    dto = LoteDTO.desde(lote)
    assert LoteDTO.model_validate_json(dto.model_dump_json()) == dto
    assert datetime.fromisoformat(dto.fecha) == lote.fecha
    assert (dto.id, dto.usuario, dto.nombre_archivo, dto.ip) == (lote.id, lote.documento_usuario, nombre, ip)


@given(st.integers(-1000, 1000))
def test_limit_valido_solo_de_1_a_100(limite: int) -> None:
    respuesta = cliente().get(f"/v1/lotes?limit={limite}", headers=autorizacion())
    assert respuesta.status_code == (200 if 1 <= limite <= 100 else 400)


@given(st.integers(0, 3), st.lists(st.ip_addresses(v=4).map(str), max_size=5))
def test_ip_del_cliente_con_proxies_de_confianza(proxies: int, entradas: list[str]) -> None:
    procesar = dobles.ProcesarLoteDePrueba()
    cabeceras = autorizacion()
    if entradas:
        cabeceras["X-Forwarded-For"] = ", ".join(entradas)
    respuesta = cliente(servicios(procesar_lote=procesar, proxies_confianza=proxies)).post(
        "/v1/lotes",
        data=archivo(),
        headers=cabeceras,
        environ_base={"REMOTE_ADDR": REMOTA},
        content_type="multipart/form-data",
    )
    assert respuesta.status_code == 201
    # la entrada que agrega el último proxy de confianza; sin ella, la dirección de la conexión
    esperada = entradas[-proxies] if proxies and len(entradas) >= proxies else REMOTA
    assert procesar.comandos[0].ip == esperada
