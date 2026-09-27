from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",   # tudo 0 para aceitar conexões de qualquer dispositivo da rede
        port=8000,
        debug=True        # recarrega ao salvar; DESLIGAR fora do desenvolvimento
    )