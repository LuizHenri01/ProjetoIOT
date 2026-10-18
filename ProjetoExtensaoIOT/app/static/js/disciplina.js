const buscaAulas = document.getElementById("busca-aulas-disciplina");
const cardsAulas = Array.from(document.querySelectorAll("#lista-aulas-disciplina .lesson-card"));
const semAulas = document.getElementById("sem-aulas-disciplina");
const statusAulas = document.getElementById("status-busca-aulas-disciplina");

function normalizarBusca(texto) {
    return texto.toLocaleLowerCase("pt-BR").normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

if (buscaAulas) {
    buscaAulas.addEventListener("input", () => {
        const termo = normalizarBusca(buscaAulas.value.trim());
        let quantidade = 0;
        cardsAulas.forEach((card) => {
            const visivel = normalizarBusca(card.textContent).includes(termo);
            card.hidden = !visivel;
            if (visivel) quantidade += 1;
        });
        semAulas.hidden = quantidade > 0;
        statusAulas.textContent = quantidade === 1
            ? "1 aula encontrada."
            : `${quantidade} aulas encontradas.`;
    });
}
