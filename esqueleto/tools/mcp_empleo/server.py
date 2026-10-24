#!/usr/bin/env python3
"""
MCP empleo — búsqueda de vacantes remotas en español para el perfil objetivo.

Herramientas expuestas:
    buscar(portal, texto, limite, pais) → lista normalizada + guarda en data/vacantes/pendientes/
    listar(estado)                      → vacantes en pendientes|aprobadas|descartadas
    detalle(vacante_id)                 → descripción completa (resuelve vía adaptador)
    marcar(vacante_id, estado)          → mueve la vacante entre estados (aprobada|descartada)

Portales soportados: getonboard (API, filtro país), remotive (API), remoteok (API),
wwr (RSS). Todos requieren Human Approval posterior en data/vacantes/aprobadas/.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Resolver DNS robusto compartido (ver tools/common/resolver_dns.py)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
import resolver_dns  # noqa: E402

resolver_dns.activar()

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adapters import REGISTRO  # noqa: E402

from mcp.server.mcpserver import MCPServer  # noqa: E402

# Ruta absoluta: independiente del CWD con el que opencode lance el proceso
_RAIZ = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("EMPLEO_DATA_DIR", str(_RAIZ / "data" / "vacantes")))
ESTADOS = {"pendientes", "aprobadas", "descartadas"}

# ── Filtro de seniority: señales de rol senior en título o descripción ──────
SENIOR_TITULO = re.compile(
    r"\b(senior|sr\.?|ssr|lead|l[íi]der|principal|staff|manager|gerente|jefe|"
    r"architect|arquitecto|head|director|expert|vp|chief|consultor|consultant|"
    r"coordinador|technical account manager)\b",
    re.IGNORECASE,
)
SENIOR_DESC = re.compile(
    r"\b(5\+|6\+|7\+|8\+|10\+)\s*(years|años|yrs)|"
    r"\b(5|7|10)\s*\+\s*(years|años)|"
    r"senior\b",
    re.IGNORECASE,
)

mcp = MCPServer("empleo")


def _es_senior(v: dict) -> bool:
    """True si la vacante tiene señales claras de rol senior."""
    if SENIOR_TITULO.search(v.get("titulo") or ""):
        return True
    blob = (v.get("descripcion_md") or "") + " " + (v.get("resumen") or "")
    return bool(SENIOR_DESC.search(blob))


def _ruta(vacante_id: str) -> Path | None:
    for estado in ESTADOS:
        p = DATA / estado / f"{vacante_id}.json"
        if p.exists():
            return p
    return None


def _guardar(v: dict) -> Path:
    carpeta = v["estado"] + "s" if not v["estado"].endswith("s") else v["estado"]
    d = DATA / carpeta
    d.mkdir(parents=True, exist_ok=True)
    ruta = d / f"{v['id']}.json"
    ruta.write_text(json.dumps(v, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def _cargar(ruta: Path) -> dict:
    return json.loads(ruta.read_text(encoding="utf-8"))


@mcp.tool()
def buscar(portal: str, texto: str, limite: int = 15, pais: str = "CO",
           nivel: str = "todos") -> str:
    """Busca vacantes en un portal y las guarda en data/vacantes/pendientes/.
    portal: getonboard|remotive|remoteok|wwr|linkedin|greenhouse|todos.
    texto: keywords de búsqueda. pais: código ISO de 2 letras para getonboard
    (CO por defecto; 'XX' = sin filtro). nivel: 'junior' filtra señales de rol
    senior (título: senior/lead/principal/manager/architect...; descripción:
    5+ años); 'todos' no filtra."""
    portales = list(REGISTRO) if portal == "todos" else [portal]
    if portal != "todos" and portal not in REGISTRO:
        return f"Error: portal '{portal}' no soportado. Usa: {', '.join(REGISTRO)}|todos"
    pais_efectivo = None if pais in (None, "", "XX") else pais

    nuevas, repetidas, errores, filtradas_senior = [], 0, [], 0
    for nombre in portales:
        try:
            crudos = REGISTRO[nombre].buscar(texto, limite=limite, pais=pais_efectivo)
        except Exception as e:  # un portal caído no bloquea los demás
            errores.append({"portal": nombre, "error": f"{type(e).__name__}: {e}"})
            continue
        for v in crudos:
            if nivel == "junior" and _es_senior(v):
                filtradas_senior += 1
                continue
            if _ruta(v["id"]):
                repetidas += 1
                continue
            _guardar(v)
            nuevas.append({"id": v["id"], "titulo": v["titulo"], "empresa": v["empresa"],
                           "portal": v["portal"], "modalidad": v["modalidad"],
                           "region_hint": v["region_hint"], "url": v["url"]})
    return json.dumps({"busqueda": texto, "nivel": nivel,
                       "nuevas_guardadas": len(nuevas),
                       "ya_conocidas": repetidas,
                       "filtradas_por_seniority": filtradas_senior,
                       "errores": errores,
                       "resultados": nuevas},
                      ensure_ascii=False, indent=1)


@mcp.tool()
def listar(estado: str = "pendientes") -> str:
    """Lista vacantes guardadas en un estado: pendientes|aprobadas|descartadas.
    Ordenadas por recencia (publicada, luego capturada) — las más nuevas primero."""
    d = DATA / estado
    if not d.exists():
        return json.dumps({"estado": estado, "total": 0, "vacantes": []}, ensure_ascii=False)
    vacantes = []
    for p in sorted(d.glob("*.json")):
        v = _cargar(p)
        vacantes.append({"id": v["id"], "titulo": v["titulo"], "empresa": v["empresa"],
                         "portal": v["portal"], "region_hint": v["region_hint"],
                         "publicada": v["publicada"], "capturada": v.get("capturada"),
                         "url": v["url"]})
    vacantes.sort(key=lambda x: (x.get("publicada") or "", x.get("capturada") or ""), reverse=True)
    return json.dumps({"estado": estado, "total": len(vacantes), "vacantes": vacantes},
                      ensure_ascii=False, indent=1)


@mcp.tool()
def agregar_manual(url: str, titulo: str = "", empresa: str = "",
                   texto: str = "", notas: str = "") -> str:
    """Ingresa una vacante que el usuario encontró por fuera de los portales.
    Detecta el portal desde la URL (greenhouse, linkedin, remotive, getonboard,
    genérico) y descarga la descripción; si se pasa 'texto', se usa como
    descripción directamente. La guarda en data/vacantes/pendientes/ para
    revisión humana."""
    from adapters import _comun

    bajo_url = url.lower()
    portal_detectado = "manual"
    descripcion = texto.strip()

    if "greenhouse.io" in bajo_url:
        portal_detectado = f"greenhouse-{(REGISTRO['greenhouse']._sacar_board_id(url) or ('?',))[0]}"
        if not descripcion:
            descripcion = REGISTRO["greenhouse"].detalle(url)
    elif "canonical.com/careers" in bajo_url:
        # canonical.com/careers/<id> es el mismo job de Greenhouse (board canonical)
        import re as _re

        m = _re.search(r"careers/(\d+)", bajo_url)
        if m:
            portal_detectado = "greenhouse-canonical"
            gh_url = f"https://job-boards.greenhouse.io/canonical/jobs/{m.group(1)}"
            if not descripcion:
                descripcion = REGISTRO["greenhouse"].detalle(gh_url)
            if descripcion:
                url = gh_url  # normalizar a la URL canónica de Greenhouse
    elif "linkedin.com/jobs/view" in bajo_url:
        portal_detectado = "linkedin"
        if not descripcion:
            descripcion = REGISTRO["linkedin"].detalle(url)
    elif "remotive.com" in bajo_url:
        portal_detectado = "remotive"
        if not descripcion:
            descripcion = REGISTRO["remotive"].detalle(url)
    elif "getonbrd" in bajo_url:
        portal_detectado = "getonboard"
        # el detalle getonboard es SPA: se cubre con buscar; texto requerido
    elif descripcion:
        portal_detectado = "manual"

    if not titulo:
        titulo = url.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").title()
    if not descripcion:
        return ("Error: no pude descargar la descripción para esta URL. "
                "Vuelve a invocar pasando 'texto' con la descripción copiada.")

    v = _comun.normalizar(
        portal=portal_detectado,
        url=url,
        titulo=titulo,
        empresa=empresa,
        descripcion_html=descripcion,  # ya es texto plano: html_a_texto lo pasa intacto
        modalidad=None,
    )
    if notas:
        v["notas_usuario"] = notas[:500]
    if _ruta(v["id"]):
        return f"Ya existía: {v['id']} ({titulo})"
    _guardar(v)
    return f"OK: guardada {v['id']} [{portal_detectado}] '{titulo}' en pendientes. Revisa y decide con empleo_marcar."


@mcp.tool()
def detalle(vacante_id: str) -> str:
    """Devuelve la descripción completa de una vacante (la resuelve vía adaptador
    si aún no se descargó) y actualiza su JSON."""
    ruta = _ruta(vacante_id)
    if not ruta:
        return f"Error: vacante '{vacante_id}' no encontrada."
    v = _cargar(ruta)
    if v.get("descripcion_md"):
        return f"## {v['titulo']}\n{v['empresa']} — {v['url']}\n\n{v['descripcion_md']}"
    portal = REGISTRO.get(v["portal"])
    if not portal:
        return f"Error: portal '{v['portal']}' sin adaptador."
    texto = portal.detalle(v["url"])
    if not texto:
        texto = v.get("resumen", "")
        fuente = "resumen (el portal no devolvió descripción completa)"
    else:
        fuente = "descripcion completa"
    v["descripcion_md"] = texto
    v["capturada"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    _guardar(v)
    return f"## {v['titulo']}\n{v['empresa']} — {v['url']}\n(fuente: {fuente})\n\n{texto}"


@mcp.tool()
def marcar(vacante_id: str, estado: str) -> str:
    """Mueve una vacante a otro estado: aprobada|descartada|pendientes.
    El usuario aprueba/descarta; esta herramienta persiste esa decisión."""
    if estado not in ESTADOS:
        return f"Error: estado '{estado}' inválido. Usa: {', '.join(ESTADOS)}"
    ruta = _ruta(vacante_id)
    if not ruta:
        return f"Error: vacante '{vacante_id}' no encontrada."
    v = _cargar(ruta)
    ruta.unlink()
    v["estado"] = estado
    _guardar(v)
    return f"OK: {vacante_id} -> {estado}"


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    mcp.run()
