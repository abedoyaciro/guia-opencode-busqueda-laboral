#Requires -Version 7.0
<#
.SYNOPSIS
    Versiona tu CV (un único YAML) sin necesidad del workspace completo.

.DESCRIPTION
    Para quien usa RenderCV solo. Renderiza tu YAML y guarda TODOS los
    artefactos (pdf, png, html, md, typ) en versions/<version>/, junto con una
    copia inmutable del YAML fuente y un manifest.yaml.

    No hace git commit ni git tag: versionar es decisión tuya. Si quieres,
    después: `git add . ; git commit -m "chore(release): v1.0.0" ; git tag v1.0.0`

.PARAMETER Cv
    Ruta a tu archivo YAML del CV (todo-en-uno o solo `cv:`).

.PARAMETER Version
    Versión semántica, con el formato vMAJOR.MINOR.PATCH. Ej: v1.0.0

.PARAMETER Rendercv
    Ruta al ejecutable de RenderCV. Por defecto busca `rendercv` en el PATH y,
    si no, .\rendercv-env\Scripts\rendercv.exe.

.PARAMETER Salida
    Carpeta destino. Por defecto: versions/<version> junto al YAML.

.EXAMPLE
    pwsh -File versionar-solo.ps1 -Cv .\mi-cv.yaml -Version v1.0.0
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Cv,
    [Parameter(Mandatory)][string]$Version,
    [string]$Rendercv,
    [string]$Salida
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $Cv)) { throw "No existe el YAML: $Cv" }
$cvAbs = (Resolve-Path $Cv).Path
if ($Version -notmatch '^v\d+\.\d+\.\d+$') { throw "Versión no semántica: '$Version'. Usa vMAJOR.MINOR.PATCH (ej: v1.0.0)." }

if (-not $Salida) {
    $Salida = Join-Path (Split-Path -Parent $cvAbs) "versions\$Version"
}
if (Test-Path $Salida) { throw "Ya existe $Salida. Elige otra versión o borra esa carpeta." }

# --- localizar el ejecutable de RenderCV ---
$exe = $null
if ($Rendercv) {
    if (-not (Test-Path $Rendercv)) { throw "No existe el ejecutable indicado: $Rendercv" }
    $exe = (Resolve-Path $Rendercv).Path
} elseif (Get-Command rendercv -ErrorAction SilentlyContinue) {
    $exe = (Get-Command rendercv).Source
} elseif (Test-Path '.\rendercv-env\Scripts\rendercv.exe') {
    $exe = (Resolve-Path '.\rendercv-env\Scripts\rendercv.exe').Path
} else {
    throw "No encuentro RenderCV. Instálalo (pip install ""rendercv[full]==2.8"" en un venv) o pasa -Rendercv <ruta>."
}
Write-Host "RenderCV: $exe" -ForegroundColor DarkGray

# --- render a una carpeta temporal ---
$tmp = Join-Path $env:TEMP ("rcv-solo-" + [guid]::NewGuid().ToString('N'))
$env:PYTHONUTF8 = '1'   # evita el UnicodeEncodeError de la consola cp1252
Write-Host "`nRenderizando $([IO.Path]::GetFileName($cvAbs))..." -ForegroundColor Cyan
& $exe render $cvAbs --output-folder $tmp
if ($LASTEXITCODE -ne 0) { throw "RenderCV falló con código $LASTEXITCODE" }

# --- guardar carpeta versionada ---
New-Item -ItemType Directory -Path $Salida -Force | Out-Null
foreach ($f in Get-ChildItem $tmp -File) { Copy-Item $f.FullName (Join-Path $Salida $f.Name) }
Copy-Item $cvAbs (Join-Path $Salida ([IO.Path]::GetFileName($cvAbs)))
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue

$artefactos = (Get-ChildItem $Salida -File | ForEach-Object { $_.Name }) -join ', '
$fecha = (Get-Date).ToString('yyyy-MM-dd')
@"
version: $Version
date: $fecha
generated_by: rendercv 2.8 (versionar-solo.ps1)
source: $([IO.Path]::GetFileName($cvAbs))
artefactos: [$artefactos]
"@ | Set-Content -Path (Join-Path $Salida 'manifest.yaml') -Encoding utf8

Write-Host "`nOK: $Version -> $Salida" -ForegroundColor Green
Get-ChildItem $Salida -File | ForEach-Object { "  $($_.Name)" }
Write-Host "`nSi quieres fijarlo en git:" -ForegroundColor DarkGray
Write-Host "  git add . ; git commit -m `"chore(release): $Version`" ; git tag $Version" -ForegroundColor DarkGray
