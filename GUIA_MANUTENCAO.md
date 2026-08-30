# Guia de Manutenção — Checklist de Produção MDF

Este guia existe pra você (ou qualquer pessoa) conseguir mexer no sistema
sem depender de mim toda vez. Cobre: o que cada arquivo faz, como cada
fluxo funciona por dentro, e o que fazer quando alguma coisa quebrar.

---

## 1. Mapa do projeto

```
checklist-producao/
├── app.py                          → Tela inicial: login, troca de senha, menu
├── pages/
│   ├── 1_📋_Preencher_Checklist.py → Operador preenche o checklist do turno
│   ├── 2_📊_Dashboard.py           → Indicadores, tabela, gráficos, exportação
│   ├── 3_🖨️_Gerar_QRCodes.py       → Gera PNG/PDF de QR Code por área
│   ├── 4_🛠️_Administração.py       → Logo, usuários, equipamentos, checklists
│   ├── 5_💡_Sugestões.py           → Sugestão de novo item + aprovação
│   └── 6_🔍_5_Porquês.py           → Análise de causa raiz (RCA)
├── src/
│   ├── db.py                       → Conexão com o Supabase (1 linha de verdade)
│   ├── auth.py                     → Login, senha, papéis de acesso
│   ├── turnos.py                   → Calcula qual turno está rolando agora
│   ├── models.py                   → TODA consulta/gravação no banco passa aqui
│   └── qrcode_gen.py               → Desenha o PNG e o PDF do QR Code
├── sql/
│   └── schema.sql                  → Cria TODAS as tabelas + dados iniciais
└── scripts/
    └── criar_master.py             → Cria o 1º usuário master (só 1x)
```

**Regra de ouro:** se você precisa mudar *o que aparece na tela*, mexe em
`pages/*.py` ou `app.py`. Se precisa mudar *como o dado é buscado/salvo*,
mexe em `src/models.py`. Nunca escreva uma consulta ao banco direto dentro
de uma página — sempre passa por uma função de `models.py`. Isso mantém
tudo num lugar só quando precisar corrigir algo.

---

## 2. Como cada fluxo funciona

### 2.1 Login (`src/auth.py`)

- `exigir_login()` é chamada no topo de **toda página**. Se não tem
  usuário na sessão (`st.session_state["usuario"]`), mostra o formulário
  de login e trava a página com `st.stop()`.
- `autenticar(identificador, senha)` decide se o texto digitado é e-mail
  (tem `@`) ou matrícula, busca na tabela `usuarios`, confere a senha com
  `bcrypt.checkpw`.
- Depois de logado, o objeto `Usuario` fica em `st.session_state["usuario"]`
  durante toda a sessão do navegador — por isso trocar de página não pede
  login de novo.
- As permissões (`pode_ver_dashboard`, `pode_gerar_qrcodes` etc.) são
  `@property` no dataclass `Usuario` — é aqui que você define **quem pode
  o quê**. Pra mudar uma regra de acesso, é só editar essas linhas.

### 2.2 Turno atual (`src/turnos.py`)

- `turno_e_data_referencia()` olha a hora **de Brasília** (`ZoneInfo`) e
  devolve qual turno está rolando (Manhã 07-15h, Tarde 15-23h, Noite
  23-07h) e a data que esse turno "pertence".
- É chamada do zero toda vez que a página de preenchimento carrega — não
  existe cache. Por isso o operador nunca preenche o turno errado: o
  sistema decide sozinho, sem depender do relógio do celular dele.

### 2.3 Preencher Checklist (`pages/1_📋_...py`)

1. Descobre qual checklist abrir: via `?area=slug` do QR Code, ou seleção
   manual (Setor → Checklist).
2. Chama `obter_ou_criar_checklist()` — se já existe um registro pra esse
   template + turno + data de hoje, reaproveita; senão cria um novo.
3. Cada pergunta usa `st.segmented_control` (os chips ✅❌➖) — **nada é
   gravado no banco a cada clique**, fica só na tela (session_state do
   Streamlit). Isso é proposital: gravar a cada resposta deixava a tela
   lenta/travando a cada clique, por causa da ida e volta ao Supabase.
4. O botão **💾 Atualizar respostas** grava tudo de uma vez, numa única
   chamada (`salvar_respostas_em_lote()` — um `upsert` com várias linhas,
   em vez de N chamadas separadas). Mostra um resumo do que foi salvo e
   avisa quantos itens ficaram como "Não".
5. Se o operador esquecer de clicar "Atualizar" e for direto pra
   "Concluir checklist", o próprio botão de concluir salva qualquer
   pendência antes de validar — não perde resposta por esquecimento.
