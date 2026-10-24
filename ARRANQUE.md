# Arranque en un paso (OpenCode clona, configura y te guía)

Para quien **no tiene OpenCode ni RenderCV instalados** y solo quiere llegar a un
CV `v1.0.0` (y, si acaso, una versión adaptada a una vacante).

No necesitas clonar nada a mano ni saber la estructura del repo: le das el enlace
a OpenCode y él hace el resto.

## Paso 0 — Lo único que instalas tú

```powershell
# OpenCode (necesita Node.js 18+)
winget install --id OpenJS.NodeJS.LTS
npm install -g @opencode/cli

# Python 3.13 (lo usa RenderCV)
winget install --id Python.Python.3.13

# Git (para clonar)
winget install --id Git.Git
```

> Ojo: **no** instales OpenCode con `winget`. El paquete `SST.opencode` es la
> versión 1.x (V1). Usa `npm install -g @opencode/cli`.

Comprueba con `opencode --version` (debe decir `2.x`), `python --version`,
`git --version`.

## Paso 1 — Modelo recomendado

Dentro de OpenCode, ejecuta `/model` y elige:

**`opencode/deepseek-v4.1-flash-free`**

Es el recomendado para todo este flujo: es gratis, rápido y sigue bien
instrucciones largas (que es justo lo que piden los prompts de esta guía). Si
tienes acceso a otro modelo con más contexto o mejor razonamiento, también sirve:
la lógica vive en las skills del repo, no en el modelo.

## Paso 2 — Crea una carpeta vacía y abre OpenCode

```powershell
mkdir C:\cv
cd C:\cv
opencode
```

## Paso 3 — Pega este prompt

Rellena los tres datos entre `<>` y pégalo tal cual en OpenCode:

```text
Monta mi sistema de CV y búsqueda laboral desde cero.

- Repo base: https://github.com/abedoyaciro/guia-opencode-busqueda-laboral
- Carpeta destino: .\busqueda-laboral
- Mi CV en YAML: <RUTA_A_TU_YAML>   (idioma: es)

Hazlo así, paso a paso y mostrándome cada resultado:

1. Clona el repo base dentro de esta carpeta:
   git clone https://github.com/abedoyaciro/guia-opencode-busqueda-laboral _guia
2. Ejecuta:
   pwsh -File _guia\scripts\arranque.ps1 -Destino .\busqueda-laboral -PlantillaCv "<RUTA_A_TU_YAML>" -Idioma es
3. Muéstrame la salida completa de la verificación y dime qué quedó pendiente.
4. Pregúntame, de a pocos, lo necesario para rellenar los placeholders
   (opencode.json: CREDLY_USER y SKILLSBOOST_PROFILE_URL; AGENTS.md: rol
   principal, rol secundario, sistema operativo; rendercv/CONTEXTO_CARRERA.md).
   No inventes nada que yo no te confirme.
5. Renderiza el CV (rendercv\build\preview) y dime las rutas exactas de los PDFs.
6. Explícame, en 5 líneas, qué comandos tengo disponibles y para qué sirve cada uno.

Reglas: nada de postulaciones automáticas ni cambios públicos en GitHub sin mi
aprobación. Si algo falla, muéstrame el error completo antes de intentar
arreglarlo.
```

Si tu CV está en inglés, cambia `-Idioma es` por `-Idioma en`.

## Qué hace OpenCode con eso

1. **Clona** este repo en `_guia` (solo para leer el esqueleto y los scripts).
2. **`arranque.ps1`** crea el workspace en `.\busqueda-laboral`:
   - copia el esqueleto (config de OpenCode, agentes, comandos, skills, scripts),
   - crea el entorno de RenderCV,
   - **adopta tu YAML**: valida que tenga la clave raíz `cv`, lo normaliza a
     contenido puro y lo deja como `rendercv/src/cv/<CANDIDATO>.es.yaml`,
   - ajusta la constante `CANDIDATO` de `tools/rendercv/renderizar.py`,
   - ejecuta la verificación.
3. **Te entrevista** para rellenar lo que solo tú sabes (credenciales, narrativa).
4. **Renderiza** y te dice dónde quedaron los PDFs.
5. **Te guía** por el resto: `/entrevista-cv`, `/buscar-vacantes`,
   `/analizar-vacante`, `/cv-vacante`, y el release `v1.0.0`.

## Cuándo NO usar este camino

- Si tu objetivo es **solo un PDF** y no quieres el agente: usa la
  [Ruta B: solo RenderCV](docs/11-ruta-rapida.md#ruta-b--solo-rendercv-sin-opencode).
  Son tres comandos.
- Si no puedes instalar Node.js: `arranque.ps1` también funciona sin OpenCode,
  pero pierdes la parte de entrevista, análisis de vacantes y tailoring guiado.

## Detalle completo

- [Ruta rápida de cero a un CV v1.0.0](docs/11-ruta-rapida.md)
- [Índice de la guía](README.md)
