# 4. Scripts Python

Cuatro piezas fuera del modelo. Son deterministas: mismas entradas, mismas
salidas. Ejecútalas con el intérprete del venv correspondiente.

| Script | Interprete | Qué produce |
|---|---|---|
| `tools/github_audit/audit.py` | `tools/.venv` | `data/audit/stack_inventory.json` + `informe_github.md` |
| `tools/mercado/agregar.py` | `tools/.venv` | `data/mercado/requisitos_agregados.json` + `reporte-AAAA-MM.md` |
| `tools/rendercv/renderizar.py` | `tools/.venv` | PDFs del CV (usa el venv de RenderCV por dentro) |
| `tools/common/resolver_dns.py` | — | Librería; la importan los servidores MCP |

Regla de oro: `renderizar.py` se lanza con el **venv del agente**, pero internamente
invoca el **ejecutable de RenderCV** del venv de RenderCV. No mezcles los venvs
llamando a `rendercv` directamente.

## 4.1 Auditoría de GitHub

```powershell
tools\.venv\Scripts\python.exe tools\github_audit\audit.py --salida data\audit
tools\.venv\Scripts\python.exe tools\github_audit\audit.py --usuario otro-login --incluir-privados --excluir-forks
```

| Flag | Efecto |
|---|---|
| `--usuario` | Login a auditar. Si se omite, usa la cuenta autenticada en `gh` |
| `--salida` | Directorio de salida (por defecto `data/audit`) |
| `--incluir-privados` | Incluye repos privados |
| `--excluir-forks` | Ignora forks |
| `--incluir-archivados` | Incluye repos archivados |

Cómo obtiene los datos, sin clonar nada:

1. `gh repo list` con campos como `nameWithOwner`, `pushedAt`, `primaryLanguage`,
   `repositoryTopics`.
2. `gh api repos/<full>/git/trees/<branch>?recursive=1` para listar archivos.
3. Descarga selectiva, por `gh api .../contents/...`, de los manifiestos
   relevantes (máximo 12 por repo) y de los lenguajes por bytes.

Qué detecta y cómo:

- **Por ruta** (`PATH_RULES`): `package.json` → Node, `requirements*.txt`/
  `pyproject.toml` → Python, `Dockerfile`/`docker-compose` → Docker,
  `.devcontainer` → Devcontainers, `*.tf` → Terraform, `Chart.yaml` → Helm,
  `kustomization.yaml` → Kustomize, `ansible.cfg` → Ansible,
  `.github/workflows/*` → GitHub Actions, `Makefile` → Make, `.streamlit` → Streamlit.
- **Por contenido** de esos manifiestos: dependencias de Python (pandas,
  scikit-learn, fastapi, boto3, pytest, rendercv, playwright…), de JavaScript
  (react, next, express, vue, jest, typescript…), proveedores de Terraform
  (`provider "aws"` → AWS, `azurerm` → Azure, `google` → GCP, kubernetes, helm) y
  acciones de CI (`aws-actions/`, `azure/`, `google-github-actions/`,
  `docker/build-push-action`).
- **README**: existe o no, cuántos caracteres, y si menciona problema,
  demo/capturas, instrucciones y arquitectura. Un README de menos de 300
  caracteres o inexistente se marca como oportunidad de mejora.
- **Lenguajes**: bytes por lenguaje según la API de GitHub.

Seguridad: solo lectura vía `gh api`; nunca ejecuta código del repo; descarta
rutas que parezcan secretos (`.env*`, `*.pem`, `*.key`, `id_rsa*`,
`credentials*`, `secrets*`, `service-account*.json`, `*.tfvars`) y corta archivos
de más de 256 KB.

Salida: `repos[]` (con `stack`, `manifiestos`, `readme`, `lenguajes_bytes`,
`topics`, `ultimo_push`) y `agregado` (`skills_por_frecuencia`,
`cloud_providers`, `repos_con_iac`, `repos_con_cicd`, `repos_con_contenedores`,
`repos_sin_readme`). El detalle de cada campo está en
[08. Datos y esquemas](08-datos-y-esquemas.md).

Esto es la fuente de verdad del stack: si una tecnología no aparece aquí, ni en
las credenciales, ni en tu experiencia confirmada, no va en el CV.

## 4.2 Agregado de mercado

```powershell
tools\.venv\Scripts\python.exe tools\mercado\agregar.py
```

Lee `data/vacantes/{pendientes,aprobadas}/*.json` (las que tengan
`descripcion_md`) y cuenta **en cuántas vacantes aparece cada requisito**, no
cuántas veces aparece. Esa distinción es la que hace útil el reporte: tres
menciones dentro de una vacante no valen más que una.

La taxonomía `TAXONOMIA` es una lista de `(nombre_canónico, regex)` por
categoría: AWS, Azure, GCP, Kubernetes, OpenShift, Docker/Contenedores,
Terraform/IaC, Ansible, CI/CD, Linux, Windows Server, Redes,
Observabilidad/Monitoreo, Seguridad/IAM, SQL/BD, Python, Bash/Shell, PowerShell,
Git, APIs REST, Microservicios, Automatización, Soporte/Ticketing-ITIL, DevOps,
Inglés requerido, Español requerido y Agile/Scrum. Ajusta esa lista a tu perfil
objetivo antes de confiar en el reporte.

