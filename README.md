# Guía: sistema de búsqueda laboral con OpenCode + MCP + RenderCV

Documentación y plantillas para montar, desde cero, un **asesor de búsqueda de
empleo operado por un agente de IA**: busca vacantes en portales remotos, audita
tu evidencia técnica real, puntúa el fit de cada vacante, mantiene un reporte de
mercado y genera versiones personalizadas del CV en PDF.

Todo corre en local. Nada se postula automáticamente: el agente propone, tú
decides.

```
                ┌──────────────────────────────────────────────────────┐
                │                     OpenCode                         │
                │  AGENTS.md (reglas) + 4 skills + 5 agentes + 10 cmd  │
                └───────┬───────────────────────────┬──────────────────┘
                        │ tools MCP (stdio)         │ shell
        ┌───────────────┴──────────┐    ┌───────────┴──────────────────┐
        │ MCP `empleo`             │    │ tools/github_audit/audit.py  │
        │  buscar/listar/detalle/  │    │ tools/mercado/agregar.py     │
        │  marcar/agregar_manual   │    │ tools/rendercv/renderizar.py │
        │ MCP `identidad`          │    └───────────┬──────────────────┘
        │  credly/skillsboost/     │                │
        │  consolidar              │                │
        └───────────┬──────────────┘                │
                    │                               │
     ┌──────────────┴───────────────┐   ┌───────────┴─────────────────┐
     │ data/vacantes/  (ciclo de    │   │ rendercv/ (CV base +        │
     │ vida: pendientes → aprobadas │   │ variantes tailored + PDFs   │
     │ → descartadas)               │   │ versionados)                │
     │ data/audit/ data/credenciales│   └─────────────────────────────┘
     │ data/mercado/ data/perfil/   │
     └──────────────────────────────┘
```

## Quickstart

```powershell
# 1. Clonar esta guía
git clone <URL_DE_ESTE_REPO> guia-busqueda-laboral

# 2. Crear tu workspace (copia el esqueleto + crea los dos venvs)
pwsh -File guia-busqueda-laboral\scripts\instalar.ps1 -Destino C:\ruta\busqueda-laboral

# 3. Personalizar: opencode.json, AGENTS.md, CONTEXTO_CARRERA.md, tu CV
# 4. Verificar que todo está en su sitio
pwsh -File guia-busqueda-laboral\scripts\verificar.ps1 -Raiz C:\ruta\busqueda-laboral

# 5. Autenticar GitHub y arrancar el agente dentro del workspace
gh auth login
opencode C:\ruta\busqueda-laboral
```

Primera sesión útil, en orden:

```
/auditar-github                 → inventario real de tu stack desde tus repos
/sincronizar-credenciales       → Credly + Google Skills consolidados
/entrevista-cv                  → completa el CV base con un reclutador-mentor
/buscar-vacantes                → barrido en los portales
/revisar-vacantes               → apruebas o descartas, una por una
/analizar-vacante <id>          → scoring 0-100 con brechas y veredicto
/cv-vacante <id>                → variante de CV en PDF para esa vacante
/reporte-mercado                → requisitos por frecuencia en el mercado
```

## Qué hay en este repo

| Carpeta | Contenido |
|---|---|
| `docs/` | La guía, en orden de lectura: instalación → configuración → uso → personalización → problemas |
| `esqueleto/` | Workspace listo para copiar: `opencode.json`, `AGENTS.md`, `.opencode/` (agentes, comandos, skills, plugin), `tools/` (servidores MCP y scripts) y un CV de ejemplo que renderiza |
| `scripts/` | `instalar.ps1` (crea el workspace y los venvs) y `verificar.ps1` (comprueba que todo funciona) |

Los textos entre «...» y `<\...>` son placeholders para que los reemplaces.

## Índice

1. [Instalación](docs/01-instalacion.md)
2. [Configurar OpenCode](docs/02-opencode-config.md)
3. [Servidores MCP](docs/03-mcp.md)
4. [Scripts Python](docs/04-tools-python.md)
5. [Skills, agentes y comandos](docs/05-skills-agentes-comandos.md)
6. [Flujo completo de trabajo](docs/06-flujo-completo.md)
7. [RenderCV: CV y versionado](docs/07-rendercv.md)
8. [Datos y esquemas](docs/08-datos-y-esquemas.md)
9. [Personalización para tu perfil](docs/09-personalizacion.md)
10. [Problemas frecuentes](docs/10-troubleshooting.md)

## Requisitos

| Componente | Versión probada | Notas |
|---|---|---|
| Sistema | Windows 11 + PowerShell 7 | Los scripts son `.ps1`; el sistema funciona igual en macOS/Linux con ajustes de rutas |
| OpenCode | v2.0.21 | `npm install -g @opencode/cli` o el binario de la web |
| Python (agente) | 3.14.7 | Crea `tools/.venv` |
| Python (RenderCV) | 3.13.5 | Crea `rendercv/rendercv-env`. RenderCV 2.8 se probó en 3.13 |
| RenderCV | 2.8 (`rendercv[full]`) | Genera PDF/PNG/HTML/Markdown/Typst |
| Node.js | 18+ | Solo si instalas OpenCode por npm |
| GitHub CLI | reciente | `gh auth login`; lo usan la auditoría y el agente |
| `make` | opcional | Solo si usas el Makefile del CV desde Git Bash/WSL |

## Principios de diseño

- **Aprobación humana en cada paso.** Una vacante no se analiza a fondo ni
  genera CV hasta que la apruebas. Ningún cambio al CV base ni a tu GitHub
  público se aplica sin tu OK.
- **Evidencia, no adjetivos.** Cada tecnología del CV debe existir en
  `data/audit/stack_inventory.json`, en `data/credenciales/consolidado.json` o en
  tu experiencia confirmada. Lo que no se puede probar se registra como brecha.
- **Determinista donde importa.** El scoring, la agregación de mercado y el
  renderizado son scripts con reglas fijas; el modelo no inventa números.
- **Secretos fuera del repo.** Un plugin bloquea la lectura de `.env`, `*.pem`,
  `id_rsa*`, `*.tfvars`, `credentials*` y `service-account*.json`, y las
  credenciales de proveedores van por variables de entorno.
- **Datos versionados, builds no.** `data/` y los YAML del CV son fuente de
  verdad; `build/` y los venvs se ignoran.

## Estado de esta guía

Es un snapshot del sistema tal como funciona hoy (octubre de 2026), con los datos
personales sustituidos por placeholders. Las versiones exactas de las
dependencias están en `esqueleto/requirements-tools.txt` y `docs/01-instalacion.md`.
