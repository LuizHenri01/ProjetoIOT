"""Inscrições e envio de notificações push por navegador/aparelho."""
import base64
import html
import json
import logging
import os
import threading
from urllib.parse import urlsplit
from datetime import datetime

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from app.database.conexao import PASTA_DADOS, obter_conexao

logger = logging.getLogger(__name__)
CAMINHO_CHAVE_VAPID = PASTA_DADOS / "vapid_private.pem"
_VAPID_LOCK = threading.Lock()


def _chaves_vapid():
    """Cria uma chave VAPID persistente; a chave privada nunca sai do servidor."""
    with _VAPID_LOCK:
        PASTA_DADOS.mkdir(parents=True, exist_ok=True)
        if not CAMINHO_CHAVE_VAPID.exists():
            chave_nova = ec.generate_private_key(ec.SECP256R1())
            temporaria = CAMINHO_CHAVE_VAPID.with_suffix(".tmp")
            temporaria.write_bytes(chave_nova.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            ))
            temporaria.replace(CAMINHO_CHAVE_VAPID)
        chave = serialization.load_pem_private_key(CAMINHO_CHAVE_VAPID.read_bytes(), password=None)
    publica = chave.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    return chave, base64.urlsafe_b64encode(publica).rstrip(b"=").decode("ascii")


def chave_publica_vapid():
    return _chaves_vapid()[1]


def push_disponivel():
    try:
        import pywebpush  # noqa: F401
        return True
    except ImportError:
        return False


def salvar_assinatura(usuario_id, assinatura):
    endpoint = assinatura.get("endpoint", "")
    chaves = assinatura.get("keys") or {}
    if not isinstance(endpoint, str) or not endpoint.startswith("https://") or len(endpoint) > 2048:
        return False
    try:
        host = urlsplit(endpoint).hostname
        host = host.lower() if host else ""
    except ValueError:
        return False
    hosts_push = (
        "fcm.googleapis.com", "push.services.mozilla.com", "push.apple.com",
        "notify.windows.com",
    )
    if (not any(host == permitido or host.endswith("." + permitido) for permitido in hosts_push)
            or not isinstance(chaves, dict) or not chaves.get("p256dh") or not chaves.get("auth")):
        return False

    conexao = obter_conexao()
    conexao.execute(
        "INSERT INTO notificacoes_push (usuario_id, endpoint, assinatura_json, criado_em) "
        "VALUES (?, ?, ?, ?) ON CONFLICT(endpoint) DO UPDATE SET "
        "usuario_id = excluded.usuario_id, assinatura_json = excluded.assinatura_json",
        (usuario_id, endpoint, json.dumps(assinatura), datetime.now().isoformat(timespec="seconds")),
    )
    conexao.commit()
    conexao.close()
    return True


def remover_assinatura(usuario_id, endpoint):
    conexao = obter_conexao()
    conexao.execute(
        "DELETE FROM notificacoes_push WHERE usuario_id = ? AND endpoint = ?",
        (usuario_id, endpoint),
    )
    conexao.commit()
    conexao.close()


def remover_assinatura_por_id(assinatura_id):
    conexao = obter_conexao()
    conexao.execute("DELETE FROM notificacoes_push WHERE id = ?", (assinatura_id,))
    conexao.commit()
    conexao.close()


def listar_notificacoes(usuario_id, limite=50):
    conexao = obter_conexao()
    linhas = conexao.execute(
        "SELECT id, titulo, mensagem, url, criada_em, lida_em "
        "FROM notificacoes WHERE usuario_id = ? "
        "ORDER BY criada_em DESC, id DESC LIMIT ?",
        (usuario_id, limite),
    ).fetchall()
    nao_lidas = conexao.execute(
        "SELECT COUNT(*) FROM notificacoes WHERE usuario_id = ? AND lida_em IS NULL",
        (usuario_id,),
    ).fetchone()[0]
    conexao.close()
    return {"notificacoes": [dict(linha) for linha in linhas], "nao_lidas": nao_lidas}


