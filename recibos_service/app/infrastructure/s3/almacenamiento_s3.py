"""Archivo del lote en el bucket privado de S3 (BR-L06, NFR-S02).

El cliente tiene 2 s para conectar, 5 s de respuesta y un reintento (modo `standard` con 2 intentos):
repetir la escritura deja el mismo archivo, porque el nombre es nuevo en cada lote (NFR-R03 ajustado).
"""

from __future__ import annotations

from typing import Any

from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.application.errores import DependenciaNoDisponible

CONFIGURACION_CLIENTE = Config(connect_timeout=2, read_timeout=5, retries={"mode": "standard", "max_attempts": 2})
TIPO_XLS = "application/vnd.ms-excel"


class AlmacenamientoS3:
    def __init__(self, cliente: Any, bucket: str) -> None:
        self._cliente = cliente
        self._bucket = bucket

    def guardar(self, contenido: bytes, nombre_interno: str) -> None:
        try:
            self._cliente.put_object(
                Bucket=self._bucket,
                Key=nombre_interno,
                Body=contenido,
                ContentType=TIPO_XLS,
                ServerSideEncryption="AES256",
            )
        except (BotoCoreError, ClientError) as error:
            raise DependenciaNoDisponible("s3") from error
