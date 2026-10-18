self.addEventListener("push", (evento) => {
    let dados = {};
    try {
        if (evento.data) {
            const bruto = evento.data.text();
            try {
                dados = JSON.parse(bruto);
            } catch (erro) {
                const launch = bruto.match(/launch="([^"]*)"/);
                if (launch) {
                    const valor = launch[1].replace(/&quot;/g, '"').replace(/&#x27;/g, "'")
                        .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
                    dados = JSON.parse(valor);
                }
            }
        }
    } catch (erro) { /* payload vazio ou inválido */ }
    evento.waitUntil(self.registration.showNotification(dados.title || "AulaMais", {
        body: dados.body || "Há uma atualização da sua aula.",
        icon: "/static/img/notificacao.svg",
        badge: "/static/img/notificacao.svg",
        data: { url: dados.url || "/aulas" },
    }));
});

self.addEventListener("notificationclick", (evento) => {
    evento.notification.close();
    const destino = new URL(evento.notification.data?.url || "/aulas", self.location.origin).href;
    evento.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientes) => {
        for (const cliente of clientes) {
            if (cliente.url.startsWith(self.location.origin) && "focus" in cliente) {
                cliente.navigate(destino);
                return cliente.focus();
            }
        }
        return self.clients.openWindow(destino);
    }));
});
