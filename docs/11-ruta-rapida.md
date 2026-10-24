# 11. Ruta rápida: de cero a un CV v1.0.0

Dos caminos para el mismo objetivo. Elige por lo que quieras hacer hoy, no por lo
que "deberías" instalar.

| | Ruta A — con OpenCode | Ruta B — solo RenderCV |
|---|---|---|
| Instalas | OpenCode, Python, Git | Python |
| Tiempo | 15-25 min | 5 min |
| Tu YAML | lo adopta y lo configura solo | lo usas tal cual |
| Te da | CV `v1.0.0`, entrevista guiada, análisis de vacantes, tailoring con reglas | CV `v1.0.0`, y tailored si lo editas tú |
| Honestidad | la imponen `AGENTS.md` y las skills | la pones tú |
| Ideal si | quieres buscar empleo, no solo un PDF | ya tienes el CV y solo quieres el PDF |

---

## Ruta A — con OpenCode (recomendada)

Sirve para el objetivo completo: CV, auditoría de tus repos, análisis de fit de
vacantes y CVs adaptados.

**Modelo recomendado: `opencode/deepseek-v4.1-flash-free`** (cámbialo con
`/model`). Es gratis, rápido, y la lógica del sistema vive en las skills del repo,
así que no necesitas un modelo caro para que funcione.

El arranque completo, con el prompt listo para pegar, está en
**[ARRANQUE.md](../ARRANQUE.md)**. En resumen:

```powershell
mkdir C:\cv ; cd C:\cv ; opencode
```

Luego pegas el prompt de `ARRANQUE.md` indicando el enlace del repo y la ruta de
tu YAML. OpenCode clona, ejecuta `scripts/arranque.ps1`, adopta tu plantilla, te
entrevista para los datos que faltan, renderiza y te guía.

Si prefieres hacerlo sin pegar prompts largos, el script se puede llamar directo:

```powershell
git clone https://github.com/abedoyaciro/guia-opencode-busqueda-laboral _guia
pwsh -File _guia\scripts\arranque.ps1 -Destino .\busqueda-laboral -PlantillaCv C:\ruta\mi-cv.yaml -Idioma es
```

`arranque.ps1` acepta además `-Minimo`, que crea **solo** el entorno de RenderCV
(sin `tools/.venv` ni Chromium) y deja `opencode.json` sin servidores MCP. Útil si
hoy solo quieres el CV.

### Qué hace con tu YAML

Tu plantilla puede ser un YAML todo-en-uno (el que genera `rendercv new`, con
`cv`, `design`, `locale` y `settings`) o uno que solo tenga `cv:`. El script:

