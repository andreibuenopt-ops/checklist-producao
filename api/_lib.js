import { createClient } from "@supabase/supabase-js";
export const admin = () => createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY, { auth: { persistSession: false } });
export const emailDe = (m) => String(m).trim().toLowerCase() + "@fts.guararapes.local";
export const SENHA = () => process.env.SENHA_PADRAO || "Guara@123";
export const FUNCOES = ["COORDENADOR", "SUPERVISOR", "DONO_AREA", "EXECUTANTE", "PCM"];
export const SETORES = ["MECÂNICA", "ELÉTRICA", "PRODUÇÃO", "OUTROS", "PCM"];
export const SETOR_DISC = { "ELÉTRICA": 0, "MECÂNICA": 1, "PRODUÇÃO": 2, "OUTROS": 3 };
export async function soMaster(req, sb) {
  const t = (req.headers.authorization || "").replace("Bearer ", "");
  if (!t) return null;
  const { data: { user } } = await sb.auth.getUser(t);
  if (!user) return null;
  const { data: p } = await sb.from("perfis").select("master,aprovado,ativo").eq("id", user.id).maybeSingle();
  return p && p.master && p.aprovado && p.ativo ? user : null;
}
export const limpa = (s, n = 120) => String(s ?? "").trim().slice(0, n);
