"""Adaptador Remotive — API JSON pública remotive.com/api/remote-jobs."""
from __future__ import annotations

from . import _comun

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json"}
BASE = "https://remotive.com/api/remote-jobs"


def buscar(texto: str, limite: int = 15, pais: str | None = None) -> list[dict]:
    import requests

    r = requests.get(
        BASE,
        params={"search": texto, "limit": min(limite * 3, 60)},
        headers=UA,
        timeout=30,
    )
    r.raise_for_status()
    jobs = r.json().get("jobs", [])
    terminos = [t for t in texto.lower().split() if len(t) > 2] or []

    salidas: list[dict] = []
    for j in jobs:
        titulo_desc = f"{j.get('title','')} {j.get('candidate_required_location','')}"
        if terminos and not any(t in titulo_desc.lower() for t in terminos):
            continue
        v = _comun.normalizar(
            portal="remotive",
            url=j.get("url") or "",
            titulo=j.get("title") or "",
            empresa=j.get("company_name") or "",
            ubicacion=j.get("candidate_required_location") or "",
            salario_texto=j.get("salary") or "",
            publicada=j.get("publication_date"),
            tags=j.get("tags") or [],
            descripcion_html=j.get("description") or "",
            modalidad="remoto",
        )
        if not v["url"]:
            continue
        salidas.append(v)
        if len(salidas) >= limite:
            break
    return salidas


def detalle(url: str) -> str:
    import requests

    r = requests.get(BASE, params={"limit": 100}, headers=UA, timeout=30)
    r.raise_for_status()
    for j in r.json().get("jobs", []):
        if j.get("url") == url:
            return _comun.html_a_texto(j.get("description") or "")
    return ""
