#!/usr/bin/env python3
"""
audit.py — Auditoría de repos GitHub → inventario de stack técnico real.

Uso:
    tools/.venv/Scripts/python.exe tools/github_audit/audit.py --usuario tu-usuario-github

Salida:
    data/audit/stack_inventory.json   Inventario estructurado (fuente de verdad)
    data/audit/informe_github.md      Resumen legible para humanos y agentes

Seguridad:
    - No ejecuta nada de los repos. Solo lectura vía gh api.
    - No descarga archivos que parezcan secretos.
    - Límite de 256 KB por archivo de manifiesto.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

MAX_FILE_BYTES = 256 * 1024

SECRET_RE = re.compile(
    r"(^|/)(\.env(\..*)?|[^/]*\.(pem|key|p12|pfx|keystore|jks)|id_rsa[^/]*|"
    r"credentials[^/]*|secrets?\.[^/]*|service-account[^/]*\.json|[^/]*\.tfvars)$",
    re.IGNORECASE,
)

# ── Detección por ruta: (regex, categoría, skill) ───────────────────────────
PATH_RULES: list[tuple[str, str, str]] = [
    (r"(^|/)package\.json$",                      "lenguajes",    "JavaScript/Node.js"),
    (r"(^|/)tsconfig\.json$",                     "lenguajes",    "TypeScript"),
    (r"(^|/)requirements[^/]*\.txt$",             "lenguajes",    "Python"),
    (r"(^|/)pyproject\.toml$",                    "lenguajes",    "Python"),
    (r"(^|/)Pipfile$",                            "lenguajes",    "Python"),
    (r"(^|/)environment\.ya?ml$",                 "lenguajes",    "Python (Conda)"),
    (r"\.rmd$|\.r$|(^|/)renv\.lock$|(^|/)DESCRIPTION$", "lenguajes", "R"),
    (r"(^|/)go\.mod$",                            "lenguajes",    "Go"),
    (r"(^|/)Cargo\.toml$",                        "lenguajes",    "Rust"),
    (r"(^|/)pom\.xml$|build\.gradle(\.kts)?$",    "lenguajes",    "Java/JVM"),
    (r"(^|/)Dockerfile[^/]*$",                    "contenedores", "Docker"),
    (r"(^|/)docker-compose[^/]*\.ya?ml$",         "contenedores", "Docker Compose"),
    (r"(^|/)\.devcontainer/devcontainer\.json$",  "contenedores", "Devcontainers"),
    (r"\.tf$",                                    "iac",          "Terraform"),
    (r"(^|/)serverless\.ya?ml$",                  "iac",          "Serverless Framework"),
    (r"(^|/)kustomization\.ya?ml$",               "kubernetes",   "Kustomize"),
    (r"(^|/)Chart\.ya?ml$",                       "kubernetes",   "Helm"),
    (r"(^|/)ansible\.cfg$|(^|/)playbooks?/",      "iac",          "Ansible"),
    (r"(^|/)\.github/workflows/[^/]+\.ya?ml$",    "cicd",         "GitHub Actions"),
    (r"(^|/)Makefile$",                           "build",        "Make"),
    (r"(^|/)\.streamlit/",                        "datos",        "Streamlit"),
]

# ── Detección por contenido de manifiestos: dep → (skill, categoría) ───────
PY_DEPS: dict[str, tuple[str, str]] = {
    "pandas": ("Pandas", "datos"),
    "scikit-learn": ("Scikit-learn", "datos"),
    "numpy": ("NumPy", "datos"),
    "streamlit": ("Streamlit", "datos"),
    "plotly": ("Plotly", "datos"),
    "matplotlib": ("Matplotlib", "datos"),
    "seaborn": ("Seaborn", "datos"),
    "fastapi": ("FastAPI", "frameworks"),
    "flask": ("Flask", "frameworks"),
    "django": ("Django", "frameworks"),
    "boto3": ("AWS boto3", "cloud"),
    "pytest": ("pytest", "calidad"),
    "rendercv": ("RenderCV", "herramientas"),
    "playwright": ("Playwright", "automatizacion"),
}
JS_DEPS: dict[str, tuple[str, str]] = {
    "react": ("React", "frameworks"),
    "next": ("Next.js", "frameworks"),
    "express": ("Express", "frameworks"),
    "vue": ("Vue", "frameworks"),
    "jest": ("Jest", "calidad"),
    "typescript": ("TypeScript", "lenguajes"),
    "playwright": ("Playwright", "automatizacion"),
}
TF_PROVIDER_RE = re.compile(r'provider\s+"(aws|azurerm|google|kubernetes|helm)"')
TF_MAPA = {"aws": "AWS", "azurerm": "Azure", "google": "GCP",
           "kubernetes": "Kubernetes", "helm": "Helm"}
WORKFLOW_SIGNALS = {
    "aws-actions/": "AWS (CI/CD)",
    "azure/": "Azure (CI/CD)",
    "google-github-actions/": "GCP (CI/CD)",
    "docker/build-push-action": "Docker build/push",
}
CONTENT_MANIFEST_RE = re.compile(
    r"(^|/)(package\.json|requirements[^/]*\.txt|pyproject\.toml|Dockerfile[^/]*|"
    r"docker-compose[^/]*\.ya?ml|[^/]*\.tf|\.github/workflows/[^/]+\.ya?ml)$"
)


def gh_json(args: list[str]) -> dict | list | None:
    """Ejecuta gh y devuelve JSON parseado; None si falla (repo vacío, etc.)."""
    proc = subprocess.run(["gh", *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def list_repos(usuario: str, incluir_privados: bool, incluir_archivados: bool) -> list[dict]:
    campos = ("name,nameWithOwner,description,url,homepageUrl,isPrivate,isFork,"
              "isArchived,pushedAt,stargazerCount,primaryLanguage,"
              "repositoryTopics,defaultBranchRef")
    repos = gh_json(["repo", "list", usuario, "--json", campos, "--limit", "200"]) or []
    if not incluir_privados:
        repos = [r for r in repos if not r.get("isPrivate")]
    if not incluir_archivados:
        repos = [r for r in repos if not r.get("isArchived")]
    return repos


def get_tree(full_name: str, branch: str) -> list[str]:
    data = gh_json(["api", f"repos/{full_name}/git/trees/{branch}?recursive=1"])
    if not data or "tree" not in data:
        return []
    return [n["path"] for n in data["tree"] if n.get("type") == "blob"]


def fetch_file(full_name: str, path: str, branch: str) -> str | None:
    if SECRET_RE.search(path):
        return None
    data = gh_json(["api", f"repos/{full_name}/contents/{path}?ref={branch}"])
    if not data or data.get("encoding") != "base64":
        return None
    if (data.get("size") or 0) > MAX_FILE_BYTES:
        return None
    try:
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except Exception:
        return None


def detect_from_paths(paths: list[str]) -> tuple[dict[str, set[str]], list[str]]:
    stack: dict[str, set[str]] = {}
    manifests: list[str] = []
    for p in paths:
        for regex, cat, skill in PATH_RULES:
            if re.search(regex, p, re.IGNORECASE):
                stack.setdefault(cat, set()).add(skill)
        if CONTENT_MANIFEST_RE.search(p):
            manifests.append(p)
    return stack, manifests


def detect_from_content(path: str, content: str, stack: dict[str, set[str]]) -> None:
    name = path.rsplit("/", 1)[-1].lower()
    low = content.lower()
    if name == "package.json":
        try:
            pkg = json.loads(content)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            for dep, (skill, cat) in JS_DEPS.items():
                if dep in deps:
                    stack.setdefault(cat, set()).add(skill)
        except json.JSONDecodeError:
            pass
    elif name.startswith("requirements") or name == "pyproject.toml":
        for dep, (skill, cat) in PY_DEPS.items():
            if re.search(rf"(?<![a-z0-9_-]){re.escape(dep)}(?![a-z0-9_-])", low):
                stack.setdefault(cat, set()).add(skill)
    elif name.endswith(".tf"):
        for provider in set(TF_PROVIDER_RE.findall(low)):
            stack.setdefault("cloud", set()).add(TF_MAPA[provider])
    elif "/workflows/" in path:
        for señal, skill in WORKFLOW_SIGNALS.items():
            if señal in content:
                stack.setdefault("cicd", set()).add(skill)


def evaluar_readme(full_name: str, paths: list[str], branch: str) -> dict:
    candidatos = [
        p for p in paths
        if "/" not in p and p.rsplit("/", 1)[-1].lower() in
        {"readme", "readme.md", "readme.txt", "readme.rst"}
    ]
    if not candidatos:
        return {"existe": False}
    contenido = fetch_file(full_name, candidatos[0], branch) or ""
    return {
        "existe": True,
        "caracteres": len(contenido),
        "describe_problema": bool(re.search(r"(?i)(problema|motivaci|overview|about|acerca)", contenido)),
        "tiene_demo_o_capturas": bool(re.search(r"(?i)(demo|screenshot|captura|!\[|http)", contenido)),
        "tiene_instrucciones": bool(re.search(r"(?i)(instal|usage|c[oó]mo usar|getting started|quickstart)", contenido)),
        "menciona_arquitectura": bool(re.search(r"(?i)arquitectur|architecture|diagrama", contenido)),
    }


def auditar(usuario: str, incluir_privados: bool, excluir_forks: bool,
            incluir_archivados: bool) -> dict:
    repos = list_repos(usuario, incluir_privados, incluir_archivados)
    inventario = {
        "generado_en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "usuario": usuario,
        "total_repos": 0,
        "repos": [],
        "agregado": {},
    }
    skills_globales: Counter[str] = Counter()

    for repo in repos:
        if repo.get("isFork") and excluir_forks:
            continue
        full = repo["nameWithOwner"]
        branch = (repo.get("defaultBranchRef") or {}).get("name", "HEAD")
        print(f"  - {full}", flush=True)

        paths = get_tree(full, branch)
        stack, manifests = detect_from_paths(paths)
        lenguajes = gh_json(["api", f"repos/{full}/languages"]) or {}

        for m in manifests[:12]:
            contenido = fetch_file(full, m, branch)
            if contenido:
                detect_from_content(m, contenido, stack)

        entrada = {
            "nombre": repo["name"],
            "url": repo["url"],
            "descripcion": repo.get("description"),
            "homepage": repo.get("homepageUrl"),
            "privado": repo["isPrivate"],
            "fork": repo["isFork"],
            "archivado": repo.get("isArchived", False),
            "ultimo_push": repo.get("pushedAt"),
            "estrellas": repo.get("stargazerCount", 0),
            "lenguaje_principal": (repo.get("primaryLanguage") or {}).get("name"),
            "lenguajes_bytes": lenguajes,
            "topics": [t["name"] for t in (repo.get("repositoryTopics") or [])],
            "manifiestos": manifests,
            "stack": {k: sorted(v) for k, v in sorted(stack.items())},
            "readme": evaluar_readme(full, paths, branch),
        }
        inventario["repos"].append(entrada)
        for skills in stack.values():
            skills_globales.update(skills)

    inventario["total_repos"] = len(inventario["repos"])
    inventario["agregado"] = {
        "skills_por_frecuencia": dict(skills_globales.most_common()),
        "cloud_providers": sorted({s for r in inventario["repos"]
                                   for s in r["stack"].get("cloud", [])}),
        "repos_con_iac": sum(1 for r in inventario["repos"] if "iac" in r["stack"]),
        "repos_con_cicd": sum(1 for r in inventario["repos"] if "cicd" in r["stack"]),
        "repos_con_contenedores": sum(1 for r in inventario["repos"] if "contenedores" in r["stack"]),
        "repos_sin_readme": [r["nombre"] for r in inventario["repos"]
                             if not r["readme"].get("existe")],
    }
    return inventario


def generar_informe(inv: dict) -> str:
    ag = inv["agregado"]
    lineas = [
        f"# Inventario técnico de {inv['usuario']} — {inv['generado_en'][:10]}",
        f"\n**{inv['total_repos']} repositorios auditados.**\n",
        "## Skills por frecuencia (evidencia en repos)\n",
        "| Skill | Repos |", "|---|---|",
    ]
    for skill, n in ag["skills_por_frecuencia"].items():
        lineas.append(f"| {skill} | {n} |")
    lineas += [
        "\n## Resumen\n",
        f"- Cloud: {', '.join(ag['cloud_providers']) or 'sin evidencia'}",
        f"- Repos con IaC: {ag['repos_con_iac']}",
        f"- Repos con CI/CD: {ag['repos_con_cicd']}",
        f"- Repos con contenedores: {ag['repos_con_contenedores']}",
        "\n## Repos y stacks\n",
    ]
    for r in inv["repos"]:
        stack = "; ".join(f"**{k}**: {', '.join(v)}" for k, v in r["stack"].items())
        lineas.append(f"### [{r['nombre']}]({r['url']})")
        lineas.append(f"- {r.get('descripcion') or '_sin descripcion_'}")
        lineas.append(f"- {stack or '_sin manifiestos detectados_'}")
        if not r["readme"].get("existe"):
            lineas.append("- sin README")
        lineas.append("")
    if ag["repos_sin_readme"]:
        lineas += ["## Repos sin README (oportunidad rapida de mejora)\n"]
        lineas += [f"- {n}" for n in ag["repos_sin_readme"]]
    return "\n".join(lineas) + "\n"


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Auditoria de stack tecnico via gh CLI")
    ap.add_argument("--usuario", help="Usuario de GitHub (default: el autenticado en gh)")
    ap.add_argument("--salida", default="data/audit", help="Directorio de salida")
    ap.add_argument("--incluir-privados", action="store_true")
    ap.add_argument("--excluir-forks", action="store_true")
    ap.add_argument("--incluir-archivados", action="store_true")
    args = ap.parse_args()

    usuario = args.usuario
    if not usuario:
        me = gh_json(["api", "user"])
        if not me:
            print("Error: gh no autenticado. Ejecuta `gh auth login`.", file=sys.stderr)
            return 1
        usuario = me["login"]

    print(f"Auditando repos de {usuario}...")
    inv = auditar(usuario, args.incluir_privados, args.excluir_forks,
                  args.incluir_archivados)

    out = Path(args.salida)
    out.mkdir(parents=True, exist_ok=True)
    (out / "stack_inventory.json").write_text(
        json.dumps(inv, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "informe_github.md").write_text(generar_informe(inv), encoding="utf-8")
    print(f"\nOK {inv['total_repos']} repos -> {out / 'stack_inventory.json'}")
    print(f"OK informe -> {out / 'informe_github.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
