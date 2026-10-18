const CHAVE_CONFIG = "aulamais:config";
const formConfig = document.getElementById("form-config");
const caixaTela = document.getElementById("cfg-tela-ligada");
const statusConfig = document.getElementById("status-config");

try {
    const salvo = JSON.parse(localStorage.getItem(CHAVE_CONFIG)) || {};
    caixaTela.checked = salvo.telaLigada !== false;
} catch (erro) { /* usa o padrão */ }

formConfig.addEventListener("submit", (evento) => {
    evento.preventDefault();
    try {
        localStorage.setItem(CHAVE_CONFIG, JSON.stringify({ telaLigada: caixaTela.checked }));
        statusConfig.textContent = "Configurações salvas neste aparelho.";
    } catch (erro) {
        statusConfig.textContent = "Não foi possível salvar neste navegador.";
    }
});
