const CHAVE_CONFIG = "aulamais:config";
const formConfig = document.getElementById("form-config");
const caixaTela = document.getElementById("cfg-tela-ligada");
const statusConfig = document.getElementById("status-config");
const botaoNotificacoes = document.getElementById("botao-notificacoes");
const statusNotificacoes = document.getElementById("status-notificacoes");

async function prepararNotificacoes() {
    if (!("serviceWorker" in navigator) || !("PushManager" in window) || !("Notification" in window)) {
        botaoNotificacoes.disabled = true;
        statusNotificacoes.textContent = "Este navegador não oferece notificações push.";
        return;
    }
    try {
        const registro = await navigator.serviceWorker.register("/sw.js");
        const inscricao = await registro.pushManager.getSubscription();
        if (inscricao && Notification.permission === "granted") {
            const resposta = await AulaMais.api("/api/notificacoes/inscricao", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ subscription: inscricao.toJSON() }),
            });
            if (!resposta.ok) throw new Error("Não foi possível atualizar este aparelho no servidor.");
            botaoNotificacoes.textContent = "Desativar notificações neste aparelho";
            statusNotificacoes.textContent = "Notificações ativadas neste aparelho.";
        }
    } catch (erro) {
        botaoNotificacoes.disabled = true;
        statusNotificacoes.textContent = "Notificações precisam de uma conexão segura (HTTPS).";
    }
}

botaoNotificacoes.addEventListener("click", async () => {
    botaoNotificacoes.disabled = true;
    try {
        const vaiDesativar = botaoNotificacoes.textContent.startsWith("Desativar");
        if (!vaiDesativar && Notification.permission !== "granted") {
            const permissao = await Notification.requestPermission();
            if (permissao !== "granted") {
                statusNotificacoes.textContent = "Permita notificações nas configurações do navegador para ativá-las.";
                return;
            }
        }
        const registro = await navigator.serviceWorker.ready;
        const existente = await registro.pushManager.getSubscription();
        if (existente) {
            const resposta = await AulaMais.api("/api/notificacoes/inscricao", {
                method: "DELETE",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ endpoint: existente.endpoint }),
            });
            if (!resposta.ok) throw new Error("Não foi possível desativar as notificações no servidor.");
            await existente.unsubscribe();
            botaoNotificacoes.textContent = "Ativar notificações neste aparelho";
            statusNotificacoes.textContent = "Notificações desativadas neste aparelho.";
            return;
        }
        if (vaiDesativar) {
            botaoNotificacoes.textContent = "Ativar notificações neste aparelho";
            statusNotificacoes.textContent = "Este aparelho não tem uma inscrição ativa.";
            return;
        }

        const respostaChave = await AulaMais.api("/api/notificacoes/chave");
        const dadosChave = await respostaChave.json();
        if (!respostaChave.ok) throw new Error(dadosChave.erro || "Servidor indisponível.");
        const chave = dadosChave.chave.replace(/-/g, "+").replace(/_/g, "/");
        const chaveComPadding = chave + "=".repeat((4 - chave.length % 4) % 4);
        const inscricao = await registro.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: Uint8Array.from(atob(chaveComPadding), c => c.charCodeAt(0)),
        });
        const resposta = await AulaMais.api("/api/notificacoes/inscricao", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ subscription: inscricao.toJSON() }),
        });
        if (!resposta.ok) {
            await inscricao.unsubscribe();
            throw new Error("Não foi possível salvar a inscrição no servidor.");
        }
        botaoNotificacoes.textContent = "Desativar notificações neste aparelho";
        statusNotificacoes.textContent = "Notificações ativadas neste aparelho.";
    } catch (erro) {
        statusNotificacoes.textContent = erro.message || "Não foi possível ativar as notificações.";
    } finally {
        botaoNotificacoes.disabled = false;
    }
});

prepararNotificacoes();

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
