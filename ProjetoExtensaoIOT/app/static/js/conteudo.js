// "Conteúdo acessível": lê em voz alta o texto colado do slide ou do quadro.
const botaoOuvir = document.getElementById("botao-ouvir");
const botaoPararLeitura = document.getElementById("botao-parar-leitura");
const textoConteudo = document.getElementById("texto-conteudo");
const statusConteudo = document.getElementById("status-conteudo");

function leituraTerminou() {
    botaoOuvir.disabled = false;
    botaoPararLeitura.disabled = true;
}

botaoOuvir.addEventListener("click", async () => {
    const texto = textoConteudo.value.trim();
    if (!texto) {
        statusConteudo.textContent = "Cole ou digite um texto para ouvir.";
        textoConteudo.focus();
        return;
    }
    if (!window.falaSuportada) {
        statusConteudo.textContent = "Este navegador não tem leitura em voz alta.";
        return;
    }

    botaoOuvir.disabled = true;
    botaoPararLeitura.disabled = false;
    statusConteudo.textContent = "Lendo o conteúdo...";
    await window.falar(texto);
    if (statusConteudo.textContent === "Lendo o conteúdo...") statusConteudo.textContent = "Leitura concluída.";
    leituraTerminou();
});

botaoPararLeitura.addEventListener("click", () => {
    window.pararFala();
    statusConteudo.textContent = "Leitura interrompida.";
    leituraTerminou();
});
