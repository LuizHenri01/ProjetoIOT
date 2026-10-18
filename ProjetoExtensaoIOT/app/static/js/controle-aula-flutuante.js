(() => {
    const controle = document.getElementById("controle-aula-flutuante");
    const botao = document.getElementById("encerrar-aula-flutuante");
    const status = document.getElementById("status-encerrar-aula-flutuante");
    if (!controle || !botao || !status || !window.AulaMais?.api) return;

    let consultando = false;
    let encerrando = false;
    let aulaAtiva = null;

    async function atualizarAulaAtiva() {
        if (consultando || encerrando || document.visibilityState !== "visible") return;
        consultando = true;
        try {
            const resposta = await AulaMais.api("/api/aulas/ativa");
            if (!resposta.ok) throw new Error("Não foi possível verificar a aula em andamento.");
            const dados = await resposta.json();
            aulaAtiva = dados.aula || null;
            controle.hidden = !aulaAtiva;
            if (aulaAtiva) {
                const nome = aulaAtiva.nome_aula || aulaAtiva.disciplina || "aula";
                botao.setAttribute("aria-label", `Encerrar ${nome}`);
                botao.querySelector("span").textContent = "Encerrar aula";
            } else {
                status.textContent = "";
            }
        } catch (erro) {
            // Uma falha momentanea na rede nÃ£o deve ocultar um controle ja visivel.
        } finally {
            consultando = false;
        }
    }

    botao.addEventListener("click", async () => {
        if (encerrando || !aulaAtiva) return;
        encerrando = true;
        botao.disabled = true;
        botao.querySelector("span").textContent = "Encerrando...";
        status.textContent = "";
        try {
            if (window.pararTranscricao) {
                try { await window.pararTranscricao(); }
                catch (erro) { /* falha ao salvar o Ãºltimo trecho nÃ£o impede o encerramento */ }
            }
            const resposta = await AulaMais.api("/api/aulas/encerrar", { method: "POST" });
            const dados = await resposta.json().catch(() => ({}));
            if (!resposta.ok) throw new Error(dados.erro || "NÃ£o foi possÃ­vel encerrar a aula.");

            aulaAtiva = null;
            controle.hidden = true;
            status.textContent = "";
        } catch (erro) {
            status.textContent = erro.message || "Falha de conexÃ£o. Tente novamente.";
            botao.querySelector("span").textContent = "Tentar novamente";
        } finally {
            encerrando = false;
            botao.disabled = false;
        }
    });

    atualizarAulaAtiva();
    window.setInterval(atualizarAulaAtiva, 8000);
    document.addEventListener("aula:estado", atualizarAulaAtiva);
    document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") atualizarAulaAtiva();
    });
})();
