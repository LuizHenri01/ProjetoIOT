(() => {
    const header = document.querySelector(".site-header");
    const toggle = header?.querySelector(".menu-toggle");
    const navigation = header?.querySelector("#navegacao-principal");
    if (!header || !toggle || !navigation) return;

    const compactLayout = window.matchMedia("(max-width: 56rem)");

    function fecharMenu() {
        header.classList.remove("menu-open");
        toggle.setAttribute("aria-expanded", "false");
    }

    function atualizarLayout() {
        header.classList.toggle("menu-compact", compactLayout.matches);
        toggle.hidden = !compactLayout.matches;
        if (!compactLayout.matches) fecharMenu();
    }

    toggle.addEventListener("click", () => {
        const aberto = toggle.getAttribute("aria-expanded") === "true";
        header.classList.toggle("menu-open", !aberto);
        toggle.setAttribute("aria-expanded", String(!aberto));
    });

    navigation.addEventListener("click", (event) => {
        if (event.target instanceof Element && event.target.closest("a")) fecharMenu();
    });

    header.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && header.classList.contains("menu-open")) {
            fecharMenu();
            toggle.focus();
        }
    });

    compactLayout.addEventListener("change", atualizarLayout);
    atualizarLayout();
})();
