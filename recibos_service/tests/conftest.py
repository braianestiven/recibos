"""Configuración común de las pruebas.

Perfiles de Hypothesis (PBT-08): `dev` corre rápido en la máquina; `ci` hace más ejemplos y deja en el
registro el blob para repetir un caso que falla. La reducción de casos queda activa en los dos. El
perfil se elige con la variable `HYPOTHESIS_PROFILE`; Drone usa `ci` y fija `--hypothesis-seed`.
"""

from __future__ import annotations

import os

from hypothesis import HealthCheck, settings

settings.register_profile("dev", max_examples=60, deadline=None)
settings.register_profile(
    "ci",
    max_examples=300,
    deadline=None,
    print_blob=True,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "dev"))
