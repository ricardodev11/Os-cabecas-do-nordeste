<#
.SYNOPSIS
    Cria o quadro Trello "Cabeças do Nordeste — Agent Battle Arena (Sprint 1)"
    a partir da especificação em board-spec.md.

.DESCRIPTION
    Usa a API REST do Trello (Invoke-RestMethod). Não salva segredos:
    requere TRELLO_KEY e TRELLO_TOKEN como variáveis de ambiente da sessão.

.PARAMETER BoardName
    Nome do board. Padrão: "Cabecas do Nordeste — Agent Battle Arena (Sprint 1)".
    (Evita acentos no nome por segurança de URL; descrição mantém acentos.)

.EXAMPLE
    $env:TRELLO_KEY = "..." ; $env:TRELLO_TOKEN = "..."
    powershell -ExecutionPolicy Bypass -File docs/trello/create-board.ps1
#>
param(
    [string]$BoardName = "Cabecas do Nordeste - Agent Battle Arena (Sprint 1)"
)

$ErrorActionPreference = "Stop"

if (-not $env:TRELLO_KEY -or -not $env:TRELLO_TOKEN) {
    throw "Defina TRELLO_KEY e TRELLO_TOKEN na sessao antes de rodar."
}

$base = "https://api.trello.com/1"
$key  = $env:TRELLO_KEY
$tok  = $env:TRELLO_TOKEN

function Invoke-Trello {
    param(
        [string]$Method,
        [string]$Path,
        [hashtable]$Query = @{}
    )
    $q = "key=$key&token=$tok"
    foreach ($k in $Query.Keys) {
        $v = [System.Uri]::EscapeDataString([string]$Query[$k])
        $q += "&$k=$v"
    }
    $uri = "$base$Path`?$q"
    $resp = Invoke-RestMethod -Method $Method -Uri $uri
    return $resp
}

Write-Host "[1/5] Criando board..." -ForegroundColor Cyan
$board = Invoke-Trello -Method POST -Path "/boards" -Query @{
    name        = $BoardName
    desc        = "Melhorias do Agent Battle Arena - Camada 1 (interface/produto). Sprint 1 (21-26/09/2026)."
    defaultLists = "false"
    prefs_background = "blue"
}
$boardId = $board.id
Write-Host "      Board id: $boardId"

Write-Host "[2/5] Criando lists e labels..." -ForegroundColor Cyan
$lists = @{
    "Backlog"     = $null
    "A Fazer"     = $null
    "Fazendo"     = $null
    "Review"      = $null
    "Em Teste"    = $null
    "Concluido"   = $null
}
foreach ($name in $lists.Keys) {
    $l = Invoke-Trello -Method POST -Path "/lists" -Query @{
        name = $name
        idBoard = $boardId
    }
    $lists[$name] = $l.id
    Write-Host "      List '$name' -> $($l.id)"
}

$labels = @{
    "critica" = "red"
    "alta"    = "orange"
    "media"   = "yellow"
    "baixa"   = "green"
    "backend" = "blue"
    "frontend" = "purple"
    "teste"   = "sky"
    "docs"    = "lime"
    "bloqueado" = "black"
}
$labelsIds = @{}
foreach ($name in $labels.Keys) {
    $lb = Invoke-Trello -Method POST -Path "/labels" -Query @{
        name = $name
        color = $labels[$name]
        idBoard = $boardId
    }
    $labelsIds[$name] = $lb.id
    Write-Host "      Label '$name' -> $($lb.id)"
}

Write-Host "[3/5] Criando cards..." -ForegroundColor Cyan
function Add-Card {
    param(
        [string]$Name,
        [string]$List,
        [string]$Desc,
        [string[]]$Label,
        [string]$Due,
        [string]$Member
    )
    $q = @{ name = $Name; idList = $lists[$List]; desc = $Desc; pos = "bottom" }
    if ($Due)      { $q.due = $Due }
    if ($Member)   { $q.idMembers = $Member }
    $card = Invoke-Trello -Method POST -Path "/cards" -Query $q
    if ($Label) {
        foreach ($lb in $Label) {
            if ($labelsIds.ContainsKey($lb)) {
                $null = Invoke-Trello -Method POST -Path "/cards/$($card.id)/idLabels" -Query @{ value = $labelsIds[$lb] }
            }
        }
    }
    Write-Host "      Card '$Name' -> $($card.id)"
    return $card
}

