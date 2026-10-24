"""Registro de adaptadores de empleo."""
from __future__ import annotations

from . import getonboard, greenhouse, linkedin, remoteok, remotive, weworkremotely

REGISTRO = {
    "getonboard": getonboard,
    "remotive": remotive,
    "remoteok": remoteok,
    "wwr": weworkremotely,
    "linkedin": linkedin,
    "greenhouse": greenhouse,
}
