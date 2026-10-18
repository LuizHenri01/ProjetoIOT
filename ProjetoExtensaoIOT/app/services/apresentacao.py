"""Transforma a linha do banco no dicionário que os templates esperam."""
import re
import unicodedata
import zlib
from datetime import datetime

CORES = ["blue", "green", "yellow", "purple", "red"]


def _slugificar(texto):
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-") or "aula"


def slug_da_disciplina(texto):
    return _slugificar(texto)


def id_do_slug(slug):
    achado = re.match(r"^(\d+)", slug)
    return int(achado.group(1)) if achado else None


def montar_aula(linha):
    inicio = linha["horario_inicio"][:5]
    fim = linha["horario_fim"][:5] if linha["horario_fim"] else None
    em_andamento = fim is None
    return {
        "id": linha["id"],
        "materia_id": linha.get("materia_id"),
        "slug": f'{linha["id"]}-{_slugificar(linha["disciplina"])}',
        "disciplina": linha["disciplina"],
        "nome": linha.get("nome_aula") or f'Aula de {linha["disciplina"]}',
        "professor": linha["professor"] or "Professor não informado",
        "data": datetime.strptime(linha["data"], "%Y-%m-%d").strftime("%d/%m/%Y"),
        "hora": f"{inicio} – {fim}" if fim else f"{inicio} – em andamento",
        "fim_previsto": (linha["horario_fim_previsto"] or "")[:5] if linha.get("horario_fim_previsto") else None,
        "status": "Em andamento" if em_andamento else "Concluída",
        "status_classe": "ongoing" if em_andamento else "done",
        "cor": CORES[zlib.crc32(linha["disciplina"].lower().encode()) % len(CORES)],
        "anotacoes": linha["anotacoes"] or "",
    }


def hora_da_foto(nome):
    """'20261012-142626.jpg' -> '14:26:26' (o nome do arquivo guarda o horário da foto)."""
    achado = re.match(r"^\d{8}-(\d{2})(\d{2})(\d{2})", nome)
    return ":".join(achado.groups()) if achado else ""
