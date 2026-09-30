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
from src.models import nomes_usuarios, obter_logo_bytes_com_fallback
from src.pdf_ecoresinator import gerar_pdf_ecoresinator
from src.turnos import turno_e_data_referencia

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


def renderizar_ecoresinator(usuario):
    st.title("🧪 Rotina de Inspeção — Ecoresinator")
    st.caption("Cozinha de cola · deve ser feita em todos os turnos, logo na primeira hora.")

    turno = turno_e_data_referencia()
    st.caption(f"Turno **{turno.nome}** · Data de referência **{turno.data_referencia.strftime('%d/%m/%Y')}**")

    checklist = obter_ou_criar_ecoresinator(turno.turno_id, turno.data_referencia)
    definir_colaborador_ecoresinator(checklist["id"], usuario.id)
    checklist = buscar_ecoresinator(checklist["id"])

    st.divider()

    if checklist["status"] == "completo":
        st.success("Esta rotina já foi concluída e assinada. ✅")
        nomes = nomes_usuarios((checklist.get("colaborador_id"), checklist.get("supervisor_id")))
        col1, col2 = st.columns(2)
        col1.metric("Colaborador", nomes.get(checklist.get("colaborador_id"), "-"))
        col2.metric("Assinado por", nomes.get(checklist.get("supervisor_id"), "-"))

        st.dataframe(pd.DataFrame(checklist.get("leituras_bicos", [])).rename(columns=ROTULOS_BICO), hide_index=True)

        dados_pdf = {
            "checklist": checklist,
            "turno_nome": turno.nome,
            "leituras_bicos": checklist.get("leituras_bicos", []),
            "colaborador_nome": nomes.get(checklist.get("colaborador_id"), "-"),
            "supervisor_nome": nomes.get(checklist.get("supervisor_id"), "-"),
        }
        pdf_bytes = gerar_pdf_ecoresinator(dados_pdf, obter_logo_bytes_com_fallback())
        st.download_button(
            "⬇️ Exportar PDF desta rotina", data=pdf_bytes,
            file_name=f"ecoresinator_{checklist['id']}.pdf", mime="application/pdf",
        )
        return

    horario_real = st.text_input(
        "Horário real da rotina (ex: 08:15)", value=checklist.get("horario_real", ""),
        help="O formulário físico não tem horário fixo — registre a hora real em que fez a inspeção.",
    )

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

    if st.button("💾 Salvar leituras", type="primary", use_container_width=True):
        payload = {**valores_globais, "horario_real": horario_real}
        payload["leituras_bicos"] = df_editado.to_dict("records")
        salvar_ecoresinator(checklist["id"], payload)
        st.success("Leituras salvas.")
        st.rerun()

    st.divider()
    comentario = st.text_area(
        "Descrever o porquê das validações em 'Não' / falhas encontradas",
        value=checklist.get("comentario", "") or "",
        key=f"eco_comentario_{checklist['id']}",
    )

    st.subheader("✍️ Assinatura de conclusão")
    st.warning("⚠️ Depois de concluída, esta rotina não pode mais ser editada. Salve as leituras antes de concluir.")

    if usuario.pode_concluir_proprio_checklist:
        st.caption(f"Você vai concluir e assinar como **{usuario.nome}**.")
        if st.button("✅ Concluir rotina", type="primary", use_container_width=True):
            concluir_ecoresinator(checklist["id"], usuario.id, comentario.strip())
            st.success(f"Rotina concluída e assinada por {usuario.nome}. ✅")
            st.balloons()
            st.rerun()
    else:
        with st.form(f"form_concluir_eco_{checklist['id']}"):
            identificador_sup = st.text_input("E-mail ou matrícula de quem assina")
            senha_sup = st.text_input("Senha", type="password")
            concluir = st.form_submit_button("Concluir rotina", type="primary", use_container_width=True)
        if concluir:
            assinante, erro = autenticar(identificador_sup, senha_sup)
            if not assinante:
                st.error(erro or "Não foi possível validar o usuário.")
            elif not assinante.pode_assinar_checklist:
                st.error("Esse usuário não tem permissão para assinar checklists.")
            else:
                concluir_ecoresinator(checklist["id"], assinante.id, comentario.strip())
                st.success(f"Rotina concluída e assinada por {assinante.nome}. ✅")
                st.balloons()
                st.rerun()
