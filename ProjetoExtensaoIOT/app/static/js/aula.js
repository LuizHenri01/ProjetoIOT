// Controla o ciclo da aula e o encerramento no horário definido.
const campoDisciplina = document.getElementById("campo-disciplina");
const campoNomeAula = document.getElementById("campo-nome-aula");
const campoProfessor = document.getElementById("campo-professor");
const campoInicio = document.getElementById("campo-horario-inicio");
const campoFim = document.getElementById("campo-horario-fim");
const botaoIniciarAula = document.getElementById("botao-iniciar-aula");
const botaoEncerrarAula = document.getElementById("botao-encerrar-aula");
const statusAula = document.getElementById("status-aula");
let temporizadorEncerramento;
let encerramentoAutomaticoEmCurso = false;

function pararTemporizador() {
    if (temporizadorEncerramento) clearTimeout(temporizadorEncerramento);
    temporizadorEncerramento = undefined;
}

function atualizarDadosMateria() {
    const materia = campoDisciplina.selectedOptions[0];
    const selecionada = Boolean(campoDisciplina.value);
    campoProfessor.value = selecionada ? materia.dataset.professor || "" : "";
    campoInicio.value = selecionada ? materia.dataset.inicio || "" : "";
    campoFim.value = selecionada ? materia.dataset.fim || "" : "";
    botaoIniciarAula.disabled = !selecionada;
}

function agendarEncerramento(aula) {
    pararTemporizador();
    if (!aula?.horario_fim_previsto) return;

    const dataHoraFim = new Date(`${aula.data}T${aula.horario_fim_previsto}:00`);
    const atraso = Math.max(0, dataHoraFim.getTime() - Date.now());
    temporizadorEncerramento = setTimeout(encerrarAutomaticamente, Math.min(atraso, 2147480000));
}

async function encerrarAutomaticamente() {
    if (encerramentoAutomaticoEmCurso) return;
    encerramentoAutomaticoEmCurso = true;
    try {
        // Salva o último trecho reconhecido antes que o servidor feche a aula.
        if (window.pararTranscricao) await window.pararTranscricao();
        const resposta = await AulaMais.api("/api/aulas/ativa");
        const dados = await resposta.json();
        if (!dados.aula) {
            mostrarEstadoAula(null);
            campoNomeAula.value = "";
            statusAula.textContent = "A aula foi encerrada automaticamente no horário programado.";
            window.location.assign("/aulas");
        } else {
            mostrarEstadoAula(dados.aula);
            // O navegador limita temporizadores longos; recalcula o tempo restante.
            agendarEncerramento(dados.aula);
        }
    } catch (erro) {
        statusAula.textContent = "Não foi possível confirmar o encerramento automático. Verifique a conexão.";
        temporizadorEncerramento = setTimeout(encerrarAutomaticamente, 5000);
    } finally {
        encerramentoAutomaticoEmCurso = false;
    }
}

function mostrarEstadoAula(aula) {
    const ativa = Boolean(aula);
    botaoIniciarAula.disabled = ativa;
    campoDisciplina.disabled = ativa;
    campoProfessor.disabled = ativa;
    campoInicio.disabled = true;
    campoFim.disabled = true;
    campoNomeAula.disabled = ativa;
    botaoEncerrarAula.disabled = !ativa;
    botaoEncerrarAula.hidden = !ativa;

    if (ativa) {
        campoDisciplina.value = String(aula.materia_id || "");
        campoProfessor.value = aula.professor || "";
        campoNomeAula.value = aula.nome_aula || "";
        campoInicio.value = aula.horario_inicio || "";
        campoFim.value = aula.horario_fim_previsto || "";
        statusAula.textContent = aula.horario_fim_previsto
            ? `${aula.nome_aula || "Aula"} em andamento. Encerramento automático às ${aula.horario_fim_previsto.slice(0, 5)}.`
            : `${aula.nome_aula || "Aula"} em andamento.`;
        agendarEncerramento(aula);
    } else {
        pararTemporizador();
        atualizarDadosMateria();
        statusAula.textContent = "Nenhuma aula em andamento.";
    }

    document.dispatchEvent(new CustomEvent("aula:estado", { detail: { ativa } }));
}

async function carregarAulaAtiva() {
    try {
        const resposta = await AulaMais.api("/api/aulas/ativa");
        const dados = await resposta.json();
        mostrarEstadoAula(dados.aula);
        return dados.aula;
    } catch (erro) {
        statusAula.textContent = "Sem conexão com o servidor. Verifique o Wi-Fi.";
        return null;
    }
}

botaoIniciarAula.addEventListener("click", async () => {
    const materiaId = Number(campoDisciplina.value);
    const nomeAula = campoNomeAula.value.trim();
    if (!materiaId) {
        statusAula.textContent = "Escolha uma matéria antes de iniciar a aula.";
        campoDisciplina.focus();
        return;
    }
    if (!nomeAula) {
        statusAula.textContent = "Informe o nome da aula antes de iniciar.";
        campoNomeAula.focus();
        return;
    }

    botaoIniciarAula.disabled = true;
    try {
        const resposta = await AulaMais.api("/api/aulas/iniciar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                materia_id: materiaId,
                nome_aula: nomeAula,
            }),
        });
        if (resposta.ok || resposta.status === 409) {
            await carregarAulaAtiva();
        } else {
            const dados = await resposta.json();
            statusAula.textContent = dados.erro || "Erro ao iniciar a aula. Tente novamente.";
            botaoIniciarAula.disabled = false;
        }
    } catch (erro) {
        statusAula.textContent = "Sem conexão com o servidor. Verifique o Wi-Fi.";
        botaoIniciarAula.disabled = false;
    }
});

botaoEncerrarAula.addEventListener("click", async () => {
    if (window.pararTranscricao) await window.pararTranscricao();
    try {
        const resposta = await AulaMais.api("/api/aulas/encerrar", { method: "POST" });
        if (resposta.ok) {
            campoNomeAula.value = "";
            window.location.assign("/aulas");
        } else if (resposta.status === 400) {
            await carregarAulaAtiva();
        } else {
            statusAula.textContent = "Erro ao encerrar a aula. Tente novamente.";
        }
    } catch (erro) {
        statusAula.textContent = "Sem conexão com o servidor. Verifique o Wi-Fi.";
    }
});

document.addEventListener("DOMContentLoaded", () => {
    campoDisciplina.addEventListener("change", atualizarDadosMateria);
    atualizarDadosMateria();
    carregarAulaAtiva();
});
