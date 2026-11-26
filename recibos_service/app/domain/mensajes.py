"""Textos para ARC (business-rules.md §10). Nunca llevan detalles internos (BR-R03)."""

from __future__ import annotations

from app.domain.modelos import FallaFila, FilaPlantilla, MotivoRechazo, Rechazo, TipoPlantilla

LARGO_MAXIMO_CODIGO_REPORTE = 30

# Filas
CODIGO_INVALIDO = "Código de estudiante inválido: debe tener solo números, hasta 15."
FALTA_CODIGO = "Falta el código del estudiante."
ESTUDIANTE_NO_ENCONTRADO = "El código no está registrado en el sistema académico."
SIN_VALOR_MATRICULA = "Sin información de matrícula; solicitar por oficio."
CARRERA_INACTIVA = "El proyecto curricular del estudiante no está activo."
NO_TERMINACION_MATERIAS = "El estado del estudiante es diferente de terminación de materias."
SIN_PERIODO_VIGENTE = (
    "No hay periodo vigente para el proyecto curricular del estudiante. Repórtelo al área de sistemas."
)
CUOTAS_INVALIDAS = "El número de cuotas es obligatorio y debe estar entre 1 y 3."
UNIDAD_INVALIDA_CREDITOS = "Los créditos son obligatorios: un número entero mayor que 0."
UNIDAD_INVALIDA_SMLV = "Los SMLV son obligatorios: un número mayor que 0, con hasta dos decimales."
DESCUENTOS_PREGRADO = "Solo se puede marcar un descuento además de la votación."
DESCUENTOS_POSGRADO = (
    "Solo se puede marcar un descuento además de la votación y de la Secretaría de Educación."
)
TIEMPO_AGOTADO = "No se alcanzó a procesar en el tiempo del lote; vuelva a cargar esta fila."
ERROR_GUARDADO = "Error al guardar la solicitud. Vuelva a cargar a este estudiante."
AVISO_CANCELACION = " Además, no se pudieron cancelar sus solicitudes sin imprimir; vuelva a cargarlo."

# Lote
PLANTILLA_ILEGIBLE = (
    "No se pudo leer la plantilla. Guárdela otra vez como Excel 97-2003 y vuelva a cargarla."
)
PLANTILLA_NO_RECONOCIDA = "La plantilla no es una de las vigentes: revise el texto de la celda A1."
PLANTILLA_CON_REINGRESO = "La plantilla de pregrado no es la vigente: trae la columna Reingreso."
PLANTILLA_SIN_FILAS = "La plantilla no tiene estudiantes."

NOMBRE_TIPO = {
    TipoPlantilla.PREGRADO: "pregrado",
    TipoPlantilla.POSGRADO_CREDITOS: "posgrado por créditos",
    TipoPlantilla.POSGRADO_SMLV: "posgrado por SMLV",
}


def codigo_repetido(fila_anterior: int) -> str:
    return f"El código ya está en la fila {fila_anterior}; solo se procesa la primera vez que aparece."


def estado_no_permitido(estado: str) -> str:
    return f"El estado del estudiante ({estado}) no permite generar el recibo."


def nivel_no_corresponde(nivel: str, tipo: TipoPlantilla) -> str:
    plantilla = "posgrado" if tipo.es_posgrado else "pregrado"
    nivel_texto = nivel.strip() or "un nivel desconocido"
    return f"El proyecto curricular del estudiante es de {nivel_texto} y la plantilla es de {plantilla}."


def _prefijo_cuota(cuota: int | None) -> str:
    return f"Cuota {cuota}: " if cuota is not None else ""


def _con_mayuscula(texto: str) -> str:
    return texto[:1].upper() + texto[1:]


def fecha_faltante(cuota: int | None) -> str:
    return _con_mayuscula(f"{_prefijo_cuota(cuota)}falta la fecha de pago.")


def fecha_inexistente(cuota: int | None) -> str:
    return _con_mayuscula(f"{_prefijo_cuota(cuota)}la fecha de pago no existe o no tiene el año completo.")


def fecha_anterior_a_hoy(cuota: int | None) -> str:
    return _con_mayuscula(f"{_prefijo_cuota(cuota)}la fecha de pago es anterior al día de la carga.")


def fecha_fuera_de_orden(cuota: int) -> str:
    return f"Cuota {cuota}: vence el mismo día o antes que la cuota {cuota - 1}."


def porcentaje_invalido(cuota: int) -> str:
    return f"Cuota {cuota}: el porcentaje debe ser un número entero de 0 a 100."


def porcentajes_no_suman_100(suma: int) -> str:
    return f"Los porcentajes de las cuotas deben sumar 100; suman {suma}."


def columnas_distintas(tipo: TipoPlantilla, detalle: str) -> str:
    return f"La plantilla de {NOMBRE_TIPO[tipo]} no tiene las columnas esperadas: {detalle}."


def demasiadas_filas(filas: int, maximo: int) -> str:
    return f"El lote tiene {filas} filas con datos y el máximo es {maximo}. Divida el archivo."


def regla_invalida(regla: str) -> str:
    return f"No se pudo leer la regla {regla} del servicio de parámetros. Repórtelo al área de sistemas."


def exencion_sin_porcentaje(id_exencion: int) -> str:
    return (
        f"La exención {id_exencion} no tiene porcentaje en el catálogo de exenciones. "
        "Repórtelo al área de sistemas."
    )


def anio_sin_festivos(anio: int) -> str:
    return f"No hay festivos registrados para el año {anio}. Repórtelo al área de sistemas."


def codigo_para_reporte(fila: FilaPlantilla) -> str | None:
    """Texto de la celda del código, sin espacios alrededor y recortado a 30 caracteres (DF-08)."""
    texto = fila.texto(1)
    if texto is None:
        return None
    return texto.strip()[:LARGO_MAXIMO_CODIGO_REPORTE]


def rechazo(fila: FilaPlantilla, falla: FallaFila) -> Rechazo:
    return Rechazo(fila=fila.numero, codigo=codigo_para_reporte(fila), motivo=falla.motivo, mensaje=falla.mensaje)


def rechazo_simple(fila: FilaPlantilla, motivo: MotivoRechazo, mensaje: str) -> Rechazo:
    return rechazo(fila, FallaFila(motivo, mensaje))


def con_aviso_de_cancelacion(rechazo_fila: Rechazo) -> Rechazo:
    """Agrega el aviso de BR-T02 cuando no se pudieron cancelar las solicitudes de una fila rechazada."""
    return Rechazo(
        fila=rechazo_fila.fila,
        codigo=rechazo_fila.codigo,
        motivo=rechazo_fila.motivo,
        mensaje=rechazo_fila.mensaje + AVISO_CANCELACION,
    )
