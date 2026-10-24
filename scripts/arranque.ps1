#Requires -Version 7.0
<#
.SYNOPSIS
    Monta el workspace completo desde cero y adopta tu CV en YAML, en un paso.

.DESCRIPTION
    Pensado para ejecutarse DENTRO del repo de la guía ya clonado. Hace:

      1. Llama a instalar.ps1 (copia el esqueleto y crea los entornos virtuales).
      2. Si le pasas -PlantillaCv, convierte TU YAML (todo-en-uno o solo `cv:`)
         a contenido puro y lo deja como
         rendercv/src/cv/<CANDIDATO>.<idioma>.yaml
      3. Ajusta la constante CANDIDATO de tools/rendercv/renderizar.py.
      4. Ejecuta verificar.ps1 y te dice los siguientes pasos.

    No toca nada fuera de -Destino y no publica en GitHub.

.PARAMETER Destino
    Carpeta donde se crea el workspace. Debe no existir o estar vacía.

.PARAMETER PlantillaCv
    Ruta a tu archivo YAML de CV. Vale tanto un YAML todo-en-uno
    (cv + design + locale + settings, el de `rendercv new`) como uno que solo
    tenga `cv:`.

.PARAMETER Idioma
    Idioma de tu plantilla: es (por defecto) o en.

.PARAMETER Candidato
    Nombre base en kebab-case para los archivos del CV. Si no lo indicas se
    deriva del nombre de la plantilla (ej: "Mi_CV.es.yaml" -> "mi-cv").

.PARAMETER Minimo
    Modo CV: crea solo el entorno de RenderCV (sin tools/.venv ni Chromium de
    Playwright) y deja opencode.json sin servidores MCP. Suficiente para
    generar el CV; más liviano y rápido.

.PARAMETER SaltarVenvs
    Solo copia el esqueleto y adopta la plantilla, sin crear entornos.

.EXAMPLE
    pwsh -File scripts/arranque.ps1 -Destino C:\cv\busqueda-laboral -PlantillaCv C:\cv\mi-cv.yaml -Idioma es

.EXAMPLE
    pwsh -File scripts/arranque.ps1 -Destino .\busqueda-laboral -PlantillaCv .\cv.yaml -Minimo
#>
[CmdletBinding()]
param(
    [string]$Destino = (Join-Path (Get-Location) 'busqueda-laboral'),
    [string]$PlantillaCv,
    [ValidateSet('es', 'en')][string]$Idioma = 'es',
    [string]$Candidato,
    [string]$PythonTools = 'python',
    [string]$PythonRenderCv = 'python',
    [switch]$Minimo,
    [switch]$SaltarVenvs
)

$ErrorActionPreference = 'Stop'
$scripts = $PSScriptRoot

function Convertir-Slug {
    param([string]$Texto)
    $t = $Texto.Normalize([Text.NormalizationForm]::FormD)
    $t = -join ($t.ToCharArray() | Where-Object {
        [Globalization.CharUnicodeInfo]::GetUnicodeCategory($_) -ne [Globalization.UnicodeCategory]::NonSpacingMark
    })
    $t = $t.ToLowerInvariant() -replace '[^a-z0-9]+', '-'
    return $t.Trim('-')
}

function Get-PythonParaYaml {
    param([string]$Destino)
    foreach ($rel in @('tools\.venv\Scripts\python.exe', 'rendercv\rendercv-env\Scripts\python.exe')) {
        $p = Join-Path $Destino $rel
        if (Test-Path $p) { return $p }
    }
    return $null
}

if ($PlantillaCv -and -not (Test-Path $PlantillaCv)) {
    throw "No existe la plantilla de CV: $PlantillaCv"
}

Write-Host "`n== 1/4 Creando el workspace ==" -ForegroundColor Cyan
$llamada = @{ Destino = $Destino; PythonTools = $PythonTools; PythonRenderCv = $PythonRenderCv }
if ($Minimo) { $llamada['SoloRendercv'] = $true }
if ($SaltarVenvs) { $llamada['SaltarVenvs'] = $true }
& (Join-Path $scripts 'instalar.ps1') @llamada

