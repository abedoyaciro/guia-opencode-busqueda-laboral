# 2. Configurar OpenCode

OpenCode es un cliente y un servidor en segundo plano. La configuración de
proyecto vive en el workspace; las credenciales de proveedores y las preferencias
de terminal viven fuera.

## 2.1 Dónde va cada archivo

| Archivo | Alcance | Qué se pone aquí |
|---|---|---|
| `opencode.json(c)` (raíz del workspace) | Proyecto | `mcp`, `permission`, `model`, `plugin` |
| `.opencode/opencode.json(c)` | Proyecto | Igual, pero **tiene más precedencia** que el directo |
| `~/.config/opencode/opencode.json(c)` | Todos tus proyectos | Proveedores, modelo por defecto, MCP globales |
| `~/.config/opencode/cli.json` | Solo la terminal (TUI) | Tema, atajos de teclado, input |
| `AGENTS.md` (raíz del workspace) | Proyecto | Instrucciones permanentes para el agente |
| `.opencode/agents/*.md` | Proyecto | Agentes especializados |
| `.opencode/commands/*.md` | Proyecto | Comandos `/slash` |
| `.opencode/skills/<nombre>/SKILL.md` | Proyecto | Conocimiento reusable del dominio |
| `.opencode/plugins/*.js` | Proyecto | Código que se engancha al ciclo del agente |

OpenCode busca configuración desde el directorio actual hacia arriba. Para este
workspace basta el `opencode.json` de la raíz.

## 2.2 El archivo del proyecto

`esqueleto/opencode.json` es el que usa este sistema:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "identidad": {
      "type": "local",
      "command": ["tools/.venv/Scripts/python.exe", "tools/mcp_identidad/server.py"],
      "enabled": true,
      "environment": {
        "CREDLY_USER": "<TU_USUARIO_CREDLY>",
        "SKILLSBOOST_PROFILE_URL": "<URL_DE_TU_PERFIL_PUBLICO_DE_GOOGLE_SKILLS>"
      }
    },
    "empleo": {
      "type": "local",
      "command": ["tools/.venv/Scripts/python.exe", "tools/mcp_empleo/server.py"],
      "enabled": true
    }
  },
  "permission": {
    "edit": "ask",
    "webfetch": "allow",
    "websearch": "allow",
    "bash": {
      "*": "ask",
      "gh repo list*": "allow",
      "gh api*": "allow",
      "gh auth status": "allow",
      "gh repo view*": "allow",
      "gh repo edit*": "ask",
      "gh repo clone*": "ask",
      "git status*": "allow",
      "git diff*": "allow",
      "git log*": "allow",
      "git commit*": "ask",
      "git push*": "ask",
      "python tools/*": "allow",
      "tools/.venv/Scripts/python.exe tools/*": "allow"
    },
    "skill": { "*": "allow" }
  }
}
```

Puntos que importan:

- **Rutas relativas al workspace.** `tools/.venv/Scripts/python.exe` funciona
  porque OpenCode arranca el servidor con la raíz del proyecto como directorio de
  trabajo. En Windows, las barras normales se aceptan en JSON.
- **`environment`** pasa variables al proceso del MCP. Las credenciales de
  servicios se quedan ahí, no en el código.
- **`enabled: true`** permite desactivar un servidor sin borrarlo.

### Nota V1/V2 del formato

OpenCode v2 sigue aceptando el formato heredado que usa este repo
(`mcp`, `permission`, `plugin`, `agents`/`commands` como archivos). Si prefieres
la forma nativa de v2, los equivalentes son:

| En este repo | Forma nativa v2 |
|---|---|
| `mcp` | `mcp.servers` |
| `permission` (objeto) | `permissions` (lista ordenada de reglas `action`/`resource`/`effect`) |
| `plugin` | `plugins` |
| `agents`, `commands` como archivos | Igual, o los bloques `agents`/`commands` en el JSON |

No mezcles las dos formas en el mismo archivo. Verifica en la documentación de la
versión que tengas instalada antes de migrar.

## 2.3 Permisos: proponer sí, ejecutar por su cuenta no

La idea del bloque `permission` es que el agente pueda **leer** casi todo y
**escribir o publicar** solo con tu aprobación.

| Valor | Efecto |
|---|---|
| `allow` | Se ejecuta sin preguntar |
| `ask` | Pide confirmación en el chat |
| `deny` | Se bloquea |

En `bash` las claves son patrones de glob. Ordena por especificidad: el `"*"`
final fija el comportamiento por defecto. Lo que está en `allow` aquí es
deliberadamente de solo lectura (`gh repo list`, `gh api`, `gh repo view`,
`git status/diff/log`) o idempotente (`renderizar.py`, `agregar.py`). Todo lo que
publica o reescribe (`git push`, `git commit`, `gh repo edit`, cualquier edición
de archivos) queda en `ask`.

Los agentes pueden endurecer estos permisos, nunca relajarlos. Ejemplo de
`analista-fit`, que no debe tocar archivos:

```yaml
permission:
  bash:
    "*": deny
    "tools/.venv/Scripts/python.exe tools/mercado/*": allow
