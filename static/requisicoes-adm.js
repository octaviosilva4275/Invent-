document.addEventListener('DOMContentLoaded', function() {
    const luaIcon = document.getElementById('lua-icon');
    const solIcon = document.getElementById('sol-icon');
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
        localStorage.setItem('theme', 'dark'); // Salva a preferência no localStorage
    }

    function activateLightMode() {
        body.classList.remove('dark-mode');
        body.classList.add('light-mode');
        toggleIcons(solIcon, luaIcon);
        localStorage.setItem('theme', 'light'); // Salva a preferência no localStorage
    }

    function toggleIcons(hiddenIcon, visibleIcon) {
        hiddenIcon.classList.add('none');
        visibleIcon.classList.remove('none');
    }

    // Eventos de clique para os ícones
    luaIcon.addEventListener('click', activateDarkMode);
    solIcon.addEventListener('click', activateLightMode);
});