def marcar_notificacao_lida(usuario_id, notificacao_id):
    conexao = obter_conexao()
    cursor = conexao.execute(
        "UPDATE notificacoes SET lida_em = ? "
        "WHERE id = ? AND usuario_id = ? AND lida_em IS NULL",
        (datetime.now().isoformat(timespec="seconds"), notificacao_id, usuario_id),
    )
    conexao.commit()
    conexao.close()
    return cursor.rowcount > 0


def marcar_todas_notificacoes_lidas(usuario_id):
    conexao = obter_conexao()
    cursor = conexao.execute(
        "UPDATE notificacoes SET lida_em = ? WHERE usuario_id = ? AND lida_em IS NULL",
        (datetime.now().isoformat(timespec="seconds"), usuario_id),
    )
    conexao.commit()
    conexao.close()
    return cursor.rowcount


def notificar_usuario(usuario_id, titulo, mensagem, url="/aulas"):
    """Envia a todos os aparelhos inscritos; falhas de um aparelho não afetam a aula."""
    try:
        conexao = obter_conexao()
        try:
            conexao.execute(
                "INSERT INTO notificacoes (usuario_id, titulo, mensagem, url, criada_em) "
                "VALUES (?, ?, ?, ?, ?)",
                (usuario_id, titulo, mensagem, url, datetime.now().isoformat(timespec="seconds")),
            )
            conexao.commit()
            inscricoes = conexao.execute(
                "SELECT id, endpoint, assinatura_json FROM notificacoes_push WHERE usuario_id = ?",
                (usuario_id,),
            ).fetchall()
        finally:
            conexao.close()
    except Exception:
        logger.exception("NÃ£o foi possÃ­vel registrar a notificaÃ§Ã£o do usuÃ¡rio %s", usuario_id)
        return {"enviadas": 0, "falhas": 1}
    if not inscricoes:
        return {"enviadas": 0, "falhas": 0}

    try:
        from pywebpush import WebPushException, webpush
        chave_privada = str(CAMINHO_CHAVE_VAPID)
        claims = {"sub": os.environ.get("VAPID_SUBJECT", "mailto:admin@example.com")}
    except ImportError:
        logger.warning("pywebpush não está instalado; notificações push não foram enviadas")
        return {"enviadas": 0, "falhas": len(inscricoes)}
    except Exception:
        logger.exception("Não foi possível preparar as chaves de notificação")
        return {"enviadas": 0, "falhas": len(inscricoes)}

    dados = {"title": titulo, "body": mensagem, "url": url}
    resultado = {"enviadas": 0, "falhas": 0}
    for inscricao in inscricoes:
        try:
            endpoint_host = urlsplit(inscricao["endpoint"]).hostname or ""
            cabecalhos = None
            if endpoint_host.endswith(".notify.windows.com") or endpoint_host == "notify.windows.com":
                payload = (
                    f'<toast launch="{html.escape(json.dumps(dados, ensure_ascii=False), quote=True)}">'
                    f'<visual><binding template="ToastGeneric">'
                    f'<text>{html.escape(titulo)}</text><text>{html.escape(mensagem)}</text>'
                    f"</binding></visual></toast>"
                )
                cabecalhos = {
                    "X-WNS-Type": "wns/toast",
                    "TTL": "600",
                    "Content-Type": "text/xml",
                }
            else:
                payload = json.dumps(dados, ensure_ascii=False)
            opcoes_envio = {
                "subscription_info": json.loads(inscricao["assinatura_json"]),
                "data": payload,
                "vapid_private_key": chave_privada,
                "vapid_claims": claims,
                "ttl": 86400,
                "timeout": 5,
            }
            if cabecalhos:
                opcoes_envio["headers"] = cabecalhos
            webpush(**opcoes_envio)
            resultado["enviadas"] += 1
        except WebPushException as erro:
            status = getattr(erro, "status_code", None) or getattr(
                getattr(erro, "response", None), "status_code", None
            )
            if status in (404, 410):
                remover_assinatura_por_id(inscricao["id"])
            else:
                resultado["falhas"] += 1
                resposta = getattr(erro, "response", None)
                detalhe = getattr(resposta, "text", "")[:300] if resposta else str(erro)[:300]
                logger.warning("Push não entregue (status %s): %s", status, detalhe)
        except Exception:
            resultado["falhas"] += 1
            logger.exception("Falha ao enviar push para o aparelho inscrito")
    return resultado
