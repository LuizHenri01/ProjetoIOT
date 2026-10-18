import qrcode
import os
import threading
import time
from app import create_app
from app.utils import obter_ip_local
from app.certificado import garantir_certificado

app = create_app()

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

    # O reloader do Flask inicia um processo filho; apenas ele mantém o monitor.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
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

    app.run(host="0.0.0.0", port=PORTA, debug=True, ssl_context=(cert, chave)) # tudo zero para aceitar conexões de qualquer IP, inclusive de outros dispositivos na rede local.
