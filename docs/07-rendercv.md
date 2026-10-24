# 7. RenderCV: CV y versionado

RenderCV convierte YAML en PDF (y PNG, HTML, Markdown, Typst) usando Typst como
motor. Aquí está la parte que más se rompe cuando algo no cuadra, así que el
sistema separa responsabilidades y automatiza el renderizado.

## 7.1 Tres archivos, un CV

RenderCV combina tres piezas en el momento de renderizar:

| Tipo | Archivo | Contiene | No contiene |
|---|---|---|---|
| Contenido | `rendercv/src/cv/<CANDIDATO>.<idioma>.yaml` | Secciones, entradas, datos de contacto | `design`, `locale` |
| Diseño | `rendercv/src/design/<tema>.yaml` | Tema, colores, márgenes, fuentes, templates | `cv`, `locale` |
| Locale | `rendercv/src/locale/<idioma>.yaml` | Idioma, frases traducidas, `month_names` | `cv`, `design` |

La ventaja es el producto cartesiano: 2 idiomas × 2 diseños = 4 variantes de un
mismo contenido. Un cambio en el contenido impacta las cuatro sin tocarlas.

```
rendercv/
├── src/
│   ├── cv/<CANDIDATO>.{es,en}.yaml     # fuente de verdad del contenido
│   ├── design/{harvard,engineeringresumes}.yaml
│   └── locale/{es,en}.yaml
├── tailored/<empresa>-<rol>/           # variante por vacante aprobada
├── versions/<vX.Y.Z>/                  # releases inmutables
├── build/                              # previews temporales (ignorado)
├── rendercv-env/                       # venv de RenderCV (ignorado)
└── Makefile                            # solo Git Bash/WSL
```

En este esqueleto el CV es `nombre-apellido.{es,en}.yaml`. Al personalizarlo
cambia también la constante `CANDIDATO` de `tools/rendercv/renderizar.py`.

## 7.2 Un CV mínimo que renderiza

```yaml
cv:
  name: «Tu Nombre»
  location: «Ciudad, País»
  email: «tu@correo»
  phone: "+12025550123"
  website: "https://«tu-sitio»"
  social_networks:
    - network: LinkedIn
      username: "«tu-usuario»"
    - network: GitHub
      username: "«tu-usuario»"
  sections:
    perfil_profesional:
      - «Una o dos frases con tu narrativa objetivo.»
    educación:
      - institution: «Universidad»
        area: «Ingeniería de Sistemas»
        degree: «Pregrado»
        start_date: 2019-01
        end_date: 2025-12
        location: «Ciudad, País»
        highlights:
          - «Logro verificable 1»
    habilidades_técnicas:
      - label: «Cloud»
        details: «AWS, Linux, Docker»
```

Reglas que evitaron horas de depuración:

- **Todo string con `:` va entre comillas.** `location: Medellín, Colombia` pasa,
  pero `details: Cloud: AWS` rompe el parser. Cuando dudes, comillas simples o
  dobles.
- **`phone` debe ser válido** para el esquema (formato E.164 o similar);
  `+12025550123` siempre sirve.
- **Los placeholders con `«...»` no van en el PDF final.** Funcionan en YAML,
  pero en Typst los `<...>` son etiquetas y el render falla con
  `unclosed label`.
- **No metas `design:`, `locale:` ni `settings:` en el archivo de contenido.** El
  diseño y el locale entran por CLI; si los pones inline, sobrescribes el diseño
  que pases y el resultado deja de ser reproducible.

## 7.3 El orquestador en vez de `make`

`make` no está garantizado en Windows, así que `tools/rendercv/renderizar.py`
hace lo mismo desde el venv del agente. Su única dependencia es `PyYAML`.

```powershell
# 4 previews del CV base
tools\.venv\Scripts\python.exe tools\rendercv\renderizar.py preview

# Variante de una vacante
tools\.venv\Scripts\python.exe tools\rendercv\renderizar.py vacante --dir «empresa-rol» --idioma es --design harvard

# Render genérico (cualquier CV + diseño + locale)
tools\.venv\Scripts\python.exe tools\rendercv\renderizar.py custom --cv a.yaml --design b.yaml --locale c.yaml --out salida\ [--pdf salida\nombre.pdf] [--sin-png]

# Release (4 variantes + manifest)
tools\.venv\Scripts\python.exe tools\rendercv\renderizar.py release --version v1.0.0
```

