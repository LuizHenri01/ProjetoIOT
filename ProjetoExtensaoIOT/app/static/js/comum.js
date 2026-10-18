// Código compartilhado por todas as páginas: chamadas à API com CSRF e preferências de acessibilidade.
(function () {
    const CHAVE_PREFS = "aulamais:prefs";
    const PADRAO = {
        tamanho: 100, espaco: "Padrão", contraste: "Padrão",
        animacoes: false, foco: false, leitura: false, velocidade: "1x",
    };

    function lerPrefs() {
        try {
            return Object.assign({}, PADRAO, JSON.parse(localStorage.getItem(CHAVE_PREFS)) || {});
        } catch (erro) {
            return Object.assign({}, PADRAO);
        }
    }

    function aplicarPrefs(p) {
        const html = document.documentElement;
        html.style.fontSize = p.tamanho + "%";
        html.dataset.espaco = { "Médio": "medio", "Amplo": "amplo" }[p.espaco] || "";
        html.dataset.contraste = p.contraste === "Alto contraste" ? "alto" : "";
        html.dataset.animacoes = p.animacoes ? "reduzir" : "";
        html.dataset.foco = p.foco ? "ligado" : "";
        const valorFlutuante = document.getElementById("quick-text-value");
        if (valorFlutuante) valorFlutuante.textContent = `${Number(p.tamanho) || 100}%`;
        atualizarBotaoLeitura(p);
    }

    function salvarPrefs(p) {
        try { localStorage.setItem(CHAVE_PREFS, JSON.stringify(p)); } catch (erro) { /* modo privado */ }
    }

    function velocidadeNumerica(p) {
        return parseFloat(String(p.velocidade).replace(",", ".")) || 1;
    }

    function inicializarAcessibilidadeRapida() {
        const widget = document.querySelector(".quick-access-widget");
        const painel = document.getElementById("quick-access-panel");
        const alternar = document.getElementById("quick-access-toggle");
        const aumentar = document.getElementById("quick-text-increase");
        const diminuir = document.getElementById("quick-text-decrease");
        const resetar = document.getElementById("quick-text-reset");
        const valor = document.getElementById("quick-text-value");
        if (!widget || !painel || !alternar || !aumentar || !diminuir || !resetar || !valor) return;

        const minimo = 80;
        const maximo = 200;
        const passo = 10;

        function atualizar(prefs) {
            const tamanho = Math.max(minimo, Math.min(maximo, Number(prefs.tamanho) || 100));
            valor.textContent = `${tamanho}%`;
            aumentar.disabled = tamanho >= maximo;
            diminuir.disabled = tamanho <= minimo;
        }

        function ajustar(delta) {
            const prefs = typeof window.AulaMais.lerPrefsEmEdicao === "function"
                ? window.AulaMais.lerPrefsEmEdicao()
                : lerPrefs();
            prefs.tamanho = Math.max(minimo, Math.min(maximo, (Number(prefs.tamanho) || 100) + delta));
            salvarPrefs(prefs);
            aplicarPrefs(prefs);
            atualizar(prefs);
            window.dispatchEvent(new CustomEvent("aulamais:preferencias-atualizadas", { detail: prefs }));
        }

        function fechar() {
            painel.hidden = true;
            widget.dataset.open = "false";
            alternar.setAttribute("aria-expanded", "false");
            alternar.setAttribute("aria-label", "Abrir acessibilidade rápida");
        }

        alternar.addEventListener("click", () => {
            const abrir = painel.hidden;
            painel.hidden = !abrir;
            widget.dataset.open = String(abrir);
            alternar.setAttribute("aria-expanded", String(abrir));
            alternar.setAttribute("aria-label", abrir ? "Fechar acessibilidade rápida" : "Abrir acessibilidade rápida");
        });
        aumentar.addEventListener("click", () => ajustar(passo));
        diminuir.addEventListener("click", () => ajustar(-passo));
        resetar.addEventListener("click", () => {
            const prefs = typeof window.AulaMais.lerPrefsEmEdicao === "function"
                ? window.AulaMais.lerPrefsEmEdicao()
                : lerPrefs();
            prefs.tamanho = 100;
            salvarPrefs(prefs);
            aplicarPrefs(prefs);
            atualizar(prefs);
            window.dispatchEvent(new CustomEvent("aulamais:preferencias-atualizadas", { detail: prefs }));
        });
        document.addEventListener("click", (evento) => {
            if (!painel.hidden && !widget.contains(evento.target)) fechar();
        });
        document.addEventListener("keydown", (evento) => {
            if (evento.key === "Escape" && !painel.hidden) {
                fechar();
                alternar.focus();
            }
        });
        atualizar(lerPrefs());
    }

    // Botão "Ouvir esta página", quando "Leitura do conteúdo" está ligada
    function atualizarBotaoLeitura(p) {
        let botao = document.getElementById("botao-ouvir-pagina");
        if (!p.leitura || !document.body) {
            if (botao) botao.remove();
            return;
        }
        if (botao) return;
        botao = document.createElement("button");
        botao.type = "button";
        botao.id = "botao-ouvir-pagina";
        botao.className = "btn-ouvir-pagina";
        botao.textContent = "Ouvir esta página";
        botao.addEventListener("click", () => {
            if (window.falando && window.falando()) {
                window.pararFala();
                botao.textContent = "Ouvir esta página";
            } else {
                const principal = document.getElementById("conteudo-principal");
                window.falar(principal ? principal.innerText : document.body.innerText);
                botao.textContent = "Parar leitura";
            }
        });
        document.body.appendChild(botao);
    }

    // fetch com o token CSRF; se a sessão acabou, volta para o login
    async function api(url, opcoes) {
        const meta = document.querySelector('meta[name="csrf-token"]');
        const config = Object.assign({ method: "GET", headers: {} }, opcoes);
        config.headers = Object.assign({ "X-CSRF-Token": meta ? meta.content : "" }, config.headers);
        const resposta = await fetch(url, config);
        if (resposta.status === 401) {
            window.location.href = "/entrar?proximo=" + encodeURIComponent(window.location.pathname);
        }
        return resposta;
    }

    window.AulaMais = { lerPrefs, aplicarPrefs, salvarPrefs, velocidadeNumerica, api, PADRAO };

    aplicarPrefs(lerPrefs());  // cedo, para a página não "piscar" no tema errado
    document.addEventListener("DOMContentLoaded", () => {
        const prefs = lerPrefs();
        atualizarBotaoLeitura(prefs);
        inicializarAcessibilidadeRapida();
    });
})();
