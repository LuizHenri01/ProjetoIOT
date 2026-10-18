// Teste do microfone: escuta por 3 segundos e diz se chegou som.
const botaoTesteMic = document.getElementById("botao-mic");
const statusTesteMic = document.getElementById("status-mic");

botaoTesteMic.addEventListener("click", async () => {
    if (!navigator.mediaDevices || !window.isSecureContext) {
        statusTesteMic.textContent = "O microfone só funciona em conexão segura (https).";
        return;
    }

    botaoTesteMic.disabled = true;
    statusTesteMic.textContent = "Fale agora. Ouvindo por 3 segundos...";
    let stream = null;
    let contexto = null;

    try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        contexto = new (window.AudioContext || window.webkitAudioContext)();
        const analisador = contexto.createAnalyser();
        analisador.fftSize = 512;
        contexto.createMediaStreamSource(stream).connect(analisador);

        const amostras = new Uint8Array(analisador.fftSize);
        let pico = 0;
        const fim = Date.now() + 3000;
        while (Date.now() < fim) {
            analisador.getByteTimeDomainData(amostras);
            for (const valor of amostras) pico = Math.max(pico, Math.abs(valor - 128));
            await new Promise((r) => setTimeout(r, 50));
        }

        statusTesteMic.textContent = pico > 8
            ? "Microfone funcionando: o som foi captado."
            : "Microfone liberado, mas quase nenhum som foi captado. Fale mais perto ou aumente o volume.";
    } catch (erro) {
        statusTesteMic.textContent = erro.name === "NotAllowedError"
            ? "Microfone negado. Libere o acesso nas permissões do navegador."
            : "Não foi possível usar o microfone neste aparelho.";
    } finally {
        if (stream) stream.getTracks().forEach((t) => t.stop());
        if (contexto) contexto.close();
        botaoTesteMic.disabled = false;
    }
});
