// Transcrição da fala do professor.
// O navegador do celular reconhece a fala (Web Speech API) e envia cada frase pronta
// para o notebook por HTTP (POST /api/transcricoes). O servidor só guarda o texto.

const botaoGravar = document.getElementById("botao-gravar");
const botaoParar = document.getElementById("botao-parar");
const statusGravacao = document.getElementById("status-gravacao");
const previaFala = document.getElementById("previa-fala");
const listaTranscricoes = document.getElementById("lista-transcricoes");

const Reconhecimento = window.SpeechRecognition || window.webkitSpeechRecognition;

let reconhecimento = null;
let ouvindo = false;
let aulaAtiva = false;
let fila = [];            // frases prontas que ainda não chegaram ao servidor
let enviando = false;
let travaTela = null;     // impede o celular de apagar a tela (o que interromperia o áudio)
let trechoFinalPendente = "";
let temporizadorTrecho = null;

const INTERVALO_CONSOLIDACAO_MS = 1000;
const esperar = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function manterTelaLigada() {
    try {
        const config = JSON.parse(localStorage.getItem("aulamais:config")) || {};
        return config.telaLigada !== false;
    } catch (erro) {
        return true;
    }
}

function atualizarBotoes() {
    botaoGravar.disabled = !aulaAtiva || ouvindo || !Reconhecimento;
    botaoParar.disabled = !ouvindo;
}

function adicionarNaTela(texto) {
    const item = document.createElement("li");
    item.textContent = texto;
    listaTranscricoes.appendChild(item);
    item.scrollIntoView({ block: "nearest" });
}

// ---------- Envio ao servidor ----------

async function enviarFila() {
    if (enviando) return;
    enviando = true;

    try {
        while (fila.length > 0) {
            try {
                const resposta = await AulaMais.api("/api/transcricoes", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ texto: fila[0] }),
                });

                if (resposta.ok) {
                    fila.shift();
                } else if (resposta.status === 400) {
                    // Aula já encerrada ou texto inválido: tentar de novo não resolve.
                    fila.shift();
                    statusGravacao.textContent = "Trecho não salvo: não há aula em andamento.";
                } else {
                    throw new Error("Erro do servidor");
                }
            } catch (erro) {
                statusGravacao.textContent = "Sem conexão com o servidor. Tentando enviar de novo...";
                if (!ouvindo) break;  // parando a transcrição: não ficar tentando para sempre
                await esperar(3000);
            }
        }
    } finally {
        enviando = false;
    }
}

function enfileirar(texto) {
    fila.push(texto);
    adicionarNaTela(texto);
    enviarFila();
}

function finalizarTrechoPendente() {
    if (temporizadorTrecho) {
        clearTimeout(temporizadorTrecho);
        temporizadorTrecho = null;
    }
    if (trechoFinalPendente) {
        enfileirar(trechoFinalPendente);
        trechoFinalPendente = "";
    }
}

function consolidarTrechoFinal(texto) {
    const novoTexto = texto.trim();
    if (!novoTexto) return;

    const novoNormalizado = novoTexto.toLocaleLowerCase("pt-BR");
    const pendenteNormalizado = trechoFinalPendente.toLocaleLowerCase("pt-BR");

    if (!trechoFinalPendente || novoNormalizado.startsWith(pendenteNormalizado)) {
        trechoFinalPendente = novoTexto;
    } else if (!pendenteNormalizado.startsWith(novoNormalizado)) {
        finalizarTrechoPendente();
        trechoFinalPendente = novoTexto;
    }

    if (temporizadorTrecho) clearTimeout(temporizadorTrecho);
    temporizadorTrecho = setTimeout(finalizarTrechoPendente, INTERVALO_CONSOLIDACAO_MS);
}

// ---------- Tela ligada ----------

async function travarTela() {
    if (!manterTelaLigada()) return;
    try {
        if ("wakeLock" in navigator) {
            travaTela = await navigator.wakeLock.request("screen");
        }
    } catch (erro) {
        // Sem suporte ou negado: a transcrição funciona, só pode parar se a tela apagar.
    }
}

