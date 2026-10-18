// Lista de aulas: busca, filtro por disciplina e paginação (tudo no navegador).
const TAMANHO_PAGINA = 8;
const cartoes = Array.from(document.querySelectorAll("#lista-aulas .lesson-card"));
const campoBusca = document.getElementById("busca-aulas");
const filtro = document.getElementById("filtro-disciplina");
const semResultado = document.getElementById("sem-resultado");
const statusBusca = document.getElementById("status-busca");
const paginacao = document.getElementById("paginacao");
let paginaAtual = 1;

function normalizar(texto) {
    return texto.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function filtrar() {
    const termo = normalizar(campoBusca.value.trim());
    const disciplina = filtro.value;
    return cartoes.filter((c) =>
        (!disciplina || c.dataset.subject === disciplina) && normalizar(c.textContent).includes(termo));
}

function botaoPagina(rotulo, pagina, opcoes = {}) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = rotulo;
    if (opcoes.rotuloAcessivel) b.setAttribute("aria-label", opcoes.rotuloAcessivel);
    if (opcoes.atual) { b.className = "selected"; b.setAttribute("aria-current", "page"); }
    if (opcoes.desabilitado) b.disabled = true;
    b.addEventListener("click", () => { paginaAtual = pagina; desenhar(); });
    return b;
}

function desenhar(anunciar) {
    const visiveis = filtrar();
    const paginas = Math.max(1, Math.ceil(visiveis.length / TAMANHO_PAGINA));
    paginaAtual = Math.min(paginaAtual, paginas);
    const inicio = (paginaAtual - 1) * TAMANHO_PAGINA;
    const daPagina = new Set(visiveis.slice(inicio, inicio + TAMANHO_PAGINA));

    cartoes.forEach((c) => { c.hidden = !daPagina.has(c); });
    semResultado.hidden = visiveis.length > 0;

    paginacao.replaceChildren();
    paginacao.hidden = paginas <= 1;
    if (paginas > 1) {
        paginacao.append(botaoPagina("‹", paginaAtual - 1, { rotuloAcessivel: "Página anterior", desabilitado: paginaAtual === 1 }));
        for (let p = 1; p <= paginas; p++) paginacao.append(botaoPagina(String(p), p, { atual: p === paginaAtual, rotuloAcessivel: `Página ${p}` }));
        paginacao.append(botaoPagina("›", paginaAtual + 1, { rotuloAcessivel: "Próxima página", desabilitado: paginaAtual === paginas }));
    }

    if (anunciar) {
        statusBusca.textContent = visiveis.length === 1 ? "1 aula encontrada." : `${visiveis.length} aulas encontradas.`;
    }
}

if (cartoes.length) {
    campoBusca.addEventListener("input", () => { paginaAtual = 1; desenhar(true); });
    filtro.addEventListener("change", () => { paginaAtual = 1; desenhar(true); });
    desenhar(false);
}
