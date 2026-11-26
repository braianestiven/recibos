"""Respuesta de "parametros" y conversión del valor de cada regla (AD-20 a AD-22; business-rules.md §11).

El objeto `Parametro` no tiene un campo de valor: la configuración dice en qué campo está y con qué
formato se lee (AD-21, D6). La conversión tiene dos pasos: el formato convierte el texto del campo
(`convertir`) y la forma de la regla revisa que el resultado tenga el tipo que espera el dominio (`dar_forma`).
Cualquier valor que no sirva lanza `ValueError`, y quien llama lo convierte en un 502 que nombra la regla.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict

Campo = Literal["CodigoAbreviacion", "Nombre", "Descripcion", "NumeroOrden"]
Formato = Literal["entero", "texto", "lista", "lista_enteros", "json"]
Forma = Literal["entero", "texto", "conjunto_textos", "conjunto_enteros", "mapa_columnas", "porcentajes"]

_ENTERO = re.compile(r"[0-9]{1,18}")
_LARGO_MAXIMO_VALOR = 8192
_COLUMNA_MAXIMA = 256  # un libro de Excel 97-2003 tiene 256 columnas


class _Dto(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


class ReferenciaId(_Dto):
    Id: int


class ParametroDTO(_Dto):
    """`Data` de `GET /v1/parametro/{id}`. `FechaCreacion` y `FechaModificacion` no se usan."""

    Id: int
    Nombre: str = ""
    Descripcion: str = ""
    CodigoAbreviacion: str = ""
    Activo: bool
    NumeroOrden: int | float = 0
    TipoParametroId: ReferenciaId | None = None
    ParametroPadreId: ReferenciaId | None = None


class RespuestaParametros(_Dto):
    """Sobre CRUD: el servicio envía `Status` como texto ("200")."""

    Success: bool
    Status: str | int
    Data: ParametroDTO | None = None

    def exitosa(self) -> bool:
        texto = str(self.Status).strip()
        return self.Success and _ENTERO.fullmatch(texto) is not None and 200 <= int(texto) <= 299


@dataclass(frozen=True)
class EspecificacionParametro:
    """Dónde está el valor de una regla en "parametros", en un ambiente (AD-21)."""

    id: int
    campo: Campo
    formato: Formato


# Las 17 reglas, en el orden de business-rules.md §11, con el tipo que espera `ReglasLiquidacion`
FORMAS: Mapping[str, Forma] = {
    "estados_permitidos": "conjunto_textos",
    "estados_terminacion": "conjunto_textos",
    "evento_periodo": "entero",
    "evento_terminacion": "entero",
    "proyectos_excluidos": "conjunto_enteros",
    "nivel_pregrado": "texto",
    "niveles_posgrado": "conjunto_textos",
    "concepto_matricula": "entero",
    "concepto_exclusivo_pregrado": "entero",
    "conceptos_columna_pregrado": "mapa_columnas",
    "conceptos_columna_posgrado": "mapa_columnas",
    "exenciones_columna_pregrado": "mapa_columnas",
    "exenciones_columna_posgrado": "mapa_columnas",
    "id_exencion_votacion": "entero",
    "id_exencion_secretaria": "entero",
    "porcentajes_por_defecto": "porcentajes",
    "dias_fecha_extraordinaria": "entero",
}

FORMATOS_POR_FORMA: Mapping[Forma, frozenset[Formato]] = {
    "entero": frozenset({"entero", "json"}),
    "texto": frozenset({"texto", "json"}),
    "conjunto_textos": frozenset({"lista", "json"}),
    "conjunto_enteros": frozenset({"lista_enteros", "json"}),
    "mapa_columnas": frozenset({"json"}),
    "porcentajes": frozenset({"json"}),
}


def problemas_de_configuracion(especificaciones: Mapping[str, EspecificacionParametro]) -> list[str]:
    """Reglas que faltan, que sobran o cuyo formato no sirve para su tipo. Vacía si la configuración sirve."""
    problemas = [f"falta {regla}" for regla in FORMAS if regla not in especificaciones]
    problemas += [f"sobra {regla}" for regla in especificaciones if regla not in FORMAS]
    for regla, espec in especificaciones.items():
        forma = FORMAS.get(regla)
        if forma is None:
            continue
        if espec.formato not in FORMATOS_POR_FORMA[forma]:
            problemas.append(f"formato de {regla}")
        if espec.campo == "NumeroOrden" and espec.formato != "entero":
            problemas.append(f"campo de {regla}")
    return problemas


def _entero(valor: object) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
        raise ValueError("no es un entero sin signo")
    return valor


def _texto(valor: object) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError("no es un texto")
    return valor.strip()


def _lista(valor: object) -> list[object]:
    if not isinstance(valor, list | tuple):
        raise ValueError("no es una lista")
    return list(valor)


def _diccionario(valor: object) -> dict[int, object]:
    if not isinstance(valor, dict) or not valor:
        raise ValueError("no es un objeto")
    resultado: dict[int, object] = {}
    for clave, contenido in valor.items():
        if not isinstance(clave, str) or _ENTERO.fullmatch(clave) is None or not 1 <= int(clave) <= _COLUMNA_MAXIMA:
            raise ValueError("clave inválida")
        resultado[int(clave)] = contenido
    return resultado


def convertir(crudo: str | int | float, formato: Formato) -> object:
    """Aplica el formato al valor del campo. `NumeroOrden` llega como número y solo sirve como entero."""
    if not isinstance(crudo, str):
        if formato != "entero" or isinstance(crudo, bool) or not float(crudo).is_integer():
            raise ValueError("número no entero")
        return _entero(int(crudo))
    texto = crudo.strip()
    if not texto or len(texto) > _LARGO_MAXIMO_VALOR:
        raise ValueError("valor vacío o demasiado largo")
    if formato == "entero":
        if _ENTERO.fullmatch(texto) is None:
            raise ValueError("no es un entero")
        return int(texto)
    if formato == "texto":
        return texto
    partes = [parte.strip() for parte in texto.split(",") if parte.strip()]
    if formato == "lista":
        return partes
    if formato == "lista_enteros":
        if not partes or any(_ENTERO.fullmatch(parte) is None for parte in partes):
            raise ValueError("lista de enteros inválida")
        return [int(parte) for parte in partes]
    return json.loads(texto)  # formato json; JSONDecodeError es un ValueError


def dar_forma(valor: object, forma: Forma) -> object:
    """Revisa y arma el tipo que espera `ReglasLiquidacion` para la regla."""
    if forma == "entero":
        return _entero(valor)
    if forma == "texto":
        return _texto(valor)
    if forma == "conjunto_textos":
        elementos = _lista(valor)
        if not elementos:
            raise ValueError("lista vacía")
        return frozenset(_texto(e) for e in elementos)
    if forma == "conjunto_enteros":
        return frozenset(_entero(e) for e in _lista(valor))
    if forma == "mapa_columnas":
        return {columna: _entero(contenido) for columna, contenido in _diccionario(valor).items()}
    # porcentajes por defecto: número de cuotas → porcentaje de cada cuota
    return {cuotas: tuple(_entero(p) for p in _lista(lista)) for cuotas, lista in _diccionario(valor).items()}
