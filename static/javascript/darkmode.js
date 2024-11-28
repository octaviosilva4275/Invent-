document.addEventListener('DOMContentLoaded', function() {
    const luaIcon = document.getElementById('lua-icon'); // Para desktop
    const solIcon = document.getElementById('sol-icon'); // Para desktop

    const luaIconMobile = document.getElementsByClassName('lua-icon'); // Para mobile
    const solIconMobile = document.getElementsByClassName('sol-icon'); // Para mobile
    const body = document.body;
    const mobileDarkModeIcon = document.getElementById('modo-escuro-mobile'); // Ícone de modo escuro no mobile

    // Verificar a preferência do tema no localStorage
    const savedTheme = localStorage.getItem('theme');
    console.log('Tema salvo no localStorage:', savedTheme); // Log para verificar o valor salvo

    if (savedTheme === 'dark') {
        console.log('Ativando Modo Escuro...');
        activateDarkMode();
    } else {
        console.log('Ativando Modo Claro...');
        activateLightMode();
    }

    // Função para ativar o modo escuro
    function activateDarkMode() {
        console.log('Modo Escuro Ativado');
        body.classList.remove('light-mode');
        body.classList.add('dark-mode');
        toggleIcons(luaIcon, solIcon, luaIconMobile, solIconMobile);
        localStorage.setItem('theme', 'dark'); // Salva a preferência no localStorage
    }

    // Função para ativar o modo claro
    function activateLightMode() {
        console.log('Modo Claro Ativado');
        body.classList.remove('dark-mode');
        body.classList.add('light-mode');
        toggleIcons(solIcon, luaIcon, solIconMobile, luaIconMobile);
        localStorage.setItem('theme', 'light'); // Salva a preferência no localStorage
    }

    // Função para alternar os ícones
    function toggleIcons(hiddenIcon, visibleIcon, hiddenIconsMobile, visibleIconsMobile) {
        console.log('Alternando ícones');
        hiddenIcon.classList.add('none');
        visibleIcon.classList.remove('none');

        // Para os ícones móveis
        Array.from(hiddenIconsMobile).forEach(icon => {
            icon.classList.add('none');
            console.log('Ícone móvel oculto:', icon);
        });

        Array.from(visibleIconsMobile).forEach(icon => {
            icon.classList.remove('none');
            console.log('Ícone móvel visível:', icon);
        });
    }

    // Eventos de clique para os ícones de desktop
    if (luaIcon) {
        luaIcon.addEventListener('click', function() {
            console.log('Ícone Modo Escuro clicado (desktop)');
            activateDarkMode();
        });
    }

    if (solIcon) {
        solIcon.addEventListener('click', function() {
            console.log('Ícone Modo Claro clicado (desktop)');
            activateLightMode();
        });
    }

    // Adicionando evento de clique aos ícones móveis
    Array.from(luaIconMobile).forEach(icon => {
        icon.addEventListener('click', function() {
            console.log('Ícone Modo Escuro clicado (mobile)');
            activateDarkMode();
        });
    });

    Array.from(solIconMobile).forEach(icon => {
        icon.addEventListener('click', function() {
            console.log('Ícone Modo Claro clicado (mobile)');
            activateLightMode();
        });
    });

    // **Evento de clique no item "Modo Escuro" (li) para mobile**
    if (mobileDarkModeIcon) {
        mobileDarkModeIcon.addEventListener('click', function() {
            console.log('Item "Modo Escuro" clicado (mobile - ícone de lista)');
            if (body.classList.contains('dark-mode')) {
                activateLightMode();
            } else {
                activateDarkMode();
            }
        });
    }
});
    