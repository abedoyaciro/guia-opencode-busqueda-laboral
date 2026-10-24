# 3. Servidores MCP

MCP (Model Context Protocol) es el estándar por el que OpenCode expone
herramientas a un proceso externo. Cada servidor declara funciones con nombre,
parámetros y descripción; el agente las llama como cualquier otra tool.

Este sistema tiene dos servidores locales, ambos en Python y hablando `stdio`:

| Servidor | Archivo | Para qué |
|---|---|---|
| `empleo` | `tools/mcp_empleo/server.py` | Buscar, guardar, leer y mover vacantes |
| `identidad` | `tools/mcp_identidad/server.py` | Credenciales de Credly y Google Skills |

En la conversación las tools aparecen como `empleo_buscar`, `identidad_consolidar`,
etc. En la configuración del código se ven como `tools.empleo.buscar`.

## 3.1 Cómo se conecta

```json
"empleo": {
  "type": "local",
  "command": ["tools/.venv/Scripts/python.exe", "tools/mcp_empleo/server.py"],
  "enabled": true
}
```

OpenCode lanza ese comando, habla JSON-RPC por stdin/stdout y registra las tools.
El servidor imprime logs a stderr y respuestas a stdout, sin mezclarlos.

Los dos servidores hacen lo mismo al arrancar:

```python
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
import resolver_dns
resolver_dns.activar()
```

`tools/common/resolver_dns.py` fuerza resolución IPv4 y añade respaldo contra
1.1.1.1 y 8.8.8.8 por UDP. Existe porque ciertos routers fallan en consultas AAAA
y en algunas cadenas CNAME (`credly.com`, `getonbrd.cl`). Si tu red es sana,
puedes quitarlo, pero no estorba.

## 3.2 MCP `empleo`

### Tools

| Tool | Parámetros | Devuelve |
|---|---|---|
| `buscar` | `portal`, `texto`, `limite=15`, `pais="CO"`, `nivel="todos"` | JSON con `nuevas_guardadas`, `ya_conocidas`, `filtradas_por_seniority`, `errores[]` y la lista de nuevas |
| `listar` | `estado="pendientes"` | Vacantes ordenadas por recencia (publicada, luego capturada) |
| `detalle` | `vacante_id` | Descripción completa en Markdown; la descarga si no estaba y actualiza el JSON |
| `marcar` | `vacante_id`, `estado` | Mueve la vacante entre `pendientes`, `aprobadas`, `descartadas` |
| `agregar_manual` | `url`, `titulo`, `empresa`, `texto`, `notas` | Ingresa una vacante encontrada por fuera de los portales |

`portal` acepta `getonboard`, `remotive`, `remoteok`, `wwr`, `linkedin`,
`greenhouse` o `todos`.

### Portales y adaptadores

Cada portal es un módulo en `tools/mcp_empleo/adapters/`:

| Portal | Fuente | Filtro de región | Limitaciones conocidas |
|---|---|---|---|
| GetOnBoard | API JSON pública | `pais: "CO"` nativo | Es LatAm-wide; la empresa a veces solo aparece en la página (SPA), así que el detalle puede venir vacío |
| Remotive | API JSON pública | región en texto | Búsqueda en inglés; revisa `candidate_required_location` |
| RemoteOK | API pública | worldwide | Solo devuelve ~100 ofertas recientes |
| We Work Remotely | RSS (2 categorías: devops-sysadmin y customer-support) | región en la descripción | Las fechas vienen en RFC 2822 y se normalizan |
| LinkedIn | Vista pública *guest*, sin sesión | `location` por país (`CO` → Colombia) | No oficial. Máximo 2 peticiones por búsqueda, retardo aleatorio de 1,5-3,5 s y **cooldown de 10 minutos tras un 429** |
| Greenhouse | API pública por board | worldwide normalmente | Se usa para ingesta manual de empresas; el board `canonical` está mapeado a "Canonical (Ubuntu)" |

Sobre LinkedIn: el adaptador se comporta como un invitado, no como un usuario
autenticado. Está calibrado para lecturas esporádicas. Si lo machacas, LinkedIn
bloquea la IP y el cooldown de 10 minutos se queda corto.

Canonical publica en Greenhouse y también en `canonical.com/careers/<id>`.
`agregar_manual` detecta esa URL, la reescribe a la URL canónica de Greenhouse y
baja la descripción desde ahí.

### Contrato de un adaptador

```python
def buscar(texto: str, limite: int = 15, pais: str | None = "CO") -> list[dict]
def detalle(url: str) -> str
```

Ambos devuelven datos ya normalizados por `_comun.normalizar()`. El `buscar`
nunca lanza por una vacante malformada: salta el registro.

`_comun.normalizar()` produce la vacante estándar:

| Campo | Cómo se calcula |
|---|---|
| `id` | `"<portal>-" + sha1(url)[:8]` → deduplicación estable por URL |
| `titulo`, `empresa`, `url`, `ubicacion` | Recortados a 200/120/160 caracteres |
| `modalidad` | Detecta remoto/híbrido/presencial en modalidad, ubicación o URL |
| `region_hint` | Detecta colombia, latam, mexico, espana o mundial |
| `salario` | `{texto, min, max, moneda}` (los portales solo dan texto) |
| `publicada` | Normaliza ISO, RFC 2822 y epoch |
| `capturada` | Marca de tiempo en UTC |
| `resumen` | Primeros 400 caracteres del texto plano |
| `descripcion_md` | HTML convertido a texto plano, ya en la respuesta de búsqueda |
| `estado` | `"pendiente"` |

