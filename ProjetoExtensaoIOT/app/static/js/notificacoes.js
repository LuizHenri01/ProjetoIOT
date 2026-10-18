const alternarCentralNotificacoes = document.getElementById("alternar-central-notificacoes");
const centralNotificacoes = document.getElementById("central-notificacoes");
const listaNotificacoes = document.getElementById("lista-notificacoes");
const statusCentralNotificacoes = document.getElementById("status-central-notificacoes");
const contadorNotificacoes = document.getElementById("contador-notificacoes");
const marcarNotificacoesLidas = document.getElementById("marcar-notificacoes-lidas");
const alternarSomNotificacoes = document.getElementById("alternar-som-notificacoes");
const CHAVE_SOM_NOTIFICACOES = "aulamais:notification-sound";
const CHAVE_TOAST_ENCERRAMENTO_PENDENTE = "aulamais:toast-after-class-end";
const AudioContexto = window.AudioContext || window.webkitAudioContext;
let contextoSom;
let idsNotificacoesConhecidos = null;
let somNotificacoesAtivo = false;
let toastNotificacaoAtual = null;
let temporizadorToastNotificacao = null;
let toastEncerramentoPendente = false;
try {
    toastEncerramentoPendente = sessionStorage.getItem(CHAVE_TOAST_ENCERRAMENTO_PENDENTE) === "1";
} catch (erro) { /* sem armazenamento de sessao, o polling ainda mostra avisos novos */ }
try {
    somNotificacoesAtivo = localStorage.getItem(CHAVE_SOM_NOTIFICACOES) === "1";
} catch (erro) { /* mantem o som desligado neste navegador */ }

function salvarPreferenciaSom() {
    try {
        localStorage.setItem(CHAVE_SOM_NOTIFICACOES, somNotificacoesAtivo ? "1" : "0");
    } catch (erro) { /* a preferencia vale ate fechar esta pagina */ }
}

function atualizarContadorNotificacoes(quantidade) {
    if (!contadorNotificacoes || !alternarCentralNotificacoes) return;
    const total = Number(quantidade) || 0;
    contadorNotificacoes.hidden = total === 0;
    contadorNotificacoes.textContent = total > 99 ? "99+" : String(total);
    alternarCentralNotificacoes.setAttribute(
        "aria-label",
        total ? `Abrir notificacoes, ${total} nao lidas` : "Abrir notificacoes",
    );
}

function atualizarBotaoSom() {
    if (!alternarSomNotificacoes) return;
    alternarSomNotificacoes.textContent = somNotificacoesAtivo ? "Desativar som" : "Ativar som";
    alternarSomNotificacoes.setAttribute("aria-pressed", String(somNotificacoesAtivo));
}

async function prepararAudio() {
    if (!AudioContexto) throw new Error("Este navegador nao oferece audio Web.");
    if (!contextoSom) contextoSom = new AudioContexto();
    if (contextoSom.state === "suspended") await contextoSom.resume();
    if (contextoSom.state !== "running") throw new Error("O navegador manteve o audio bloqueado.");
}

function tocarSomNotificacao() {
    if (!contextoSom || contextoSom.state !== "running") return;
    const instante = contextoSom.currentTime;
    [740, 988].forEach((frequencia, indice) => {
        const inicio = instante + indice * 0.16;
        const oscilador = contextoSom.createOscillator();
        const volume = contextoSom.createGain();
        oscilador.type = "sine";
        oscilador.frequency.setValueAtTime(frequencia, inicio);
        volume.gain.setValueAtTime(0.0001, inicio);
        volume.gain.exponentialRampToValueAtTime(0.12, inicio + 0.025);
        volume.gain.exponentialRampToValueAtTime(0.0001, inicio + 0.2);
        oscilador.connect(volume);
        volume.connect(contextoSom.destination);
        oscilador.start(inicio);
        oscilador.stop(inicio + 0.21);
    });
}

async function liberarSomAoInteragir() {
    if (!somNotificacoesAtivo || contextoSom?.state === "running") return;
    try { await prepararAudio(); } catch (erro) { /* o navegador pode manter o audio bloqueado */ }
}

function formatarDataNotificacao(valor) {
    const data = new Date(String(valor || "").replace(" ", "T"));
    if (Number.isNaN(data.getTime())) return valor || "";
    return new Intl.DateTimeFormat("pt-BR", {
        dateStyle: "short",
        timeStyle: "short",
    }).format(data);
}

function criarItemNotificacao(notificacao) {
    const item = document.createElement("li");
    const link = document.createElement("a");
    const destino = typeof notificacao.url === "string"
        && notificacao.url.startsWith("/")
        && !notificacao.url.startsWith("//")
        ? notificacao.url
        : "/aulas";

    link.className = notificacao.lida_em
        ? "notification-item"
        : "notification-item notification-item--unread";
    link.href = destino;

    const titulo = document.createElement("strong");
    titulo.textContent = notificacao.titulo || "Notificacao";
    const mensagem = document.createElement("span");
    mensagem.textContent = notificacao.mensagem || "";
    const data = document.createElement("small");
    data.textContent = formatarDataNotificacao(notificacao.criada_em);

    link.append(titulo, mensagem, data);
    link.addEventListener("click", async (evento) => {
        evento.preventDefault();
        try {
            await AulaMais.api(`/api/notificacoes/${notificacao.id}/lida`, { method: "POST" });
        } finally {
            window.location.assign(destino);
        }
    });
    item.append(link);
    return item;
}

