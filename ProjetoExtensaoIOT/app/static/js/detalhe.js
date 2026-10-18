// Detalhe da aula: ouvir a fala, abas e anotações.
// Carrossel do quadro: as fotos tambem podem ser navegadas com gesto de deslizar.
(() => {
    const carrossel = document.querySelector("[data-photo-carousel]");
    if (!carrossel) return;

    const viewport = carrossel.querySelector("[data-photo-viewport]");
    const slides = Array.from(carrossel.querySelectorAll(".photo-carousel-slide"));
    const anterior = carrossel.querySelector("[data-photo-prev]");
    const proxima = carrossel.querySelector("[data-photo-next]");
    const contador = carrossel.querySelector("[data-photo-counter]");
    if (!viewport || !slides.length) return;

    let indiceAtual = -1;
    let quadroPendente = false;

    function atualizar() {
        const largura = viewport.clientWidth || 1;
        const indice = Math.min(slides.length - 1, Math.max(0, Math.round(viewport.scrollLeft / largura)));
        if (indice === indiceAtual) return;
        indiceAtual = indice;
        if (contador) contador.textContent = `${indice + 1} / ${slides.length}`;
        if (anterior) anterior.disabled = indice === 0;
        if (proxima) proxima.disabled = indice === slides.length - 1;
    }

    function irPara(indice) {
        const destino = Math.min(slides.length - 1, Math.max(0, indice));
        viewport.scrollTo({ left: destino * viewport.clientWidth, behavior: "smooth" });
        atualizar();
    }

    anterior?.addEventListener("click", () => irPara(indiceAtual - 1));
    proxima?.addEventListener("click", () => irPara(indiceAtual + 1));
    viewport.addEventListener("scroll", () => {
        if (quadroPendente) return;
        quadroPendente = true;
        window.requestAnimationFrame(() => {
            quadroPendente = false;
            atualizar();
        });
    }, { passive: true });
    viewport.addEventListener("keydown", (evento) => {
        if (evento.key === "ArrowLeft" || evento.key === "ArrowRight") {
            evento.preventDefault();
            irPara(indiceAtual + (evento.key === "ArrowRight" ? 1 : -1));
        }
    });
    window.addEventListener("resize", atualizar);
    atualizar();
})();

const botaoOuvirResumo = document.getElementById("botao-ouvir-resumo");
const botaoPararResumo = document.getElementById("botao-parar-resumo");
const statusAudio = document.getElementById("status-audio");

// A busca consulta a API e recebe somente os trechos que correspondem ao termo.
const buscaTranscricao = document.getElementById("busca-transcricao");
const resultadosBusca = document.getElementById("resultados-busca-transcricao");
const statusBuscaTranscricao = document.getElementById("status-busca-transcricao");

if (buscaTranscricao && resultadosBusca) {
    let temporizadorBusca = null;
    let requisicaoAtual = 0;
    buscaTranscricao.addEventListener("input", () => {
        clearTimeout(temporizadorBusca);
        const termo = buscaTranscricao.value.trim();
        const idRequisicao = ++requisicaoAtual;
        resultadosBusca.replaceChildren();
        resultadosBusca.hidden = true;
        if (!termo) {
            statusBuscaTranscricao.textContent = "";
            return;
        }

        statusBuscaTranscricao.textContent = "Buscando na transcrição…";
        temporizadorBusca = setTimeout(async () => {
            try {
                const url = `/api/aulas/${secaoAnotacoes.dataset.aulaId}/transcricoes?busca=${encodeURIComponent(termo)}`;
                const resposta = await AulaMais.api(url);
                if (!resposta.ok) throw new Error("Falha na busca");
                const dados = await resposta.json();
                if (idRequisicao !== requisicaoAtual) return;

                for (const fala of dados.transcricoes) {
                    const item = document.createElement("li");
                    const horario = document.createElement("time");
                    const texto = document.createElement("p");
                    horario.textContent = fala.timestamp;
                    texto.textContent = fala.texto;
                    item.append(horario, texto);
                    resultadosBusca.append(item);
                }
                resultadosBusca.hidden = dados.transcricoes.length === 0;
                const quantidade = dados.total;
                statusBuscaTranscricao.textContent = quantidade
                    ? `${quantidade} ${quantidade === 1 ? "trecho encontrado" : "trechos encontrados"}${quantidade > dados.limite ? `; mostrando os primeiros ${dados.limite}` : ""}.`
                    : "Nenhum trecho encontrado. Tente outra palavra.";
            } catch (erro) {
                if (idRequisicao === requisicaoAtual) {
                    statusBuscaTranscricao.textContent = "Não foi possível pesquisar. Verifique sua conexão.";
                }
            }
        }, 300);
    });
}

