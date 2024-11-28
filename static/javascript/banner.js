// Função para criar caixinhas
function criarCaixinhas() {
    const container = document.getElementById('caixinhas-container');
    for (let i = 0; i < 30; i++) {
        const caixinha = document.createElement('div');
        caixinha.classList.add('caixinha');
        
        // Posicionamento aleatório no eixo X
        caixinha.style.left = Math.random() * 100 + 'vw';
        
        // Tamanho aleatório
        const tamanho = Math.random() * 250 + 50 + 'px';
        caixinha.style.width = tamanho;
        caixinha.style.height = tamanho;

        // Duração aleatória da queda entre 2 e 5 segundos
        const duracao = Math.random() * 3 + 2 + 's';
        caixinha.style.animationDuration = duracao;

        // Atraso aleatório para cada caixinha começar a cair
        const atraso = Math.random() * 2 + 's';
        caixinha.style.animationDelay = atraso;

        container.appendChild(caixinha);
    }
}

// Função para iniciar a animação das caixinhas
window.onload = function() {
    criarCaixinhas();
};

// Botão "Continuar" sobe o banner
document.getElementById('continuarBtn').addEventListener('click', function() {
    const banner = document.getElementById('banner');
    const conteudo = document.getElementById('conteudo');
    
    // Subir o banner
    banner.classList.add('subindo');
    
    // Mostrar o conteúdo após a animação do banner
    setTimeout(function() {
        conteudo.style.display = 'block';
    }, 1000); // Tempo da transição do banner
});