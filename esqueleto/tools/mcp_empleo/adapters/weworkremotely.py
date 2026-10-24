"""Adaptador WeWorkRemotely — RSS por categoría (devops-sysadmin + customer-support)."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from . import _comun

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
CATEGORIAS = ["remote-devops-sysadmin-jobs", "remote-customer-support-jobs"]


def _feed(categoria: str) -> ET.ElementTree:
    import requests

    r = requests.get(
        f"https://weworkremotely.com/categories/{categoria}.rss",
        headers=UA,
        timeout=30,
    )
    r.raise_for_status()
    return ET.fromstring(r.content)


def _items() -> list[dict]:
    items: list[dict] = []
    for cat in CATEGORIAS:
        try:
            raiz = _feed(cat)
        except Exception:
            continue
        for item in raiz.iter("item"):
            titulo = (item.findtext("title") or "").strip()
            if ":" in titulo:
                empresa, titulo_limpio = titulo.split(":", 1)
            else:
                empresa, titulo_limpio = "", titulo
            link = item.findtext("link") or ""
            # WWR emite 2 links por item (vacante + empresa): tomar el 1º
            links = [l for l in item.iter("link") if (l.text or "").strip()]
            link = (links[0].text or "").strip() if links else link
            desc = item.findtext("description") or ""
            items.append(
                {
                    "portal": "wwr",
                    "url": link,
                    "titulo": titulo_limpio.strip(),
                    "empresa": empresa.strip(),
                    "ubicacion": "",
                    "salario_texto": "",
                    "publicada": (item.findtext("pubDate") or "").strip(),
                    "tags": [],
                    "descripcion_html": desc,
                }
            )
    return items


def buscar(texto: str, limite: int = 15, pais: str | None = None) -> list[dict]:
    terminos = [t for t in texto.lower().split() if len(t) > 2]
    salidas: list[dict] = []
    for j in _items():
        blob = f"{j['titulo']} {j['empresa']} {j['descripcion_html']}".lower()
        if terminos and not any(t in blob for t in terminos):
            continue
        v = _comun.normalizar(portal="wwr", **{k: v for k, v in j.items() if k != "portal"}, modalidad="remoto")
        if not v["url"]:
            continue
        salidas.append(v)
        if len(salidas) >= limite:
            break
    return salidas


def detalle(url: str) -> str:
    for j in _items():
        if j["url"] == url:
            texto = _comun.html_a_texto(j["descripcion_html"])
            return re.sub(r"\n{3,}", "\n\n", texto)
    return ""
