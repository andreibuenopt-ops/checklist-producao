# Guia de Manutenção — Checklist de Produção MDF

Este guia existe pra você (ou qualquer pessoa) conseguir mexer no sistema
sem depender de mim toda vez. Cobre: o que cada arquivo faz, como cada
fluxo funciona por dentro, e o que fazer quando alguma coisa quebrar.

---

## 1. Mapa do projeto

```
checklist-producao/
├── app.py                          → Login, troca de senha, menu, E também
│                                      renderiza o preenchimento quando chega
│                                      via QR Code (ver seção 2.3)
├── pages/
│   ├── 1_📋_Preencher_Checklist.py → Só o caminho manual (sidebar) — resolve
│   │                                  o template e delega pra preenchimento_ui
│   ├── 2_📊_Dashboard.py           → Indicadores, tabela, gráficos, exportação
│   ├── 3_🖨️_Gerar_QRCodes.py       → Gera PNG/PDF de QR Code por área
│   ├── 4_🛠️_Administração.py       → Logo/cor, usuários, equipamentos, checklists
│   ├── 5_💡_Sugestões.py           → Sugestão de novo item + aprovação
│   └── 6_🔍_5_Porquês.py           → Formulário 5 Porquês (Parada de Linha)
├── src/
│   ├── db.py                       → Conexão com o Supabase (1 linha de verdade)
│   ├── auth.py                     → Login, senha, papéis de acesso
│   ├── turnos.py                   → Calcula qual turno está rolando agora
│   ├── models.py                   → TODA consulta/gravação no banco passa aqui
│   ├── preenchimento_ui.py         → Formulário de preenchimento em si (usado
│   │                                  por app.py E por pages/1_...)
│   ├── sidebar.py                  → Logo + nome de quem está logado + Sair,
│   │                                  chamado em toda página
│   ├── tema.py                     → Aplica a cor de identidade visual (CSS)
│   ├── qrcode_gen.py                → Desenha o PNG e o PDF do QR Code
│   └── pdf_5_porques.py             → Gera o PDF do Formulário 5 Porquês
├── sql/
│   └── schema.sql                  → Cria TODAS as tabelas + dados iniciais
├── assets/
│   └── logo_guararapes.png         → Logo padrão (fallback até subir outra)
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
  usuário na sessão (`st.session_state["usuario"]`), mostra 2 abas —
  **Entrar** e **🆕 Primeira vez aqui?** — e trava a página com `st.stop()`.
- **Aba de cadastro**: qualquer pessoa cria a própria conta (nome, e-mail,
  matrícula, senha). O papel é **forçado como `"producao"` direto no
  código** (`criar_usuario(..., "producao", None)`) — o formulário nem
  mostra campo de nível, então não tem como a pessoa se autopromover.
  Se **Administração → Usuários → "Autocadastro fica pendente até o
  master aprovar"** estiver ligado, a conta nasce inativa e a pessoa só
  loga depois que o master ativar (`alternar_status`); desligado (padrão),
  já loga automaticamente. Pra promover o nível de alguém, o master usa
  Administração → Usuários → **Alterar nível de acesso**
  (`atualizar_papel_usuario()`).
- **`autenticar(identificador, senha)` NUNCA busca o hash da senha.**
  Chama `supabase.rpc("autenticar_usuario", ...)` — uma função Postgres
  (`security definer`, em `sql/schema.sql`) que compara a senha *dentro*
  do banco (`pgcrypto.crypt()`) e devolve só um `boolean`. Antes, o app
  buscava a linha inteira (`select "*"`) e comparava em Python — com a
  chave publishable (não-secreta por natureza), qualquer um podia pedir
  `senha_hash` direto pela API, sem nem passar pelo app. Isso fechou essa
  brecha: `revoke select on usuarios` + `grant select` só nas colunas
  não-sensíveis (ver schema).
  ⚠️ Se algum dia trocar como a senha é gerada (`bcrypt.hashpw`), lembra
  que a função SQL normaliza `$2b$/$2y$` → `$2a$` antes de comparar —
  testado à mão porque a build de `pgcrypto` usada não reconhecia `$2b$`
  (o que o Python sempre gera). Não mexe nisso sem testar de novo contra
  um Postgres de verdade — quebrar essa normalização derruba o login de
  todo mundo.
- Depois de logado, o objeto `Usuario` fica em `st.session_state["usuario"]`
  durante toda a sessão do navegador — por isso trocar de página não pede
  login de novo.
- As permissões (`pode_ver_dashboard`, `pode_gerar_qrcodes` etc.) são
  `@property` no dataclass `Usuario` — é aqui que você define **quem pode
  o quê**. Pra mudar uma regra de acesso, é só editar essas linhas.

### 2.2 Turno atual (`src/turnos.py`)

- `turno_e_data_referencia()` olha a hora **de Brasília** (`ZoneInfo`) e
  devolve qual turno está rolando (A/Manhã 05:20-13:40, B/Tarde 13:40-22:00,
  C/Noite 22:00-05:20) e o *dia de produção* a que ele pertence (o dia
  começa pelo C — ver seção 8).
- É chamada do zero toda vez que a página de preenchimento carrega — não
  existe cache. Por isso o operador nunca preenche o turno errado: o
  sistema decide sozinho, sem depender do relógio do celular dele.

### 2.3 Preencher Checklist (`src/preenchimento_ui.py`, chamado por `app.py` e `pages/1_📋_...py`)

**Dois pontos de entrada, um só formulário:**
- **Via QR Code**: a URL chega em `app.py` (a raiz do site) já com `?area=slug`.
  `app.py` resolve o template e chama `renderizar_preenchimento()` **direto
  ali, sem trocar de página**. Isso é proposital — `st.switch_page()` tem
  um bug do próprio Streamlit que apaga o `?area=` da URL durante a troca
  de página ([streamlit/streamlit#9050](https://github.com/streamlit/streamlit/issues/9050)),
  o que fazia o QR Code não abrir o checklist certo. Não usa mais
  `switch_page` por causa disso.
- **Via menu lateral** (só supervisor/coordenação/master —
  `pode_escolher_checklist_manualmente`): cai em
  `pages/1_📋_Preencher_Checklist.py`, que mostra os dois dropdowns
  (Setor → Checklist) e chama a mesma `renderizar_preenchimento()`.

**O que o formulário faz** (dentro de `renderizar_preenchimento()`):
1. Chama `obter_ou_criar_checklist()` — se já existe um registro pra esse
   template + turno + data de hoje, reaproveita; senão cria um novo.
2. **Todas as perguntas ficam dentro de um único `st.form(...)`.** Isso é
   proposital: sem form, cada clique num chip Sim/Não/N-A reexecuta a
   página inteira (o indicador "Stop" piscando no topo do navegador a
   cada toque — mesmo já não gravando mais no banco a cada clique).
   Dentro do form, nenhum clique dispara nada — só quando aperta
   "💾 Atualizar respostas" (que é o `st.form_submit_button`) é que tudo
   é processado de uma vez. Testado com `AppTest` do Streamlit: clicar
   nos chips sem apertar o botão não chama `salvar_respostas_em_lote`
   nenhuma vez; apertar o botão chama uma vez só, com todas as respostas
   junto.
3. Como nada reexecuta durante o preenchimento, a contagem "X pergunta(s)
   sem resposta" / o aviso de "Não" só atualiza **depois** de apertar
   Atualizar — fica guardado em `st.session_state[f"estado_preenchimento_{checklist_id}"]`
   porque não dá pra recalcular a cada clique (não tem clique-a-clique
   mais).
4. **Não existe mais salvamento automático ao concluir.** Antes, se
   esquecesse de apertar "Atualizar" e fosse direto pra "Concluir", o
   sistema salvava por baixo dos panos. Agora não: como as respostas
   dentro do form só chegam ao servidor quando o form é confirmado,
   tentar concluir sem ter apertado "Atualizar respostas" antes trava
   com "Confirme com 'Atualizar respostas' primeiro" — é proposital,
   seguindo o mesmo padrão de "só processa quando confirma".
5. No fim, pede login de um supervisor/coordenação/master pra "assinar"
   (`concluir_checklist()`) — é o que trava o checklist como completo e
   **impede qualquer edição depois** (a função já checa
   `status == "completo"` e para com `return`).

**Importante ao editar**: se mudar algo no formulário, mexe só em
`src/preenchimento_ui.py` — os dois pontos de entrada (`app.py` e
`pages/1_...py`) chamam a mesma função, então a mudança vale pros dois
automaticamente. Não duplique lógica entre eles.

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
| Tela trava/demora a cada resposta marcada no preenchimento | Cada clique reexecutava a página inteira (indicador "Stop" piscando) | Já corrigido: perguntas ficam dentro de um `st.form()` — nenhum clique dispara nada, só o botão "💾 Atualizar respostas" processa tudo de uma vez |
| Escaneou o QR Code e caiu na tela de "escolha manual" ou de bloqueio, em vez de abrir o checklist direto | Bug do próprio Streamlit: `st.switch_page()` apaga o `?area=` da URL do navegador durante a troca de página ([streamlit/streamlit#9050](https://github.com/streamlit/streamlit/issues/9050)) | Já corrigido: `app.py` não usa mais `switch_page` pra esse caso — renderiza o formulário direto, na mesma URL que veio do QR (`src/preenchimento_ui.py`) |
| `function set_atualizado_em() does not exist` rodando `schema.sql` num banco novo do zero | Ordem errada no arquivo: `configuracoes_sistema` criava um trigger usando essa função antes dela ser definida mais abaixo | Já corrigido: a função agora é definida logo no topo do arquivo, antes de qualquer tabela |
| Login parou de funcionar depois de mexer em como a senha é verificada | `pgcrypto.crypt()` só reconhece hash com prefixo `$2a$` — o `bcrypt` do Python sempre gera `$2b$` (confirmado testando num Postgres real) | A função `autenticar_usuario()` no schema já normaliza `$2b$/$2y$` → `$2a$` antes de comparar. Se mexer nessa função, testa de novo com um hash gerado pelo `bcrypt.hashpw()` de verdade antes de subir — não confia só na leitura do SQL |
| `APIError: function crypt(text, text) does not exist` (código `42883`) no login | No Supabase (diferente de Postgres comum), `pgcrypto` é instalado no schema `extensions`, não em `public`. Uma função `security definer` com `search_path` travado só em `public` não acha `crypt()` | Já corrigido: `autenticar_usuario()` usa `set search_path = public, extensions`. Se criar outra função `security definer` que use qualquer coisa do `pgcrypto` (`crypt`, `gen_salt`, `gen_random_uuid` etc.), lembra de incluir `extensions` no `search_path` dela também |

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
3. Roda `pytest tests/ -v` (ver seção 6) — pega regressão em login,
   preenchimento e permissões antes de você descobrir no ar.
4. Se mexeu no `sql/schema.sql`, **nunca** roda o arquivo inteiro de novo
   sem revisar — ele é idempotente pra criação de tabela (`if not
   exists`), mas um `update` ou `insert` sem `on conflict` pode duplicar
   dado. Se for só adicionar uma tabela nova, copia só o trecho novo pro
   SQL Editor em vez de rodar tudo.
5. Sobe pro GitHub → confere no painel do Streamlit Cloud se o rebuild
   passou (ele mostra "Your app is in the oven" enquanto builda, e um
   erro em vermelho se falhar).

---

## 6. Testes automatizados (`tests/`)

Antes de qualquer mudança em `src/auth.py`, `src/preenchimento_ui.py` ou
nas páginas, roda a suite — ela pega regressão antes de você descobrir
no ar:

```bash
pip install -r requirements-dev.txt --break-system-packages
pytest tests/ -v
```

**Como funciona**: cada arquivo em `tests/fixture_apps/` é um "app de
teste" minúsculo — importa o módulo real (`src/auth.py`,
`src/preenchimento_ui.py`, uma página inteira), troca as funções que
tocam o Supabase por versões falsas em memória (`monkeypatch` direto no
módulo), e roda com `AppTest` do próprio Streamlit — a mesma ferramenta
usada pra construir e validar esse projeto do início. Os arquivos
`tests/test_*.py` simulam clique/digitação real (`set_value()`,
`.click()`) e conferem o resultado.

**Adicionar teste novo**: se o fluxo já tem um fixture app parecido
(login, preenchimento), só adiciona uma função `test_...` no arquivo
`test_*.py` correspondente. Se é fluxo novo, cria um fixture app novo em
`tests/fixture_apps/`, seguindo o padrão dos existentes — mocka só o que
esse fluxo específico usa, não precisa mockar tudo.

**Nem todo teste precisa de fixture app/`AppTest`** — `test_hierarquia_admin.py`
testa direto as funções de `src/auth.py` (sem simular tela nenhuma),
usando uma fixture `auth_mod` que importa o módulo só *depois* de
`secrets_fake` já ter rodado (se importasse no topo do arquivo, quebra —
`src/db.py` lê `st.secrets` na hora da importação, antes de qualquer
fixture rodar). Segue esse padrão pra testar lógica de permissão sem
precisar renderizar página nenhuma.

⚠️ **Cuidado com poluição entre arquivos de teste**: os fixture apps
trocam função de módulo direto (`auth_mod.criar_usuario = fake`), sem
usar o `monkeypatch` do pytest — que desfaz sozinho depois do teste. Sem
cuidado, um teste que roda depois herdaria a versão falsa de outro
arquivo. `conftest.py` já resolve isso recarregando `src.auth`/
`src.models`/`src.preenchimento_ui` do zero antes de cada teste — se
criar um fixture app novo que mockar outro módulo, adiciona o nome dele
na lista de `for nome_modulo in (...)` no `conftest.py`.

**O que a suite NÃO cobre**: integração real contra Supabase/Streamlit
Cloud — tudo aqui é com banco falso em memória. Não substitui testar no
ambiente real depois de uma mudança grande.

---

## 7. Glossário rápido das tabelas do banco

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
| `configuracoes_sistema` | Linha única: logo, cor, e se autocadastro exige aprovação |

## 8. Turnos, fotos, histórico, assinatura pendente e relatórios (versão de outubro/2026)

**Turnos oficiais** (`src/turnos.py`): A/Manhã 05:20–13:40 · B/Tarde 13:40–22:00 · C/Noite 22:00–05:20.
O **dia de produção começa pelo C**: a sequência do dia é C, A, B, e a Noite que começa às 22h de domingo
pertence a **segunda-feira**. Toda data gravada em `checklists.data` é o *dia de produção*.

**Ordem para subir (Supabase → código):**
1. `sql/migration_fotos_historico.sql` (tabela de fotos, bucket privado `checklist-fotos`, coluna `incompleto`,
   funções de medição de espaço, remove índice redundante)
2. `sql/migration_paradas_supervisor.sql` (sub-perguntas + as 3 perguntas de parada no Supervisor de Turno)
3. `sql/migration_dia_producao_noite.sql` — **uma vez só** (tem trava). Empurra 1 dia os registros antigos de Noite.
   Rodar junto com a subida do código, de preferência na virada de turno.
4. Subir o código e dar Reboot.

**Fotos** — qualquer item tem "📷 Adicionar foto (opcional)". `src/fotos.py` reduz a imagem (1280 px, JPEG 72) antes de
enviar; ~100–200 KB por foto. O plano free do Supabase tem 1 GB de Storage: acompanhe em Storage → `checklist-fotos`.
As fotos aparecem no histórico e no PDF do checklist.

**Histórico** (`pages/8_📜_Histórico.py`, todos os papéis, somente leitura) e o toggle "Ver o que aconteceu no turno anterior"
dentro do preenchimento (`models.checklist_anterior`, sequência C → A → B).

**Assinatura no dia seguinte** — aba "Pendentes de assinatura" do Histórico. O checklist continua valendo no dia em que foi
feito. Se faltar resposta, assina como **incompleto** (`checklists.incompleto`): conta como realizado, mas fica marcado.
Checklist aberto sem nenhuma resposta não aparece nessa lista. *Não cobre o Ecoresinator.*

**Aderência / relatório mensal** (`pages/9_📈_Aderência.py`, supervisor+; exportar = supervisor/admin/master):
`src/aderencia.py` calcula esperado × realizado por checklist e turno (só turnos já encerrados, só checklists concluídos).
PDF em `src/pdf_relatorio_mensal.py`; CSV com `;` e acentos prontos pro Excel.

**Armadilha corrigida:** o Supabase devolve no máximo 1000 linhas por consulta. Consultas grandes devem usar
`models._todas_as_linhas()` — antes, o Dashboard contava só as 1000 primeiras respostas do dia.

### Perguntas com SUB-perguntas (paradas no Supervisor de Turno)
`checklist_template_itens.pai_item_id` liga uma pergunta-filha ao pai; `exige_foto` bloqueia a conclusão sem foto.
Quando o pai é respondido **Sim**, as filhas abrem num quadro naquela ronda (`src/itens.py`); se o pai volta pra
**Não**, as respostas e fotos das filhas são apagadas. Cadastro: Administração → Checklists Cadastrados →
botão **➕ Sub** ao lado da pergunta. Atenção: no Supervisor de Turno as perguntas se repetem em cada ronda do turno.

### Peso no Supabase grátis (500 MB de banco, 1 GB de fotos, 5 GB de tráfego/mês)
- Foto reduzida a ~110 KB (1024 px) + miniatura de 240 px; máx. 3 por pergunta; as telas usam só a miniatura.
- PDF é gerado **sob demanda** (botão "📄 Gerar PDF") — só então as fotos inteiras são baixadas.
- Dashboard guarda em cache por 2 min as respostas do dia (consulta de milhares de linhas).
- Administração → **💾 Armazenamento**: barras de uso (banco e fotos) e "Apagar fotos antigas".
- O banco cresce ~2 MB por dia de uso (milhares de respostas/dia). Acompanhe a barra; quando passar de ~70%
  é hora de arquivar dados antigos.
