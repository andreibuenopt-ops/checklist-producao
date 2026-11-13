"""Parada de linha: "Houve parada?" -> tipo (programada, saída de finos,
corretiva) -> checklist específico daquele tipo, com foto por pergunta.
Cada parada abre um checklist NOVO (pode haver várias no turno)."""
import streamlit as st

from src.auth import exigir_login
from src.models import obter_logo_bytes_com_fallback
from src.paradas import TIPOS, TIPOS_CURTOS, criar_parada, listar_paradas_do_turno
from src.paradas_ui import renderizar_parada
from src.sidebar import mostrar_usuario_logado
from src.tema import aplicar_tema, desativar_traducao_automatica
from src.turno_ui import escolher_turno

st.set_page_config(page_title="Parada de linha", page_icon="🛑", layout="wide")

desativar_traducao_automatica()
usuario = exigir_login()
aplicar_tema(usuario)
mostrar_usuario_logado(usuario)

st.title("🛑 Parada de linha")
st.caption("Registre aqui as paradas do turno. Cada parada tem o seu checklist, com foto do local em cada pergunta.")

turno = escolher_turno("parada")
paradas = listar_paradas_do_turno(turno.turno_id, turno.data_referencia)
sufixo = f"{turno.turno_id}_{turno.data_referencia.isoformat()}"

houve = st.radio(
    "Houve parada na linha neste turno?", ["Não", "Sim"], index=1 if paradas else 0,
    horizontal=True, key=f"houve_parada_{sufixo}",
)

if houve == "Não":
    st.info("Nenhuma parada para registrar neste turno. ✅")
else:
    tipo = st.radio(
        "Qual o tipo da parada?", list(TIPOS_CURTOS), format_func=lambda t: TIPOS_CURTOS[t],
        horizontal=True, key=f"tipo_parada_{sufixo}",
    )
    if st.button(f"➕ Abrir checklist de parada {TIPOS_CURTOS[tipo].lower()}", type="primary", use_container_width=True):
        nova = criar_parada(tipo, turno.turno_id, turno.data_referencia, usuario.id)
        st.session_state[f"parada_sel_{sufixo}"] = nova["id"]
        st.rerun()

if paradas:
    st.divider()
    st.subheader("Paradas deste turno")
    ids = [p["id"] for p in paradas]
    por_id = {p["id"]: p for p in paradas}
    # abre direto a que acabou de ser criada; se a escolhida sumiu, volta pra última
    if st.session_state.get(f"parada_sel_{sufixo}") not in ids:
        st.session_state[f"parada_sel_{sufixo}"] = ids[-1]

    def _rotulo(pid):
        p = por_id[pid]
        hora = str(p["iniciada_em"])[11:16]
        return f"{TIPOS_CURTOS[p['tipo']]} · iniciada {hora} · {'concluída' if p['status'] == 'completo' else 'em andamento'}"

    escolhida = st.selectbox("Parada", ids, format_func=_rotulo, key=f"parada_sel_{sufixo}")
    renderizar_parada(usuario, escolhida, obter_logo_bytes_com_fallback())
