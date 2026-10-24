#!/usr/bin/env python3
"""
renderizar.py — orquestador de RenderCV para Windows (pwsh).

Sustituye los targets del Makefile en entornos sin make. Envuelve
rendercv/rendercv-env/Scripts/rendercv.exe con PYTHONUTF8=1 (requerido en
consolas cp1252) y rutas absolutas.

Uso:
    python tools/rendercv/renderizar.py preview
        → 4 previews (es/en × harvard/engineeringresumes) en rendercv/build/preview/

    python tools/rendercv/renderizar.py vacante --dir <carpeta> --idioma es --design harvard
        → renderiza rendercv/tailored/<carpeta>/cv.<idioma>.yaml a
          rendercv/tailored/<carpeta>/output/ con PDF nombrado
          <CANDIDATO>-<carpeta>.pdf

    python tools/rendercv/renderizar.py custom --cv <yaml> --design <yaml> --locale <yaml> --out <dir> [--pdf <pdf>] [--sin-png]

    python tools/rendercv/renderizar.py release --version v2.0.0
        → renderiza las 4 variantes y guarda TODOS los artefactos
          (pdf, md, html, typ, png) en rendercv/versions/v2.0.0/<variante>/
          + manifest.yaml + versions/latest.txt
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

# PyYAML viene con tools/.venv; el venv de RenderCV solo trae ruamel.yaml.
# Este orquestador debe poder correr con cualquiera de los dos intérpretes.
try:
    import yaml

    def _yaml_dump(obj: dict) -> str:
        return yaml.dump(obj, allow_unicode=True, sort_keys=False)
except ImportError:  # pragma: no cover - depende del intérprete
    from io import StringIO

    from ruamel.yaml import YAML as _RuamelYAML

    def _yaml_dump(obj: dict) -> str:
        y = _RuamelYAML()
        y.default_flow_style = False
        buf = StringIO()
        y.dump(obj, buf)
        return buf.getvalue()

RAIZ = Path(__file__).resolve().parents[2]
RENDERCV = RAIZ / "rendercv"
EXE = RENDERCV / "rendercv-env" / "Scripts" / "rendercv.exe"
SRC = RENDERCV / "src"
# Nombre base de los YAML del CV (src/cv/<CANDIDATO>.<idioma>.yaml) y prefijo
# de los PDFs. Cámbialo por tu nombre en kebab-case al personalizar el esqueleto.
CANDIDATO = "nombre-apellido"
DESIGNES = {"harvard": SRC / "design" / "harvard.yaml",
            "engineeringresumes": SRC / "design" / "engineeringresumes.yaml"}
LOCALES = {"es": SRC / "locale" / "es.yaml", "en": SRC / "locale" / "en.yaml"}


def render(cv: Path, design: Path, locale: Path, out: Path,
           pdf: Path | None = None, png: bool = True) -> Path:
    if not EXE.exists():
        print(f"Error: no existe {EXE}. Crea el venv (ver AGENTS.md §7).", file=sys.stderr)
        sys.exit(1)
    cmd = [str(EXE), "render", str(cv),
           "--design", str(design), "--locale-catalog", str(locale),
           "--output-folder", str(out)]
    if pdf:
        cmd += ["--pdf-path", str(pdf)]
    if not png:
        cmd += ["--dont-generate-png"]
    env = {**os.environ, "PYTHONUTF8": "1"}
    r = subprocess.run(cmd, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=str(RENDERCV))
    if r.returncode != 0:
        print(r.stdout[-1500:], file=sys.stderr)
        print(r.stderr[-1500:], file=sys.stderr)
        sys.exit(1)
    return pdf if pdf else next(out.glob("*.pdf"), None)


def modo_preview() -> None:
    combos = [("es", "harvard"), ("es", "engineeringresumes"),
              ("en", "harvard"), ("en", "engineeringresumes")]
    hechos = 0
    for idioma, design in combos:
        cv = SRC / "cv" / f"{CANDIDATO}.{idioma}.yaml"
        if not cv.exists():
            print(f"-- omito {idioma}-{design}: no existe src/cv/{cv.name}")
            continue
        out = RENDERCV / "build" / "preview" / f"{idioma}-{'er' if design == 'engineeringresumes' else 'harvard'}"
        pdf = render(cv, DESIGNES[design], LOCALES[idioma], out)
        print(f"OK {idioma}-{design}: {pdf}")
        hechos += 1
    if not hechos:
        print(f"Error: no existe ningún src/cv/{CANDIDATO}.{{es,en}}.yaml", file=sys.stderr)
        sys.exit(1)
    print("\nPreview completa en rendercv/build/preview/")


def modo_vacante(carpeta: str, idioma: str, design: str, sin_png: bool) -> None:
    d = RENDERCV / "tailored" / carpeta
    cv = d / f"cv.{idioma}.yaml"
    if not cv.exists():
        print(f"Error: no existe {cv}", file=sys.stderr)
        sys.exit(1)
    out = d / "output"
    pdf = render(cv, DESIGNES[design], LOCALES[idioma], out,
                 pdf=out / f"{CANDIDATO}-{carpeta}.pdf", png=not sin_png)
    print(f"OK vacante '{carpeta}': {pdf}")


def modo_custom(args: argparse.Namespace) -> None:
    pdf = Path(args.pdf) if args.pdf else None
    resultado = render(Path(args.cv), Path(args.design), Path(args.locale),
                       Path(args.out), pdf=pdf, png=not args.sin_png)
    print(f"OK custom: {resultado}")


def modo_release(version: str) -> None:
    """Renderiza las 4 variantes y guarda TODOS los artefactos (pdf, md, html,
    typ, png) en versions/<version>/<variante>/, + manifest.yaml + latest.txt."""
    if not re.fullmatch(r"v\d+\.\d+\.\d+", version):
        print(f"Error: versión '{version}' no es semántica (ej: v2.0.0)", file=sys.stderr)
        sys.exit(1)
    dest = RENDERCV / "versions" / version
    if dest.exists():
        print(f"Error: ya existe {dest}. Elige otra versión.", file=sys.stderr)
        sys.exit(1)

    tmp = RENDERCV / "build" / f"release-{version}"
    combos = [("es", "harvard"), ("es", "engineeringresumes"),
              ("en", "harvard"), ("en", "engineeringresumes")]
    variantes: list[dict] = []

    for idioma, design in combos:
        vid = f"{idioma}-{'er' if design == 'engineeringresumes' else 'harvard'}"
        out = tmp / vid
        cv = SRC / "cv" / f"{CANDIDATO}.{idioma}.yaml"
        if not cv.exists():
            print(f"-- omito {vid}: no existe src/cv/{cv.name}")
            continue
        render(cv, DESIGNES[design], LOCALES[idioma], out)  # con PNGs
        vdir = dest / vid
        vdir.mkdir(parents=True)
        for f in sorted(out.iterdir()):
            shutil.copy2(f, vdir / f.name)
        variantes.append({
            "id": vid,
            "source": f"src/cv/{CANDIDATO}.{idioma}.yaml",
            "design": f"src/design/{design}.yaml",
            "locale": f"src/locale/{idioma}.yaml",
            "artefactos": sorted(f.name for f in vdir.iterdir()),
        })

    commit = ""
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                                capture_output=True, text=True, cwd=str(RENDERCV),
                                encoding="utf-8").stdout.strip()
    except Exception:
        pass
    manifest = {
        "version": version,
        "date": date.today().isoformat(),
        "commit": commit,
        "generated_by": "rendercv v2.8 (renderizar.py release)",
        "nota": "Cada variante incluye TODOS los artefactos: pdf, md, html, typ y png. El .md es el formato recomendado para que los agentes lean el CV sin gastar tokens en PDFs.",
        "variants": variantes,
    }
    (dest / "manifest.yaml").write_text(
        _yaml_dump(manifest), encoding="utf-8")
    (RENDERCV / "versions" / "latest.txt").write_text(version + "\n", encoding="utf-8")
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"OK release {version} -> rendercv/versions/{version}/")
    for v in variantes:
        print(f"  {v['id']}: {len(v['artefactos'])} artefactos")
    print("Manifest + latest.txt actualizados. (git commit/tag queda a decisión del usuario)")


def main() -> int:
    ap = argparse.ArgumentParser(description="Orquestador RenderCV del workspace")
    sub = ap.add_subparsers(dest="modo", required=True)
    sub.add_parser("preview", help="4 previews del CV base")
    pv = sub.add_parser("vacante", help="renderiza un CV tailored")
    pv.add_argument("--dir", required=True, help="carpeta en rendercv/tailored/")
    pv.add_argument("--idioma", default="es", choices=["es", "en"])
    pv.add_argument("--design", default="harvard", choices=list(DESIGNES))
    pv.add_argument("--sin-png", action="store_true")
    cu = sub.add_parser("custom", help="render genérico")
    cu.add_argument("--cv", required=True)
    cu.add_argument("--design", required=True)
    cu.add_argument("--locale", required=True)
    cu.add_argument("--out", required=True)
    cu.add_argument("--pdf")
    cu.add_argument("--sin-png", action="store_true")
    rl = sub.add_parser("release", help="versiona las 4 variantes con todos los artefactos")
    rl.add_argument("--version", required=True, help="versión semántica, ej: v2.0.0")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if args.modo == "preview":
        modo_preview()
    elif args.modo == "vacante":
        modo_vacante(args.dir, args.idioma, args.design, args.sin_png)
    elif args.modo == "release":
        modo_release(args.version)
    else:
        modo_custom(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