También extrae:

- Niveles de inglés explícitos (A1 a C2).
- Senioridad por bloques (`junior` → `mid` → `senior`), con la primera
  coincidencia ganando.
- Distribución por portal, modalidad e idioma de publicación.
- Rango salarial cuando el portal da mínimo y máximo en texto parseable.

Y calcula brechas: requisitos que aparecen en **≥20 % de las vacantes** y que no
están en tu evidencia (stack del inventario + skills de las credenciales + el
conjunto `MI_EVIDENCIA_EXTRA` del script).

Salidas:

- `data/mercado/requisitos_agregados.json` — el agregado completo, incluido
  `detalle_por_vacante`.
- `data/mercado/reporte-AAAA-MM.md` — la versión legible, un archivo por mes.

```powershell
# Ejemplo de consulta rápida al agregado
Get-Content data\mercado\requisitos_agregados.json -Raw |
  ConvertFrom-Json |
  Select-Object -ExpandProperty brechas_vs_mi_evidencia
```

Que el reporte diga `0 brechas` no significa que no tengas brechas: significa
que los requisitos frecuentes ya están cubiertos por tu evidencia registrada. Las
brechas reales suelen aparecer en los análisis por vacante
(`data/vacantes/aprobadas/<id>/analisis.md`).

## 4.3 Orquestador de RenderCV

Sustituye al `Makefile` en Windows. Envuelve el ejecutable de RenderCV con
`PYTHONUTF8=1` (necesario en consolas cp1252) y rutas absolutas, y comprueba que
el ejecutable exista antes de intentar nada.

```powershell
# 4 PDFs del CV base (es/en × harvard/engineeringresumes) en rendercv/build/preview/
tools\.venv\Scripts\python.exe tools\rendercv\renderizar.py preview

# Una variante por vacante
tools\.venv\Scripts\python.exe tools\rendercv\renderizar.py vacante --dir <carpeta> --idioma es --design harvard

# Render genérico
tools\.venv\Scripts\python.exe tools\rendercv\renderizar.py custom --cv <yaml> --design <yaml> --locale <yaml> --out <dir>

# Versión: 4 variantes con todos los artefactos + manifest
tools\.venv\Scripts\python.exe tools\rendercv\renderizar.py release --version v2.0.0
```

| Modo | Salida |
|---|---|
| `preview` | `rendercv/build/preview/{es,en}-{harvard,er}/` |
| `vacante` | `rendercv/tailored/<carpeta>/output/<CANDIDATO>-<carpeta>.pdf` |
| `custom` | Donde diga `--out`, con `--pdf` opcional para nombrar el archivo |
| `release` | `rendercv/versions/<version>/<variante>/` + `manifest.yaml` + `versions/latest.txt` |

`release` valida que la versión sea semántica (`vMAJOR.MINOR.PATCH`) y que no
exista ya, y no hace `git commit` ni `git tag`: eso queda en tus manos. El detalle
del formato de salida está en [07. RenderCV](07-rendercv.md).

La constante `CANDIDATO` al inicio de `renderizar.py` define el nombre base de
los YAML (`rendercv/src/cv/<CANDIDATO>.<idioma>.yaml`) y el prefijo de los PDFs.
En este esqueleto viene parametrizada; cámbiala por tu nombre en kebab-case.

### Por qué el nombre del archivo importa

El orquestador construye rutas a partir de `CANDIDATO`. Si renombras el YAML y no
actualizas la constante, `preview` fallará con "no existe ...". Es el error más
común al personalizar el esqueleto.

## 4.4 Resolver DNS

```python
import resolver_dns
resolver_dns.activar()
```

Fuerza IPv4 en todo el proceso, añade respaldo UDP contra 1.1.1.1 y 8.8.8.8 con
la librería estándar, y expone `ip_de(host)` para pasar una IP a Chromium con
`--host-resolver-rules`. Ningún script de este repo necesita API keys ni
dependencias externas para usarlo.

Solo está porque algunos routers fallan de forma intermitente en consultas IPv6 y
en ciertas cadenas CNAME. Si tu red es estable, no notarás la diferencia; si ves
`gaierror` en `credly.com` o `getonbrd.cl`, este módulo es lo que lo evita.

## 4.5 Convenciones para scripts nuevos

- Rutas absolutas calculadas desde `Path(__file__).resolve().parents[N]`, nunca
  relativas al directorio de trabajo.
- `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` al inicio de cada
  entrypoint, más `PYTHONUTF8=1` cuando invocas un subproceso.
- Mensajes de error a `stderr` y salida estructurada a `stdout`.
- Salidas en JSON con `ensure_ascii=False, indent=2` para que el diff en git sea
  legible.
- Nada de secretos en el código; todo por variables de entorno.
