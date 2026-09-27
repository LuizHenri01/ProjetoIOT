async function verificarConexao() {
    const statusEl = document.getElementById("status-conexao");

    try {
        const resposta = await fetch("/health");

        if (resposta.ok) {
            statusEl.textContent = "Conectado ao servidor. Sistema pronto para uso.";
        } else {
            statusEl.textContent = "Servidor respondeu com erro. Avise o mediador.";
        }
    } catch (erro) {
        statusEl.textContent = "Sem conexão com o servidor. Verifique o Wi-Fi.";
    }
}

document.addEventListener("DOMContentLoaded", verificarConexao);