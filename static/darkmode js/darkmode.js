document.addEventListener('DOMContentLoaded', function () {
    const luaIcon = document.getElementById('lua-icon');
    const solIcon = document.getElementById('sol-icon');
    const luaIconMobile = document.querySelector('.lua-icon');
    const solIconMobile = document.querySelector('.sol-icon');
    const darkModeDesktop = document.querySelector('.darkmode'); // Pai do desktop
    const darkModeMobile = document.querySelector('#modo-escuro-mobile'); // Pai do mobile
    const body = document.body;

    // Verificar a preferência do tema no localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        activateDarkMode();
    } else {
        activateLightMode();
    }

    function activateDarkMode() {
        body.classList.remove('light-mode');
        body.classList.add('dark-mode');
        toggleIcons(luaIcon, solIcon);
        toggleIcons(luaIconMobile, solIconMobile);
        localStorage.setItem('theme', 'dark'); // Salva a preferência no localStorage
    }

    function activateLightMode() {
        body.classList.remove('dark-mode');
        body.classList.add('light-mode');
        toggleIcons(solIcon, luaIcon);
        toggleIcons(solIconMobile, luaIconMobile);
        localStorage.setItem('theme', 'light'); // Salva a preferência no localStorage
    }

    function toggleIcons(hiddenIcon, visibleIcon) {
        if (hiddenIcon && visibleIcon) {
            hiddenIcon.classList.add('none');
            visibleIcon.classList.remove('none');
        }
    }

    // Adicionar eventos para desktop (clique no span ou nas imagens)
    darkModeDesktop.addEventListener('click', () => {
        if (body.classList.contains('dark-mode')) {
            activateLightMode();
        } else {
            activateDarkMode();
        }
    });

    // Adicionar eventos para mobile (clique no span ou nas imagens)
    darkModeMobile.addEventListener('click', () => {
        if (body.classList.contains('dark-mode')) {
            activateLightMode();
        } else {
            activateDarkMode();
        }
    });
});
