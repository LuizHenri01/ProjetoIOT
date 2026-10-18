// Preferências de acessibilidade: aplicação imediata e gravação local quando a pessoa salva.
const form = document.getElementById("form-acessibilidade");
const statusPreferencias = document.getElementById("status-preferencias");
const controleTamanho = document.getElementById("ac-tam");
const valorTamanho = document.getElementById("valor-tamanho");
const botaoDiminuir = document.getElementById("diminuir-tamanho");
const botaoAumentar = document.getElementById("aumentar-tamanho");
const TAMANHO_MINIMO = 80;
const TAMANHO_MAXIMO = 200;
const PASSO_TAMANHO = 10;

const campos = {
    tamanho: controleTamanho,
    espaco: form.elements["espaco"],
    contraste: form.elements["contraste"],
    animacoes: form.elements["animacoes"],
    foco: form.elements["foco"],
    leitura: form.elements["leitura"],
    velocidade: form.elements["velocidade"],
};

function atualizarControleTamanho() {
    const tamanho = Number(controleTamanho.value);
    valorTamanho.value = `${tamanho}%`;
    valorTamanho.textContent = `${tamanho}%`;
    botaoDiminuir.disabled = tamanho <= TAMANHO_MINIMO;
    botaoAumentar.disabled = tamanho >= TAMANHO_MAXIMO;
}

function preencher(preferencias) {
    campos.tamanho.value = Math.max(
        TAMANHO_MINIMO,
        Math.min(TAMANHO_MAXIMO, Number(preferencias.tamanho) || 100)
    );
    campos.espaco.value = preferencias.espaco;
    campos.contraste.value = preferencias.contraste;
    campos.animacoes.checked = preferencias.animacoes;
    campos.foco.checked = preferencias.foco;
    campos.leitura.checked = preferencias.leitura;
    campos.velocidade.value = preferencias.velocidade;
    atualizarControleTamanho();
}

function ler() {
    return {
        tamanho: Number(campos.tamanho.value),
        espaco: campos.espaco.value,
        contraste: campos.contraste.value,
        animacoes: campos.animacoes.checked,
        foco: campos.foco.checked,
        leitura: campos.leitura.checked,
        velocidade: campos.velocidade.value,
    };
}

// Permite que o controle flutuante leia as escolhas ainda não salvas desta tela.
AulaMais.lerPrefsEmEdicao = ler;

function ajustarTamanho(delta) {
    const tamanhoAtual = Number(controleTamanho.value);
    controleTamanho.value = String(Math.max(
        TAMANHO_MINIMO,
        Math.min(TAMANHO_MAXIMO, tamanhoAtual + delta)
    ));
    atualizarControleTamanho();
    controleTamanho.dispatchEvent(new Event("input", { bubbles: true }));
}

botaoDiminuir.addEventListener("click", () => ajustarTamanho(-PASSO_TAMANHO));
botaoAumentar.addEventListener("click", () => ajustarTamanho(PASSO_TAMANHO));

preencher(AulaMais.lerPrefs());

// Mostra o efeito enquanto a pessoa ajusta; só "Salvar" guarda de verdade.
form.addEventListener("input", () => {
    atualizarControleTamanho();
    AulaMais.aplicarPrefs(ler());
    statusPreferencias.textContent = "";
});

form.addEventListener("submit", (evento) => {
    evento.preventDefault();
    AulaMais.salvarPrefs(ler());
    statusPreferencias.textContent = "Preferências salvas neste aparelho.";
});

form.addEventListener("reset", (evento) => {
    evento.preventDefault();
    preencher(AulaMais.PADRAO);
    AulaMais.aplicarPrefs(AulaMais.PADRAO);
    AulaMais.salvarPrefs(AulaMais.PADRAO);
    statusPreferencias.textContent = "Padrão restaurado.";
});

// Se saiu sem salvar, volta ao que estava salvo.
window.addEventListener("pagehide", () => AulaMais.aplicarPrefs(AulaMais.lerPrefs()));
window.addEventListener("aulamais:preferencias-atualizadas", (evento) => {
    preencher(evento.detail);
    statusPreferencias.textContent = "Tamanho do texto atualizado e salvo neste aparelho.";
});
