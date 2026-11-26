"""`POST /v1/lotes` y `GET /v1/lotes` (api-contract.md; BR-L01 a BR-L03, BR-H01)."""

from __future__ import annotations

import re
import unicodedata

from flask import Response, current_app, g, request
from pydantic import ValidationError

from app.application.errores import ArchivoNoPermitido, ParametrosConsultaInvalidos
from app.application.procesar_lote import CargarLoteComando
from app.interfaces.middlewares.errores import mensaje_tamano
from app.interfaces.schemas.lotes import ConsultaLotes, LoteDTO, MetadataPagina, ResumenLoteDTO
from app.interfaces.schemas.respuesta import exito
from app.interfaces.servicios import CLAVE_EXTENSION, Servicios

FIRMA_OLE2 = bytes.fromhex("D0CF11E0A1B11AE1")
_NUMERO = re.compile(r"[0-9]{1,8}")
FALTA_ARCHIVO = "Falta el archivo de la plantilla."
NOMBRE_INVALIDO = "El nombre del archivo no es válido."
TIPO_NO_PERMITIDO = "Solo se aceptan plantillas .xls (Excel 97-2003)."
LIMIT_INVALIDO = "El parámetro limit debe ser un entero de 1 a 100."
OFFSET_INVALIDO = "El parámetro offset debe ser un entero de 0 o más."


def _servicios() -> Servicios:
    servicios: Servicios = current_app.extensions[CLAVE_EXTENSION]
    return servicios


def nombre_valido(nombre: str, largo_maximo: int) -> bool:
    """Sin rutas ni caracteres de control, y hasta la longitud de `nombreOriginal` (BR-L01)."""
    if not nombre or len(nombre) > largo_maximo or nombre.strip() in {".", ".."}:
        return False
    if "/" in nombre or "\\" in nombre:
        return False
    return not any(unicodedata.category(c).startswith("C") for c in nombre)


def crear_lote() -> Response:
    servicios = _servicios()
    archivo = request.files.get("archivo")
    if archivo is None or not archivo.filename:
        raise ArchivoNoPermitido(400, FALTA_ARCHIVO)
    nombre = archivo.filename
    if not nombre_valido(nombre, servicios.max_nombre_archivo):
        raise ArchivoNoPermitido(400, NOMBRE_INVALIDO)
    contenido = archivo.stream.read(servicios.max_archivo_bytes + 1)  # BR-L02
    if len(contenido) > servicios.max_archivo_bytes:
        raise ArchivoNoPermitido(413, mensaje_tamano(servicios.max_archivo_bytes))
    if not nombre.lower().endswith(".xls") or not contenido.startswith(FIRMA_OLE2):  # BR-L03
        raise ArchivoNoPermitido(415, TIPO_NO_PERMITIDO)
    comando = CargarLoteComando(
        contenido=contenido,
        nombre_original=nombre,
        usuario=g.usuario,
        ip=request.remote_addr or "",
        recibida_en=g.recibida_en,
    )
    resultado = servicios.procesar_lote.ejecutar(comando)
    g.datos_auditoria = resultado.auditoria
    return exito(201, ResumenLoteDTO.desde(resultado.resumen).model_dump(mode="json"))


def _entero(nombre: str, por_defecto: int, mensaje: str) -> int:
    texto = request.args.get(nombre)
    if texto is None:
        return por_defecto
    if _NUMERO.fullmatch(texto) is None:
        raise ParametrosConsultaInvalidos(mensaje)
    return int(texto)


def listar_lotes() -> Response:
    limite = _entero("limit", 20, LIMIT_INVALIDO)
    desplazamiento = _entero("offset", 0, OFFSET_INVALIDO)
    try:
        consulta = ConsultaLotes(limit=limite, offset=desplazamiento)
    except ValidationError as error:
        campo = str(error.errors()[0]["loc"][0])
        raise ParametrosConsultaInvalidos(LIMIT_INVALIDO if campo == "limit" else OFFSET_INVALIDO) from None
    pagina = _servicios().consultar_lotes.ejecutar(consulta.limit, consulta.offset)
    datos = [LoteDTO.desde(lote).model_dump(mode="json") for lote in pagina.elementos]
    return exito(200, datos, metadata=MetadataPagina.desde(pagina).model_dump(mode="json"))
