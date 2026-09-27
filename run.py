import qrcode
from app import create_app
from app.utils import obter_ip_local

app = create_app()

if __name__ == "__main__":
    PORTA = 8000
    ip = obter_ip_local()
    url = f"http://{ip}:{PORTA}"

    print("\n" + "=" * 50)
    print(f"  Servidor disponível em: {url}")
    print("=" * 50)

    qr = qrcode.QRCode()
    qr.add_data(url)
    qr.print_ascii(invert=True)

    print("=" * 50 + "\n")

    app.run(host="0.0.0.0", port=PORTA, debug=True) # tudo zero para aceitar conexões de qualquer IP, inclusive de outros dispositivos na rede local.