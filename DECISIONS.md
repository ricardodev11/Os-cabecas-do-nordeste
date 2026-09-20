# DECISIONS.md — Decision Log do Fork (Competição)

Arquivo mantido pelo time candidato em `ricardodev11/Os-cabecas-do-nordeste`.
Registra o escopo da entrega, as decisões tomadas e os riscos conhecidos —
o que decidimos **fazer**, o que decidimos **não fazer** (com motivo) e o porquê.

---

## 1. Contexto

O projeto base (`LavitaCode/agent-battle-arena`) é uma arena competitive onde
agentes de IA duelam em código sobre **quests** com testes, judge, replay e ranking.
Este fork foi entregue como **produto funcional e validado**, não apenas como
código espelho do upstream.

Para a competição, definimos corte claro: **entregar o Modo A (Arena Quests)
completo, rodando de ponta a ponta e com evidência**, e apenas sinalizar o Modo B
(Arena Live 3D em Unity) como fora de escopo.

## 2. Decisões registradas

### D-1 — Sandbox de execução oficial: Docker (com fallback local)
- **O quê:** toda quest/run/batalha roda dentro de um contêiner isolado
  (`Dockerfile.runner`, usuário não-root uid 10001, sem rede, com timeout).
- **Por quê:** o motor original expunha risco de execução arbitrária no host.
- **Como:** preferência `docker`; se o daemon estiver indisponível, `local-process`
  é usado como fallback explícito e logado (`provider` na nota da corrida).

### D-2 — Persistência: motor SQL do alpha como fonte de verdade das batalhas
- Batalhas, runs, replays, post-mortens e leaderboard persistem em SQLite
  (`alpha.db`), imunes a restart do processo.
- O motor `in-memory` (rota `/runs/`) permanece apenas para execuções avulsas e
  testes isolados; as rotas de leitura resolvem a run em **um ou outro** motor.

### D-3 — Escopo do frontend entregue
- Landing explicativa ("Como funciona"), perfis de agente, replay/painel da
  batalha com post-mortem embutido e rebuild do ranking. Telas do upstream que
  não fazem parte do fluxo validado (ex.: editor avançado do Modo B) foram
  minimizadas, não removidas.

### D-4 — [DESCOPE] Arena Live / monitor em tempo real
- **Decisão:** NÃO construir a tela de batalha ao vivo nesta rodada.
- **O que fica:** endpooint SSE `/battles/{battle_id}/stream` continua no backend
  (emite `starting → running → completed/failed`), consumível por qualquer cliente.
- **Por quê:** o replay pós-partida já entrega o valor central (placar, timeline,
  post-mortem) com custo baixo e risco zero. Feature ao vivo parcial custaria
  tempo de entregável sem receita de produto suficiente — decisão consciente de
  timing, não omissão.

## 3. Riscos conhecidos e mitigados

| Risco | Tratamento |
|---|---|
| Testes apagavam o banco real de dev | Isolamento dos testes em DB temporário; suíte 66 testes (6 skipped pela dependência de runner) |
| Sandbox roda como root e sem isolamento | Contêiner não-root, sem rede, sem escrita fora de `/sandbox` |
| Imagem do runner sem deps dos quests (ImportError) | `Dockerfile.runner` instala fastapi/httpx/starlette/uvicorn/pydantic (pins iguais ao host) |
| Execução arbitrária no host | `settings.SANDBOX_EXECUTE_ON_HOST=false`; provider Docker com fallback explícito |
| Duas instâncias de backend brigando pela porta | Process manager: uma única instância `uvicorn`, health `GET /api/v1/health` |

## 4. Estado validado (evidência)

- Batalha 1v1 E2E real rodando em Docker: `battle-928059317e`
  → Esquerda **100.0** (visible 2/2, hidden 1/1) × Direita **33.33**, ambos via
  provider `docker`; vencedor por `higher_technical_score`.
- Rotas de run individual de batalha disponíveis e 200:
  `/runs/{run_id}`, `/runs/{run_id}/replay`, `/runs/{run_id}/post-mortem`,
  `/runs/{run_id}/artifacts`.
- Suíte de backend: **66 testes passando (6 skipped)**; frontend compila (`ng build`).
- Landing reescrita para explicar o produto em 4 passos (agente → quest → batalha → replay).

## 5. Backlog (futuro, se houver tempo)

- Tela da battle ao vivo consumindo o SSE existente (D-4 reversível).
- Tela/contrato do Modo B (Unity) — fora de escopo desta entrega.
- Validar visualmente as demais telas herdadas do upstream contra o fork.