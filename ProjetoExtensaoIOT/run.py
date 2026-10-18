import os
import sys
from pathlib import Path

# O comando documentado `python run.py` usa o ambiente virtual do projeto,
# inclusive quando o Python global está selecionado no terminal/IDE.
if __name__ == "__main__":
    python_venv = Path(__file__).resolve().parent / ".venv" / "Scripts" / "python.exe"
    if python_venv.is_file() and Path(sys.executable).resolve() != python_venv.resolve():
        os.execv(str(python_venv), [str(python_venv), str(Path(__file__).resolve()), *sys.argv[1:]])

import qrcode
import threading
import time
from app import create_app
from app.utils import obter_ip_local
from app.certificado import garantir_certificado

app = create_app()
DEBUG = os.environ.get("AULAMAIS_DEBUG", "").strip().lower() in {"1", "true", "yes"}

if __name__ == "__main__":
    def acompanhar_fins_programados():
        """Confere horários mesmo sem navegador aberto e envia o push no encerramento."""
        from app.services.aulas_service import encerrar_aulas_vencidas
        while True:
            try:
                encerrar_aulas_vencidas()
            except Exception:
                app.logger.exception("Falha ao conferir o encerramento programado das aulas")
            time.sleep(20)

    # Com o reloader ligado, apenas o processo filho mantém o monitor.
    if not DEBUG or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Thread(
            target=acompanhar_fins_programados,
            name="aulamais-encerramento-aulas",
            daemon=True,
        ).start()

    PORTA = 8000
    ip = obter_ip_local()
    cert, chave = garantir_certificado(ip)
    url = f"https://{ip}:{PORTA}"

    print("\n" + "=" * 50)
    print(f"  Servidor disponível em: {url}")
    print("=" * 50)

    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.print_ascii(invert=True)

    print("=" * 50 + "\n")

    app.run(
        host="0.0.0.0", port=PORTA, debug=DEBUG, use_reloader=DEBUG,
        ssl_context=(cert, chave),
    )
