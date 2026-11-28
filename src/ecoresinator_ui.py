"""Renderização do formulário do Ecoresinator — extraída pra função
reutilizável porque tanto a página própria (sidebar) quanto o fluxo de
QR code fixo (app.py) precisam do mesmo formulário."""
import pandas as pd
import streamlit as st

from src.auth import autenticar
from src.ecoresinator import (
    CAMPOS_GLOBAIS_NUMERICOS,
    CAMPOS_GLOBAIS_SIMNAO,
    CAMPOS_GLOBAIS_TEXTO,
    buscar_ecoresinator,
    concluir_ecoresinator,
    definir_colaborador_ecoresinator,
    obter_ou_criar_ecoresinator,
    salvar_ecoresinator,
)
from src.fotos import baixar_miniatura, enviar_foto_ecoresinator, listar_fotos_ecoresinator
from src.models import nomes_usuarios, obter_logo_bytes_com_fallback
from src.pdf_ecoresinator import gerar_pdf_ecoresinator
from src.turno_ui import escolher_turno

MAX_FOTOS_ECO = 8


def tem_leituras_digitadas(checklist: dict) -> bool:
    """True se alguma leitura/parâmetro foi digitado e salvo (alternativa à foto)."""
    if any(
        l.get(c) not in (None, "") for l in (checklist.get("leituras_bicos") or [])
        for c in ("vazao_lmin", "eficiencia_pct", "abertura_valvula_pct")
    ):
        return True
    return any(
        checklist.get(c) not in (None, "", 0, 0.0)
        for c in (*CAMPOS_GLOBAIS_SIMNAO, *CAMPOS_GLOBAIS_NUMERICOS, *CAMPOS_GLOBAIS_TEXTO)
    )


def _mostrar_fotos(fotos: list):
    if not fotos:
        return
    cols = st.columns(4)
    for i, f in enumerate(fotos):
        try:
            cols[i % 4].image(baixar_miniatura(f["caminho"]), use_container_width=True)
        except Exception:
            cols[i % 4].caption("(foto salva, miniatura indisponível)")


def _fotos_seguras(checklist_id: str) -> list:
    try:
        return listar_fotos_ecoresinator(checklist_id)
    except Exception:          # tabela ainda não criada (migration_ecoresinator_fotos.sql)
        return []


ROTULOS_BICO = {
    "numero": "Bico", "vazao_lmin": "Vazão (L/min)", "eficiencia_pct": "Eficiência (%)",
    "abertura_valvula_pct": "Abertura válvula (%)", "falha_3_vias": "Falha 3 vias?",
    "falha_agulha": "Falha agulha?", "falha_vazao": "Falha vazão?",
}
ROTULOS_GLOBAIS = {
    "bicos_em_manutencao": "Bicos em manutenção (quais/quantos)",
    "bicos_em_producao": "Bicos em produção",
    "rodizio_ligado": "Rodízio ligado?",
    "flush_ligado": "Flush ligado?",
    "pressao_bomba_resina": "Pressão bomba resina",
    "pressao_coletor_resina": "Pressão coletor resina",
    "pressao_bomba_agua": "Pressão bomba água",
    "pressao_coletor_agua": "Pressão coletor água",
    "pressao_vapor_coletor": "Pressão vapor coletor",
    "vazao_resina_bomba": "Vazão resina na bomba (L/min)",
    "valvula_proporcional_auto": "Válvula proporcional em automático?",
    "agulhas_force_abertura": "Agulhas com \"force\" de abertura?",
    "bomba_resina_manutencao": "Alguma bomba de resina em manutenção?",
    "bomba_resina_em_uso": "Qual bomba de resina está em uso?",
    "bomba_parafina_em_uso": "Qual bomba de parafina está em uso?",
}


def renderizar_ecoresinator_somente_leitura(checklist: dict, turno_nome: str, nomes: dict):
    """Mostra na tela tudo que foi lido/registrado (bicos + parâmetros + comentário)."""
    situacao = "✅ Concluída e assinada" if checklist["status"] == "completo" else "🟡 Em andamento (não assinada)"
    st.markdown(
        f"**{situacao}** · Turno {turno_nome} · {str(checklist['data'])[:10][8:]}/{str(checklist['data'])[5:7]}/{str(checklist['data'])[:4]}"
        + (f" · Hora real **{checklist['horario_real']}**" if checklist.get("horario_real") else "")
    )
    col1, col2 = st.columns(2)
    col1.metric("Colaborador", nomes.get(checklist.get("colaborador_id"), "-"))
    col2.metric("Assinado por", nomes.get(checklist.get("supervisor_id"), "-"))

    fotos_ro = _fotos_seguras(checklist["id"])
    if fotos_ro:
        st.markdown(f"**📷 Fotos da rotina ({len(fotos_ro)})**")
        _mostrar_fotos(fotos_ro)

    leituras = [l for l in (checklist.get("leituras_bicos") or [])
                if any(l.get(c) not in (None, "") for c in ("vazao_lmin", "eficiencia_pct", "abertura_valvula_pct"))]
    if leituras:
        st.markdown("**Leituras por bico**")
        st.dataframe(pd.DataFrame(leituras).rename(columns=ROTULOS_BICO), hide_index=True, use_container_width=True)

    linhas = []
    for campo, rotulo in ROTULOS_GLOBAIS.items():
        valor = checklist.get(campo)
        if valor not in (None, "", 0, 0.0):
            linhas.append({"Parâmetro": rotulo, "Valor": str(valor)})
    if linhas:
        st.markdown("**Parâmetros gerais**")
        st.dataframe(pd.DataFrame(linhas), hide_index=True, use_container_width=True)
    if checklist.get("comentario"):
        st.markdown(f"**💬 Comentário:** {checklist['comentario']}")


