# Trello — Squad Cabeças do Nordeste

Pasta de configuração do quadro Trello do time.

## Como usar (fluxo com o SM)

1. **Criar a conta Trello** (2 min, manual — só o dono pode fazer):
   - Acesse https://trello.com -> sign up com seu email.
   - Pode ser a conta da equipe ou uma conta "bot" criada pelo Ricardo.

2. **Gerar API Key + Token** (uma vez por máquina):
   - https://trello.com/power-ups/admin -> crie um Power-Up "Squad Cabeças" -> copie a **API Key**.
   - Abra https://trello.com/1/authorize?expiration=never&scope=read,write,account&response_type=token&key=SUA_KEY
   - Copie o **Token** gerado.

3. **Rodar o script de criação** (cria board, lists, labels, cards, prazos e responsáveis):
   ```powershell
   $env:TRELLO_KEY = "SUA_KEY"
   $env:TRELLO_TOKEN = "SEU_TOKEN"
   powershell -ExecutionPolicy Bypass -File docs/trello/create-board.ps1
   ```
   - As variáveis de ambiente ficam só na sessão; nunca salve key/token em arquivo no repo.

4. **Manter o quadro vivo**: ao final de cada sessão, o SM atualiza status/datas no Trello e reflete aqui no `board-spec.md`.

## Arquivos

- `board-spec.md` — especificação canônica do quadro (lists, cards, labels, prazos, responsáveis, DoD).
- `create-board.ps1` — automação de criação via API do Trello (power shell + Invoke-RestMethod).
- `README.md` — este arquivo.