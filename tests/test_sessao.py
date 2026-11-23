from src.sessao import gerar_token, validar_token

UID = "0b9a6c1e-1111-4222-8333-444455556666"


def test_token_valido_devolve_usuario():
    assert validar_token(gerar_token(UID)) == UID


def test_token_vencido_ou_adulterado_ou_vazio_e_rejeitado():
    assert validar_token(gerar_token(UID, agora=1_000, validade_h=1), agora=1_000 + 3601) is None
    t = gerar_token(UID)
    assert validar_token(t[:-1] + ("0" if t[-1] != "0" else "1")) is None       # assinatura alterada
    assert validar_token(t.replace(UID, "outro-id")) is None                      # trocou o usuário
    assert validar_token("") is None and validar_token(None) is None and validar_token("lixo") is None


def test_login_volta_pela_url(monkeypatch):
    from streamlit.testing.v1 import AppTest
    import src.auth as auth
    from src.auth import Usuario

    token = gerar_token(UID)

    def app():
        import streamlit as st
        from src.auth import exigir_login
        u = exigir_login()
        st.write(f"logado:{u.nome}")

    monkeypatch.setattr(auth, "_usuario_por_id", lambda uid: Usuario(uid, "Maria", "m@x", "1", "producao", True, False))
    at = AppTest.from_function(app)
    at.query_params["s"] = token
    at.run()
    assert not at.exception and "logado:Maria" in at.markdown[0].value

    outro = AppTest.from_function(app)           # sem token → tela de login
    outro.run()
    assert any("Login" in t.value for t in outro.title)
