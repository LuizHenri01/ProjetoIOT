import os
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename

PASTA_FOTOS = Path(__file__).resolve().parents[2] / "data" / "fotos"


EXTENSOES_PERMITIDAS = {"jpg", "jpeg", "png", "webp", "gif", "heic", "heif"}


def conteudo_de_imagem_valido(arquivo, extensao):
    """Confere a assinatura do arquivo, além da extensão enviada pelo navegador."""
    assinaturas = {
        "jpg": lambda dados: dados.startswith(b"\xff\xd8\xff"),
        "jpeg": lambda dados: dados.startswith(b"\xff\xd8\xff"),
        "png": lambda dados: dados.startswith(b"\x89PNG\r\n\x1a\n"),
        "gif": lambda dados: dados.startswith((b"GIF87a", b"GIF89a")),
        "webp": lambda dados: len(dados) >= 12 and dados[:4] == b"RIFF" and dados[8:12] == b"WEBP",
        "heic": lambda dados: _assinatura_heif(dados),
        "heif": lambda dados: _assinatura_heif(dados),
    }
    try:
        inicio = arquivo.stream.read(32)
        arquivo.stream.seek(0)
    except (AttributeError, OSError):
        return False
    return assinaturas.get(extensao, lambda _: False)(inicio)


def _assinatura_heif(dados):
    marcas_heif = (b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1")
    return len(dados) >= 12 and dados[4:8] == b"ftyp" and any(
        marca in dados[8:32] for marca in marcas_heif
    )


def listar_fotos(aula_id):
    """Nomes das fotos da aula, da mais antiga para a mais nova."""
    pasta = PASTA_FOTOS / f"aula_{aula_id}"
    if not pasta.is_dir():
        return []
    return sorted(arquivo.name for arquivo in pasta.iterdir() if arquivo.is_file())


def pasta_da_aula(aula_id):
    return PASTA_FOTOS / f"aula_{aula_id}"


def salvar_foto(arquivo, aula_id):
    agora = datetime.now()
    timestamp = agora.strftime("%Y%m%d-%H%M%S-%f")
    nome_seguro = secure_filename(arquivo.filename or "foto.jpg").lower()
    extensao = nome_seguro.rsplit(".", 1)[-1] if "." in nome_seguro else "jpg"

    pasta_aula = PASTA_FOTOS / f"aula_{aula_id}"
    pasta_aula.mkdir(parents=True, exist_ok=True)
    for tentativa in range(100):
        sufixo = f"-{tentativa}" if tentativa else ""
        caminho_completo = pasta_aula / f"{timestamp}{sufixo}.{extensao}"
        try:
            descritor = os.open(
                caminho_completo,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError:
            continue

        try:
            with os.fdopen(descritor, "wb") as destino:
                arquivo.save(destino)
        except Exception:
            caminho_completo.unlink(missing_ok=True)
            raise
        break
    else:
        raise OSError("Não foi possível criar um nome único para a foto")

    return str(caminho_completo.relative_to(PASTA_FOTOS.parents[1]))
