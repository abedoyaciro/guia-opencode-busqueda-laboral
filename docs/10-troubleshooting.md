# 10. Problemas frecuentes

## Diagnóstico en dos pasos

```powershell
# 1. Estado general del workspace
pwsh -File guia-busqueda-laboral\scripts\verificar.ps1 -Raiz C:\ruta\busqueda-laboral

# 2. Log de OpenCode
Get-Content "$env:USERPROFILE\.local\share\opencode\log\opencode.log" -Tail 80
```

La verificación cubre archivos, JSON/YAML, venvs, RenderCV, OpenCode, `gh` y
placeholders. Si todo sale `[OK]` y el problema sigue, es de configuración de
OpenCode o de red, no del esqueleto.

## OpenCode

| Síntoma | Causa probable | Arreglo |
|---|---|---|
| `opencode: command not found` | No está en el PATH | Reinstala con npm o añade la carpeta del binario al PATH; abre una consola nueva |
| `opencode --version` dice `1.x` | Lo instalaste con `winget` (`SST.opencode`) o con la URL `/install`, que son V1 | Desinstala (`npm uninstall -g opencode-ai`) e instala `npm install -g @opencode/cli` |
| Los comandos `/...` no aparecen | No arrancaste en la raíz del workspace | `opencode C:\ruta\busqueda-laboral`; los comandos se leen de `.opencode/commands/` |
| El agente ignora las reglas | `AGENTS.md` fuera de la raíz | Debe estar en la raíz del proyecto que abres |
| Cambiaste `opencode.json` y no toma efecto | Config en caché | `opencode service restart` |
| Un plugin rompe el arranque | Error de sintaxis JS | Mira el log con `role=server`; comenta el plugin y aísla |
| El modelo no responde o la sesión muere | `limit.context`/`limit.output` faltantes en el proveedor | Declara ambos en la config del proveedor |
| Todo pide permiso | El patrón glob no coincide | Revisa el orden: el `\"*\"` debe ir primero para actuar de base |

Si trabajas sobre un modelo con ventana chica, las skills son lo primero que se
recorta al compactar. Sesiones largas de búsqueda + análisis es mejor partirlas.

## MCP no aparece o falla

```powershell
opencode mcp list
```

| Síntoma | Causa | Arreglo |
|---|---|---|
| El servidor no aparece | Error en el JSON (`opencode.json` no parsea) | Valida el JSON; el error de sintaxis suele estar en la coma antes de `}` |
| Aparece pero con error | El comando del MCP no arranca | Ejecuta el comando a mano: `tools\.venv\Scripts\python.exe tools\mcp_empleo\server.py` |
| `ModuleNotFoundError: mcp` | Falta instalar dependencias o usas el Python equivocado | `tools\.venv\Scripts\python.exe -m pip install -r requirements-tools.txt` |
| `ModuleNotFoundError: adapters` | Lanzaste el servidor desde otro directorio | OpenCode lo lanza desde la raíz; si lo pruebas a mano, `cd` a la raíz primero |
| Las tools usan datos de otro lado | `EMPLEO_DATA_DIR`/`IDENTIDAD_DATA_DIR` definidos en tu shell | Quítalos del entorno o apunta a la ruta correcta |

Un servidor que imprime `print()` a stdout rompe el protocolo JSON-RPC. Los
servidores de este repo escriben logs a `stderr` por esa razón: si añades código,
haz lo mismo.

## Búsqueda de vacantes

| Síntoma | Causa | Arreglo |
|---|---|---|
| `nuevas_guardadas: 0` y todo en `ya_conocidas` | Ya las tenías guardadas | Normal; mira `listar` con otro estado |
| `nuevas_guardadas: 0` y `filtradas_por_seniority` alto | Los portales devuelven senior primero | Cambia el vocabulario de búsqueda; abre `nivel: todos` para inspeccionar |
| `errores[]` con un portal | Ese portal cambió su API o está caído | Lee el mensaje; los demás portales siguen funcionando |
| LinkedIn devuelve 429 | Superaste el ritmo de la vista guest | Espera; el cooldown interno es de 10 minutos, pero la IP puede tardar más |
| Fechas raras en `publicada` | Zona horaria del portal | Es informativo; el orden en `listar` usa la fecha normalizada |
| Un portal devuelve empresas vacías | El listado no trae la empresa (SPA) | Ejecuta `detalle` sobre el `id`; a veces aparece en la descripción |

`buscar` con `portal: "todos"` no falla entero por un portal caído: por eso el
resultado trae `errores[]`. Léelo antes de concluir que no hay mercado.

## Credenciales

| Síntoma | Causa | Arreglo |
|---|---|---|
| `Falta la variable de entorno CREDLY_USER` | No configuraste `opencode.json` | Añádela en `mcp.identidad.environment` y reinicia el servicio |
| Credly devuelve 404 | Perfil privado o usuario mal escrito | Pon tu perfil público y revisa el slug exacto de la URL |
| Credly devuelve menos badges de los esperados | Paginación o badges ocultas | Solo se leen las públicas; las ocultas no se sincronizan |
| Google Skills devuelve 0 | Selector cambiado o perfil no público | Revisa `.profile-badge` contra el HTML actual |
| Playwright falla al abrir el navegador | Chromium no instalado | `tools\.venv\Scripts\python.exe -m playwright install chromium` |
| El consolidado duplica insignias | El mismo badge con nombres distintos en cada fuente | Es esperado sin homogeneizar nombres; `consolidar` deduplica por nombre, no por contenido |

