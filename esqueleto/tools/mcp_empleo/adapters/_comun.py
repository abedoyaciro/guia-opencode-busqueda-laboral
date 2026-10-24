"""Utilidades compartidas de los adaptadores de empleo."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

ETIQUETAS_REGION = [
    (r"colombia", "colombia"),
    (r"latin\s*america|latam|south\s*america|am[ée]rica\s*latina|sudam[ée]rica", "latam"),
    (r"m[ée]xico|mexico", "mexico"),
    (r"spain|espa[ñn]a", "espana"),
    (r"worldwide|anywhere|global|cualquier\s*lugar|remoto", "mundial"),
]
ETIQUETAS_MODALIDAD = [
    (r"hybrid|h[íi]brido", "hibrido"),
    (r"remote|remoto", "remoto"),
    (r"onsite|presencial", "presencial"),
]


def _buscar_patron(texto: str, pares: list[tuple[str, str]]) -> str:
    if not texto:
        return "desconocida" if pares is ETIQUETAS_REGION else "desconocido"
    bajo = texto.lower()
    for patron, valor in pares:
        if re.search(patron, bajo):
            return valor
    return "desconocida" if pares is ETIQUETAS_REGION else "desconocido"


def _s(x) -> str:
    """Conversión segura a str (los portales mandan ints/dicts donde uno espera texto)."""
    if x is None:
        return ""
    return x if isinstance(x, str) else str(x)


def region_hint(texto: str) -> str:
    return _buscar_patron(_s(texto), ETIQUETAS_REGION)


def modalidad_de(texto: str) -> str:
    return _buscar_patron(_s(texto), ETIQUETAS_MODALIDAD)


def id_de(portal: str, url: str) -> str:
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return f"{portal}-{h}"


def html_a_texto(html: str) -> str:
    if not html:
        return ""
    texto = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    texto = re.sub(r"<br\s*/?>|</p>|</li>|</div>", "\n", texto, flags=re.I)
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"&nbsp;|&amp;|&lt;|&gt;|&#\d+;", " ", texto)
    texto = re.sub(r"[ \t]{2,}", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def resumen_de(texto: str, maximo: int = 400) -> str:
    texto = " ".join((texto or "").split())
    return texto[:maximo] + ("…" if len(texto) > maximo else "")


def fecha_iso(texto) -> str | None:
    if not texto:
        return None
    if isinstance(texto, (int, float)):
        try:
            return datetime.fromtimestamp(texto, tz=timezone.utc).isoformat(timespec="seconds")
        except (OverflowError, OSError, ValueError):
            return None
    t = _s(texto).strip()
    if re.match(r"\d{4}-\d{2}-\d{2}", t):
        return t[:10]
    # RFC 2822 (WWR): "Wed, 26 Aug 2026 10:00:00 +0000"
    if re.search(r"\d{1,2}\s+\w+\s+\d{4}", t):
        try:
            from email.utils import parsedate_to_datetime

            return parsedate_to_datetime(t).isoformat(timespec="seconds")
        except (TypeError, ValueError):
            pass
    # epoch en texto
    if re.fullmatch(r"\d{10}", t):
        try:
            return datetime.fromtimestamp(int(t), tz=timezone.utc).isoformat(timespec="seconds")
        except (OverflowError, OSError, ValueError):
            return None
    return t


def capturada() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalizar(
    portal: str,
    url: str,
    titulo: str,
    empresa: str = "",
    ubicacion: str = "",
    salario_texto: str = "",
    publicada: str | None = None,
    tags: list[str] | None = None,
    descripcion_html: str = "",
    modalidad: str | None = None,
) -> dict:
    texto_mod = _s(modalidad) or _s(ubicacion) or _s(url)
    texto_limpio = html_a_texto(_s(descripcion_html))
    return {
        "id": id_de(portal, _s(url)),
        "portal": portal,
        "titulo": _s(titulo).strip()[:200],
        "empresa": _s(empresa).strip()[:120],
        "url": _s(url),
        "ubicacion": _s(ubicacion).strip()[:160],
        "modalidad": modalidad_de(texto_mod),
        "region_hint": region_hint(ubicacion),
        "salario": {"texto": _s(salario_texto).strip()[:80], "min": None, "max": None, "moneda": None},
        "publicada": fecha_iso(publicada),
        "capturada": capturada(),
        "tags": tags or [],
        "resumen": resumen_de(texto_limpio),
        # La descripción completa llega en la respuesta de búsqueda de los 4
        # portales: se guarda ya para que `detalle` no dependa de la SPA.
        "descripcion_md": texto_limpio or None,
        "estado": "pendiente",
    }
