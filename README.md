# Checklist Diário Rotineiro — Produção MDF

Sistema em **Python (Streamlit + Supabase)** para digitalizar os checklists
de inspeção das 9 áreas de uma planta de MDF, do pátio de madeira ao
acabamento. Cada área tem um **QR Code fixo** para imprimir e colar no
local; ao escanear, o operador identificado preenche o checklist do turno
atual (Manhã / Tarde / Noite — um horário de checagem por turno, definido
pelo administrador master). Quando concluído e assinado por um supervisor,
coordenador ou master, fica salvo permanentemente no banco.

## Estrutura do projeto

```
checklist-producao/
├── app.py                             # tela inicial / login
├── pages/
│   ├── 1_📋_Preencher_Checklist.py    # formulário do operador
│   ├── 2_📊_Dashboard.py              # cards, tabela, gráficos, exportação
│   ├── 3_🖨️_Gerar_QRCodes.py          # QR Code + cartaz PDF por área
│   ├── 4_🛠️_Administração.py          # usuários e checklists (master)
│   └── 5_💡_Sugestões.py              # sugestão de novos itens de inspeção
├── src/
│   ├── db.py                          # cliente Supabase
│   ├── auth.py                        # login, papéis, reset de senha (bcrypt)
│   ├── turnos.py                      # detecção do turno atual
│   ├── models.py                      # todo o acesso a dados
│   └── qrcode_gen.py                  # geração de QR Code / cartaz PDF
├── sql/
│   └── schema.sql                     # schema completo + seed das 9 áreas
├── scripts/
│   └── criar_master.py                # bootstrap do 1º usuário master
├── requirements.txt
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

## Níveis de acesso

| Papel | Preenche checklist | Assina checklist | Vê dashboard | Exporta dashboard | Gera QR Code | Administração |
|---|---|---|---|---|---|---|
| **producao** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **supervisor** | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| **coordenacao** | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| **master** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Cada colaborador tem registro próprio: **crachá (matrícula)**, **e-mail da
empresa** e **senha pessoal**. Não existe autocadastro — só o master cria
usuários, pela aba Administração → Usuários. Quando alguém esquece a senha,
o master faz o reset por lá; a pessoa é obrigada a definir uma nova senha
no próximo login.

## Como funciona

1. **Login**: e-mail ou matrícula + senha pessoal.
2. **QR Code fixo por área**: aponta para `SEU_APP_URL/?area=slug`. Ao
   escanear, o app detecta a data e o turno atual pelo horário (Manhã
   07h-15h, Tarde 15h-23h, Noite 23h-07h, com o turno Noite "pertencendo"
   à data em que começou) e abre/retoma o checklist daquele turno.
3. **Preenchimento**: cada pergunta é respondida no horário de checagem do
   turno (Sim/Não/N-A). Salva a cada clique — nada se perde se o operador
   fechar o navegador no meio.
4. **Conclusão**: exige comentário quando existe resposta "Não", e a
   confirmação (login) de um usuário supervisor, coordenação ou master —
   é a assinatura digital.
5. **Dashboard**: cards de indicadores (incluindo "Não" em itens
   críticos), tabela do dia, gráficos, exportação em CSV (supervisor/master).
6. **Sugestões**: qualquer usuário pode propor um novo item de inspeção
   com justificativa; o master aprova (o item entra automaticamente no
   checklist) ou rejeita com motivo.
7. **Administração** (master): cadastra usuários, cria checklists novos
   (código, título, área do processo, perguntas, horário de checagem por
   turno), desativa/reativa checklists e remove itens.

---

## Passo a passo — do zero ao ar

### 1. Aplicar o banco de dados no Supabase

1. Acesse o painel do seu projeto: `https://pmwpawnmjnxtvixebfap.supabase.co`
2. Vá em **SQL Editor** → **New query**.
3. Cole o conteúdo inteiro de `sql/schema.sql` e clique em **Run**.
4. Confira em **Table Editor** se as tabelas `usuarios`, `setores_processo`,
   `checklist_templates`, `checklist_template_itens`,
   `checklist_template_horarios`, `checklists`, `checklist_respostas` e
   `checklist_sugestoes` foram criadas, e se `checklist_templates` já tem
   as 9 áreas.

### 2. Baixar e preparar o projeto localmente

```bash
# descompacte o .zip baixado e entre na pasta
cd checklist-producao

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configurar as credenciais do Supabase

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Abra `.streamlit/secrets.toml` e confirme os valores (já vêm preenchidos
com os dados do seu projeto):

```toml
SUPABASE_URL = "https://pmwpawnmjnxtvixebfap.supabase.co"
SUPABASE_KEY = "sb_publishable_yFV_k20saeCCMjG6G7Tv6Q_XxNbmxeb"
APP_BASE_URL = ""
```

Esse arquivo **nunca** é commitado (está no `.gitignore`).

### 4. Criar o primeiro usuário master

Com o venv ativado:

```bash
python scripts/criar_master.py
```

Preencha nome, e-mail, matrícula e a senha mestre quando solicitado. Esse
é o único usuário criado fora da tela do app — todos os demais (produção,
supervisor, coordenação, outros masters) são cadastrados depois, já
logado, em **Administração → Usuários**.

### 5. Rodar localmente

```bash
streamlit run app.py
```

Acesse `http://localhost:8501`, faça login com o usuário master criado no
passo 4.

### 6. Colocar o app no ar (deploy)

Streamlit precisa de um servidor com estado (WebSocket) rodando
continuamente — não roda em serverless (Vercel, Netlify). Caminho gratuito
recomendado: **Streamlit Community Cloud**.

1. Suba o projeto pro GitHub:
   ```bash
   git init
   git add .
   git commit -m "Checklist de produção MDF"
   git remote add origin <url_do_seu_repo>
   git push -u origin main
   ```
2. Acesse [share.streamlit.io](https://share.streamlit.io), conecte sua
   conta GitHub, clique em **New app**.
3. Selecione o repositório, branch `main`, arquivo `app.py`.
4. Em **Advanced settings → Secrets**, cole o conteúdo do seu
   `.streamlit/secrets.toml` — e preencha `APP_BASE_URL` com a URL pública
   que o Streamlit Cloud vai gerar (ex:
   `https://checklist-producao.streamlit.app`).
5. Deploy.

### 7. Gerar e imprimir os QR Codes definitivos

Já com o app publicado e logado como supervisor/coordenação/master, abra
**🖨️ Gerar QR Codes**, confirme a URL pública (deve bater com
`APP_BASE_URL`) e baixe o cartaz PDF de cada área para imprimir e colar.

### 8. Cadastrar a equipe

Logado como master, em **🛠️ Administração → Usuários**, cadastre cada
colaborador com crachá, e-mail e senha inicial, escolhendo o nível de
acesso correto (produção / supervisor / coordenação / master).

### 9. Ajustar checklists conforme a operação evolui

- **Criar checklist novo**: Administração → Novo Checklist.
- **Adicionar item a um checklist existente**: qualquer usuário manda pela
  aba 💡 Sugestões; o master aprova e o item entra automaticamente.
- **Remover item ou desativar checklist**: Administração → Checklists
  Cadastrados.

---

## Segurança

- Senhas: hash bcrypt, nunca texto puro.
- `secrets.toml` nunca é commitado.
- RLS habilitado em todas as tabelas no Supabase; o controle de acesso real
  (quem loga, quem faz o quê) é feito pelo próprio app — a chave do
  Supabase fica em `st.secrets` e nunca chega ao navegador do usuário.
- Sem autocadastro: só o master cria contas.
