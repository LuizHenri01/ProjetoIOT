import unicodedata
from datetime import datetime

from app.database.conexao import PASTA_TRANSCRICOES

TAMANHO_MAXIMO_TEXTO = 2000
LIMITE_RESULTADOS_BUSCA = 50


def _normalizar_busca(texto):
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode("ascii").lower()


def _iterar_linhas(aula_id):
    """Lê uma transcrição por linha, sem carregar o arquivo inteiro na memória."""
    caminho = PASTA_TRANSCRICOES / f"aula_{aula_id}.txt"
    if not caminho.exists():
        return

    with caminho.open("r", encoding="utf-8") as arquivo:
        for indice, linha in enumerate(arquivo, start=1):
            timestamp, separador, texto = linha.rstrip("\r\n").partition(" - ")
            if not separador:
                raise ValueError(f"Formato inválido no arquivo de transcrição: {caminho}")
            yield {"id": indice, "timestamp": timestamp, "texto": texto}


def salvar_transcricao(aula_id, texto):
    """Acrescenta uma fala ao arquivo de texto da aula."""
    texto = " ".join(texto.split())[:TAMANHO_MAXIMO_TEXTO]
    timestamp = datetime.now().strftime("%H:%M:%S")

    PASTA_TRANSCRICOES.mkdir(parents=True, exist_ok=True)
    caminho = PASTA_TRANSCRICOES / f"aula_{aula_id}.txt"
    with caminho.open("a", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(f"{timestamp} - {texto}\n")

    return {"timestamp": timestamp, "texto": texto}


def listar_transcricoes(aula_id):
    """Lê todos os trechos quando uma função realmente precisa do conteúdo completo."""
    return list(_iterar_linhas(aula_id) or [])


def obter_previa_transcricoes(aula_id, limite=3, tamanho_maximo=240):
    previa = []
    total = 0
    trecho_grande = False
    for fala in _iterar_linhas(aula_id) or ():
        total += 1
        if len(fala["texto"]) > tamanho_maximo and total <= limite:
            trecho_grande = True
        if total <= limite:
            previa.append({
                **fala,
                "texto": fala["texto"][:tamanho_maximo] + ("…" if len(fala["texto"]) > tamanho_maximo else ""),
            })

    return {
        "transcricoes": previa,
        "total": total,
        "tem_mais": total > limite or trecho_grande,
    }


def buscar_transcricoes(aula_id, busca, limite=LIMITE_RESULTADOS_BUSCA):
    termo = _normalizar_busca(str(busca or "").strip())
    if not termo:
        return {"transcricoes": [], "total": 0, "limite": limite}

    encontrados = []
    total = 0
    for fala in _iterar_linhas(aula_id) or ():
        normalizado = _normalizar_busca(fala["texto"])
        posicao = normalizado.find(termo)
        if posicao < 0:
            continue

        total += 1
        if len(encontrados) >= limite:
            continue
        inicio = max(0, posicao - 100)
        fim = min(len(fala["texto"]), posicao + len(termo) + 140)
        trecho = fala["texto"][inicio:fim]
        if inicio:
            trecho = "…" + trecho
        if fim < len(fala["texto"]):
            trecho += "…"
        encontrados.append({
            "id": fala["id"], "timestamp": fala["timestamp"], "texto": trecho,
        })

    return {"transcricoes": encontrados, "total": total, "limite": limite}
