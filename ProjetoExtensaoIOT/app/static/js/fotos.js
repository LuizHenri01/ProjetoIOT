const inputFoto = document.getElementById("input-foto");
const statusFoto = document.getElementById("status-foto");

// O botão da foto só vale com aula em andamento (o servidor recusaria de qualquer forma).
document.addEventListener("aula:estado", (evento) => {
    inputFoto.disabled = !evento.detail.ativa;
    statusFoto.textContent = evento.detail.ativa ? "" : "Inicie uma aula para tirar fotos do quadro.";
});

inputFoto.addEventListener("change", async (evento) => {
    const arquivo = evento.target.files[0];
    if (!arquivo) {
        return;
    }

    statusFoto.textContent = "Enviando foto...";
    const dados = new FormData();
    dados.append("foto", arquivo);

    try {
        const resposta = await AulaMais.api("/api/fotos", { method: "POST", body: dados });

        if (resposta.ok) {
            statusFoto.textContent = "Foto capturada.";
        } else if (resposta.status === 400) {
            const erro = await resposta.json().catch(() => ({}));
            statusFoto.textContent = erro.erro || "Não foi possível salvar a foto.";
        } else {
            statusFoto.textContent = "Erro ao enviar a foto. Tente novamente.";
        }
    } catch (erro) {
        statusFoto.textContent = "Sem conexão com o servidor. Verifique o Wi-Fi.";
    }
    inputFoto.value = "";
});
