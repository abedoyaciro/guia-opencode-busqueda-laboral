"""Adaptador Greenhouse — API pública boards-api.greenhouse.io (ATS de muchas
empresas: Canonical, etc.). Permite ingesta manual de vacantes que el usuario
encuentra fuera de los portales automáticos."""
from __future__ import annotations

import re

from . import _comun

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "application/json"}
API = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
BOARDS_CONOCIDOS = {"canonical": "Canonical (Ubuntu)"}


def _sacar_board_id(url: str) -> tuple[str, str] | None:
    m = re.search(r"greenhouse\.io/([a-z0-9_]+)/jobs/(\d+)", url.lower())
    return (m.group(1), m.group(2)) if m else None


def buscar(texto: str, limite: int = 15, pais: str | None = None,
           board: str = "canonical") -> list[dict]:
    import requests

    r = requests.get(API.format(board=board), params={"content": "true"},
                     headers=UA, timeout=30)
    r.raise_for_status()
    jobs = r.json().get("jobs", [])
    terminos = [t for t in texto.lower().split() if len(t) > 2]
    empresa = BOARDS_CONOCIDOS.get(board, board.capitalize())

    salidas: list[dict] = []
    for j in jobs:
        titulo = (j.get("title") or "").lower()
        blob = f"{titulo} {j.get('content','')}".lower()
        # relevancia: el título debe tocar al menos 1 término y el blob todos
        if terminos and not (any(t in titulo for t in terminos) and all(t in blob for t in terminos)):
            continue
        v = _comun.normalizar(
            portal=f"greenhouse-{board}",
            url=j.get("absolute_url") or "",
            titulo=j.get("title") or "",
            empresa=empresa,
            ubicacion=(j.get("location") or {}).get("name") or "",
            publicada=j.get("updated_at") or j.get("first_published"),
            tags=[],
            descripcion_html=j.get("content") or "",
            modalidad=None,
        )
        if not v["url"]:
            continue
        salidas.append(v)
        if len(salidas) >= limite:
            break
    return salidas


def detalle(url: str) -> str:
    import requests

    par = _sacar_board_id(url)
    if not par:
        return ""
    board, job_id = par
    r = requests.get(f"{API.format(board=board)}/{job_id}", headers=UA, timeout=30)
    if r.status_code != 200:
        return ""
    j = r.json()
    return _comun.html_a_texto(j.get("content") or "")
