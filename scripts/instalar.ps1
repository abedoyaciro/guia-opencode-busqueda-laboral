#Requires -Version 7.0
<#
.SYNOPSIS
    Crea un workspace de búsqueda laboral a partir del esqueleto de esta guía.

.DESCRIPTION
    Copia esqueleto/ al destino y prepara los dos entornos virtuales:
      - tools/.venv        -> servidores MCP y scripts del agente
      - rendercv/rendercv-env -> RenderCV 2.8 (genera los PDFs)

    No toca tu configuración global de OpenCode ni pide credenciales.

.PARAMETER Destino
    Carpeta donde se crea el workspace. Debe no existir o estar vacía.

.PARAMETER PythonTools
    Intérprete para tools/.venv. Por defecto "python" del PATH.

.PARAMETER PythonRenderCv
    Intérprete para rendercv/rendercv-env. Por defecto "python".
    RenderCV 2.8 funciona con Python 3.12/3.13; si tu "python" es 3.14 y falla,
    pasa -PythonRenderCv "py -3.13".

.PARAMETER SaltarVenvs
    Solo copia el esqueleto, sin crear entornos ni instalar dependencias.

.EXAMPLE
    pwsh -File scripts/instalar.ps1 -Destino C:\Users\yo\busqueda-laboral

.EXAMPLE
    pwsh -File scripts/instalar.ps1 -Destino .\mi-busqueda -PythonRenderCv "py -3.13"
#>
[CmdletBinding()]
param(
    [string]$Destino = (Join-Path (Get-Location) 'busqueda-laboral'),
    [string]$PythonTools = 'python',
    [string]$PythonRenderCv = 'python',
    [switch]$SaltarVenvs
)

$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
$origen = Join-Path $raiz 'esqueleto'

function New-Venv {
    param([string]$Python, [string]$Ruta)
    # Permite "python" o "py -3.13"
    $partes = $Python -split '\s+', 2
    if ($partes.Count -eq 2) { & $partes[0] $partes[1] -m venv $Ruta }
    else { & $partes[0] -m venv $Ruta }
}

if (-not (Test-Path $origen)) { throw "No encuentro el esqueleto en $origen" }
if (Test-Path $Destino) {
    $contenido = Get-ChildItem -Force $Destino -ErrorAction SilentlyContinue
    if ($contenido) { throw "El destino $Destino ya existe y no está vacío." }
} else {
    New-Item -ItemType Directory -Path $Destino | Out-Null
}

Write-Host "`n== 1/3 Copiando esqueleto ==" -ForegroundColor Cyan
robocopy $origen $Destino /E /NFL /NDL /NJH /NJS | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy falló con código $LASTEXITCODE" }
$global:LASTEXITCODE = 0
Write-Host "OK: archivos copiados en $Destino"

if ($SaltarVenvs) {
    Write-Host "`nSaltando entornos virtuales (-SaltarVenvs)." -ForegroundColor Yellow
} else {
    Write-Host "`n== 2/3 Entorno del agente (tools/.venv) ==" -ForegroundColor Cyan
    $venvTools = Join-Path $Destino 'tools\.venv'
    if (Test-Path $venvTools) {
        Write-Host "Ya existe $venvTools, no lo recreo." -ForegroundColor Yellow
    } else {
        New-Venv -Python $PythonTools -Ruta $venvTools
        if ($LASTEXITCODE -ne 0) { throw "No pude crear tools/.venv con '$PythonTools'." }
    }
    $pyTools = Join-Path $venvTools 'Scripts\python.exe'
    & $pyTools -m pip install --upgrade pip --quiet
    & $pyTools -m pip install -r (Join-Path $Destino 'requirements-tools.txt')
    if ($LASTEXITCODE -ne 0) { throw "Falló la instalación de requirements-tools.txt" }
    Write-Host "Instalando Chromium para Playwright (puede tardar)..." -ForegroundColor DarkGray
    & $pyTools -m playwright install chromium
    if ($LASTEXITCODE -ne 0) { Write-Host "Aviso: Playwright no pudo instalar Chromium. Skills Boost no funcionará hasta arreglarlo." -ForegroundColor Yellow }

    Write-Host "`n== 3/3 Entorno de RenderCV (rendercv/rendercv-env) ==" -ForegroundColor Cyan
    $venvRcv = Join-Path $Destino 'rendercv\rendercv-env'
    if (Test-Path $venvRcv) {
        Write-Host "Ya existe $venvRcv, no lo recreo." -ForegroundColor Yellow
    } else {
        New-Venv -Python $PythonRenderCv -Ruta $venvRcv
        if ($LASTEXITCODE -ne 0) { throw "No pude crear rendercv/rendercv-env con '$PythonRenderCv'." }
    }
    $pyRcv = Join-Path $venvRcv 'Scripts\python.exe'
    & $pyRcv -m pip install --upgrade pip --quiet
    & $pyRcv -m pip install "rendercv[full]==2.8"
    if ($LASTEXITCODE -ne 0) { throw "Falló la instalación de RenderCV 2.8." }
}

Write-Host @"

Listo. Siguientes pasos:
  1. cd "$Destino"
  2. Edita opencode.json: CREDLY_USER y SKILLSBOOST_PROFILE_URL.
  3. Reemplaza los placeholders de AGENTS.md y rendercv/CONTEXTO_CARRERA.md.
  4. Autentica GitHub:  gh auth login
  5. Verifica el entorno:  pwsh -File "$raiz\scripts\verificar.ps1" -Raiz "$Destino"
  6. Abre OpenCode en la carpeta:  opencode "$Destino"
"@ -ForegroundColor Green