function liberarTela() {
    if (travaTela) {
        travaTela.release().catch(() => {});
        travaTela = null;
    }
}

document.addEventListener("visibilitychange", () => {
    // O navegador solta a trava quando a aba some; pega de novo ao voltar.
    if (ouvindo && document.visibilityState === "visible") travarTela();
});

// ---------- Reconhecimento de fala ----------

function criarReconhecimento() {
    const r = new Reconhecimento();
    r.lang = "pt-BR";
    r.continuous = true;
    r.interimResults = true;

    r.onresult = (evento) => {
        let parcial = "";
        for (let i = evento.resultIndex; i < evento.results.length; i++) {
            const resultado = evento.results[i];
            const texto = resultado[0].transcript.trim();
            if (resultado.isFinal) {
                if (texto) consolidarTrechoFinal(texto);
            } else {
                parcial += texto + " ";
            }
        }
        previaFala.textContent = parcial.trim();
    };

    r.onerror = (evento) => {
        if (evento.error === "not-allowed" || evento.error === "service-not-allowed") {
            statusGravacao.textContent = "Microfone negado. Libere o acesso nas permissões do navegador.";
            pararTranscricao();
        } else if (evento.error === "audio-capture") {
            statusGravacao.textContent = "Nenhum microfone encontrado neste aparelho.";
            pararTranscricao();
        } else if (evento.error === "network") {
            statusGravacao.textContent = "O reconhecimento de voz precisa de internet. Verifique a conexão do celular.";
        }
        // "no-speech" e "aborted" são normais (silêncio): o onend religa.
    };

    r.onend = () => {
        previaFala.textContent = "";
        finalizarTrechoPendente();
        // O navegador encerra sozinho após silêncio ou tempo longo; religa enquanto o usuário quiser.
        if (ouvindo) {
            setTimeout(() => {
                if (ouvindo) {
                    try { r.start(); } catch (erro) { /* já estava iniciando */ }
                }
            }, 500);
        }
    };

    return r;
}

function iniciarTranscricao() {
    if (!Reconhecimento) {
        statusGravacao.textContent = "Este navegador não tem reconhecimento de voz. Use o Chrome no Android.";
        return;
    }
    if (!window.isSecureContext) {
        statusGravacao.textContent = "Contexto inseguro. Acesse o sistema por https.";
        return;
    }
    if (!aulaAtiva) {
        statusGravacao.textContent = "Inicie uma aula antes de transcrever.";
        return;
    }

    reconhecimento = criarReconhecimento();
    ouvindo = true;

    try {
        reconhecimento.start();
        statusGravacao.textContent = "Transcrevendo. Fale normalmente.";
        travarTela();
    } catch (erro) {
        ouvindo = false;
        statusGravacao.textContent = "Não foi possível iniciar o microfone.";
    }
    atualizarBotoes();
}

async function pararTranscricao() {
    ouvindo = false;

    if (reconhecimento) {
        reconhecimento.stop();  // entrega o último trecho pendente antes de encerrar
        reconhecimento = null;
    }

    liberarTela();
    previaFala.textContent = "";
    atualizarBotoes();

    // Dá um instante para o último resultado chegar e então esvazia a fila.
    await esperar(800);
    finalizarTrechoPendente();
    await enviarFila();

    if (!statusGravacao.textContent.startsWith("Trecho") && !statusGravacao.textContent.startsWith("Sem conexão")) {
        statusGravacao.textContent = "Transcrição parada.";
    }
}

window.pararTranscricao = pararTranscricao;

botaoGravar.addEventListener("click", iniciarTranscricao);
botaoParar.addEventListener("click", pararTranscricao);

document.addEventListener("aula:estado", (evento) => {
    aulaAtiva = evento.detail.ativa;

    if (!aulaAtiva) {
        listaTranscricoes.innerHTML = "";
        if (ouvindo) pararTranscricao();
    }
    atualizarBotoes();
});

if (!Reconhecimento) {
    statusGravacao.textContent = "Este navegador não tem reconhecimento de voz. Use o Chrome no Android.";
}
atualizarBotoes();
