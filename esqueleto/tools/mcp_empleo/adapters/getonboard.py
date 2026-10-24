"""Adaptador GetOnBoard — API JSON pública /api/v0/search/jobs (getonbrd.cl)."""
from __future__ import annotations

from datetime import datetime, timezone

from . import _comun

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json"}
BASE = "https://www.getonbrd.cl/api/v0/search/jobs"
MODALIDADES = {"remote_local": "remoto", "hybrid": "hibrido", "office": "presencial", "remote": "remoto"}


def _epoch_a_iso(epoch) -> str | None:
    try:
        return datetime.fromtimestamp(int(epoch), tz=timezone.utc).isoformat(timespec="seconds")
    except (TypeError, ValueError):
        return None


def buscar(texto: str, limite: int = 15, pais: str | None = "CO") -> list[dict]:
    import requests

    params: dict = {"query": texto, "per_page": min(limite * 2, 40)}
    if pais and len(pais) == 2:
        params["country_code"] = pais.upper()
    r = requests.get(BASE, params=params, headers=UA, timeout=30)
    r.raise_for_status()

    salidas: list[dict] = []
    for j in r.json().get("data", []):
        a = j.get("attributes") or {}
        url = (j.get("links") or {}).get("public_url") or f"https://www.getonbrd.cl/jobs/{j.get('id')}"
        paises = [str(c) for c in (a.get("countries") or []) if c]
        ubicacion = ", ".join(paises)
        sal_min, sal_max = a.get("min_salary"), a.get("max_salary")
        v = _comun.normalizar(
            portal="getonboard",
            url=url,
            titulo=a.get("title") or "",
            empresa="",  # el nombre de la empresa solo está en la página (SPA); se extrae en detalle
            ubicacion=ubicacion,
            salario_texto=f"USD {sal_min}-{sal_max}/mes" if sal_min and sal_max else "",
            publicada=_epoch_a_iso(a.get("published_at")),
            tags=[],
            descripcion_html=a.get("description") or "",
            modalidad=MODALIDADES.get(str(a.get("remote_modality") or "").lower()),
        )
        if v["modalidad"] == "desconocido" and a.get("remote") is True:
            v["modalidad"] = "remoto"
        if sal_min:
            v["salario"]["min"] = sal_min
        if sal_max:
            v["salario"]["max"] = sal_max
        if sal_min or sal_max:
            v["salario"]["moneda"] = "USD"
        # Con filtro de país, el API devuelve vacantes abiertas a ese país:
        # "Remote" sin ciudad => accesible desde el país consultado.
        if v["region_hint"] == "desconocida" and pais and len(pais) == 2:
            v["region_hint"] = f"accesible desde {pais.lower()}"
        v["idioma_publicacion"] = a.get("lang")
        salidas.append(v)
        if len(salidas) >= limite:
            break
    return salidas


def detalle(url: str) -> str:
    # La página es una SPA: la descripción completa ya viene en la respuesta
    # de búsqueda del API. Aquí solo descargamos y limpiamos el HTML crudo.
    import requests

    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=30)
    if r.status_code != 200:
        return ""
    return _comun.html_a_texto(r.text)
