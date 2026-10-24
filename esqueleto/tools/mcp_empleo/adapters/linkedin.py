"""Adaptador LinkedIn Jobs — vista pública "guest" (SIN sesión, solo lecturas
esporádicas). Endpoints no oficiales: extremadamente defensivo (máx 2 requests
por búsqueda, delays aleatorios, abortar ante 429)."""
from __future__ import annotations

import random
import re
import time

from . import _comun

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
}
SEARCH = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
PAIS_UBICACION = {"CO": "Colombia", "MX": "México", "ES": "España", "CL": "Chile", "AR": "Argentina", "PE": "Perú"}
ULTIMO_429 = 0.0


def _get(url: str, params: dict | None = None) -> "requests.Response | None":
    import requests

    global ULTIMO_429
    # cooldown tras un 429: no reintentar durante 10 minutos
    if ULTIMO_429 and time.time() - ULTIMO_429 < 600:
        raise RuntimeError("LinkedIn en cooldown (429 reciente): reintenta en ~10 min")
    time.sleep(random.uniform(1.5, 3.5))
    r = requests.get(url, params=params, headers=UA, timeout=30)
    if r.status_code == 429:
        ULTIMO_429 = time.time()
        raise RuntimeError("LinkedIn devolvió 429 (límite de la vista guest)")
    r.raise_for_status()
    return r


def _extraer(html: str) -> list[dict]:
    crudos = re.findall(r"<li>(.*?)</li>", html, re.S)
    items: list[dict] = []
    for it in crudos:
        # título: <span class="sr-only"> dentro del link de la tarjeta; fallback h3
        titulo = (re.search(r'base-card__full-link.*?sr-only">\s*([^<]{3,150})<', it, re.S)
                  or re.search(r'base-search-card__title">\s*([^<]+)<', it))
        link = re.search(r'href="(https://[a-z-]*\.?linkedin\.com/jobs/view/[^"?]+)', it)
        empresa = re.search(r'base-search-card__subtitle">\s*([^<]+)<', it)
        loc = re.search(r'job-search-card__location">\s*([^<]+)<', it)
        fecha = re.search(r'datetime="([^"]+)"', it)
        if not (titulo and link):
            continue
        items.append({
            "url": link.group(1),
            "titulo": titulo.group(1).strip(),
            "empresa": (empresa.group(1).strip() if empresa else ""),
            "ubicacion": (loc.group(1).strip() if loc else ""),
            "publicada": (fecha.group(1)[:10] if fecha else None),
        })
    return items


def buscar(texto: str, limite: int = 15, pais: str | None = "CO") -> list[dict]:
    params: dict = {"keywords": texto, "start": 0}
    if pais and pais.upper() in PAIS_UBICACION:
        params["location"] = PAIS_UBICACION[pais.upper()]
    r = _get(SEARCH, params)
    items = _extraer(r.text)[: limite * 2]
    salidas: list[dict] = []
    for it in items:
        v = _comun.normalizar(
            portal="linkedin",
            url=it["url"],
            titulo=it["titulo"],
            empresa=it["empresa"],
            ubicacion=it["ubicacion"],
            publicada=it["publicada"],
            tags=[],
            descripcion_html="",
            modalidad="remoto" if "remot" in it["ubicacion"].lower() else None,
        )
        salidas.append(v)
        if len(salidas) >= limite:
            break
    return salidas


def detalle(url: str) -> str:
    r = _get(url)
    html = r.text
    m = re.search(r'show-more-less-html__markup[^>]*>(.*?)</div>', html, re.S)
    if not m:
        return ""
    return _comun.html_a_texto(m.group(1))
