"""Reglas de dependencia entre capas (component-dependency.md §1; NFR-M01)."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent / "app"
STDLIB = set(sys.stdlib_module_names) | {"__future__"}

PERMITIDOS = {
    "domain": {"app.domain"},
    "application": {"app.domain", "app.application"},
    "interfaces": {"app.domain", "app.application", "app.interfaces", "flask", "flask_cors", "pydantic", "werkzeug"},
    "infrastructure": {
        "app.domain",
        "app.application",
        "app.infrastructure",
        "sqlalchemy",
        "oracledb",
        "pymysql",
        "boto3",
        "botocore",
        "requests",
        "urllib3",
        "xlrd",
        "pydantic",
    },
}


def _importaciones(archivo: Path) -> set[str]:
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    nombres: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            nombres.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
            nombres.add(nodo.module)
    return nombres


def _permitido(modulo: str, capa: str) -> bool:
    raiz = modulo.split(".", maxsplit=1)[0]
    if raiz in STDLIB:
        return True
    return any(modulo == p or modulo.startswith(p + ".") for p in PERMITIDOS[capa])


@pytest.mark.parametrize("capa", sorted(PERMITIDOS))
def test_cada_capa_solo_importa_lo_permitido(capa: str) -> None:
    archivos = sorted((RAIZ / capa).rglob("*.py"))
    assert archivos, f"la capa {capa} no tiene módulos"
    prohibidas = {
        f"{archivo.relative_to(RAIZ)}: {modulo}"
        for archivo in archivos
        for modulo in _importaciones(archivo)
        if not _permitido(modulo, capa)
    }
    assert not prohibidas, prohibidas
