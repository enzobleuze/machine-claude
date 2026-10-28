# Essai d'un appel Claude sans fenêtre (claude -p), version PowerShell (Windows sans Git Bash).
#   powershell -File scripts\essai-claude-p.ps1            appel normal
#   powershell -File scripts\essai-claude-p.ps1 leger      appel allégé
# Sort 0 si Claude a répondu, 1 sinon. Ne montre jamais le jeton.
param([string]$Mode = "normal")

$secret = Join-Path $HOME ".claude\secrets\claude-oauth-token.env"
if (-not $env:CLAUDE_CODE_OAUTH_TOKEN -and (Test-Path $secret)) {
    $ligne = Get-Content $secret | Where-Object { $_ -like "CLAUDE_CODE_OAUTH_TOKEN=*" } | Select-Object -First 1
    if ($ligne) { $env:CLAUDE_CODE_OAUTH_TOKEN = ($ligne -replace '^CLAUDE_CODE_OAUTH_TOKEN=', '').Trim('"', "`r") }
}
if (-not $env:CLAUDE_CODE_OAUTH_TOKEN) { Write-Output "ATTENTION : pas de jeton longue durée trouvé ($secret)." }
if ($env:ANTHROPIC_API_KEY) { Write-Output "ATTENTION : ANTHROPIC_API_KEY est définie : facturation possible au tarif public." }
if (-not (Get-Command claude -ErrorAction SilentlyContinue)) { Write-Output "ÉCHEC : commande claude introuvable."; exit 1 }

$modele = if ($env:MODELE_TACHE) { $env:MODELE_TACHE } else { "sonnet" }
$opts = @("-p", "Réponds seulement : ok", "--output-format", "json", "--model", $modele)
if ($Mode -eq "leger") {
    $opts += "--strict-mcp-config"
    if ((claude --help 2>$null) -match "--safe-mode") { $opts += "--safe-mode" }
}

$debut = Get-Date
$sortie = (& claude @opts 2>&1) -join "`n"
$code = $LASTEXITCODE
$duree = [int]((Get-Date) - $debut).TotalSeconds

try { $d = $sortie | ConvertFrom-Json } catch { $d = $null }
if ($code -ne 0 -or -not $d -or -not $d.result) {
    Write-Output "ÉCHEC (code $code, $duree s) :"
    Write-Output ($sortie.Substring(0, [Math]::Min(400, $sortie.Length)))
    if ($sortie -match "(?i)not logged in|401|authentication") { Write-Output "Piste : jeton absent ou expiré. Refais claude setup-token dans un terminal normal." }
    if ($sortie -match "(?i)limit") { Write-Output "Piste : limite de l'abonnement atteinte." }
    exit 1
}
Write-Output ("OK : " + "$($d.result)".Trim())
Write-Output ("Jetons écrits en cache : $($d.usage.cache_creation_input_tokens) | relus : $($d.usage.cache_read_input_tokens)")
Write-Output ("Équivalent tarif public (indicatif sur abonnement) : $($d.total_cost_usd) $")
Write-Output "Mode : $Mode | durée : $duree s"
