// Leitura em voz alta com a voz do próprio aparelho (Web Speech API). Não precisa de servidor.
(function () {
    const suportado = "speechSynthesis" in window;
    let leituraAtual = 0;   // invalida leituras antigas quando o usuário manda parar
    let ativa = false;

    function dividir(texto) {
        // Pedaços curtos: alguns navegadores cortam falas longas no meio.
        const pedacos = [];
        for (const frase of texto.replace(/\s+/g, " ").trim().split(/(?<=[.!?;:])\s+/)) {
            if (frase.length <= 220) { pedacos.push(frase); continue; }
            for (let i = 0; i < frase.length; i += 220) pedacos.push(frase.slice(i, i + 220));
        }
        return pedacos.filter(Boolean);
    }

    // Devolve uma Promise que resolve quando a leitura termina (ou é interrompida).
    window.falar = function (texto, opcoes) {
        if (!suportado) return Promise.reject(new Error("sem-suporte"));
        window.pararFala();
        const id = ++leituraAtual;
        const velocidade = (opcoes && opcoes.velocidade) ||
            (window.AulaMais ? window.AulaMais.velocidadeNumerica(window.AulaMais.lerPrefs()) : 1);
        const pedacos = dividir(String(texto));
        ativa = pedacos.length > 0;

        return new Promise((resolve) => {
            let i = 0;
            const proximo = () => {
                if (id !== leituraAtual || i >= pedacos.length) {
                    if (id === leituraAtual) ativa = false;
                    resolve();
                    return;
                }
                const fala = new SpeechSynthesisUtterance(pedacos[i++]);
                fala.lang = "pt-BR";
                fala.rate = velocidade;
                fala.onend = proximo;
                fala.onerror = () => { if (id === leituraAtual) ativa = false; resolve(); };
                window.speechSynthesis.speak(fala);
            };
            proximo();
        });
    };

    window.pararFala = function () {
        leituraAtual++;
        ativa = false;
        if (suportado) window.speechSynthesis.cancel();
    };

    window.falando = () => ativa;
    window.falaSuportada = suportado;
})();
