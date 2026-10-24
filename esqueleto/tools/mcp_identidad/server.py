#!/usr/bin/env python3
"""
MCP identidad — credenciales profesionales del candidato.

Herramientas expuestas:
    credly_sincronizar()       → data/credenciales/credly.json
    skillsboost_sincronizar()  → data/credenciales/skillsboost.json
    identidad_consolidar()     → data/credenciales/consolidado.json

Config via variables de entorno (con valores por defecto públicos):
    CREDLY_USER, SKILLSBOOST_PROFILE_URL
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Resolver DNS robusto compartido (ver tools/common/resolver_dns.py)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
import resolver_dns  # noqa: E402

resolver_dns.activar()

from mcp.server.mcpserver import MCPServer  # noqa: E402

DATA = Path(os.environ.get("IDENTIDAD_DATA_DIR", "data/credenciales"))
# Configura estos dos valores en opencode.json (bloque mcp.identidad.environment)
# o como variables de entorno antes de arrancar el servidor.
CREDLY_USER = os.environ.get("CREDLY_USER", "").strip()
SKILLSBOOST_URL = os.environ.get("SKILLSBOOST_PROFILE_URL", "").strip()


def _exigir(valor: str, variable: str) -> str:
    if not valor:
        raise RuntimeError(
            f"Falta la variable de entorno {variable}. "
            "Defínela en opencode.json (mcp.identidad.environment) o en tu shell."
        )
    return valor

mcp = MCPServer("identidad")


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _guardar(nombre_archivo: str, payload: dict) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / nombre_archivo).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _credly_descargar() -> list[dict]:
    import requests

    usuario = _exigir(CREDLY_USER, "CREDLY_USER")
    insignias: list[dict] = []
    for page in range(1, 11):
        r = requests.get(
            f"https://www.credly.com/users/{usuario}/badges.json",
            params={"page": page, "page_size": 100},
            headers={"Accept": "application/json", "User-Agent": "Mozilla/5.0"},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json().get("data", [])
        if not data:
            break
        for b in data:
            bt = b.get("badge_template") or {}
            insignias.append(
                {
                    "fuente": "credly",
                    "nombre": bt.get("name"),
                    "emisor": ((bt.get("issuer") or {}).get("summary") or "").removeprefix("issued by "),
                    "emitida": (b.get("issued_at_date") or "")[:10],
                    "skills": [s.get("name") for s in (bt.get("skills") or []) if s.get("name")],
                    "url": b.get("url") or bt.get("url"),
                }
            )
    return insignias


@mcp.tool()
def credly_sincronizar() -> str:
    """Descarga todas las insignias públicas de Credly y las guarda en
    data/credenciales/credly.json."""
    insignias = _credly_descargar()
    _guardar(
        "credly.json",
        {"actualizado": _ahora(), "usuario": CREDLY_USER, "insignias": insignias},
    )
    return f"OK: {len(insignias)} insignias de Credly -> data/credenciales/credly.json"


@mcp.tool()
def skillsboost_sincronizar() -> str:
    """Scrapea el perfil público de Google Skills (skills.google) con Playwright
    y guarda las insignias en data/credenciales/skillsboost.json."""
    from playwright.sync_api import sync_playwright

    url_perfil = _exigir(SKILLSBOOST_URL, "SKILLSBOOST_PROFILE_URL")
    UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=UA)
        page.goto(url_perfil, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)
        crudos = page.eval_on_selector_all(
            ".profile-badge",
            "els => els.map(el => ({"
            "texto: el.innerText,"
            "url: (el.querySelector('a')||{}).href || '',"
            "imagen: (el.querySelector('img')||{}).src || ''}))",
        )
        browser.close()

    insignias: list[dict] = []
    for c in crudos:
        lineas = [l.strip() for l in c["texto"].splitlines() if l.strip()]
        if not lineas:
            continue
        nombre = lineas[0]
        emitida = next(
            (l.replace("Earned", "").strip() for l in lineas if l.lower().startswith("earned")),
            None,
        )
        insignias.append(
            {
                "fuente": "skillsboost",
                "nombre": nombre,
                "emisor": "Google Skills",
                "emitida": emitida,
                "skills": [],
                "url": c["url"],
                "imagen": c["imagen"],
            }
        )
    _guardar(
        "skillsboost.json",
        {"actualizado": _ahora(), "perfil": SKILLSBOOST_URL, "insignias": insignias},
    )
    return f"OK: {len(insignias)} insignias de Google Skills -> data/credenciales/skillsboost.json"


@mcp.tool()
def consolidar() -> str:
    """Fusiona credly.json y skillsboost.json en data/credenciales/consolidado.json,
    deduplicando credenciales por nombre."""
    credly = json.loads((DATA / "credly.json").read_text(encoding="utf-8"))
    sb = json.loads((DATA / "skillsboost.json").read_text(encoding="utf-8"))

    fusion: dict[str, dict] = {}
    for ins in credly.get("insignias", []) + sb.get("insignias", []):
        clave = "".join(ch for ch in (ins.get("nombre") or "").lower() if ch.isalnum())
        if not clave:
            continue
        if clave in fusion:
            f = fusion[clave]
            if ins["fuente"] not in f["fuentes"]:
                f["fuentes"].append(ins["fuente"])
            f["skills"] = sorted(set(f["skills"]) | set(ins.get("skills") or []))
            f["url"] = f["url"] or ins.get("url")
        else:
            fusion[clave] = {
                "nombre": ins["nombre"],
                "emisor": ins.get("emisor"),
                "emitida": ins.get("emitida"),
                "skills": sorted(set(ins.get("skills") or [])),
                "url": ins.get("url"),
                "fuentes": [ins["fuente"]],
            }

    consolidado = {
        "actualizado": _ahora(),
        "usuario": CREDLY_USER,
        "total": len(fusion),
        "credenciales": sorted(fusion.values(), key=lambda x: x["emitida"] or "", reverse=True),
    }
    _guardar("consolidado.json", consolidado)
    return f"OK: {consolidado['total']} credenciales consolidadas -> data/credenciales/consolidado.json"


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    mcp.run()