## Auditoría de GitHub

| Síntoma | Causa | Arreglo |
|---|---|---|
| `gh auth status` falla | Sin sesión | `gh auth login` |
| Repos privados no aparecen | Falta el scope | `gh auth refresh -s repo` |
| `API rate limit exceeded` | Demasiadas llamadas por hora | Espera; el token autenticado tiene más cuota que el anónimo |
| Un repo sale `null` en lenguajes | Repo vacío o sin commits | Normal; se registra sin ese dato |
| `error: no such file` en manifiestos | El repo cambió entre el listado y la descarga | Reintenta; es una condición de carrera |
| El conteo de skills no cuadra con tu CV | El CV declaraba más de lo que los repos muestran | Ese es el hallazgo, no el fallo: corrige el CV |

## RenderCV

El detalle está en [07. RenderCV § 7.8](07-rendercv.md#78-errores-frecuentes). Los
dos más comunes aquí:

- **`no existe rendercv/src/cv/<X>.yaml`** → renombraste el YAML y no actualizaste
  `CANDIDATO`.
- **`no existe .../rendercv.exe`** → falta el venv de RenderCV. Revisa
  [01. Instalación](01-instalacion.md).

Consejo de diagnóstico: reproduce el fallo con

```powershell
tools\.venv\Scripts\python.exe tools\rendercv\renderizar.py custom --cv rendercv\src\cv\<CANDIDATO>.es.yaml --design rendercv\src\design\harvard.yaml --locale rendercv\src\locale\es.yaml --out rendercv\build\debug
```

El error real de Typst aparece en `stderr` con las últimas 1500 líneas de salida.

## Reporte de mercado

| Síntoma | Causa | Arreglo |
|---|---|---|
| `No hay vacantes con descripción` | Ninguna vacante tiene `descripcion_md` | Ejecuta `/buscar-vacantes`; si el portal no da descripción, usa `detalle` |
| `vacantes_analizadas` no sube | Solo se leen `pendientes` y `aprobadas` | Es intencional: las descartadas no cuentan para el mercado objetivo |
| `0 brechas` con vacantes claras | Todo cubierto por tu evidencia o `MI_EVIDENCIA_EXTRA` | Revisa que los canónicos de `MI_EVIDENCIA_EXTRA` coincidan con `TAXONOMIA` |
| Frecuencias altas pero irrelevantes | La taxonomía captura de más | Ajusta las regex (ver [09 § 9.4](09-personalizacion.md#94-adaptar-la-taxonomía-de-requisitos)) |
| El reporte no cambia entre meses | Poca búsqueda nueva o taxonomía corta | Añade vocabulario y busca de nuevo |

## Red y DNS

Si ves `gaierror`, `Temporary failure in name resolution` o timeouts al resolver
`credly.com` o `getonbrd.cl`, es la red, no el código. Los dos servidores MCP ya
activan `tools/common/resolver_dns.py` al arrancar (IPv4 forzado + respaldo
1.1.1.1/8.8.8.8 por UDP). Si aun así falla:

- Prueba con otra red (el problema suele ser el router).
- Comprueba que puedas abrir el dominio en el navegador.
- Si usas VPN, verifica que permita UDP 53 hacia resolvers públicos.

## Windows y codificación

| Síntoma | Causa | Arreglo |
|---|---|---|
| Acentos rotos en la consola (`Ã©`) | Console cp1252 | `[Console]::OutputEncoding = [Text.Encoding]::UTF8` o usa Windows Terminal |
| `UnicodeEncodeError` en Python | Salida estándar sin UTF-8 | El orquestador fija `PYTHONUTF8=1`; hazlo igual en scripts nuevos |
| `UnicodeEncodeError: 'charmap' codec can't encode character '\u2713'` al usar `rendercv new` o `rendercv render` | Consola cp1252: la CLI imprime un `✓` | `$env:PYTHONUTF8='1'`. Puede salir **después** de generar los archivos: comprueba la carpeta antes de repetir |
| Un YAML con tildes no parsea | BOM o codificación distinta | Guarda como UTF-8 sin BOM |
| `pwsh` no encuentra el script | Estás en otra carpeta | Usa ruta absoluta: `pwsh -File C:\...\scripts\verificar.ps1` |

## Git y estructura

El workspace tiene `rendercv/` como repositorio anidado. El repo de la guía (este)
es distinto de tu workspace. Para evitar que un `git add .` arrastre cosas que no
quieres:

- En el repo del workspace, ignora la carpeta de esta guía:
  `guia-opencode-busqueda-laboral/`.
- No inicialices git dentro del esqueleto copiado sin querer queriendo: si copias
  el esqueleto con robocopy no se copia ningún `.git`, así que arrancas limpio.
- Los releases del CV no se commitean solos: `renderizar.py release` no toca git.

## Cuándo pedir ayuda al agente

Dentro de OpenCode, en vez de adivinar:

```
Ejecuta el diagnóstico: revisa el log con role=server, prueba `opencode mcp list`
y muéstrame el error completo del MCP que falla.
```

El agente tiene los mismos permisos de lectura que tú, y el log suele decir en una
línea lo que un `[FALTA]` genérico no dice.