1. comprueba que exista la clave raíz `cv` (si no, te lo dice y no toca nada);
2. se queda solo con `cv` y descarta `design`, `locale` y `settings`, porque el
   esqueleto ya aporta diseño y locale por separado (ver
   [07. RenderCV § 7.1](07-rendercv.md#71-tres-archivos-un-cv));
3. lo guarda como `rendercv/src/cv/<CANDIDATO>.<idioma>.yaml`;
4. actualiza la constante `CANDIDATO` en `tools/rendercv/renderizar.py`;
5. borra el CV de ejemplo (`nombre-apellido.es.yaml`, `nombre-apellido.en.yaml`)
   para que no se cuele en el preview ni en tu `v1.0.0`.

Solo generas las variantes del idioma que tengas: si tu plantilla es `es`, el
release produce las dos variantes `es` (Harvard y Engineering Resumes) y omite las
`en` que no existan.

Efectos que conviene saber: el YAML se **normaliza** (se pierden los comentarios)
y tu diseño/locale propios se ignoran. Si querías conservarlos, deja tu diseño en
`rendercv/src/design/` y tu locale en `rendercv/src/locale/` después del arranque.

### De ahí al v1.0.0

```powershell
cd .\busqueda-laboral
tools\.venv\Scripts\python.exe tools\rendercv\renderizar.py preview      # PDFs en rendercv\build\preview\
tools\.venv\Scripts\python.exe tools\rendercv\renderizar.py release --version v1.0.0
```

El release deja `rendercv/versions/v1.0.0/` con todos los artefactos y su
`manifest.yaml`, y **no** hace `git commit` ni `git tag`: eso lo decides tú
([07 § 7.5](07-rendercv.md#75-versionado-semántico)).

Si estás en modo `-Minimo`, usa el intérprete del venv de RenderCV:

```powershell
rendercv\rendercv-env\Scripts\python.exe tools\rendercv\renderizar.py preview
```

### Un tailored para una vacante

```
/buscar-vacantes        → trae vacantes a data\vacantes\pendientes\
/revisar-vacantes       → apruebas o descartas
/analizar-vacante <id>  → score 0-100, brechas y veredicto
/cv-vacante <id>        → variante en PDF para esa vacante
```

Las reglas de tailoring honesto (qué se puede y qué no cambiar) están en
[07 § 7.4](07-rendercv.md#74-tailoring-por-vacante). El agente las aplica porque
están escritas en las skills del repo.

---

## Ruta B — solo RenderCV (sin OpenCode)

Si tu único objetivo es el PDF.

### 1. Instala RenderCV en un entorno virtual

```powershell
mkdir C:\cv ; cd C:\cv
python -m venv rendercv-env
rendercv-env\Scripts\python.exe -m pip install "rendercv[full]==2.8"
```

En Windows, activa UTF-8 en la consola antes de usar la CLI:

```powershell
$env:PYTHONUTF8 = '1'
```

Sin esa variable, `rendercv` revienta al imprimir su panel de resultado con un
`UnicodeEncodeError: 'charmap' codec can't encode character '\u2713'`. Verificado:
el error es cosmético y puede ocurrir **después** de generar los archivos, pero es
mejor evitarlo.

### 2. Tu YAML

Tres casos:

- **Ya tienes tu plantilla** → úsala tal cual. RenderCV acepta un YAML
  todo-en-uno con `cv`, `design`, `locale` y `settings`, y también uno que solo
  tenga `cv:` (en ese caso aplica el diseño por defecto de RenderCV).
- **Empiezas de cero** → `rendercv new "Tu Nombre"` genera `Tu_Nombre_CV.yaml`
  con todas las secciones comentadas para rellenar.
- **Quieres el diseño de este repo** → copia
  `esqueleto/rendercv/src/design/harvard.yaml` o `engineeringresumes.yaml` y
  pásalos con `--design`.

### 3. Renderiza

```powershell
rendercv-env\Scripts\rendercv.exe render mi-cv.yaml
```

Salida en `rendercv_output\`: PDF, PNG (una por página), HTML, Markdown y Typst.
Markdown es el más útil para que un agente lea tu CV sin gastar contexto en un PDF.

Flags que vas a usar:

| Flag | Para qué |
|---|---|
| `-o, --output-folder` | Cambiar la carpeta de salida (por defecto `rendercv_output/`) |
| `-d, --design` | Aplicar un diseño externo YAML |
| `-lc, --locale-catalog` | Aplicar un locale externo YAML (idioma, frases) |
| `-pdf, --pdf-path` | Nombrar/ubicar el PDF (ruta relativa al archivo de entrada) |
| `--dont-generate-png` / `-nopng` | Omitir los PNG |
| `-w, --watch` | Re-renderizar al guardar el YAML |

Renderizar un YAML con diseño y locale externos:

```powershell
rendercv-env\Scripts\rendercv.exe render mi-cv.yaml `
  --design esqueleto\rendercv\src\design\harvard.yaml `
  --locale-catalog esqueleto\rendercv\src\locale\es.yaml `
  --output-folder salida\harvard
```

### 4. Fíjalo como v1.0.0

```powershell
pwsh -File _guia\scripts\versionar-solo.ps1 -Cv .\mi-cv.yaml -Version v1.0.0
```

Deja `versions\v1.0.0\` con los artefactos, una copia inmutable del YAML fuente y
un `manifest.yaml`. No toca git; si quieres fijarlo:

```powershell
git add . ; git commit -m "chore(release): v1.0.0" ; git tag v1.0.0
```

Alternativa mínima sin script: `git tag v1.0.0` sobre el commit que tenga tu YAML
y tu `rendercv_output/`. El script solo te ahorra hacerlo a mano cada vez.

### 5. Un tailored para una vacante (a mano)

Sin agente, eres tú quien aplica las reglas:

1. Copia tu YAML: `copy mi-cv.yaml vacantes\acme-support.yaml`.
2. Edita **solo el énfasis**: reordena secciones y proyectos, reescribe el
   resumen con el vocabulario del anuncio, quita lo irrelevante.
3. No toques fechas, contacto, empresa, institución ni métricas.
4. Si el anuncio pide algo que no tienes, escríbelo aparte en un `notas.md` en
   vez de inventarlo.
5. Renderiza: `rendercv-env\Scripts\rendercv.exe render vacantes\acme-support.yaml -o vacantes\acme-support`.

Las mismas reglas, con más detalle, en
[07. RenderCV § 7.4](07-rendercv.md#74-tailoring-por-vacante).

---

## Qué te pierdes con la Ruta B

- **La honestidad impuesta por reglas**: en la Ruta A, `AGENTS.md` y las skills
  prohíben inventar experiencia y citar fuentes. Aquí depende de tu disciplina.
- **El análisis de fit**: nada calcula si vale la pena postular.
- **El reporte de mercado**: nada agrega lo que piden las vacantes de tu sector.
- **La adopción automática de credenciales** (Credly, Google Skills) y el
  inventario de tu stack real desde tus repos.
- **El `Makefile` y el orquestador** `renderizar.py`: siguen disponibles si luego
  montas el workspace completo con `scripts/instalar.ps1`.

Puedes empezar con la Ruta B y pasar a la A después: el YAML que ya tienes es el
mismo que adopta `arranque.ps1` con `-PlantillaCv`.

## Instalación en paralelo (las dos cosas)

Si quieres el CV ya y el sistema completo después, no escojas: instala RenderCV
para tu YAML hoy (Ruta B) y, cuando tengas tiempo, corre
`scripts/instalar.ps1` en una carpeta nueva para montar el workspace completo. No
comparten estado, así que no se estorban.
