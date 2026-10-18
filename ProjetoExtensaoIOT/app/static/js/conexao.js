async function verificarConexao() {
    const statusEl = document.getElementById("status-conexao");
    if (!statusEl) return;

    try {
        const resposta = await fetch("/health");
        statusEl.textContent = resposta.ok
            ? "Conectado ao servidor. Sistema pronto para uso."
            : "Servidor respondeu com erro. Avise o mediador.";
    } catch (erro) {
        statusEl.textContent = "Sem conexão com o servidor. Verifique o Wi-Fi.";
    }
}

document.addEventListener("DOMContentLoaded", verificarConexao);
