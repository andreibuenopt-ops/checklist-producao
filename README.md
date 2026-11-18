# FTS Manager — Guararapes (Vercel + Supabase)
SQL (Supabase > SQL Editor), nesta ordem: schema.sql → schema2_acesso.sql → migracao3_vercel.sql → migracao4_aprovacao.sql → migracao5_areas.sql → migracao6_cc_mdf02.sql → migracao7_ce_planilha.sql → migracao8_ftcm.sql → migracao9_especialidade.sql → migracao10_sdcv.sql → seed_fts.sql
1. Supabase > Authentication > Sign In / Providers: desligue "Allow new users to sign up"
2. GitHub: suba esta pasta no repositório (substitui o app Streamlit)
3. Vercel: importe o repositório (Framework: Other). Environment Variables: SUPABASE_URL, SUPABASE_SERVICE_KEY, SENHA_PADRAO=Guara@123
`index.html` é gerado por `python3 build.py` a partir de `src/`.
