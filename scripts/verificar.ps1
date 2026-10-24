#Requires -Version 7.0
<#
.SYNOPSIS
    Comprueba que un workspace creado con esta guía está listo para usarse.

.DESCRIPTION
    Verifica archivos, JSON/YAML válidos, los dos entornos virtuales, RenderCV,
    OpenCode, gh y placeholders sin reemplazar. No modifica nada.

.PARAMETER Raiz
    Carpeta del workspace a verificar. Por defecto, el directorio actual.

.EXAMPLE
    pwsh -File scripts/verificar.ps1 -Raiz C:\Users\yo\busqueda-laboral
#>
[CmdletBinding()]
param(
    [string]$Raiz = (Get-Location).Path
)

$ErrorActionPreference = 'Continue'
$fallos = 0
$avisos = 0

function Ok([string]$msg)    { Write-Host "  [OK]    $msg" -ForegroundColor Green }
function Falta([string]$msg) { Write-Host "  [FALTA] $msg" -ForegroundColor Red; $script:fallos++ }
function Aviso([string]$msg) { Write-Host "  [AVISO] $msg" -ForegroundColor Yellow; $script:avisos++ }
function Seccion([string]$msg) { Write-Host "`n$msg" -ForegroundColor Cyan }

Write-Host "Verificando workspace en: $Raiz"

Seccion '1. Archivos base'
foreach ($rel in @(
    'opencode.json',
    'AGENTS.md',
    '.opencode\agents',
    '.opencode\commands',
    '.opencode\skills',
    'tools\mcp_empleo\server.py',
    'tools\mcp_identidad\server.py',
    'tools\rendercv\renderizar.py',
    'tools\github_audit\audit.py',
    'tools\mercado\agregar.py',
    'rendercv\src\cv',
    'rendercv\src\design',
    'rendercv\src\locale',
    'rendercv\CONTEXTO_CARRERA.md'
)) {
    if (Test-Path (Join-Path $Raiz $rel)) { Ok $rel } else { Falta $rel }
}

Seccion '2. opencode.json válido'
$cfg = Join-Path $Raiz 'opencode.json'
if (Test-Path $cfg) {
    try {
        $json = Get-Content $cfg -Raw | ConvertFrom-Json
        Ok 'JSON parseado'
        if ($json.mcp.empleo) { Ok 'MCP empleo declarado' } else { Falta 'MCP empleo no está en opencode.json' }
        if ($json.mcp.identidad) { Ok 'MCP identidad declarado' } else { Falta 'MCP identidad no está en opencode.json' }
        $creds = $json.mcp.identidad.environment.CREDLY_USER
        if ($creds -and $creds -notmatch '<') { Ok "CREDLY_USER = $creds" }
        else { Falta 'CREDLY_USER sigue con placeholder o vacío' }
        $sb = $json.mcp.identidad.environment.SKILLSBOOST_PROFILE_URL
        if ($sb -and $sb -notmatch '<') { Ok 'SKILLSBOOST_PROFILE_URL configurado' }
        else { Aviso 'SKILLSBOOST_PROFILE_URL con placeholder: la sincronización de Google Skills fallará' }
    } catch {
        Falta "opencode.json no parsea: $($_.Exception.Message)"
    }
}

Seccion '3. Entorno del agente (tools/.venv)'
$pyTools = Join-Path $Raiz 'tools\.venv\Scripts\python.exe'
if (Test-Path $pyTools) {
    Ok "python: $(& $pyTools -V 2>&1)"
    $imports = & $pyTools -c 'import mcp, playwright, yaml, requests, pydantic; print("imports ok")' 2>&1
    if ($LASTEXITCODE -eq 0) { Ok $imports } else { Falta "faltan dependencias: $imports" }
    & $pyTools -c 'from playwright.sync_api import sync_playwright' 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Ok 'Playwright importable' } else { Falta 'Playwright no importa' }
} else {
    Falta 'no existe tools/.venv (ejecuta scripts/instalar.ps1)'
}

Seccion '4. Entorno de RenderCV (rendercv/rendercv-env)'
$exeRcv = Join-Path $Raiz 'rendercv\rendercv-env\Scripts\rendercv.exe'
$pyRcv = Join-Path $Raiz 'rendercv\rendercv-env\Scripts\python.exe'
if (Test-Path $exeRcv) { Ok 'rendercv.exe presente' } else { Falta 'no existe rendercv.exe (ejecuta scripts/instalar.ps1)' }
if (Test-Path $pyRcv) {
    $ver = & $pyRcv -c 'import rendercv; print(rendercv.__version__)' 2>&1
    if ($LASTEXITCODE -eq 0 -and $ver -match '^2\.') { Ok "RenderCV $ver" }
    elseif ($LASTEXITCODE -eq 0) { Aviso "RenderCV $ver (la guía se probó con 2.8)" }
    else { Falta "RenderCV no importa: $ver" }
}

Seccion '5. YAML del CV'
$pyYaml = if (Test-Path $pyTools) { $pyTools } else { $pyRcv }
if (Test-Path $pyYaml) {
    $yamls = Get-ChildItem -Recurse (Join-Path $Raiz 'rendercv\src') -Include *.yaml,*.yml -File
    if ($yamls) {
        $res = & $pyYaml -c 'import sys, yaml
for p in sys.argv[1:]:
    yaml.safe_load(open(p, encoding="utf-8"))
print("yaml ok")' @($yamls.FullName) 2>&1
        if ($LASTEXITCODE -eq 0) { Ok "$($yamls.Count) YAML parseados" } else { Falta "YAML inválido: $res" }
    } else {
        Aviso 'no hay YAML en rendercv/src'
    }
} else {
    Aviso 'no hay intérprete con PyYAML para validar los YAML'
}

Seccion '6. Herramientas externas'
if (Get-Command opencode -ErrorAction SilentlyContinue) {
    Ok "opencode $(& opencode --version 2>&1)"
} else {
    Falta 'opencode no está en el PATH'
}
if (Get-Command gh -ErrorAction SilentlyContinue) {
    & gh auth status 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Ok 'gh autenticado' } else { Aviso 'gh sin sesión: ejecuta gh auth login' }
} else {
    Aviso 'gh no está instalado: la auditoría de GitHub no funcionará'
}

Seccion '7. Placeholders pendientes'
# Solo los archivos que una persona debe personalizar: CV, contrato del agente,
# agentes/comandos/skills y contexto de carrera.
$objetivo = @()
foreach ($rel in @('AGENTS.md', 'opencode.json', 'rendercv\CONTEXTO_CARRERA.md')) {
    $ruta = Join-Path $Raiz $rel
    if (Test-Path $ruta) { $objetivo += Get-Item $ruta }
}
foreach ($dir in @('.opencode', 'rendercv\src\cv')) {
    $ruta = Join-Path $Raiz $dir
    if (Test-Path $ruta) { $objetivo += Get-ChildItem -Recurse $ruta -Include *.md,*.yaml -File }
}
$pendientes = $objetivo | Select-String -Pattern '<TU_|<CANDIDATO>|«' -List
if ($pendientes) {
    Aviso "$($pendientes.Count) archivo(s) con placeholders sin reemplazar:"
    $pendientes | ForEach-Object { Write-Host "          $($_.Path.Replace($Raiz + '\',''))" -ForegroundColor DarkGray }
} else {
    Ok 'sin placeholders en el workspace'
}

Write-Host ("`nResultado: {0} fallo(s), {1} aviso(s)." -f $fallos, $avisos) -ForegroundColor $(if ($fallos) { 'Red' } else { 'Green' })
if ($fallos) { exit 1 } else { exit 0 }