def botao_pdf_ecoresinator(checklist: dict, turno_nome: str, nomes: dict, chave: str):
    dados_pdf = {
        "checklist": checklist, "turno_nome": turno_nome,
        "leituras_bicos": checklist.get("leituras_bicos", []),
        "colaborador_nome": nomes.get(checklist.get("colaborador_id"), "-"),
        "supervisor_nome": nomes.get(checklist.get("supervisor_id"), "-"),
    }
    st.download_button(
        "⬇️ Exportar PDF desta rotina (opcional)",
        data=lambda: gerar_pdf_ecoresinator(dados_pdf, obter_logo_bytes_com_fallback()), on_click="ignore",
        file_name=f"ecoresinator_{checklist['id']}.pdf", mime="application/pdf", key=f"pdf_eco_{chave}",
    )


def renderizar_ecoresinator(usuario):
    st.title("🧪 Rotina de Inspeção — Ecoresinator")
    st.caption("Cozinha de cola · deve ser feita em todos os turnos, logo na primeira hora.")

    turno = escolher_turno("ecoresinator")
    st.caption(f"Turno **{turno.nome}** · Data de referência **{turno.data_referencia.strftime('%d/%m/%Y')}**")

    checklist = obter_ou_criar_ecoresinator(turno.turno_id, turno.data_referencia)
    definir_colaborador_ecoresinator(checklist["id"], usuario.id)
    checklist = buscar_ecoresinator(checklist["id"])

    st.divider()

    if checklist["status"] == "completo":
        nomes = nomes_usuarios((checklist.get("colaborador_id"), checklist.get("supervisor_id")))
        renderizar_ecoresinator_somente_leitura(checklist, turno.nome, nomes)
        botao_pdf_ecoresinator(checklist, turno.nome, nomes, f"preench_{checklist['id']}")
        return

    horario_real = st.text_input(
        "Horário real da rotina (ex: 08:15)", value=checklist.get("horario_real", ""),
        help="O formulário físico não tem horário fixo — registre a hora real em que fez a inspeção.",
    )

    # ---- FOTOS (jeito rápido): fotografe o painel/leituras em vez de digitar tudo --------------
    st.subheader("📷 Fotos da rotina")
    st.caption("Fotografe a tela/painel do Ecoresinator (leituras dos bicos, pressões e vazão). "
               "Isso já vale como registro — digitar é opcional.")
    fotos_eco = _fotos_seguras(checklist["id"])
    _mostrar_fotos(fotos_eco)
    versao = st.session_state.setdefault(f"eco_vfoto_{checklist['id']}", 0)
    if len(fotos_eco) < MAX_FOTOS_ECO:
        novas = st.file_uploader(
            "Foto", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True,
            key=f"eco_foto_{checklist['id']}_{versao}", label_visibility="collapsed",
            help=f"No celular, escolha 'Tirar foto'. Até {MAX_FOTOS_ECO} fotos.",
        )
        if novas and st.button("📤 Enviar fotos", type="primary", use_container_width=True):
            enviadas, falhas = 0, 0
            for arq in novas[: MAX_FOTOS_ECO - len(fotos_eco)]:
                try:
                    enviar_foto_ecoresinator(checklist["id"], arq.getvalue(), usuario.id)
                    enviadas += 1
                except Exception:
                    falhas += 1
            st.session_state[f"eco_vfoto_{checklist['id']}"] = versao + 1
            if falhas:
                st.error(f"{falhas} foto(s) não foram enviadas (confira se a atualização do banco foi feita). Tente de novo.")
            if enviadas:
                st.toast(f"{enviadas} foto(s) enviada(s).")
                st.rerun()
    else:
        st.caption(f"Limite de {MAX_FOTOS_ECO} fotos atingido.")

    with st.expander("⌨️ Digitar leituras e parâmetros (opcional)"):
        _formulario_digitado(checklist, usuario, horario_real)

    st.divider()
    comentario = st.text_area(
        "Descrever o porquê das validações em 'Não' / falhas encontradas",
        value=checklist.get("comentario", "") or "",
        key=f"eco_comentario_{checklist['id']}",
    )

    st.subheader("✍️ Conclusão")
    st.warning("⚠️ Depois de concluída, esta rotina não pode mais ser editada.")
    tem_registro = bool(fotos_eco) or tem_leituras_digitadas(checklist)
    if not tem_registro:
        st.info("Envie pelo menos 1 foto (ou digite as leituras e salve) para poder concluir.")

    # Qualquer usuário logado conclui sozinho, com a própria sessão.
    st.caption(f"Você vai concluir e assinar como **{usuario.nome}**.")
    if st.button("✅ Concluir rotina", type="primary", use_container_width=True, disabled=not tem_registro):
        _salvar_horario(checklist, horario_real)
        concluir_ecoresinator(checklist["id"], usuario.id, comentario.strip())
        st.success(f"Rotina concluída e assinada por {usuario.nome}. ✅")
        st.balloons()
        st.rerun()

    with st.expander("🔏 Assinar com outro usuário (supervisor) — opcional"):
        with st.form(f"form_concluir_eco_{checklist['id']}"):
            identificador_sup = st.text_input("E-mail ou matrícula de quem assina")
            senha_sup = st.text_input("Senha", type="password")
            concluir = st.form_submit_button("Assinar e concluir com outro usuário", use_container_width=True,
                                             disabled=not tem_registro)
        if concluir:
            assinante, erro = autenticar(identificador_sup, senha_sup)
            if not assinante:
                st.error(erro or "Não foi possível validar o usuário.")
            elif not assinante.pode_assinar_checklist:
                st.error("Esse usuário não tem permissão para assinar checklists.")
            else:
                _salvar_horario(checklist, horario_real)
                concluir_ecoresinator(checklist["id"], assinante.id, comentario.strip())
                st.success(f"Rotina concluída e assinada por {assinante.nome}. ✅")
                st.balloons()
                st.rerun()