Qué aporta sobre llamar a `rendercv` a mano:

- Fija `PYTHONUTF8=1`, sin el cual Typst falla en consolas cp1252 al emitir la
  línea `Last updated: / Actualizado: →`.
- Usa rutas absolutas y `cwd=rendercv/`, así da igual desde dónde lo lances.
- Comprueba que exista `rendercv/rendercv-env/Scripts/rendercv.exe` y aborta con
  un mensaje claro en vez de un traceback.
- Valida la versión semántica y la inexistencia de la carpeta de destino antes de
  escribir un release.
- Nombrar los PDFs según `CANDIDATO`, para que el archivo diga algo.

### Modos y salidas

| Modo | Escribe en | Nombre del PDF |
|---|---|---|
| `preview` | `rendercv/build/preview/{es,en}-{harvard,er}/` | El que asigne RenderCV (`<CANDIDATO>_CV.pdf`) |
| `vacante` | `rendercv/tailored/<carpeta>/output/` | `<CANDIDATO>-<carpeta>.pdf` |
| `custom` | `--out` | `--pdf` si se indica |
| `release` | `rendercv/versions/<version>/<variante>/` | Artefactos de RenderCV copiados tal cual |

Con `vacante` el orquestador pasa `--dont-generate-png` solo si usas `--sin-png`;
por defecto genera PNG además del PDF.

## 7.4 Tailoring por vacante

Una variante vive en `rendercv/tailored/<empresa>-<rol>/`:

```
rendercv/tailored/<empresa>-<rol>/
├── cv.es.yaml          # copia del base con cambios de énfasis
├── vacante.ref.json    # trazabilidad: id, url, estado de aprobación
├── notas-fit.md        # qué se cambió, por qué, y qué brechas quedan
└── output/             # PDF (+PNG) generado
```

`cv.es.yaml` es una copia del CV base, no un archivo que referencia al base. Esto
es deliberado: cada variante debe ser autocontenida y reproducible aunque el CV
base cambie después. `vacante.ref.json` deja rastro de a qué vacante corresponde.

### Permitido

- Reordenar secciones y entradas (lo relevante primero).
- Reescribir `headline` y perfil con el vocabulario de la vacante, **sin agregar
  hechos**.
- Elegir 3-4 proyectos afines y omitir los irrelevantes.
- Reescribir `label`/`details` de habilidades agrupando por lo que pide la
  vacante.
- Recortar secciones de bajo valor para ganar espacio.

### Prohibido

- Inventar experiencia, métricas, certificaciones o tecnologías sin evidencia en
  `data/audit/stack_inventory.json`, `data/credenciales/consolidado.json` o el CV
  actual.
- Cambiar fechas, institución, contacto o cualquier dato duro.
- Ocultar brechas. Si la vacante pide algo que no tienes, va a `notas-fit.md`.

El tailoring **no** se aplica al CV base. Si el cambio vale para todas las
vacantes (una credencial nueva, un proyecto terminado), se absorbe al base con
`/cv-general` y luego un release.

## 7.5 Versionado semántico

| Nivel | Cuándo | Ejemplo |
|---|---|---|
| MAJOR | Cambio de plantilla, reestructuración de secciones, formato de contacto | `v1.0.0` → `v2.0.0` |
| MINOR | Sección nueva, proyecto nuevo, certificación nueva, diseño distinto | `v1.0.0` → `v1.1.0` |
| PATCH | Typo, fecha, enlace, GPA | `v1.0.0` → `v1.0.1` |

`release` es inmutable: si la carpeta existe, se niega a sobrescribir. Escribe
todos los artefactos (pdf, md, html, typ, png) de las 4 variantes, actualiza
`versions/latest.txt` y genera `manifest.yaml`:

