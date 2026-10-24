# 1. Instalación

Objetivo: tener el workspace creado, con los dos entornos virtuales y las
herramientas externas autenticadas. Tiempo estimado: 15-25 minutos (la mayor
parte es descargar Chromium y RenderCV).

## 1.1 Herramientas del sistema

Instala una sola vez. Si un identificador de `winget` no existe en tu catálogo,
búscalo antes de instalar en lugar de adivinar:

```powershell
winget search python
winget search nodejs
winget search github
```

```powershell
# GitHub CLI (lo usan la auditoría y el agente)
winget install --id GitHub.cli

# Python 3.13 (sirve para los dos entornos virtuales)
winget install --id Python.Python.3.13

# Node.js LTS (solo si instalas OpenCode por npm)
winget install --id OpenJS.NodeJS.LTS

# Git
winget install --id Git.Git

# PowerShell 7 (los scripts de este repo lo requieren)
winget install --id Microsoft.PowerShell
```

Verifica que quedaron en el PATH:

```powershell
python --version
gh --version
pwsh --version
```

### OpenCode

En Windows no hay paquetes gestionados por el sistema. Dos vías válidas:

```powershell
# Opción A: npm (requiere Node.js 18+)
npm install -g @opencode/cli

# Opción B: binario standalone x64
# https://opencode.ai/update/api/latest/cli/opencode/opencode-windows-x64.zip
# Descomprime y añade la carpeta al PATH.
```

Comprueba:

```powershell
opencode --version
```

### Git

```powershell
winget install --id Git.Git
```

`make` es opcional y solo si vas a usar el `Makefile` del CV desde Git Bash o
WSL. El flujo recomendado en Windows no lo necesita: el orquestador
`tools/rendercv/renderizar.py` hace lo mismo.## 1.2 Crear el workspace

```powershell
git clone <URL_DE_ESTE_REPO> guia-busqueda-laboral
pwsh -File guia-busqueda-laboral\scripts\instalar.ps1 -Destino C:\ruta\busqueda-laboral
```

`instalar.ps1` hace tres cosas:

1. Copia `esqueleto/` al destino (incluidos `AGENTS.md`, `.opencode/` y `tools/`).
2. Crea `tools/.venv` e instala `requirements-tools.txt` + Chromium de Playwright.
3. Crea `rendercv/rendercv-env` e instala `rendercv[full]==2.8`.

Si tu `python` por defecto no es compatible con RenderCV 2.8, indícalo:

```powershell
pwsh -File guia-busqueda-laboral\scripts\instalar.ps1 `
  -Destino C:\ruta\busqueda-laboral `
  -PythonTools "py -3.13" `
  -PythonRenderCv "py -3.13"
```

Con `-SaltarVenvs` solo se copian los archivos, útil si quieres montar los
entornos a mano.

### Montaje manual (referencia)

```powershell
cd C:\ruta\busqueda-laboral

# Entorno del agente
python -m venv tools\.venv
tools\.venv\Scripts\python.exe -m pip install -r requirements-tools.txt
tools\.venv\Scripts\python.exe -m playwright install chromium

# Entorno de RenderCV
python -m venv rendercv\rendercv-env
rendercv\rendercv-env\Scripts\python.exe -m pip install "rendercv[full]==2.8"
```

Versiones verificadas de las dependencias del agente:

```
mcp==2.1.1
playwright==1.62.0
requests>=2.32,<3
PyYAML>=6.0,<7
pydantic>=2.9,<3
```

`mcp` es la librería oficial del protocolo. Los servidores de este sistema usan
el estilo `MCPServer` de `mcp` 2.x:

```python
from mcp.server.mcpserver import MCPServer
```

Si el import falla, revisa la versión de `mcp` antes de tocar el código.

## 1.3 Autenticar GitHub

```powershell
gh auth login
gh auth status
```

La auditoría usa `gh repo list` y `gh api` sobre **tu** cuenta. Si no la
autenticas, `/auditar-github` falla.

## 1.4 Configurar el workspace

Dos archivos y una carpeta de datos:

1. **`opencode.json`** — cambia `CREDLY_USER` y `SKILLSBOOST_PROFILE_URL`
   (bloque `mcp.identidad.environment`). Detalle en
   [02. Configurar OpenCode](02-opencode-config.md).
2. **`AGENTS.md`** y **`rendercv/CONTEXTO_CARRERA.md`** — reemplaza los
   placeholders con tu narrativa y tus hechos. Detalle en
   [09. Personalización](09-personalizacion.md).
3. **`rendercv/src/cv/`** — renombra `nombre-apellido.es.yaml` y `.en.yaml` a
   `<tu-nombre>.es.yaml` / `.en.yaml` y ajusta la constante `CANDIDATO` en
   `tools/rendercv/renderizar.py` al mismo nombre base.

## 1.5 Verificar

```powershell
pwsh -File guia-busqueda-laboral\scripts\verificar.ps1 -Raiz C:\ruta\busqueda-laboral
```

Revisa archivos, JSON/YAML, los dos entornos, RenderCV, OpenCode, `gh` y
placeholders sin reemplazar. Si sale `0 fallo(s)`, estás listo:

```powershell
opencode C:\ruta\busqueda-laboral
```

### Primera prueba de humo

Dentro de OpenCode, confirma que los MCP responden y que el CV renderiza:

```
Lista las herramientas MCP disponibles.
```

```
tools/.venv/Scripts/python.exe tools/rendercv/renderizar.py preview
```

El segundo comando (o pídeselo al agente) debe dejar 4 PDFs en
`rendercv/build/preview/`.
