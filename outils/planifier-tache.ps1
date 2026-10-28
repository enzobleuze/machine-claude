<#
planifier-tache.ps1 : enregistre ou met a jour une tache planifiee Windows qui lance
scripts/run-tache.sh avec le bash de Git for Windows. Idempotent (relancer = mettre a jour).
Ce fichier reste en ASCII : PowerShell 5.1 lit un .ps1 sans BOM avec la page de code ANSI.

Exemples (depuis la racine du vault) :
  powershell -ExecutionPolicy Bypass -File scripts\planifier-tache.ps1 -Nom jardinier -Commande "python scripts/jardinier.py" -Heure 03:00 -Simuler
  powershell -ExecutionPolicy Bypass -File scripts\planifier-tache.ps1 -Nom gardien -Commande "python scripts/gardien.py --notifier" -Heure 11:00
  powershell -ExecutionPolicy Bypass -File scripts\planifier-tache.ps1 -Nom scoreboard -Commande "bash scripts/scoreboard.sh" -Heure 18:00 -Jours Sunday
  powershell -ExecutionPolicy Bypass -File scripts\planifier-tache.ps1 -Nom veille-compte -Commande "python scripts/veille.py" -ToutesLesMinutes 20
  powershell -ExecutionPolicy Bypass -File scripts\planifier-tache.ps1 -Nom jardinier -LancerMaintenant
  powershell -ExecutionPolicy Bypass -File scripts\planifier-tache.ps1 -Nom jardinier -Supprimer

-Simuler affiche ce qui serait cree, sans rien enregistrer.
-LancerMaintenant lance la tache tout de suite (le vrai test : le contexte planifie, pas la session).
#>
param(
    [Parameter(Mandatory = $true)][ValidatePattern('^[a-z0-9-]+$')][string]$Nom,
    [string]$Commande,
    [ValidatePattern('^\d{2}:\d{2}$')][string]$Heure = "03:00",
    [ValidateSet("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")][string[]]$Jours,
    [int]$ToutesLesMinutes = 0,
    [int]$DureeMaxMinutes = 120,
    [string]$Vault = "",
    [string]$Prefixe = "Machine",
    [switch]$Reveiller,
    [switch]$LancerMaintenant,
    [switch]$Supprimer,
    [switch]$Simuler
)
$ErrorActionPreference = "Stop"
# PowerShell 5.1 : $PSScriptRoot est vide dans les valeurs par defaut de param, on le lit ici.
if (-not $Vault) { $Vault = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path }
$NomTache = "$Prefixe $Nom"

if ($Supprimer) {
    if ($Simuler) { Write-Output "[simulation] supprimerait la tache '$NomTache'"; exit 0 }
    Unregister-ScheduledTask -TaskName $NomTache -Confirm:$false
    Write-Output "Tache '$NomTache' supprimee."
    exit 0
}

if ($LancerMaintenant -and -not $Commande) {
    if ($Simuler) { Write-Output "[simulation] lancerait la tache '$NomTache' maintenant"; exit 0 }
    Start-ScheduledTask -TaskName $NomTache
    Write-Output "Tache '$NomTache' lancee. Regarde outputs/cron-logs/.etat/$Nom.json dans une minute."
    exit 0
}

if (-not $Commande) { throw "-Commande est obligatoire pour creer ou mettre a jour une tache." }
if ($Commande.Contains('"') -or $Commande.Contains("'")) {
    throw "Pas de guillemets dans -Commande : mets la logique dans un script et appelle ce script."
}
if ($Vault.Contains("'")) { throw "Le chemin du vault contient une apostrophe : deplace le vault ou renomme le dossier." }

$candidats = @(
    (Join-Path $env:ProgramFiles "Git\bin\bash.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Git\bin\bash.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Git\bin\bash.exe")
)
$bash = $candidats | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $bash) { throw "bash.exe de Git introuvable. Installe Git for Windows (git-scm.com) puis relance." }

if (-not (Test-Path (Join-Path $Vault "scripts\run-tache.sh"))) {
    throw "scripts\run-tache.sh absent dans $Vault : copie d'abord les outils du bloc F."
}

# C:\Users\x\vault -> /c/Users/x/vault
$vaultBash = $Vault -replace '\\', '/'
if ($vaultBash -match '^([A-Za-z]):(.*)$') { $vaultBash = '/' + $Matches[1].ToLower() + $Matches[2] }
$argument = "-c `"cd '$vaultBash' && bash scripts/run-tache.sh $Nom $Commande`""

$at = [datetime]::ParseExact($Heure, "HH:mm", $null)
if ($ToutesLesMinutes -gt 0) {
    $trigger = New-ScheduledTaskTrigger -Once -At $at -RepetitionInterval (New-TimeSpan -Minutes $ToutesLesMinutes)
    $quand = "toutes les $ToutesLesMinutes minutes a partir de $Heure"
} elseif ($Jours) {
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $Jours -At $at
    $quand = "chaque " + ($Jours -join ", ") + " a $Heure"
} else {
    $trigger = New-ScheduledTaskTrigger -Daily -At $at
    $quand = "chaque jour a $Heure"
}

# StartWhenAvailable : une execution ratee (PC eteint ou en veille) est rattrapee au reveil.
# IgnoreNew : jamais deux copies de la meme tache en meme temps.
$reglages = @{
    StartWhenAvailable         = $true
    AllowStartIfOnBatteries    = $true
    DontStopIfGoingOnBatteries = $true
    ExecutionTimeLimit         = (New-TimeSpan -Minutes $DureeMaxMinutes)
    MultipleInstances          = "IgnoreNew"
}
if ($Reveiller) { $reglages.WakeToRun = $true }
$settings = New-ScheduledTaskSettingsSet @reglages
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$action = New-ScheduledTaskAction -Execute $bash -Argument $argument -WorkingDirectory $Vault

if ($Simuler) {
    Write-Output "[simulation] tache   : $NomTache"
    Write-Output "[simulation] quand   : $quand (rattrapage au reveil : oui, reveil du PC : $([bool]$Reveiller))"
    Write-Output "[simulation] lance   : $bash $argument"
    Write-Output "[simulation] limite  : $DureeMaxMinutes min, compte $env:USERNAME (session ouverte)"
    exit 0
}

Register-ScheduledTask -TaskName $NomTache -Description "machine-claude : $Nom" `
    -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
$info = Get-ScheduledTaskInfo -TaskName $NomTache
Write-Output "Tache '$NomTache' enregistree ($quand). Prochaine execution : $($info.NextRunTime)"

if ($LancerMaintenant) {
    Start-ScheduledTask -TaskName $NomTache
    Write-Output "Lancee maintenant. Regarde outputs/cron-logs/.etat/$Nom.json dans une minute."
}
