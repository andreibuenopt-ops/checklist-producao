import { admin, emailDe, limpa } from "./_lib.js";
export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ erro: "Método inválido" });
  const b = req.body || {}, nome = limpa(b.nome).toUpperCase(), email = limpa(b.email).toLowerCase(), mat = limpa(b.matricula, 30), senha = String(b.senha || "");
  if (!nome || !/^\S+@\S+\.\S+$/.test(email) || !/^[A-Za-z0-9]+$/.test(mat) || senha.length < 6) return res.status(400).json({ erro: "Preencha tudo corretamente (senha com 6+ caracteres)" });
  const sb = admin();
  const { data, error } = await sb.auth.admin.createUser({ email: emailDe(mat), password: senha, email_confirm: true });
  if (error) return res.status(400).json({ erro: "Matrícula já cadastrada" });
  const { error: e2 } = await sb.from("perfis").insert({ id: data.user.id, nome, email, matricula: mat, funcao: "EXECUTANTE", aprovado: false, trocar_senha: false });
  if (e2) { await sb.auth.admin.deleteUser(data.user.id); return res.status(400).json({ erro: "Não foi possível cadastrar" }); }
  return res.json({ ok: true });
}