```

## 2.4 Modelo y proveedores

El modelo se elige en `model` con el formato `proveedor/modelo`, o en la sesión
con `/connect`. Para un endpoint compatible con OpenAI:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "miproxy/auto",
  "provider": {
    "miproxy": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Mi proxy",
      "options": {
        "baseURL": "http://localhost:3001/v1",
        "apiKey": "{env:MI_PROXY_API_KEY}"
      },
      "models": {
        "auto": { "name": "Auto", "limit": { "context": 1048576, "output": 8192 } }
      }
    }
  }
}
```

### Modelo recomendado para esta guía

V2 incluye proveedores listos para usar: con `/connect` o `/model` eliges el
modelo sin escribir configuración. Para todo el flujo de esta guía:

```
opencode/deepseek-v4.1-flash-free
```

Es gratis, rápido y sigue bien instrucciones largas, que es lo que piden los
prompts de las skills. Para fijarlo en el proyecto, añade a `opencode.json`:

```json
{ "model": "opencode/deepseek-v4.1-flash-free" }
```

Para listar lo disponible desde la terminal: `opencode models`.

Reglas prácticas:

- Nunca escribas la API key en el archivo. Usa `{env:VARIABLE}` o
  `{file:ruta}` (OpenCode sustituye el contenido del archivo).
- `limit.context` y `limit.output` son obligatorios para que OpenCode gestione
  la compactación; si el proveedor no los declara, la sesión fallará.
- Para el trabajo de esta guía prioriza modelos con buen seguimiento de
  instrucciones y salida larga en JSON/YAML. El scoring y los umbrales están en
  las skills, así que un modelo pequeño bien guiado puede sostenerlo.
- Fija el modelo del proyecto en `opencode.json`; deja el global para lo demás.

## 2.5 Plugins

Un plugin es un módulo JavaScript que exporta funciones de hook. Este workspace
usa uno para bloquear la lectura de secretos:

```javascript
// .opencode/plugins/proteccion-secretos.js
const SECRETOS =
  /\.env(\..*)?$|\.(pem|key|p12|pfx|jks|keystore)$|id_rsa|credentials|service-account.*\.json|\.tfvars$/i

export const ProteccionSecretos = async () => ({
  "tool.execute.before": async (input, output) => {
    const ruta = output?.args?.filePath ?? output?.args?.command ?? ""
    if ((input.tool === "read" || input.tool === "bash") && SECRETOS.test(ruta)) {
      throw new Error("Bloqueado por política del workspace: posible archivo de secretos.")
    }
  },
})
```

- Los plugins en `.opencode/plugins/` se cargan solos.
- `tool.execute.before` corre antes de cada tool y puede abortarla lanzando un
  error.
- Aquí el hook es una última línea de defensa. Las reglas del prompt
  (`AGENTS.md`) y los permisos son la primera.

## 2.6 AGENTS.md: el contrato del agente

`AGENTS.md` se carga en cada sesión. Es donde van las reglas que no quieres
repetir. En este sistema define ocho invariantes: no inventar, narrativa
principal y secundaria, aprobación humana, dónde viven los datos, secretos
prohibidos, consistencia es/en, los dos venvs y la estructura de `data/`.

Escríbelo como reglas verificables ("no leer `.env`") y no como deseos ("ser
cuidadoso con los secretos").

## 2.7 Operación diaria

```powershell
opencode                       # abre la TUI en el directorio actual
opencode C:\ruta\workspace     # abre en otro directorio
opencode service status        # estado del servidor en segundo plano
opencode service restart       # si algo se queda pegado
opencode mcp list              # servidores MCP configurados
opencode models                # modelos disponibles
```

Logs, si algo no arranca:

```
~/.local/share/opencode/log/opencode.log
```

Filtra `role=server` para problemas de MCP, plugins y permisos, y `role=cli` para
el arranque de la interfaz. Con `OPENCODE_LOG_LEVEL=DEBUG` obtienes una
reproducción detallada de un solo caso.
