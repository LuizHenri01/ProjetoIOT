const dialogExclusao = document.getElementById("dialog-exclusao");
const tituloExclusao = document.getElementById("titulo-dialog-exclusao");
const mensagemExclusao = document.getElementById("mensagem-dialog-exclusao");
const erroExclusao = document.getElementById("erro-dialog-exclusao");
const botaoConfirmarExclusao = document.getElementById("confirmar-exclusao");
const botaoCancelarExclusao = document.getElementById("cancelar-exclusao");
let acaoExclusao = null;
let destinoDepoisDeExcluir = null;

document.addEventListener("click", (evento) => {
    const botao = evento.target.closest("[data-delete-kind]");
    if (!botao || !dialogExclusao) return;

    acaoExclusao = botao;
    destinoDepoisDeExcluir = null;
    erroExclusao.hidden = true;
    erroExclusao.textContent = "";
    botaoConfirmarExclusao.disabled = false;
    botaoConfirmarExclusao.hidden = false;
    botaoConfirmarExclusao.innerHTML = '<i class="bi bi-trash3" aria-hidden="true"></i> Excluir';
    botaoCancelarExclusao.textContent = "Cancelar";

    if (botao.dataset.deleteKind === "subject") {
        const quantidade = Number(botao.dataset.deleteCount) || 0;
        tituloExclusao.textContent = "Excluir matéria?";
        mensagemExclusao.textContent = `A matéria “${botao.dataset.deleteName}” e suas ${quantidade} ${quantidade === 1 ? "aula" : "aulas"} serão removidas, incluindo imagens, transcrições e anotações. Esta ação não pode ser desfeita.`;
    } else {
        tituloExclusao.textContent = "Excluir aula?";
        mensagemExclusao.textContent = `${botao.dataset.deleteName} será removida, incluindo suas imagens, transcrições e anotações. Esta ação não pode ser desfeita.`;
    }

    dialogExclusao.showModal();
});

botaoCancelarExclusao?.addEventListener("click", () => {
    dialogExclusao.close();
});

dialogExclusao?.addEventListener("click", (evento) => {
    if (evento.target === dialogExclusao) dialogExclusao.close();
});

dialogExclusao?.addEventListener("close", () => {
    if (destinoDepoisDeExcluir) window.location.assign(destinoDepoisDeExcluir);
});

botaoConfirmarExclusao?.addEventListener("click", async () => {
    if (!acaoExclusao || botaoConfirmarExclusao.disabled) return;
    botaoConfirmarExclusao.disabled = true;
    botaoCancelarExclusao.disabled = true;
    botaoConfirmarExclusao.innerHTML = '<span class="delete-spinner" aria-hidden="true"></span> Excluindo…';
    erroExclusao.hidden = true;

    try {
        const resposta = await AulaMais.api(acaoExclusao.dataset.deleteUrl, { method: "DELETE" });
        const dados = await resposta.json();
        if (!resposta.ok) throw new Error(dados.erro || "Não foi possível excluir este registro.");

        if (dados.arquivos_removidos === false) {
            erroExclusao.textContent = "O registro foi excluído, mas alguns arquivos não puderam ser removidos. Entre em contato com o suporte.";
            erroExclusao.hidden = false;
            mensagemExclusao.textContent = "A alteração já foi salva.";
            destinoDepoisDeExcluir = acaoExclusao.dataset.deleteKind === "subject"
                ? "/aulas"
                : (dados.aulas_restantes ? window.location.pathname : "/aulas");
            botaoConfirmarExclusao.hidden = true;
            botaoCancelarExclusao.textContent = "Concluir";
            botaoCancelarExclusao.disabled = false;
            return;
        }

        if (acaoExclusao.dataset.deleteKind === "subject" || dados.aulas_restantes === 0) {
            window.location.assign("/aulas");
        } else {
            window.location.reload();
        }
    } catch (erro) {
        erroExclusao.textContent = erro.message || "Falha de conexão. Tente novamente.";
        erroExclusao.hidden = false;
        botaoConfirmarExclusao.disabled = false;
        botaoConfirmarExclusao.innerHTML = '<i class="bi bi-trash3" aria-hidden="true"></i> Tentar novamente';
        botaoCancelarExclusao.disabled = false;
    }
});