6. No fim, pede login de um supervisor/coordenação/master pra "assinar"
   (`concluir_checklist()`) — é o que trava o checklist como completo e
   **impede qualquer edição depois** (a página já checa
   `status == "completo"` e bloqueia com `st.stop()` lá em cima).

### 2.4 Dashboard (`pages/2_📊_...py`)

- Busca dados em `checklists_do_dia()` e `respostas_por_data()`.
- Os gráficos usam `plotly` — se quiser mudar cor/estilo, as constantes
  `COR_SIM`, `COR_NAO`, `COR_NA` no topo do arquivo controlam tudo.
- Exportação CSV só aparece pra quem tem `pode_exportar_dashboard = True`.

### 2.5 QR Codes (`pages/3_🖨️_...py` + `src/qrcode_gen.py`)

- `gerar_etiqueta_png()` desenha o PNG (logo + QR + texto) com `Pillow`.
- `gerar_cartaz_pdf()` desenha o PDF A5 com `reportlab`.
- A URL do QR aponta pra `SEU_APP_URL/?area=slug` — é esse `slug` que faz
  o app abrir o checklist certo automaticamente.

### 2.6 Administração (`pages/4_🛠️_...py`) — só master

5 abas, cada uma mexendo numa parte diferente:
- **Identidade Visual**: logo (Storage) + cor principal do sistema (tabela
  `configuracoes_sistema`, campo `cor_primaria`). A cor é aplicada por
  `src/tema.py` via injeção de CSS em toda página — funciona bem pra
  botões, mas **não é garantido pra 100% dos widgets** (Streamlit não tem
  API oficial de troca de tema em tempo real). Se algo não acompanhar,
  o método garantido é editar `primaryColor` em `.streamlit/config.toml`
  e fazer redeploy.
- **Usuários**: cadastra, reseta senha, ativa/desativa.
- **Áreas/Equipamentos**: catálogo que alimenta o campo "área" na criação
  de checklist.
- **Novo Checklist**: cria template + itens + horário por turno de uma vez.
- **Checklists Cadastrados**: editar item (texto/criticidade), editar
  horário, remover item, desativar/reativar checklist inteiro.

### 2.7 Sugestões (`pages/5_💡_...py`)

Qualquer usuário sugere um item novo → fica pendente → master aprova (o
item entra automaticamente no checklist via `aprovar_sugestao()`) ou
rejeita com motivo.

### 2.8 5 Porquês (`pages/6_🔍_...py`)

Espelha o "Formulário 5 Porquês – Parada de Linha" físico da Guararapes.
Regra impressa no papel (aviso, não bloqueia): preencher para paradas
entre 30min e 1h30min — `JANELA_MINUTOS_MIN`/`JANELA_MINUTOS_MAX` em
`src/models.py`.

- **Nova análise**: formulário completo (data, equipamento, setor, tempo
  de parada, descrição, os 5 porquês, causa raiz), com atalho opcional
  pra puxar a partir de um "Não" crítico de checklist já registrado —
  mas funciona 100% avulso também, igual ao papel.
- **Plano de Ação**: tabela à parte (`analise_5_porques_acoes`), aceita
  múltiplas ações corretivas por análise, cada uma com responsável e
  prazo — igual às 5 linhas em branco do formulário físico.
- **Verificação da Eficácia**: só quem `pode_assinar_checklist` (supervisor/
  coordenação/master) registra Sim/Não + evidências — vira o "Coordenador
  de produção" do papel.
- **Exportar PDF** (`src/pdf_5_porques.py`): recria o layout do formulário
  físico 1:1 — cabeçalho, aviso amarelo, tabela dos porquês, plano de
  ação, verificação de eficácia, nota de rodapé sobre o Qualiex.

---

## 3. Erros já vistos e como resolver

