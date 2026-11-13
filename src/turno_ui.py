"""Seletor de turno na hora de preencher.

Por padrão o sistema escolhe o turno pelo relógio. Mas quem chega antes da
virada de turno (ou termina depois dela) acabava preenchendo o turno
vizinho — e o histórico mostrava a turma errada. Aqui a pessoa confirma ou
troca: turno anterior, atual ou próximo.
"""
import streamlit as st

from src.turnos import LETRA_TURNO, NOME_TURNO, Turno, turno_e_data_referencia, turnos_selecionaveis


def escolher_turno(chave: str) -> Turno:
    """Mostra o seletor e devolve o Turno escolhido (padrão: o turno atual).
    `chave` separa as escolhas de telas diferentes (cada checklist/rotina)."""
    atual = turno_e_data_referencia()
    opcoes = turnos_selecionaveis(atual)
    ids = [(t.turno_id, t.data_referencia) for t in opcoes]
    rotulos = dict(zip(ids, ("Anterior", "Atual", "Próximo")))

    chave_sel = f"turno_escolhido_{chave}"
    # Se o turno atual virou no meio do preenchimento, mantém a escolha
    # enquanto ela ainda for uma das 3 opções; senão volta pro atual.
    if st.session_state.get(chave_sel) not in ids:
        st.session_state[chave_sel] = ids[1]

    escolhido = st.radio(
        "Turno deste checklist",
        options=ids,
        format_func=lambda i: f"{rotulos[i]}: {LETRA_TURNO[i[0]]} {NOME_TURNO[i[0]]}",
        key=chave_sel,
        horizontal=True,
        help="O sistema sugere o turno pelo horário. Se você chegou antes da virada do turno, "
             "ou está terminando o turno que acabou de passar, escolha o certo aqui.",
    )
    if escolhido != ids[1]:
        st.warning(
            f"Você escolheu o turno **{LETRA_TURNO[escolhido[0]]} {NOME_TURNO[escolhido[0]]}** "
            f"({escolhido[1].strftime('%d/%m/%Y')}), que não é o turno atual."
        )
    return Turno(escolhido[0], NOME_TURNO[escolhido[0]], escolhido[1])