### Filtro de seniority

Con `nivel: "junior"` el servidor descarta antes de guardar, y reporta cuántas
descartó en `filtradas_por_seniority`. Dos expresiones regulares:

- En el título: `senior|sr|ssr|lead|líder|principal|staff|manager|gerente|jefe|architect|arquitecto|head|director|expert|vp|chief|consultor|consultant|coordinador|technical account manager`
- En la descripción: `5+/6+/7+/8+/10+ years|años|yrs`

Es un filtro por señales, no por seniority declarada. Revisa siempre los
resultados: una vacante junior puede usar "lead" en otro sentido, y una senior
puede no decirlo en el texto.

### Almacenamiento

```
data/vacantes/pendientes/<id>.json     ← lo que entra
data/vacantes/aprobadas/<id>.json      ← lo que aceptas
data/vacantes/descartadas/<id>.json    ← lo que rechazas
```

`marcar` **mueve el archivo** entre carpetas y actualiza `estado`. La dedupe es
por URL: si un portal vuelve a devolver algo ya guardado, se cuenta en
`ya_conocidas` y no se duplica. Puedes cambiar la raíz con la variable de entorno
`EMPLEO_DATA_DIR`.

## 3.3 MCP `identidad`

### Tools

| Tool | Qué hace | Salida |
|---|---|---|
| `credly_sincronizar` | Descarga todas las insignias públicas del usuario | `data/credenciales/credly.json` |
| `skillsboost_sincronizar` | Scrapea el perfil público de Google Skills con Playwright | `data/credenciales/skillsboost.json` |
| `consolidar` | Fusiona ambos archivos y deduplica por nombre | `data/credenciales/consolidado.json` |

Configuración por variables de entorno, definidas en `opencode.json`:

```json
"identidad": {
  "type": "local",
  "command": ["tools/.venv/Scripts/python.exe", "tools/mcp_identidad/server.py"],
  "enabled": true,
  "environment": {
    "CREDLY_USER": "<TU_USUARIO_CREDLY>",
    "SKILLSBOOST_PROFILE_URL": "<URL_DE_TU_PERFIL_PUBLICO_DE_GOOGLE_SKILLS>"
  }
}
```

Las dos variables son obligatorias: si faltan, la tool lanza un error con el
nombre de la variable que falta, en lugar de fallar en silencio.

Detalles:

- **Credly** usa la API pública `credly.com/users/<usuario>/badges.json`,
  paginando de 100 en 100 hasta 10 páginas. Necesita que tu perfil sea público.
- **Google Skills** abre el perfil con Playwright en modo headless, espera
  `networkidle`, y lee los elementos `.profile-badge`. Si el scraping devuelve 0
  insignias, revisa el selector antes de culpar a la red.
- **`consolidar`** deduplica por nombre en minúsculas y sin caracteres no
  alfanuméricos, no por URL. Así un badge que está en Credly y en Google Skills
  queda como una sola credencial con `fuentes: ["credly", "skillsboost"]`.

Nota: `IDENTIDAD_DATA_DIR` es relativo, mientras que el servidor de `empleo`
resuelve su ruta de forma absoluta. En la práctica funciona porque OpenCode
arranca el proceso en la raíz del workspace. Si lanzas el servidor a mano desde
otro directorio, define `IDENTIDAD_DATA_DIR` explícitamente.

## 3.4 Probar los servidores

Primero, que OpenCode los vea:

```powershell
opencode mcp list
```

Luego, una prueba directa de los adaptadores con el intérprete del venv (sin
pasar por MCP):

```powershell
tools\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, 'tools/mcp_empleo'); from adapters import REGISTRO; r = REGISTRO['remotive'].buscar('support', limite=3); print(len(r), r[0]['titulo'] if r else '')"
```

Y para `identidad`, ejecuta `/sincronizar-credenciales` dentro de OpenCode: el
comando llama a las tres tools en orden y resume el resultado.

## 3.5 Añadir un portal nuevo

1. Crea `tools/mcp_empleo/adapters/<portal>.py` con `buscar(texto, limite, pais)`
   y `detalle(url)`.
2. Normaliza cada registro con `_comun.normalizar(portal=..., url=..., ...)`. No
   devuelvas diccionarios a mano: el `id`, la dedupe y `region_hint` dependen de
   esa función.
3. Regístralo en `tools/mcp_empleo/adapters/__init__.py`:

```python
REGISTRO = {
    "getonboard": getonboard,
    "remotive": remotive,
    "remoteok": remoteok,
    "wwr": weworkremotely,
    "linkedin": linkedin,
    "greenhouse": greenhouse,
    "miportal": miportal,   # ← nuevo
}
```

4. Reinicia el servidor MCP (`opencode service restart`) y prueba con
   `empleo_buscar(portal="miportal", ...)`.
5. Añade el portal a la skill `mercado-laboral` para que el scout lo use.

## 3.6 Límites que no conviene cruzar

- **Nada de postular automáticamente.** No hay tool para enviar aplicaciones, y
  es a propósito: el sistema analiza y prepara el CV.
- **Respeta los límites de cada portal.** El adaptador de LinkedIn es defensivo
  porque es la vista guest; los demás usan APIs públicas con sus propios límites.
- **Un fallo de un portal no tumba la búsqueda.** `buscar` captura la excepción,
  la agrega a `errores[]` y sigue con los demás. Lee ese campo antes de concluir
  que "no hay vacantes".
- **Sin sesión, sin cookies.** Ningún adaptador guarda credenciales de portales.
