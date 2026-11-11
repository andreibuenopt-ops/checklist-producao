"""Lógica de perguntas com SUB-PERGUNTAS (ex.: "Houve parada programada?").

Uma pergunta-PAI respondida "Sim" abre, naquela ronda, as perguntas-FILHAS
(`pai_item_id` aponta pro pai). Filhas podem exigir foto (`exige_foto`).
Se o pai fica "Não" (ou sem resposta), as filhas não aparecem nem contam.

Tudo aqui é função pura (sem Streamlit/banco) pra poder testar à parte.
`respostas` = {(item_id, horario_id): {"resposta": ..., ...}} (como em
models.listar_respostas); `fotos_por_item` = {(item_id, horario_id): [...]}.
"""
from collections import defaultdict


def separar_itens(itens: list) -> tuple[list, dict]:
    """(itens de topo na ordem, {pai_id: [filhos na ordem]})"""
    topo, filhos = [], defaultdict(list)
    for i in itens:
        if i.get("pai_item_id"):
            filhos[i["pai_item_id"]].append(i)
        else:
            topo.append(i)
    return topo, filhos


def itens_da_ronda(itens: list, respostas: dict, horario_id: str, resposta_de=None) -> list:
    """[(item, eh_filho)] na ordem de exibição: cada pergunta de topo e,
    logo depois do pai respondido 'Sim', as filhas dele.

    `resposta_de(item_id)` deixa usar o valor ATUAL da tela (ainda não
    salvo) no lugar do salvo — o processamento do "Atualizar" precisa disso."""
    if resposta_de is None:
        def resposta_de(item_id):
            return (respostas.get((item_id, horario_id)) or {}).get("resposta")

    topo, filhos = separar_itens(itens)
    saida = []
    for item in topo:
        saida.append((item, False))
        if filhos.get(item["id"]) and resposta_de(item["id"]) == "Sim":
            saida.extend((f, True) for f in filhos[item["id"]])
    return saida


def faltando_respostas(itens: list, respostas: dict, horarios: list) -> int:
    """Perguntas ATIVAS (topo + filhas de pais 'Sim') ainda sem resposta."""
    return sum(
        1
        for h in horarios
        for item, _ in itens_da_ronda(itens, respostas, h["id"])
        if (item["id"], h["id"]) not in respostas
    )


def contar_esperadas(itens: list, respostas: dict, horarios: list) -> int:
    """Total de respostas esperadas hoje (topo + filhas dos pais 'Sim')."""
    return sum(len(itens_da_ronda(itens, respostas, h["id"])) for h in horarios)


def faltando_fotos(itens: list, respostas: dict, fotos_por_item: dict, horarios: list,
                   recem_enviadas=frozenset()) -> int:
    """Itens ATIVOS que exigem foto, já foram respondidos e ainda não têm
    nenhuma foto. `recem_enviadas` = {(item_id, horario_id)} de fotos
    subidas agora, que ainda não estão em `fotos_por_item`."""
    total = 0
    for h in horarios:
        for item, _ in itens_da_ronda(itens, respostas, h["id"]):
            chave = (item["id"], h["id"])
            if not item.get("exige_foto") or chave not in respostas:
                continue
            if not fotos_por_item.get(chave) and chave not in recem_enviadas:
                total += 1
    return total


def ids_filhos_inativos(itens: list, respostas: dict, horario_id: str, resposta_de=None) -> list:
    """Filhas que ficaram SEM pai 'Sim' nessa ronda mas ainda têm resposta
    gravada (o supervisor mudou de Sim pra Não) — precisam ser limpas."""
    ativos = {i["id"] for i, _ in itens_da_ronda(itens, respostas, horario_id, resposta_de)}
    return [
        i["id"] for i in itens
        if i.get("pai_item_id") and i["id"] not in ativos and (i["id"], horario_id) in respostas
    ]