function fecharToastNotificacao() {
    if (!toastNotificacaoAtual) return;
    const toast = toastNotificacaoAtual;
    toast.classList.remove("app-notification-toast--visible");
    window.clearTimeout(temporizadorToastNotificacao);
    window.setTimeout(() => toast.remove(), 220);
    toastNotificacaoAtual = null;
}

function exibirToastNotificacao(notificacao) {
    fecharToastNotificacao();

    const toast = document.createElement("div");
    toast.className = "app-notification-toast";
    toast.setAttribute("role", "status");
    toast.setAttribute("aria-live", "polite");

    const destino = typeof notificacao.url === "string"
        && notificacao.url.startsWith("/")
        && !notificacao.url.startsWith("//")
        ? notificacao.url
        : "/aulas";
    const link = document.createElement("a");
    link.className = "app-notification-toast-link";
    link.href = destino;
    const titulo = document.createElement("strong");
    titulo.textContent = notificacao.titulo || "Novo aviso";
    const mensagem = document.createElement("span");
    mensagem.textContent = notificacao.mensagem || "Você recebeu uma nova notificação.";
    link.append(titulo, mensagem);
    link.addEventListener("click", async (evento) => {
        evento.preventDefault();
        try {
            await AulaMais.api(`/api/notificacoes/${notificacao.id}/lida`, { method: "POST" });
        } finally {
            window.location.assign(destino);
        }
    });

    const fechar = document.createElement("button");
    fechar.className = "app-notification-toast-close";
    fechar.type = "button";
    fechar.setAttribute("aria-label", "Fechar aviso");
    fechar.textContent = "×";
    fechar.addEventListener("click", fecharToastNotificacao);

    toast.append(link, fechar);
    document.body.append(toast);
    toastNotificacaoAtual = toast;
    window.requestAnimationFrame(() => toast.classList.add("app-notification-toast--visible"));
    temporizadorToastNotificacao = window.setTimeout(fecharToastNotificacao, 6500);
}

async function carregarNotificacoes() {
    if (idsNotificacoesConhecidos !== null && document.visibilityState !== "visible") return;
    try {
        const resposta = await AulaMais.api("/api/notificacoes");
        if (!resposta.ok) throw new Error("Falha ao consultar notificacoes.");
        const dados = await resposta.json();
        const notificacoes = Array.isArray(dados.notificacoes) ? dados.notificacoes : [];
        const idsAtuais = new Set(notificacoes.map((notificacao) => notificacao.id));
        if (idsNotificacoesConhecidos === null && toastEncerramentoPendente
                && notificacoes.length && document.visibilityState === "visible") {
            exibirToastNotificacao(notificacoes[0]);
            toastEncerramentoPendente = false;
            try { sessionStorage.removeItem(CHAVE_TOAST_ENCERRAMENTO_PENDENTE); }
            catch (erro) { /* o aviso ja foi exibido */ }
        } else if (idsNotificacoesConhecidos !== null && document.visibilityState === "visible") {
            const novasNotificacoes = notificacoes.filter(
                (notificacao) => !idsNotificacoesConhecidos.has(notificacao.id),
            );
            if (novasNotificacoes.length) {
                exibirToastNotificacao(novasNotificacoes[0]);
                if (somNotificacoesAtivo) tocarSomNotificacao();
            }
        }
        idsNotificacoesConhecidos = idsAtuais;
        atualizarContadorNotificacoes(dados.nao_lidas);
        if (listaNotificacoes) {
            listaNotificacoes.replaceChildren(...notificacoes.map(criarItemNotificacao));
        }
        if (statusCentralNotificacoes) {
            statusCentralNotificacoes.textContent = notificacoes.length
                ? ""
                : "Nenhum aviso por enquanto.";
        }
    } catch (erro) {
        if (statusCentralNotificacoes) {
            statusCentralNotificacoes.textContent = "Nao foi possivel carregar os avisos.";
        }
    }
}

if (alternarCentralNotificacoes && centralNotificacoes) {
    alternarCentralNotificacoes.addEventListener("click", () => {
        const aberta = centralNotificacoes.hidden;
        centralNotificacoes.hidden = !aberta;
        alternarCentralNotificacoes.setAttribute("aria-expanded", String(aberta));
        if (aberta) carregarNotificacoes();
    });
}

if (marcarNotificacoesLidas) {
    marcarNotificacoesLidas.addEventListener("click", async () => {
        marcarNotificacoesLidas.disabled = true;
        try {
            await AulaMais.api("/api/notificacoes/lidas", { method: "POST" });
            await carregarNotificacoes();
        } finally {
            marcarNotificacoesLidas.disabled = false;
        }
    });
}

if (alternarSomNotificacoes) {
    atualizarBotaoSom();
    alternarSomNotificacoes.addEventListener("click", async () => {
        somNotificacoesAtivo = !somNotificacoesAtivo;
        salvarPreferenciaSom();
        atualizarBotaoSom();
        if (somNotificacoesAtivo) {
            try {
                await prepararAudio();
                tocarSomNotificacao();
                if (statusCentralNotificacoes) {
                    statusCentralNotificacoes.textContent = "Som ativado. Este aparelho tocará quando um aviso novo chegar com o AulaMais aberto.";
                }
            } catch (erro) {
                somNotificacoesAtivo = false;
                salvarPreferenciaSom();
                atualizarBotaoSom();
                if (statusCentralNotificacoes) statusCentralNotificacoes.textContent = erro.message;
            }
        }
    });
}

document.addEventListener("pointerdown", liberarSomAoInteragir);
document.addEventListener("keydown", liberarSomAoInteragir);
carregarNotificacoes();
window.setInterval(carregarNotificacoes, 5000);
document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") carregarNotificacoes();
});