def _salvar_horario(checklist: dict, horario_real: str):
    """Só-foto não passa pelo 'Salvar leituras': grava a hora real ao concluir."""
    if (horario_real or "") != (checklist.get("horario_real") or ""):
        salvar_ecoresinator(checklist["id"], {"horario_real": horario_real})


def _formulario_digitado(checklist: dict, usuario, horario_real: str):
    st.subheader("Leituras por bico")
    df_bicos = pd.DataFrame(checklist.get("leituras_bicos", []))
    df_editado = st.data_editor(
        df_bicos,
        column_config={
            "numero": st.column_config.NumberColumn("Bico", disabled=True),
            "vazao_lmin": st.column_config.NumberColumn("Vazão (L/min)"),
            "eficiencia_pct": st.column_config.NumberColumn("Eficiência (%)"),
            "abertura_valvula_pct": st.column_config.NumberColumn("Abertura válvula (%)"),
            "falha_3_vias": st.column_config.SelectboxColumn("Falha 3 vias?", options=["Sim", "Não"]),
            "falha_agulha": st.column_config.SelectboxColumn("Falha agulha?", options=["Sim", "Não"]),
            "falha_vazao": st.column_config.SelectboxColumn("Falha vazão?", options=["Sim", "Não"]),
        },
        hide_index=True, use_container_width=True, key=f"editor_bicos_{checklist['id']}",
    )

    st.subheader("Parâmetros gerais")
    valores_globais = {}
    col1, col2 = st.columns(2)
    campos = list(ROTULOS_GLOBAIS.items())
    for i, (campo, rotulo) in enumerate(campos):
        col = col1 if i % 2 == 0 else col2
        if campo in CAMPOS_GLOBAIS_SIMNAO:
            valor_atual = checklist.get(campo)
            valores_globais[campo] = col.selectbox(
                rotulo, ["", "Sim", "Não"],
                index=["", "Sim", "Não"].index(valor_atual) if valor_atual in ("Sim", "Não") else 0,
                key=f"eco_{campo}_{checklist['id']}",
            ) or None
        elif campo in CAMPOS_GLOBAIS_NUMERICOS:
            valores_globais[campo] = col.number_input(
                rotulo, value=float(checklist.get(campo) or 0.0), key=f"eco_{campo}_{checklist['id']}",
            )
        else:
            valores_globais[campo] = col.text_input(
                rotulo, value=checklist.get(campo, "") or "", key=f"eco_{campo}_{checklist['id']}",
            )

    if st.button("💾 Salvar leituras", use_container_width=True):
        payload = {**valores_globais, "horario_real": horario_real}
        payload["leituras_bicos"] = df_editado.to_dict("records")
        salvar_ecoresinator(checklist["id"], payload)
        st.success("Leituras salvas.")
        st.rerun()