| Sintoma | Causa | Solução |
|---|---|---|
| `postgrest.exceptions.APIError` com `permission denied for table X (42501)` | O schema `public` do Supabase não tinha GRANT pro role `anon` | Já corrigido no `schema.sql` (bloco de GRANT no topo). Se acontecer numa tabela nova criada fora do script, roda: `grant select, insert, update, delete on all tables in schema public to anon, authenticated;` |
| App abre direto numa página errada (ex: preenchimento) em vez da tela de login | "Main file path" errado no Streamlit Cloud | Settings do app → confirma que está `app.py`, nunca `pages/algo.py` nem `streamlit_app.py` |
| Nomes de arquivo tipo `pages/1_ÐŸ"..._Checklist.py` aparecendo corrompidos no terminal | PowerShell/terminal antigo não lê UTF-8 direito (é só exibição, não estraga o arquivo) | Roda uma vez por máquina: `git config --global core.quotepath false` + `git config --global i18n.commitEncoding utf-8`. Se subir pelo GitHub web (arrastar arquivo), esse problema nem aparece |
| Erro de build no deploy logo depois de instalar dependências | Versão do Python muito nova pra alguma lib do `requirements.txt` | Advanced settings → Python version → usa **3.12** (evita 3.13+ recém-lançado) |
| Login falha sem mensagem clara | Secrets do Streamlit Cloud desalinhados com o projeto Supabase certo | Manage app → Settings → Secrets: confere se `SUPABASE_URL`/`SUPABASE_KEY` batem com o projeto que você rodou o `schema.sql` |
| Checklist não aparece na lista pra preencher | Template está com `ativo = false` | Administração → Checklists Cadastrados → botão "Reativar checklist" |
| Erro genérico e a mensagem vem "redacted to prevent data leaks" | Streamlit Cloud esconde detalhes do erro por padrão | Manage app (canto inferior direito do app) → aba **Logs** → mesma stack trace, mas completa |
| Tela trava/demora a cada resposta marcada no preenchimento | Era gravado no banco a cada clique (1 chamada por resposta) | Já corrigido: agora só grava com o botão "💾 Atualizar respostas" (1 chamada só, pra todas as respostas de uma vez) |

---

## 4. Onde mexer para...

| Quero... | Mexo em... |
|---|---|
| Mudar quem pode fazer o quê (permissões) | `src/auth.py`, classe `Usuario`, as `@property` |
| Mudar hora de início dos turnos | `src/turnos.py`, constantes `_MANHA_INICIO` etc. — **e também** atualizar os horários de ronda de cada checklist em Administração |
| Adicionar um campo novo num item de checklist | `sql/schema.sql` (`alter table checklist_template_itens add column...`) + `src/models.py` (funções que leem/gravam itens) + a página que usa esse campo |
| Mudar cor do gráfico do dashboard | `pages/2_📊_Dashboard.py`, constantes `COR_SIM`/`COR_NAO`/`COR_NA` no topo |
| Mudar a cor principal do app (botões) | Administração → Identidade Visual (rápido, sem redeploy) **ou** `.streamlit/config.toml` → `primaryColor` + redeploy (garantido pra tudo) |
| Adicionar uma página nova | Cria `pages/7_🆕_Nome.py` com `exigir_login()` no topo, igual as outras. O número no início do nome controla a ordem no menu |
| Trocar a logo | Administração → aba Logo (não precisa mexer em código) |
| Ver o que um usuário fez de errado | Supabase → Table Editor → tabela `checklist_respostas` (tem `respondido_por` e `respondido_em`) |

---

## 5. Antes de subir qualquer mudança de código

1. Roda local primeiro: `streamlit run app.py` — se quebrar, quebra na
   sua máquina, não em produção.
2. Se mexeu em algum `.py`, confere se não tem erro de digitação óbvio
   rodando: `python -m py_compile nome_do_arquivo.py` (sem erro = sintaxe
   ok, não garante que a lógica está certa, só que o Python consegue ler
   o arquivo).
3. Se mexeu no `sql/schema.sql`, **nunca** roda o arquivo inteiro de novo
   sem revisar — ele é idempotente pra criação de tabela (`if not
   exists`), mas um `update` ou `insert` sem `on conflict` pode duplicar
   dado. Se for só adicionar uma tabela nova, copia só o trecho novo pro
   SQL Editor em vez de rodar tudo.
4. Sobe pro GitHub → confere no painel do Streamlit Cloud se o rebuild
   passou (ele mostra "Your app is in the oven" enquanto builda, e um
   erro em vermelho se falhar).

---

## 6. Glossário rápido das tabelas do banco

| Tabela | Pra que serve |
|---|---|
| `usuarios` | Login e nível de acesso de cada pessoa |
| `turnos` | Os 3 turnos fixos (Manhã/Tarde/Noite) |
| `setores_processo` | As 9 macro-áreas da planta |
| `equipamentos` | Catálogo de área/equipamento específico (ex: Picador) |
| `checklist_templates` | Um registro por checklist (Sifter, Prensa etc.) |
| `checklist_template_itens` | As perguntas de cada checklist |
| `checklist_template_horarios` | Horário de ronda por turno de cada checklist |
| `checklists` | Uma instância por template+turno+data (o que o operador preenche) |
| `checklist_respostas` | Cada resposta (Sim/Não/N-A) de cada pergunta |
| `checklist_sugestoes` | Sugestões de item novo, aguardando aprovação |
| `analises_5_porques` | Formulário 5 Porquês de paradas de linha (RCA) |
| `analise_5_porques_acoes` | Plano de ação (N linhas) de cada análise 5 Porquês |
| `configuracoes_sistema` | Linha única: URL da logo e cor principal do sistema |
