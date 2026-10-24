#!/usr/bin/env python3
"""
agregar.py — Agrega requisitos del mercado a partir de las vacantes guardadas.

Uso:
    tools/.venv/Scripts/python.exe tools/mercado/agregar.py

Entrada:  data/vacantes/{pendientes,aprobadas}/*.json (usa descripcion_md)
Salida:   data/mercado/requisitos_agregados.json
          data/mercado/reporte-<AAAA-MM>.md

Métrica clave: en CUÁNTAS vacantes aparece cada requisito (no ocurrencias).
Cruza contra el inventario real (data/audit/stack_inventory.json) y las
credenciales (data/credenciales/consolidado.json) para detectar brechas.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
VACANTES = RAIZ / "data" / "vacantes"
AUDIT = RAIZ / "data" / "audit" / "stack_inventory.json"
CRED = RAIZ / "data" / "credenciales" / "consolidado.json"
SALIDA = RAIZ / "data" / "mercado"

# (canon, regex) — presencia por vacante, EN+ES
TAXONOMIA: list[tuple[str, str]] = [
    ("AWS", r"\baws\b|amazon web services"),
    ("Azure", r"\bazure\b"),
    ("GCP", r"\bgcp\b|google cloud"),
    ("Kubernetes", r"kubernetes|\bk8s\b|\beks\b|\baks\b|\bgke\b"),
    ("OpenShift", r"openshift"),
    ("Docker/Contenedores", r"docker|podman|containers?|contenedores"),
    ("Terraform/IaC", r"terraform|infrastructure as code|iac|cloudformation"),
    ("Ansible", r"ansible"),
    ("CI/CD", r"ci/?cd|jenkins|github actions|gitlab ci|argocd|continuous integration|integraci[óo]n continua"),
    ("Linux", r"\blinux\b|unix"),
    ("Windows Server", r"windows server"),
    ("Redes", r"\bdns\b|tcp/?ip|firewall|vpc|load balancer|balancer|vpn|http|tls|ssl|redes"),
    ("Observabilidad/Monitoreo", r"monitoring|monitor[eo]o|observability|observabilidad|prometheus|grafana|datadog|cloudwatch|new relic|splunk|zabbix|alertas"),
    ("Seguridad/IAM", r"\biam\b|security groups|least privilege|m[íi]nimo privilegio| SOC 2|owasp"),
    ("SQL/BD", r"\bsql\b|postgresql|postgres|mysql|mariadb|mongodb|oracle db"),
    ("Python", r"python"),
    ("Bash/Shell", r"\bbash\b|shell script|shell scripting"),
    ("PowerShell", r"powershell"),
    ("Git", r"\bgit\b(?!hub)|github|gitlab"),
    ("APIs REST", r"rest\s*api|\bapi[s]?\b(?! gateway)"),
    ("Microservicios", r"microservices?|microservicios"),
    ("Automatización", r"automation|automatizaci[óo]n"),
    ("Soporte/Ticketing-ITIL", r"ticketing|zendesk|jira|servicenow|freshdesk|\bitil\b|\bsla\b|escalation|escalamiento|troubleshooting|diagn[óo]stico"),
    ("DevOps (concepto)", r"devops|sre\b"),
    ("Inglés requerido", r"english|ingl[eé]s"),
    ("Español requerido", r"spanish|espa[ñn]ol"),
    ("Agile/Scrum", r"agile|scrum|kanban|[áa]giles"),
]

SENIORIDAD = [
    ("junior", r"junior|entry[- ]level|graduate|asociado|practicante|recien egresado|\bjr\b"),
    ("mid", r"mid[- ]level|intermedio|semi[- ]senior|\bsr\b-?|engineer ii"),
    ("senior", r"senior|lead|principal|staff|\b5\+ years|\b3\+ years"),
]

# Skills que puedes evidenciar sin un repo público (experiencia laboral,
# credenciales, cursos). Ajusta esta lista a tu caso: es lo que el reporte usa
# para decidir si una brecha es real o ya está cubierta.
MI_EVIDENCIA_EXTRA: set[str] = set()


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    vacantes: list[dict] = []
    for estado in ("pendientes", "aprobadas"):
        d = VACANTES / estado
        if d.exists():
            for p in sorted(d.glob("*.json")):
                v = json.loads(p.read_text(encoding="utf-8"))
                if v.get("descripcion_md"):
                    vacantes.append(v)

    if not vacantes:
        print("No hay vacantes con descripción. Ejecuta /buscar-vacantes primero.")
        return 1

    requisitos: dict[str, int] = {}
    idioma_ingles_nivel: dict[str, int] = {}
    senioridad_niveles: dict[str, int] = {}
    por_portal: dict[str, int] = {}
    modalidades: dict[str, int] = {}
    idiomas_publicacion: dict[str, int] = {}
    salarios: list[tuple[float, float]] = []
    requisitos_por_vacante: list[dict] = []

    for v in vacantes:
        texto = (v.get("descripcion_md") or "") + " " + v.get("titulo", "")
        bajo = texto.lower()
        presentes = [canon for canon, patron in TAXONOMIA if re.search(patron, bajo)]
        for canon in presentes:
            requisitos[canon] = requisitos.get(canon, 0) + 1

        # niveles de inglés explícitos
        for nivel in ("a1", "a2", "b1", "b2", "c1", "c2"):
            if re.search(rf"{nivel}\b", bajo):
                idioma_ingles_nivel[nivel.upper()] = idioma_ingles_nivel.get(nivel.upper(), 0) + 1

        for nivel, patron in SENIORIDAD:
            if re.search(patron, bajo):
                senioridad_niveles[nivel] = senioridad_niveles.get(nivel, 0) + 1
                break

        por_portal[v["portal"]] = por_portal.get(v["portal"], 0) + 1
        modalidades[v.get("modalidad") or "desconocido"] = modalidades.get(v.get("modalidad") or "desconocido", 0) + 1
        if v.get("idioma_publicacion"):
            idiomas_publicacion[v["idioma_publicacion"]] = idiomas_publicacion.get(v["idioma_publicacion"], 0) + 1
        s = v.get("salario") or {}
        if isinstance(s.get("min"), (int, float)) and isinstance(s.get("max"), (int, float)):
            salarios.append((s["min"], s["max"]))

        requisitos_por_vacante.append(
            {"id": v["id"], "titulo": v["titulo"], "portal": v["portal"], "requisitos": presentes}
        )

    n = len(vacantes)
    requisitos_ordenados = sorted(requisitos.items(), key=lambda x: -x[1])

    # evidencia propia
    evidencia: set[str] = set(MI_EVIDENCIA_EXTRA)
    if AUDIT.exists():
        inv = json.loads(AUDIT.read_text(encoding="utf-8"))
        for r in inv.get("repos", []):
            for cat, skills in (r.get("stack") or {}).items():
                for sk in skills:
                    evidencia.add(sk)
    if CRED.exists():
        cred = json.loads(CRED.read_text(encoding="utf-8"))
        for c in cred.get("credenciales", []):
            for sk in c.get("skills") or []:
                for canon, patron in TAXONOMIA:
                    if re.search(patron, sk.lower()):
                        evidencia.add(canon)

    brechas = [
        {"requisito": canon, "vacantes_que_lo_piden": conteo,
         "porcentaje": round(100 * conteo / n)}
        for canon, conteo in requisitos_ordenados
        if conteo / n >= 0.2 and canon not in evidencia
    ]

    resumen = {
        "generado": datetime.now().isoformat(timespec="seconds"),
        "vacantes_analizadas": n,
        "por_portal": por_portal,
        "modalidades": modalidades,
        "idiomas_publicacion": idiomas_publicacion,
        "senioridad": senioridad_niveles,
        "ingles_niveles": idioma_ingles_nivel,
        "salario_usd_mes": {
            "muestras": len(salarios),
            "min": min((a for a, _ in salarios), default=None),
            "max": max((b for _, b in salarios), default=None),
            "promedio_min": round(sum(a for a, _ in salarios) / len(salarios)) if salarios else None,
            "promedio_max": round(sum(b for _, b in salarios) / len(salarios)) if salarios else None,
        },
        "requisitos_por_frecuencia": [
            {"requisito": canon, "vacantes": conteo, "porcentaje": round(100 * conteo / n)}
            for canon, conteo in requisitos_ordenados
        ],
        "brechas_vs_mi_evidencia": brechas,
        "detalle_por_vacante": requisitos_por_vacante,
    }

    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / "requisitos_agregados.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")

    # reporte markdown
    mes = datetime.now().strftime("%Y-%m")
    L = [
        f"# Reporte de mercado — {mes}",
        f"\n**{n} vacantes analizadas** (pendientes + aprobadas con descripción).\n",
        f"Portales: " + ", ".join(f"{k} {v}" for k, v in por_portal.items())
        + " · Modalidades: " + ", ".join(f"{k} {v}" for k, v in modalidades.items())
        + " · Idiomas: " + ", ".join(f"{k} {v}" for k, v in idiomas_publicacion.items()),
        "",
        "## Requisitos por frecuencia",
        "",
        "| Requisito | Vacantes | % |",
        "|---|---|---|",
    ]
    for canon, conteo in requisitos_ordenados:
        L.append(f"| {canon} | {conteo} | {round(100*conteo/n)}% |")
    L += [
        "",
        "## Senioridad e idioma",
        "",
        f"- Senioridad detectada: {senioridad_niveles}",
        f"- Niveles de inglés explícitos: {idioma_ingles_nivel or 'ninguno explícito'}",
    ]
    if salarios:
        L.append(f"- Salario USD/mes: min {resumen['salario_usd_mes']['min']}, "
                 f"prom {resumen['salario_usd_mes']['promedio_min']}-{resumen['salario_usd_mes']['promedio_max']}, "
                 f"max {resumen['salario_usd_mes']['max']} ({len(salarios)} muestras)")
    L += [
        "",
        "## Brechas frecuentes vs mi evidencia (≥20% de vacantes)",
        "",
    ]
    if brechas:
        for b in brechas:
            L.append(f"- **{b['requisito']}** — pedido en {b['porcentaje']}% de vacantes")
    else:
        L.append("- Sin brechas frecuentes detectadas con la evidencia actual.")
    L += [
        "",
        "## Cómo usar este reporte",
        "- Priorizar proyectos del backlog que cierren las brechas más frecuentes.",
        "- Alinear keywords del CV con el vocabulario real del mercado.",
        "- `/analizar-vacante <id>` para el análisis individual de una vacante.",
    ]
    (SALIDA / f"reporte-{mes}.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"OK {n} vacantes -> {SALIDA / 'requisitos_agregados.json'}")
    print(f"OK reporte   -> {SALIDA / f'reporte-{mes}.md'}")
    print(f"\nTOP 10: " + ", ".join(f"{c} ({100*ct//n}%)" for c, ct in requisitos_ordenados[:10]))
    if brechas:
        print("BRECHAS: " + ", ".join(b['requisito'] for b in brechas))
    return 0


if __name__ == "__main__":
    sys.exit(main())
