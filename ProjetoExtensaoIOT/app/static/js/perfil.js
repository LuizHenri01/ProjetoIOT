const inputFotoPerfil = document.getElementById("profile-photo-input");
const imagemPerfil = document.getElementById("profile-avatar-image");
const inicialPerfil = document.getElementById("profile-avatar-fallback");
const salvarFotoPerfil = document.getElementById("profile-photo-submit");
const orientacaoFotoPerfil = document.getElementById("profile-photo-help");
let urlPreviewFotoPerfil = null;

inputFotoPerfil?.addEventListener("change", () => {
    const arquivo = inputFotoPerfil.files?.[0];
    if (!arquivo) {
        salvarFotoPerfil.disabled = true;
        return;
    }

    if (arquivo.size > 5 * 1024 * 1024) {
        inputFotoPerfil.value = "";
        salvarFotoPerfil.disabled = true;
        orientacaoFotoPerfil.textContent = "A imagem precisa ter no máximo 5 MB.";
        orientacaoFotoPerfil.classList.add("profile-photo-help--error");
        return;
    }

    if (urlPreviewFotoPerfil) URL.revokeObjectURL(urlPreviewFotoPerfil);
    urlPreviewFotoPerfil = URL.createObjectURL(arquivo);
    imagemPerfil.src = urlPreviewFotoPerfil;
    imagemPerfil.hidden = false;
    inicialPerfil.hidden = true;
    salvarFotoPerfil.disabled = false;
    orientacaoFotoPerfil.textContent = `${arquivo.name} · pronta para salvar`;
    orientacaoFotoPerfil.classList.remove("profile-photo-help--error");
});