Write-Host "`n== 2/4 Adoptando tu plantilla de CV ==" -ForegroundColor Cyan
if (-not $PlantillaCv) {
    Write-Host "Sin -PlantillaCv: queda el CV de ejemplo. Edita rendercv/src/cv/*.yaml." -ForegroundColor Yellow
} else {
    if (-not $Candidato) {
        $base = [IO.Path]::GetFileNameWithoutExtension($PlantillaCv)
        $base = $base -replace '\.(es|en)$', ''
        $Candidato = Convertir-Slug $base
    }
    if (-not $Candidato) { throw 'No pude derivar el nombre base del CV. Usa -Candidato "nombre-apellido".' }

    $py = Get-PythonParaYaml -Destino $Destino
    if (-not $py) { $py = 'python' }

    $helper = Join-Path $env:TEMP 'arranque_cv_convert.py'
    @'
import pathlib, sys

def load(ruta):
    texto = pathlib.Path(ruta).read_text(encoding="utf-8")
    try:
        import yaml
        return yaml.safe_load(texto)
    except ImportError:
        from ruamel.yaml import YAML
        return YAML(typ="safe").load(texto)

def dump(obj, ruta):
    try:
        import yaml
        pathlib.Path(ruta).write_text(
            yaml.dump(obj, allow_unicode=True, sort_keys=False, width=1000),
            encoding="utf-8")
        return "PyYAML"
    except ImportError:
        from io import StringIO
        from ruamel.yaml import YAML
        y = YAML()
        y.default_flow_style = False
        y.width = 1000
        buf = StringIO()
        y.dump(obj, buf)
        pathlib.Path(ruta).write_text(buf.getvalue(), encoding="utf-8")
        return "ruamel.yaml"

origen, destino = sys.argv[1], sys.argv[2]
raw = load(origen)
if not isinstance(raw, dict) or "cv" not in raw:
    print("ERROR: el YAML no tiene la clave raiz 'cv'", file=sys.stderr)
    sys.exit(2)
descartadas = [k for k in raw if k != "cv"]
lib = dump({"cv": raw["cv"]}, destino)
print(f"conversor: {lib} | claves descartadas: {', '.join(descartadas) if descartadas else 'ninguna'}")
'@ | Set-Content -Path $helper -Encoding utf8

    $destinoCv = Join-Path $Destino "rendercv\src\cv\$Candidato.$Idioma.yaml"
    & $py $helper $PlantillaCv $destinoCv
    if ($LASTEXITCODE -ne 0) { throw 'No pude convertir la plantilla. Revisa que sea un YAML válido con la clave raíz "cv".' }

    $otro = if ($Idioma -eq 'es') { 'en' } else { 'es' }
    Write-Host "CV adoptado: rendercv\src\cv\$Candidato.$Idioma.yaml" -ForegroundColor Green
    Write-Host "Nota: el YAML se normaliza (se pierden comentarios) y se usa el diseño/locale del esqueleto." -ForegroundColor DarkGray
    # El CV de ejemplo deja de tener sentido cuando ya adoptamos el tuyo: si se
    # queda, aparece mezclado en preview y en el release.
    foreach ($otroIdioma in @('es', 'en')) {
        $ejemplo = Join-Path $Destino "rendercv\src\cv\nombre-apellido.$otroIdioma.yaml"
        if (Test-Path $ejemplo) {
            Remove-Item $ejemplo -Force
            Write-Host "Quité el CV de ejemplo 'nombre-apellido.$otroIdioma.yaml' (ya tienes el tuyo)." -ForegroundColor DarkGray
        }
    }
    if (-not (Test-Path (Join-Path $Destino "rendercv\src\cv\$Candidato.$otro.yaml"))) {
        Write-Host "Solo tienes la versión '$Idioma'. Si quieres la '$otro' para postular en ese idioma, créala a partir de la tuya." -ForegroundColor Yellow
    }

    Write-Host "`n== 3/4 Ajustando CANDIDATO en renderizar.py ==" -ForegroundColor Cyan
    $rutaRender = Join-Path $Destino 'tools\rendercv\renderizar.py'
    $txt = Get-Content $rutaRender -Raw
    $txt = [regex]::Replace($txt, '(?m)^CANDIDATO = ".*"$', "CANDIDATO = `"$Candidato`"")
    Set-Content -Path $rutaRender -Value $txt -NoNewline -Encoding utf8
    Write-Host "CANDIDATO = `"$Candidato`"" -ForegroundColor Green
}

if ($Minimo) {
    Write-Host "`nModo mínimo: quitando los servidores MCP de opencode.json..." -ForegroundColor Cyan
    $cfg = Join-Path $Destino 'opencode.json'
    if (Test-Path $cfg) {
        $obj = Get-Content $cfg -Raw | ConvertFrom-Json
        if ($obj.PSObject.Properties.Name -contains 'mcp') {
            $obj.PSObject.Properties.Remove('mcp')
            $obj | ConvertTo-Json -Depth 20 | Set-Content $cfg -Encoding utf8
            Write-Host "Listo. Para el agente completo (vacantes + credenciales), más tarde:" -ForegroundColor DarkGray
            Write-Host "  $Destino\tools\.venv  ->  python -m venv y pip install -r requirements-tools.txt; playwright install chromium" -ForegroundColor DarkGray
        }
    }
}

Write-Host "`n== 4/4 Verificando ==" -ForegroundColor Cyan
& (Join-Path $scripts 'verificar.ps1') -Raiz $Destino
$verificacion = $LASTEXITCODE

$pyCv = if ($Minimo -or $SaltarVenvs) {
    'rendercv\rendercv-env\Scripts\python.exe'
} else {
    'tools\.venv\Scripts\python.exe'
}
Write-Host @"

Siguientes pasos
  1. cd "$Destino"
  2. Renderiza el CV:  $pyCv tools\rendercv\renderizar.py preview
  3. Revisa los PDFs en rendercv\build\preview\
  4. Publica tu v1.0.0: $pyCv tools\rendercv\renderizar.py release --version v1.0.0
  5. Abre OpenCode:    opencode "$Destino"
"@ -ForegroundColor Green

if ($verificacion -ne 0) {
    Write-Host "La verificación reportó fallos. Revisa arriba: casi siempre son los placeholders de opencode.json/AGENTS.md." -ForegroundColor Yellow
}
