document.addEventListener('DOMContentLoaded', function() {
    const luaIcon = document.getElementById('lua-icon'); // Para desktop
    const solIcon = document.getElementById('sol-icon'); // Para desktop

    const luaIconMobile = document.getElementsByClassName('lua-icon'); // Para mobile
    const solIconMobile = document.getElementsByClassName('sol-icon'); // Para mobile
    const body = document.body;
    const mobileDarkModeIcon = document.getElementById('modo-escuro-mobile'); // Ícone de modo escuro no mobile

    // Verificar a preferência do tema no localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        activateDarkMode();
    } else {
        activateLightMode();
    }

    // Função para ativar o modo escuro
    function activateDarkMode() {
        body.classList.remove('light-mode');
        body.classList.add('dark-mode');
        toggleIcons(luaIcon, solIcon, luaIconMobile, solIconMobile);
        localStorage.setItem('theme', 'dark'); // Salva a preferência no localStorage
    }

    // Função para ativar o modo claro
    function activateLightMode() {
        body.classList.remove('dark-mode');
        body.classList.add('light-mode');
        toggleIcons(solIcon, luaIcon, solIconMobile, luaIconMobile);
        localStorage.setItem('theme', 'light'); // Salva a preferência no localStorage
    }

    // Função para alternar os ícones
    function toggleIcons(hiddenIcon, visibleIcon, hiddenIconsMobile, visibleIconsMobile) {
        hiddenIcon.classList.add('none');
        visibleIcon.classList.remove('none');

        // Para os ícones móveis
        Array.from(hiddenIconsMobile).forEach(icon => {
            icon.classList.add('none');
        });

        Array.from(visibleIconsMobile).forEach(icon => {
            icon.classList.remove('none');
        });
    }

    // Eventos de clique para os ícones de desktop
    if (luaIcon) {
        luaIcon.addEventListener('click', function() {
            activateDarkMode();
        });
    }

    if (solIcon) {
        solIcon.addEventListener('click', function() {
            activateLightMode();
        });
    }

    // Adicionando evento de clique aos ícones móveis
    Array.from(luaIconMobile).forEach(icon => {
        icon.addEventListener('click', function() {
            activateDarkMode();
        });
    });

    Array.from(solIconMobile).forEach(icon => {
        icon.addEventListener('click', function() {
            activateLightMode();
        });
    });

    // **Evento de clique no item "Modo Escuro" (li) para mobile**
    if (mobileDarkModeIcon) {
        mobileDarkModeIcon.addEventListener('click', function() {
            if (body.classList.contains('dark-mode')) {
                activateLightMode();
            } else {
                activateDarkMode();
            }
            location.reload(); // Atualiza a página após o clique no botão
        });
    }
});
