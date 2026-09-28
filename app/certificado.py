import os
import ipaddress
from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

PASTA_CERTS = "certs"
CAMINHO_CERT = os.path.join(PASTA_CERTS, "cert.pem")
CAMINHO_CHAVE = os.path.join(PASTA_CERTS, "key.pem")


def garantir_certificado(ip):
    if os.path.exists(CAMINHO_CERT) and os.path.exists(CAMINHO_CHAVE):
        return CAMINHO_CERT, CAMINHO_CHAVE

    os.makedirs(PASTA_CERTS, exist_ok=True)

    chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nome = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "projeto-iot-local")])
    agora = datetime.now(timezone.utc)

    certificado = (
        x509.CertificateBuilder()
        .subject_name(nome)
        .issuer_name(nome)  # emissor = o próprio dono: é isso que "autoassinado" significa
        .public_key(chave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(agora)
        .not_valid_after(agora + timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.ip_address(ip)),
            ]),
            critical=False,
        )
        .sign(chave, hashes.SHA256())
    )

    with open(CAMINHO_CHAVE, "wb") as f:
        f.write(chave.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    with open(CAMINHO_CERT, "wb") as f:
        f.write(certificado.public_bytes(serialization.Encoding.PEM))

    return CAMINHO_CERT, CAMINHO_CHAVE