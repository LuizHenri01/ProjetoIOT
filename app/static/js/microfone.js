// Testezinho
const botaoMic = document.getElementById("botao-mic");
const statusMic = document.getElementById("status-mic");

botaoMic.addEventListener("click", async () => {
    if (!window.isSecureContext || !navigator.mediaDevices) {
        statusMic.textContent = "Contexto inseguro. Acesse o sistema por https.";
        return;
    }

    try {
        const fluxo = await navigator.mediaDevices.getUserMedia({ audio: true });
        fluxo.getTracks().forEach((faixa) => faixa.stop());
        statusMic.textContent = "Microfone liberado. Pronto para gravar.";
    } catch (erro) {
        statusMic.textContent = "Microfone negado ou indisponível.";
    }
});