function leituraResumoTerminou() {
    botaoOuvirResumo.disabled = false;
    botaoPararResumo.disabled = true;
}

botaoOuvirResumo.addEventListener("click", async () => {
    if (!window.falaSuportada) {
        statusAudio.textContent = "Este navegador não tem leitura em voz alta.";
        return;
    }
    botaoOuvirResumo.disabled = true;
    botaoPararResumo.disabled = true;
    statusAudio.textContent = "Carregando transcrição...";
    try {
        const resposta = await AulaMais.api(
            `/api/aulas/${botaoOuvirResumo.dataset.aulaId}/transcricoes`
        );
        if (!resposta.ok) {
            statusAudio.textContent = "Não foi possível carregar a transcrição.";
            leituraResumoTerminou();
            return;
        }

        const dados = await resposta.json();
        const texto = dados.transcricoes.map((fala) => fala.texto).join(" ");
        if (!texto) {
            statusAudio.textContent = "Nenhuma fala foi transcrita nesta aula.";
            leituraResumoTerminou();
            return;
        }

        statusAudio.textContent = "Lendo...";
        botaoPararResumo.disabled = false;
        await window.falar(texto);
        if (statusAudio.textContent === "Lendo...") statusAudio.textContent = "Leitura concluída.";
    } catch (erro) {
        statusAudio.textContent = "Não foi possível carregar a transcrição. Verifique sua conexão.";
    } finally {
        leituraResumoTerminou();
    }
});

botaoPararResumo.addEventListener("click", () => {
    window.pararFala();
    statusAudio.textContent = "Leitura interrompida.";
    leituraResumoTerminou();
});

window.addEventListener("pagehide", () => window.pararFala());

// Abas: marca a seção para a qual a pessoa foi
const abas = Array.from(document.querySelectorAll(".detail-tabs a"));
abas.forEach((aba) => aba.addEventListener("click", () => {
    abas.forEach((a) => { a.classList.remove("tab-current"); a.removeAttribute("aria-current"); });
    aba.classList.add("tab-current");
    aba.setAttribute("aria-current", "true");
}));

// Anotações
const secaoAnotacoes = document.getElementById("anotacoes");
const campoAnotacoes = document.getElementById("campo-anotacoes");
const botaoSalvarAnotacoes = document.getElementById("botao-salvar-anotacoes");
const statusAnotacoes = document.getElementById("status-anotacoes");

botaoSalvarAnotacoes.addEventListener("click", async () => {
    botaoSalvarAnotacoes.disabled = true;
    statusAnotacoes.textContent = "Salvando...";
    try {
        const resposta = await AulaMais.api(`/api/aulas/${secaoAnotacoes.dataset.aulaId}/anotacoes`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ texto: campoAnotacoes.value }),
        });
        statusAnotacoes.textContent = resposta.ok ? "Anotações salvas." : "Não foi possível salvar. Tente novamente.";
    } catch (erro) {
        statusAnotacoes.textContent = "Sem conexão com o servidor. Verifique o Wi-Fi.";
    } finally {
        botaoSalvarAnotacoes.disabled = false;
    }
});
