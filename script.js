let currentChamadoId = null;

function toggleSidebar() {
    const menu = document.getElementById("menu");
    menu.classList.toggle("show");
}

function toggleUserMenu() {
    const dropdown = document.getElementById("user-dropdown");
    dropdown.classList.toggle("show");
}

function showClosePopup(chamadoId) {
    currentChamadoId = chamadoId;
    const form = document.getElementById("solucao-form");
    const isTecnico = window.location.pathname.includes("tecnico");
    form.action = `/fechar_chamado${isTecnico ? '_tecnico' : ''}/${chamadoId}`;
    document.getElementById("close-popup").style.display = "flex";
}

function hideClosePopup() {
    document.getElementById("close-popup").style.display = "none";
}

function togglePecasDetalhes() {
    const trocaPecas = document.getElementById("troca_pecas");
    if (trocaPecas) {
        const pecasDetalhes = document.getElementById("pecas-detalhes");
        if (trocaPecas.value === "Sim") {
            pecasDetalhes.style.display = "block";
            document.getElementById("qual_peca").required = true;
            document.getElementById("nome_marca_peca").required = true;
        } else {
            pecasDetalhes.style.display = "none";
            document.getElementById("qual_peca").required = false;
            document.getElementById("nome_marca_peca").required = false;
        }
    }
}

function openTab(tabName) {
    const tabs = document.getElementsByClassName("tab-content");
    const buttons = document.getElementsByClassName("tab-button");
    for (let i = 0; i < tabs.length; i++) {
        tabs[i].classList.remove("active");
        buttons[i].classList.remove("active");
    }
    document.getElementById(tabName).classList.add("active");
    for (let i = 0; i < buttons.length; i++) {
        if (buttons[i].getAttribute("onclick").includes(tabName)) {
            buttons[i].classList.add("active");
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // Gerenciar dropdowns
    const dropdowns = document.querySelectorAll(".dropdown-container");
    dropdowns.forEach(dropdown => {
        const input = dropdown.querySelector("input");
        const dropdownContent = dropdown.querySelector(".dropdown-content");
        const options = dropdownContent.querySelectorAll("div");

        // Abrir/fechar dropdown ao clicar no input
        input.addEventListener("click", () => {
            dropdownContent.classList.toggle("show");
        });

        // Selecionar opção ao clicar
        options.forEach(option => {
            option.addEventListener("click", () => {
                input.value = option.textContent;
                dropdownContent.classList.remove("show"); // Fechar após selecionar
            });
        });

        // Fechar dropdown se clicar fora
        document.addEventListener("click", (event) => {
            if (!dropdown.contains(event.target)) {
                dropdownContent.classList.remove("show");
            }
        });
    });

    // WebSocket para técnicos (mantido como está)
    if (window.location.pathname === "/dashboard" && document.querySelector("body").innerHTML.includes("Técnico")) {
        const socket = io('http://localhost:5000/tecnico', {
            transports: ['websocket'],
            reconnection: true,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000
        });

        socket.on('connect', () => {
            console.log('Conectado ao WebSocket');
        });

        socket.on('novo_chamado', (data) => {
            const table = document.querySelector('#abertos table');
            if (table) {
                const row = table.insertRow(-1);
                row.insertCell(0).innerText = data.id;
                row.insertCell(1).innerText = data.solicitador_id;
                row.insertCell(2).innerText = data.categoria;
                row.insertCell(3).innerText = data.setor;
                row.insertCell(4).innerText = data.regiao;
                row.insertCell(5).innerText = '2025-03-26';
                row.insertCell(6).innerText = 'aberto';
                row.insertCell(7).innerHTML = '<span class="sla-bubble green"></span> ? dias';
                row.insertCell(8).innerHTML = `<button class="close-btn" onclick="showClosePopup(${data.id})">✖</button>`;
            }
        });
    }
});