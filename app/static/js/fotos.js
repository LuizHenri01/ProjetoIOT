const inputFoto = document.getElementById("input-foto");
const statusFoto = document.getElementById("status-foto");

inputFoto.addEventListener("change", async (evento) => {
    const arquivo = evento.target.files[0];

    if (!arquivo) {
        return;
    }

    statusFoto.textContent = "Enviando foto...";
    const dados = new FormData();
    dados.append("foto", arquivo);

    try {
        const resposta = await fetch("/api/fotos", {
            method: "POST",
            body: dados,
        });

        if (resposta.ok) {
            statusFoto.textContent = "Foto capturada.";
        } else {
            statusFoto.textContent = "Erro ao enviar a foto. Tente novamente.";
        }
    } catch (erro) {
        statusFoto.textContent = "Sem conexão com o servidor. Verifique o Wi-Fi.";
    }
    inputFoto.value = "";
});