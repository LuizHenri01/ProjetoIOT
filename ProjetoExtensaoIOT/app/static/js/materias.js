const buscaMaterias = document.getElementById("busca-materias");
const cardsMaterias = Array.from(document.querySelectorAll("#lista-materias .subject-card"));
const semMaterias = document.getElementById("sem-materias");
const statusMaterias = document.getElementById("status-busca-materias");
const formularioMateria = document.getElementById("nova-materia");
const botaoAlternarFormulario = document.querySelector("[data-toggle-subject-form]");
const botaoFecharFormulario = document.querySelector("[data-close-subject-form]");

function definirFormularioAberto(aberto, focarCampo = false, rolarAteFormulario = false) {
    if (!formularioMateria) return;
    formularioMateria.hidden = !aberto;
    botaoAlternarFormulario?.setAttribute("aria-expanded", String(aberto));

    const rotulo = botaoAlternarFormulario?.querySelector("[data-toggle-subject-label]");
    const icone = botaoAlternarFormulario?.querySelector("[data-toggle-subject-icon]");
    if (rotulo) rotulo.textContent = aberto ? "Fechar formulário" : "Nova matéria";
    if (icone) {
        icone.classList.toggle("bi-plus-lg", !aberto);
        icone.classList.toggle("bi-x-lg", aberto);
    }

    if (aberto && rolarAteFormulario) {
        formularioMateria.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    if (aberto && focarCampo) {
        formularioMateria.querySelector('input[name="nome"]')?.focus({ preventScroll: true });
    }
}

botaoAlternarFormulario?.addEventListener("click", () => {
    const aberto = formularioMateria?.hidden;
    definirFormularioAberto(aberto, aberto, aberto);
});

botaoFecharFormulario?.addEventListener("click", () => {
    definirFormularioAberto(false);
    botaoAlternarFormulario?.focus();
});

if (window.location.hash === "#nova-materia" && formularioMateria?.hidden) {
    definirFormularioAberto(true, false, true);
}

function normalizarBusca(texto) {
    return texto.toLocaleLowerCase("pt-BR").normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

if (buscaMaterias) {
    buscaMaterias.addEventListener("input", () => {
        const termo = normalizarBusca(buscaMaterias.value.trim());
        let quantidade = 0;
        cardsMaterias.forEach((card) => {
            const visivel = normalizarBusca(card.dataset.subject).includes(termo);
            card.hidden = !visivel;
            if (visivel) quantidade += 1;
        });
        semMaterias.hidden = quantidade > 0;
        statusMaterias.textContent = quantidade === 1
            ? "1 matéria encontrada."
            : `${quantidade} matérias encontradas.`;
    });
}
