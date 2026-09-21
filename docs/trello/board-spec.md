# Board Spec — Squad Cabeças do Nordeste (Sprint 1)

> Fonte da verdade do quadro Trello. Atualizar sempre que o status mudar.
> **Última atualização: 2026-09-21 — véspera da entrega. Main em `2f06a84`.**

## Board

- **Nome:** Cabeças do Nordeste — Agent Battle Arena (Sprint 1)
- **Descrição:** Melhorias do projeto Agent Battle Arena — Camada 1 (interface/produto). Sprint de ~1 semana (21–26/09/2026).
- **Regra de merge vigente (2026-09-21):** review obrigatório externo REMOVIDO (`required_approving_review_count = 0`). PR continua obrigatório; merge feito pelo SM após validação própria (build/testes/contrato). Código nunca vai direto para `main`.

## Lists (colunas de fluxo)

1. `📋 Backlog` — tarefas levantadas, sem dono/prazo.
2. `🔜 A Fazer` — priorizadas e com dono, ainda não iniciadas.
3. `🔨 Fazendo` — em execução.
4. `👀 Review` — PR aberto aguardando avaliação do time.
5. `🧪 Em Teste` — aprovado no review, validando no ambiente.
6. `✅ Concluído` — merged na `main` + validação OK.

## Labels (etiquetas)

| Nome | Cor | Uso |
|---|---|---|
| `crítica` | vermelho | bloqueia entrega / destrava time |
| `alta` | laranja | prioridade alta |
| `média` | amarelo | prioridade média |
| `baixa` | verde | prioridade baixa |
| `backend` | azul | toca API/serviços |
| `frontend` | roxo | toca Angular/UI |
| `teste` | ciano | trabalho de validação/teste |
| `docs` | cinza | documentação |
| `bloqueado` | preto | aguardando terceiro |

## Cards

### B1 — Construir teste de contrato SSE (backend)
- **Status:** ✅ Concluído (mergeado) · **Donos:** Ricardo (SM) · **Prazo:** 21/09
- **Labels:** `alta`, `backend`, `teste`
- **Evidência:** PR #7 — 3 testes verdes (`test_sse_contract.py`).
- **Nota:** mergeado na main.

### B2 — Fix portabilidade Windows (backend)
- **Status:** ✅ Concluído (mergeado) · **Donos:** Ricardo (SM) · **Prazo:** 21/09
- **Labels:** `crítica`, `backend`
- **Evidência:** PR #6 — `sys.executable` (Bug A: python3) + `contextlib.closing` (Bug B: sqlite WinError 32). Corrige 5 erros + 1 falha da suíte.
- **Nota:** mergeado na main.

### B3 — Live SSE Battle Room (frontend) — Issue #3
- **Status:** ✅ Concluído (mergeado) · **Donos:** Ricardo (SM) · **Prazo:** 21/09
- **Labels:** `crítica`, `frontend`
- **Evidência:** PR #8 — `BattleService.stream()`, `battle-room.ts` sem polling, badge "ao vivo", E2E real Windows validado (running→completed).
- **Nota:** issue #3 fechada. Anteriormente do @LucasSTMT; concluída pelo SM pelo prazo (validação E2E delegada ao Lucas — issue #10).

### B4 — UX Dashboard "minhas battles" — Issue #2
- **Status:** 🔨 Fazendo · **Donos:** Levi (`@levi-marcos`) · **Prazo:** 21/09 (entrega amanhã)
- **Labels:** `alta`, `frontend`
- **Descrição:** dashboard com as battles do usuário autenticado (filtro por dono/participação).
- **Nota:** aviso postado na issue #2 em 21/09 (rebase `origin/main` antes de codar).

### B5 — UX agent-profile-list formalizar — Issue #1
- **Status:** 🔨 Fazendo · **Donos:** Clara (`@claralimadev`) · **Prazo:** 21/09 (entrega amanhã)
- **Labels:** `média`, `frontend`
- **Descrição:** página já existe na main (11f5e62); formalizar em PR dedicado (retroformalização).
- **Nota:** aviso postado na issue #1 em 21/09.

### B6 — UX Polimento visual — Issue #4
- **Status:** 🔨 Fazendo · **Donos:** Clara (`@claralimadev`) · **Prazo:** 21/09 (entrega amanhã)
- **Labels:** `média`, `frontend`
- **Descrição:** polimento visual geral (alinhamentos, estados vazios, feedbacks).
- **Nota:** issue #4 atribuída à Clara em 21/09; branch própria `feat/issue-4-ui-polish` deve ser rebaseada contra `origin/main`.

### B7 — Config baseUrl por environment — Issue #5
- **Status:** ✅ Concluído (mergeado) · **Donos:** Ricardo (SM) · **Prazo:** 22/09
- **Labels:** `baixa`, `frontend`
- **Evidência:** baseUrl central na main (0185aec) + `environment.prod.ts` e fileReplacements (PR #9).
- **Nota:** issue #5 fechada.

### B8 — Auditoria + regras de fluxo do squad
- **Status:** 🔨 Fazendo · **Donos:** Ricardo (SM) · **Prazo:** 23/09
- **Labels:** `docs`
- **Descrição:** `docs/audit-2026-09-20.md` + `docs/trello/` (commit pendente) + formalizar regras (branch/PR/review/merge).

### B9 — Decidir instalação dos MCPs/skills
- **Status:** 📋 Backlog · **Donos:** Time · **Prazo:** aberto
- **Labels:** `docs`
- **Descrição:** pacote curado apresentado (GitHub MCP, Playwright MCP, Codebase Memory, Context7, code-review-skill). Aguarda decisão.

## Delivered no Sprint (21/09 — véspera da entrega)

- PR #6 (sandbox Windows) — merged
- PR #7 (contrato SSE backend) — merged
- PR #8 (front SSE live, Issue #3) — merged
- PR #9 (config env prod, Issue #5) — merged
- Issues fechadas: **#3** e **#5**
- Issues abertas com dono: **#1** (Clara), **#2** (Levi), **#4** (Clara), **#10** (Lucas — validação E2E demo)

## Definition of Done (global)

Um card só entra em `✅ Concluído` quando **todos** valerem:
- [ ] Código entregue em **PR** (nunca commit direto na main)
- [ ] **Validação técnica** pelo SM/DEV com evidência (build, suíte, contrato ou checagem manual)
- [ ] **Merge** na main (feito pelo SM; PR obrigatório)
- [ ] Issue fechada com comentário de evidência

## Cadência

- Daily leve via Trello (status do próprio card) ou Discord.
- Atualização do quadro pelo SM ao fim de cada sessão (este arquivo reflete o estado real).