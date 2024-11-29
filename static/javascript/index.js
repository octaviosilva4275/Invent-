document.addEventListener('DOMContentLoaded', () => {
    const texts = document.querySelectorAll('.text');
    const buttons = document.querySelectorAll('.btn');

    // Função para revelar textos
    function revealTexts() {
        texts.forEach((text, index) => {
            setTimeout(() => {
                text.classList.add('visible');
            }, index * 500);
        });
    }

    // Função para revelar botões com direções aleatórias
    function revealButtons() {
        buttons.forEach((button, index) => {
            setTimeout(() => {
                button.classList.add('visible');
            }, (index + 1) * 500);
        });
    }

    // Executa as funções de revelação de texto e botões
    revealTexts();
    revealButtons();
});