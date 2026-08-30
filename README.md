# Checklist Diário Rotineiro — Produção

Sistema em **Python (Streamlit + Supabase)** para digitalizar os checklists de
inspeção de produção. Cada área tem um **QR Code fixo** para imprimir e colar
no local; ao escanear, o operador identificado preenche o checklist do turno
atual (Manhã / Tarde / Noite), e quando ele é concluído e assinado pelo
supervisor, fica salvo permanentemente no banco (Supabase). Um dashboard
mostra os resultados do dia atual ou de qualquer dia passado.

Checklists digitalizados nesta versão:
- **FRCDM2011.r02** — Sifter e Ventiladores Externos (9 itens)
- **FRCDM2003.r02** — Linha de Formação (15 itens)

## Estrutura do projeto

```
checklist-producao/
├── app.py                          # tela inicial / login
├── pages/
│   ├── 1_📋_Preencher_Checklist.py # formulário do operador
│   ├── 2_📊_Dashboard.py           # cards, tabela e gráficos
│   └── 3_🖨️_Gerar_QRCodes.py       # gera QR Code + cartaz PDF por área (supervisor/admin)
├── src/
│   ├── db.py                       # cliente Supabase
│   ├── auth.py                     # cadastro/login (bcrypt)
│   ├── turnos.py                   # detecção do turno atual
│   ├── models.py                   # acesso a dados (checklists, respostas, dashboard)
│   └── qrcode_gen.py                # geração de QR Code / cartaz PDF
├── sql/
│   └── schema.sql                  # schema completo + seed dos 2 checklists
├── requirements.txt
└── .streamlit/
    ├── config.toml
    └── secrets.toml.example
```

## Como funciona

1. **Cadastro/login**: nome completo, e-mail, matrícula e senha (senha
   armazenada com hash bcrypt — nunca em texto puro).
2. **QR Code fixo por área**: aponta para `SEU_APP_URL/?area=sifter` (ou
   `linha-formacao`). Ao escanear, o app detecta a data e o turno atual pelo
   horário (Manhã 07h-15h, Tarde 15h-23h, Noite 23h-07h, com o turno Noite
   "pertencendo" à data em que começou) e abre/retoma automaticamente o
   checklist daquele turno.
3. **Preenchimento**: cada pergunta é respondida em cada horário de ronda do
   turno (Sim/Não/N-A). As respostas são salvas no Supabase a cada clique —
   nada se perde se o operador fechar o navegador no meio.
4. **Conclusão**: exige comentário quando existe alguma resposta "Não", e a
   confirmação (login) de um usuário com papel *supervisor* ou *admin* — é a
   "assinatura" digital. Só então o checklist muda para **completo**.
5. **Dashboard**: cards de indicadores, tabela de checklists do dia e dois
   gráficos (pizza de Sim/Não/N-A e barras das perguntas com mais "Não"),
   filtráveis por data (qualquer dia) e por área.

## Rodando localmente

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # preencha com suas chaves
streamlit run app.py
```

## Banco de dados (Supabase)

O projeto Supabase já foi criado e o schema (`sql/schema.sql`) já foi aplicado
com os dois checklists cadastrados. Dados de conexão:

- **URL do projeto**: `https://siejpolqypphzzjrnzxo.supabase.co`
- **Chave**: a chave `anon` do projeto (Settings → API no painel do Supabase)

Para recriar em outro projeto Supabase do zero, basta rodar `sql/schema.sql`
inteiro no SQL Editor do projeto.

## Deploy

**Importante:** Streamlit precisa de um servidor com estado (WebSocket)
rodando continuamente — a Vercel só executa funções serverless sem estado, e
por isso **não roda Streamlit**. O caminho recomendado (gratuito, feito para
Streamlit) é o **Streamlit Community Cloud**:

1. Suba este repositório no GitHub (veja abaixo).
2. Acesse [share.streamlit.io](https://share.streamlit.io), conecte sua conta
   GitHub e clique em "New app".
3. Selecione o repositório, branch `main` e o arquivo `app.py`.
4. Em "Advanced settings → Secrets", cole o conteúdo do seu
   `.streamlit/secrets.toml` (URL, chave do Supabase e a URL pública que o
   Streamlit Cloud vai te dar, ex: `https://checklist-producao.streamlit.app`).
5. Deploy. Depois, na página **Gerar QR Codes**, informe essa URL pública para
   gerar os QR Codes definitivos e imprimir.

## Segurança

- Senhas: hash bcrypt, nunca texto puro.
- `secrets.toml` nunca é commitado (está no `.gitignore`).
- RLS habilitado em todas as tabelas no Supabase; o controle de acesso real é
  feito pelo próprio app (login), já que ele roda inteiramente no servidor —
  a chave do Supabase nunca chega ao navegador do usuário.