```yaml
version: v2.0.0
date: 2026-10-23
commit: a1b2c3d
generated_by: rendercv v2.8 (renderizar.py release)
nota: Cada variante incluye TODOS los artefactos...
variants:
  - id: es-harvard
    source: src/cv/<CANDIDATO>.es.yaml
    design: src/design/harvard.yaml
    locale: src/locale/es.yaml
    artefactos: [«...»]
```

Lo que el orquestador **no** hace a propósito: `git commit` ni `git tag`. Versionar
tu CV es una decisión tuya y se toma fuera del script.

### Por qué `.md` importa

Cada variante liberada incluye el Markdown. Es el formato que el agente lee para
comparar versiones del CV sin gastar contexto en un PDF. Si quieres que el agente
razone sobre tu CV, dale el `.md`, no el PDF.

### El `Makefile`

Se conserva para Git Bash o WSL:

| Target | Equivalente |
|---|---|
| `make preview` | `renderizar.py preview` |
| `make release VERSION=vX.Y.Z` | `renderizar.py release` + `git add/commit/tag` |
| `make versions` | `ls rendercv/versions` |
| `make clean` | Borra `build/` |

Diferencia clave: el Makefile **sí** hace commit y tag. Usa uno u otro según
dónde estés; no los mezcles en el mismo release. En Windows, el symlink
`versions/latest` del Makefile no funciona: por eso el orquestador escribe
`versions/latest.txt` con la versión en texto plano.

## 7.6 Editar el diseño y el locale

Colores y márgenes, en `src/design/<tema>.yaml`:

```yaml
design:
  theme: harvard
  page:
    top_margin: 0.5in
  colors:
    name: rgb(0,0,0)
    section_titles: rgb(0, 79, 144)
```

Frases traducidas, en `src/locale/<idioma>.yaml`:

```yaml
locale:
  language: spanish
  phrases:
    degree_with_area: DEGREE en AREA
```

Cambiar un tema afecta las dos variantes de ese tema. Si el YAML pide un campo
que el tema no reconoce, RenderCV falla con error de validación: es la señal de
que ese campo pertenece al diseño o al locale, no al contenido.

## 7.7 Consistencia es/en

La regla del workspace es que las dos versiones cuenten lo mismo. En la práctica:

- Mismo orden de secciones y de entradas.
- Mismas fechas y mismos datos duros.
- Mismos logros, expresados en el idioma correspondiente.
- Las habilidades pueden agruparse distinto si el vocabulario del mercado lo
  pide, pero no pueden aparecer tecnologías en una versión y no en la otra.

Si una vacante está en inglés, se usa `cv.en.yaml` **solo si** el CV en inglés ya
está alineado con el español. Si no lo está, primero se alinean.

## 7.8 Errores frecuentes

| Síntoma | Causa | Arreglo |
|---|---|---|
| `UnicodeEncodeError` o Typst corta con caracteres raros | Console cp1252 | El orquestador ya fija `PYTHONUTF8=1`; si llamas a `rendercv` a mano, expórtalo |
| `TypstError: unclosed label` | `<...>` en el texto | Cambia los placeholders por `«...»` o elimínalos |
| `Error: no existe rendercv/src/cv/<X>.yaml` | Renombraste el YAML sin actualizar `CANDIDATO` | Alinea ambos |
| `Error: ya existe .../versions/vX.Y.Z` | Versión repetida | Usa otra versión |
| Validación de Pydantic en `phone` | Teléfono inválido | Usa formato internacional, ej. `+12025550123` |
| `YAML parse error` con un `:` en un valor | Escalar sin comillas | Pon comillas |
| `make: command not found` | Windows sin make | Usa `renderizar.py` |

## 7.9 Reiniciar el entorno de RenderCV

Si el venv se corrompe o cambias de versión de Python:

```powershell
Remove-Item -Recurse -Force rendercv\rendercv-env
python -m venv rendercv\rendercv-env
rendercv\rendercv-env\Scripts\python.exe -m pip install "rendercv[full]==2.8"
```

Luego valida con `renderizar.py preview`. No reinstales RenderCV dentro de
`tools/.venv`: los dos entornos están separados porque RenderCV 2.8 y las
dependencias del agente no comparten versiones de Python.
