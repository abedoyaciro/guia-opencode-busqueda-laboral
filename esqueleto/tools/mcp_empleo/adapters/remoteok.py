"""Adaptador RemoteOK — JSON público remoteok.com/api (filtro de keywords client-side)."""
from __future__ import annotations

from . import _comun

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}
BASE = "https://remoteok.com/api"


def _cargar() -> list[dict]:
    import requests

    r = requests.get(BASE, headers=UA, timeout=30)
    r.raise_for_status()
    data = r.json()
    return [x for x in data if isinstance(x, dict) and x.get("position")]


def buscar(texto: str, limite: int = 15, pais: str | None = None) -> list[dict]:
    jobs = _cargar()
    terminos = [t for t in texto.lower().split() if len(t) > 2]

    salidas: list[dict] = []
    for j in jobs:
        blob = f"{j.get('position','')} {j.get('description','')}".lower()
        if terminos and not all(t in blob for t in terminos):
            continue
        v = _comun.normalizar(
            portal="remoteok",
            url=f"https://remoteok.com/remote-jobs/{j.get('slug','')}",
            titulo=j.get("position") or "",
            empresa=j.get("company") or "",
            ubicacion=j.get("location") or "remoto",
            salario_texto="",
            publicada=j.get("date"),
            tags=j.get("tags") or [],
            descripcion_html=j.get("description") or "",
            modalidad="remoto",
        )
        if j.get("salary_min"):
            v["salario"]["min"] = j["salary_min"]
        if j.get("salary_max"):
            v["salario"]["max"] = j["salary_max"]
        if j.get("salary_min") and j.get("salary_max"):
            v["salario"]["texto"] = f"USD {j['salary_min']}-{j['salary_max']} (estimado RemoteOK)"
            v["salario"]["moneda"] = "USD"
        salidas.append(v)
        if len(salidas) >= limite:
            break
    return salidas


def detalle(url: str) -> str:
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    for j in _cargar():
        if j.get("slug") == slug:
            return _comun.html_a_texto(j.get("description") or "")
    return ""
