import { admin, emailDe, SENHA, FUNCOES, SETORES, SETOR_DISC, soMaster, limpa } from "./_lib.js";
export default async function handler(req, res) {
  if (req.method !== "POST") return res.status(405).json({ erro: "Método inválido" });
  const sb = admin();
  if (!(await soMaster(req, sb))) return res.status(403).json({ erro: "Somente o Master" });
  const b = req.body || {};
  try {
    if (b.action === "create_user") {
      const nome = limpa(b.nome).toUpperCase(), email = limpa(b.email).toLowerCase(), mat = limpa(b.matricula, 30);
      if (!nome || !email || !/^[A-Za-z0-9]+$/.test(mat)) return res.status(400).json({ erro: "Preencha nome, e-mail e matrícula (só letras/números)" });
      if (!FUNCOES.includes(b.funcao) || !SETORES.includes(b.setor)) return res.status(400).json({ erro: "Função/setor inválidos" });
      const { data, error } = await sb.auth.admin.createUser({ email: emailDe(mat), password: SENHA(), email_confirm: true });
      if (error) return res.status(400).json({ erro: "Matrícula já cadastrada?" });
      const { error: e2 } = await sb.from("perfis").insert({ id: data.user.id, nome, email, matricula: mat, funcao: b.funcao, setor: b.setor, disc: SETOR_DISC[b.setor] ?? null, aprovado: true, trocar_senha: true });
      if (e2) { await sb.auth.admin.deleteUser(data.user.id); return res.status(400).json({ erro: "Não foi possível criar o perfil" }); }
      await sb.from("permissoes").upsert(["dashboard", "fts", "cm", "ce", "fotos"].map((m) => ({ perfil_id: data.user.id, modulo: m, nivel: 1 })));
      return res.json({ ok: true });
    }
    if (b.action === "reset_password") {
      const id = limpa(b.id, 60);
      const { error } = await sb.auth.admin.updateUserById(id, { password: SENHA() });
      if (error) return res.status(400).json({ erro: "Falha ao redefinir" });
      await sb.from("perfis").update({ trocar_senha: true }).eq("id", id);
      return res.json({ ok: true });
    }
    return res.status(400).json({ erro: "Ação inválida" });
  } catch (e) { return res.status(500).json({ erro: "Erro interno" }); }
}