# Mantemos o board funcional mesmo sem mapear ids de membros locais:
# responsáveis ficam na descrição (handle GitHub) e podem ser convertidos
# depois por API (getMembers). Prazo em ISO (UTC).

$null = Add-Card -Name "B1 - Teste de contrato SSE (backend)" `
    -List "Concluido" `
    -Desc "PR #7 - backend/tests/test_sse_contract.py (3 testes verdes). Responsavel: @ricardodev11" `
    -Label @("alta","backend","teste") -Due "2026-09-21T22:00:00.000Z"

$null = Add-Card -Name "B2 - Fix portabilidade Windows (backend)" `
    -List "Review" `
    -Desc "PR #6 - sys.executable (Bug A: python3) + contextlib.closing (Bug B: sqlite). Corrige 5 erros+1 falha da suite. Responsavel: @ricardodev11. BLOQUEADO: aguardando review." `
    -Label @("critica","backend","bloqueado") -Due "2026-09-21T22:00:00.000Z"

$null = Add-Card -Name "B3 - Live SSE Battle Room (frontend) - Issue #3" `
    -List "Fazendo" `
    -Desc "Substituir polling por SSE. Backend pronto e testado (B1). Responsavel: @LucasSTMT. Checklist: BattleService.stream(); battle-room consome SSE; fechar em status terminal; PR com review." `
    -Label @("critica","frontend") -Due "2026-09-25T22:00:00.000Z"

$null = Add-Card -Name "B4 - UX Dashboard minhas battles - Issue #2" `
    -List "Fazendo" `
    -Desc "Dashboard com battles do usuario autenticado. Responsavel: @levi-marcos" `
    -Label @("alta","frontend") -Due "2026-09-24T22:00:00.000Z"

$null = Add-Card -Name "B5 - agent-profile-list formalizar - Issue #1" `
    -List "Review" `
    -Desc "Pagina ja existe na main (11f5e62); formalizar em PR com review. Responsavel: @claralimadev. Bloqueado por definicao de fluxo (retroformalizar)." `
    -Label @("media","frontend","bloqueado") -Due "2026-09-24T22:00:00.000Z"

$null = Add-Card -Name "B6 - UX Polimento visual - Issue #4" `
    -List "Backlog" `
    -Desc "Polimento visual geral. Responsavel: Time" `
    -Label @("media","frontend") -Due "2026-09-26T22:00:00.000Z"

$null = Add-Card -Name "B7 - Config baseUrl por environment - Issue #5" `
    -List "Concluido" `
    -Desc "Ja na main via 0185aec + feat/config-api-baseurl. Issue #5 obsoleta - fechar. Responsavel: @ricardodev11" `
    -Label @("baixa","frontend") -Due "2026-09-22T22:00:00.000Z"

$null = Add-Card -Name "B8 - Auditoria + regras de fluxo do squad" `
    -List "Fazendo" `
    -Desc "docs/audit-2026-09-20.md (untracked) + formalizar regras branch/PR/review/merge. Responsavel: @ricardodev11" `
    -Label @("docs") -Due "2026-09-23T22:00:00.000Z"

$null = Add-Card -Name "B9 - Decidir instalação de MCPs/skills" `
    -List "Backlog" `
    -Desc "Pacote curado apresentado (GitHub MCP, Playwright MCP, Codebase Memory, Context7, code-review-skill). Aguarda decisao do time." `
    -Label @("docs")

Write-Host "[4/5] Lendo membros do board (para responsáveis via API)..." -ForegroundColor Cyan
$members = Invoke-Trello -Method GET -Path "/boards/$boardId/members" -Query @{}
foreach ($m in $members) {
    Write-Host "      Membro: $($m.fullName) ($($m.username))"
}

Write-Host "[5/5] URL do board:" -ForegroundColor Cyan
Write-Host "      https://trello.com/b/$boardId" -ForegroundColor Green
Write-Host "Pronto! Compartilhe a URL com o time (Invite -> membros)." -ForegroundColor Green