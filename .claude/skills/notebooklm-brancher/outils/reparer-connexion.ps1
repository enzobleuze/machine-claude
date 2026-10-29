# reparer-connexion.ps1 : rend la connexion NotebookLM durable sous Windows.
# A lancer par l'utilisateur dans un terminal ADMINISTRATEUR, hors de l'application Claude
# (clic droit sur le bouton Demarrer > Terminal (administrateur)) :
#   powershell -ExecutionPolicy Bypass -File "<chemin>\reparer-connexion.ps1" -Email <adresse Google>
# Etapes : 1 Python, 2 exclusion antivirus du seul lecteur de cookies, 3 notebooklm-py + lecteur
# de cookies, 4 Firefox et connexion a NotebookLM dedans, 5 import de la connexion et verification,
# 6 tache "NotebookLM garder connexion" toutes les 20 minutes (garder-connexion.pyw, sans fenetre).
# Relancer ce script ne casse rien : c'est aussi le remede quand l'alerte de deconnexion apparait.
param(
    [Parameter(Mandatory = $true)][string]$Email,
    [string]$Navigateur = "firefox"
)
$ErrorActionPreference = "Continue"
$env:PYTHONUTF8 = "1"
$ici = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "1/6 Python"
$lanceur = @("py", "python") | Where-Object { Get-Command $_ -ErrorAction SilentlyContinue } | Select-Object -First 1
$py = if ($lanceur) { "$(& $lanceur -c "import sys;print(sys.executable)")".Trim() }
if (-not $py -or -not (Test-Path $py)) {
    Write-Host "   Python introuvable. Installe-le (winget install Python.Python.3.12), ferme ce terminal, relance."
    exit 1
}
Write-Host "   $py"

Write-Host "2/6 Exclusion antivirus pour le lecteur de cookies (dossier rookie_cookies seulement)"
$dossiers = & $py -c "import site,sysconfig;print(sysconfig.get_paths()['purelib']);print(site.getusersitepackages())"
foreach ($d in $dossiers) {
    $cible = Join-Path $d.Trim() "rookie_cookies"
    try { Add-MpPreference -ExclusionPath $cible -ErrorAction Stop; Write-Host "   OK $cible" }
    catch { Write-Host "   Pas fait pour $cible (terminal non administrateur, ou autre antivirus : ajoute ce dossier a ses exclusions)" }
}

Write-Host "3/6 Installation de notebooklm-py et du lecteur de cookies"
& $py -m pip install --upgrade -q "notebooklm-py[browser,cookies]"
& $py -c "import rookie_cookies"
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Le lecteur de cookies manque (souvent supprime par l'antivirus). Ouvre la quarantaine de"
    Write-Host "   l'antivirus, autorise rookie_cookies, puis relance ce script."
    exit 1
}

Write-Host "4/6 $Navigateur"
if ($Navigateur -eq "firefox") {
    $ff = @("$env:ProgramFiles\Mozilla Firefox\firefox.exe", "$env:LOCALAPPDATA\Mozilla Firefox\firefox.exe") |
        Where-Object { Test-Path $_ } | Select-Object -First 1
    $store = Get-ChildItem "$env:LOCALAPPDATA\Packages" -Directory -Filter "Mozilla.MozillaFirefox_*" -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if (-not $ff -and -not $store) {
        winget install --id Mozilla.Firefox -e --source winget --accept-package-agreements --accept-source-agreements
    }
}
Write-Host "   Ouvre $Navigateur DEPUIS LE MENU DEMARRER, va sur https://notebooklm.google.com"
Write-Host "   et connecte-toi avec $Email. Ne te deconnecte jamais de Google dans ce navigateur."
Read-Host "   Appuie sur Entree quand tes carnets s'affichent"

# Firefox du Microsoft Store range son profil ailleurs : une jonction le rend visible au lecteur de cookies
if ($Navigateur -eq "firefox" -and $store -and -not (Test-Path "$env:APPDATA\Mozilla\Firefox")) {
    $profilStore = Join-Path $store.FullName "LocalCache\Roaming\Mozilla\Firefox"
    if (Test-Path $profilStore) {
        New-Item -ItemType Directory -Force "$env:APPDATA\Mozilla" | Out-Null
        New-Item -ItemType Junction -Path "$env:APPDATA\Mozilla\Firefox" -Target $profilStore | Out-Null
        Write-Host "   Profil Firefox du Store relie"
    }
}

Write-Host "5/6 Import de la connexion et verification en ligne"
& $py -m notebooklm login --browser-cookies $Navigateur --account $Email
if ($LASTEXITCODE -eq 0) { & $py -m notebooklm auth refresh --browser-cookies $Navigateur --verify }
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ECHEC : le navigateur n'est pas vu connecte. Ferme-le completement, rouvre-le,"
    Write-Host "   verifie que NotebookLM s'affiche, puis relance ce script."
    exit 1
}

Write-Host "6/6 Tache de maintien toutes les 20 minutes"
$dest = Join-Path $env:USERPROFILE ".notebooklm"
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item (Join-Path $ici "garder-connexion.pyw") $dest -Force
$pyw = Join-Path (Split-Path $py) "pythonw.exe"
if (-not (Test-Path $pyw)) { $pyw = $py }
schtasks /Create /F /SC MINUTE /MO 20 /TN "NotebookLM garder connexion" /TR "`"$pyw`" `"$dest\garder-connexion.pyw`" --navigateur $Navigateur" | Out-Null
& $py "$dest\garder-connexion.pyw" --une-fois --navigateur $Navigateur

Write-Host ""
Write-Host "FINI. NotebookLM reste connecte tant que l'ordinateur tourne et que $Navigateur reste connecte a Google."
Write-Host "Dis a Claude : NotebookLM est repare."
