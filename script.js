const wrapper = document.querySelector('.wrapper');
const signUpLink = document.querySelector('.signUp-link');
const signInLink = document.querySelector('.signIn-link');

// Verificar se os elementos existem antes de adicionar event listeners
if (signUpLink) {
    signUpLink.addEventListener('click', () => {
        wrapper.classList.add('animate-signIn');
        wrapper.classList.remove('animate-signUp');
    });
}

if (signInLink) {
    signInLink.addEventListener('click', () => {
        wrapper.classList.add('animate-signUp');
        wrapper.classList.remove('animate-signIn');
    });
}

// URL base da API
const API_URL = 'http://localhost:5000/api';

// Credenciais do admin
const ADMIN_USERNAME = 'adminleilão';
const ADMIN_PASSWORD = '12345678';

// Estado da aplicação
let isAdminLoggedIn = false;

// Função para verificar se o admin está logado
function checkAdminLogin() {
    return localStorage.getItem('adminLoggedIn') === 'true';
}

// Função para fazer login do admin
function loginAdmin(username, password) {
    if (username === ADMIN_USERNAME && password === ADMIN_PASSWORD) {
        localStorage.setItem('adminLoggedIn', 'true');
        isAdminLoggedIn = true;
        return true;
    }
    return false;
}

// Função para fazer logout do admin
function logoutAdmin() {
    localStorage.removeItem('adminLoggedIn');
    isAdminLoggedIn = false;
}

// Função para salvar o valor do lance no localStorage
function salvarLance(leilaoId, valor) {
    localStorage.setItem(`lance_${leilaoId}`, valor);
}

// Função para recuperar o valor do lance do localStorage
function recuperarLance(leilaoId) {
    return localStorage.getItem(`lance_${leilaoId}`);
}

// Função para salvar carros no localStorage
function salvarCarros(carros) {
    localStorage.setItem('carros', JSON.stringify(carros));
}

// Função para recuperar carros do localStorage
function recuperarCarros() {
    const carros = localStorage.getItem('carros');
    return carros ? JSON.parse(carros) : [];
}

// Função para adicionar um novo carro
function adicionarCarro(carro) {
    const carros = recuperarCarros();
    // Gerar ID único para o carro
    carro.id_leilao = Date.now();
    carros.push(carro);
    salvarCarros(carros);
    return carro;
}

// Função para remover um carro
function removerCarro(id) {
    const carros = recuperarCarros();
    const index = carros.findIndex(carro => carro.id_leilao === parseInt(id));
    if (index !== -1) {
        carros.splice(index, 1);
        salvarCarros(carros);
        return true;
    }
    return false;
}

// Função para atualizar a exibição do lance na interface
function atualizarExibicaoLance(leilaoId, valor) {
    const elementoLance = document.querySelector(`[data-leilao-id="${leilaoId}"] .lance-valor`);
    if (elementoLance) {
        elementoLance.textContent = parseFloat(valor).toFixed(2);
    }
}

// Função para processar um novo lance
function processarNovoLance(leilaoId, valor) {
    // Verificar se o valor é válido
    if (!valor || isNaN(valor) || valor <= 0) {
        alert('Por favor, insira um valor válido para o lance.');
        return;
    }
    
    // Salvar o valor no localStorage
    salvarLance(leilaoId, valor);
    
    // Atualizar a interface
    atualizarExibicaoLance(leilaoId, valor);
    
    // Aqui você pode adicionar código para enviar o lance para o backend
    alert(`Lance de R$ ${parseFloat(valor).toFixed(2)} registrado com sucesso!`);
}

// Função para carregar os leilões do backend ou localStorage
function carregarLeiloes() {
    const listaCarros = document.getElementById('lista-carros');
    if (!listaCarros) return;
    
    // Limpar a lista atual
    listaCarros.innerHTML = '';
    
    // Carregar carros do localStorage
    const carros = recuperarCarros();
    
    // Se não houver carros no localStorage, usar exemplos
    if (carros.length === 0) {
        const leiloesExemplo = [
            { id_leilao: 1, carro_nome: 'Honda Civic', marca: 'Honda', modelo: 'Civic', ano: 2020, preco_inicial: 80000, lance_atual: 85000 },
            { id_leilao: 2, carro_nome: 'Toyota Corolla', marca: 'Toyota', modelo: 'Corolla', ano: 2019, preco_inicial: 75000, lance_atual: 78000 },
            { id_leilao: 3, carro_nome: 'Volkswagen Golf', marca: 'Volkswagen', modelo: 'Golf', ano: 2021, preco_inicial: 90000, lance_atual: 92000 }
        ];
        
        // Salvar os exemplos no localStorage
        salvarCarros(leiloesExemplo);
        
        leiloesExemplo.forEach(leilao => {
            adicionarCardLeilao(leilao, listaCarros);
        });
    } else {
        carros.forEach(leilao => {
            adicionarCardLeilao(leilao, listaCarros);
        });
    }
}

// Função para carregar os carros no painel admin
function carregarCarrosAdmin() {
    const listaAdminCarros = document.getElementById('lista-admin-carros');
    if (!listaAdminCarros) return;
    
    // Limpar a lista atual
    listaAdminCarros.innerHTML = '';
    
    // Carregar carros do localStorage
    const carros = recuperarCarros();
    
    carros.forEach(carro => {
        adicionarCardAdmin(carro, listaAdminCarros);
    });
}

// Função para adicionar um card de leilão à interface
function adicionarCardLeilao(leilao, container) {
    const template = document.getElementById('template-card-leilao');
    if (!template) return;
    
    const clone = document.importNode(template.content, true);
    const card = clone.querySelector('.card');
    
    // Definir o ID do leilão como atributo data
    card.setAttribute('data-leilao-id', leilao.id_leilao);
    
    // Preencher as informações do leilão
    card.querySelector('.carro-nome').textContent = leilao.carro_nome || `${leilao.marca} ${leilao.modelo}`;
    card.querySelector('.carro-info').textContent = `${leilao.marca} ${leilao.modelo} (${leilao.ano})`;
    
    // Verificar se há um lance salvo no localStorage
    const lanceSalvo = recuperarLance(leilao.id_leilao);
    const valorLance = lanceSalvo || leilao.lance_atual || leilao.preco_inicial;
    
    // Atualizar o valor do lance
    card.querySelector('.lance-valor').textContent = parseFloat(valorLance).toFixed(2);
    
    // Configurar o formulário de lance
    const inputLance = card.querySelector('.novo-lance');
    const btnLance = card.querySelector('.btn-lance');
    
    // Definir o valor mínimo para o lance
    inputLance.min = parseFloat(valorLance) + 1;
    inputLance.placeholder = `Mínimo: R$ ${parseFloat(valorLance) + 1}`;
    
    // Adicionar evento para o botão de lance
    btnLance.addEventListener('click', () => {
        const novoValor = inputLance.value;
        if (parseFloat(novoValor) <= parseFloat(valorLance)) {
            alert('O lance deve ser maior que o valor atual!');
            return;
        }
        processarNovoLance(leilao.id_leilao, novoValor);
        inputLance.value = '';
        // Atualizar o valor mínimo após o lance
        inputLance.min = parseFloat(novoValor) + 1;
        inputLance.placeholder = `Mínimo: R$ ${parseFloat(novoValor) + 1}`;
    });
    
    // Adicionar o card ao container
    container.appendChild(clone);
}

// Função para adicionar um card de leilão ao painel admin
function adicionarCardAdmin(carro, container) {
    const template = document.getElementById('template-card-admin');
    if (!template) return;
    
    const clone = document.importNode(template.content, true);
    const card = clone.querySelector('.card');
    
    // Definir o ID do leilão como atributo data
    card.setAttribute('data-leilao-id', carro.id_leilao);
    
    // Preencher as informações do carro
    card.querySelector('.carro-nome').textContent = carro.carro_nome || `${carro.marca} ${carro.modelo}`;
    card.querySelector('.carro-info').textContent = `${carro.marca} ${carro.modelo} (${carro.ano})`;
    card.querySelector('.preco-inicial').textContent = parseFloat(carro.preco_inicial).toFixed(2);
    
    // Verificar se há um lance salvo no localStorage
    const lanceSalvo = recuperarLance(carro.id_leilao);
    const valorLance = lanceSalvo || carro.lance_atual || carro.preco_inicial;
    
    // Atualizar o valor do lance
    card.querySelector('.lance-valor').textContent = parseFloat(valorLance).toFixed(2);
    
    // Adicionar evento para o botão de remover
    const btnRemover = card.querySelector('.btn-remover');
    btnRemover.addEventListener('click', () => {
        if (confirm(`Tem certeza que deseja remover o carro ${carro.carro_nome || `${carro.marca} ${carro.modelo}`}?`)) {
            removerCarro(carro.id_leilao);
            card.remove();
            alert('Carro removido com sucesso!');
            // Recarregar a lista de carros na home
            carregarLeiloes();
        }
    });
    
    // Adicionar o card ao container
    container.appendChild(clone);
}

// Função para mostrar a página selecionada
function mostrarPagina(id) {
    // Verificar se o admin está tentando acessar o painel admin
    if (id === 'admin-panel' && !isAdminLoggedIn) {
        id = 'login-admin';
        alert('Você precisa fazer login como administrador para acessar esta página.');
    }
    
    // Esconder todas as páginas
    document.querySelectorAll('.pagina').forEach(pagina => {
        pagina.classList.remove('ativa');
    });
    
    // Mostrar a página selecionada
    document.getElementById(id).classList.add('ativa');
    
    // Carregar conteúdo específico da página
    if (id === 'home') {
        carregarLeiloes();
    } else if (id === 'cliente') {
        carregarLeiloes(); // Por enquanto, carrega os mesmos leilões
    } else if (id === 'admin-panel') {
        carregarCarrosAdmin();
    }
}

// Carregar os valores dos lances ao iniciar a página
document.addEventListener('DOMContentLoaded', () => {
    // Verificar se o admin está logado
    isAdminLoggedIn = checkAdminLogin();
    
    // Inicializar a página home por padrão
    mostrarPagina('home');
    
    // Configurar o formulário de login do admin
    const formLoginAdmin = document.getElementById('form-login-admin');
    if (formLoginAdmin) {
        formLoginAdmin.addEventListener('submit', (e) => {
            e.preventDefault();
            const username = document.getElementById('admin-username').value;
            const password = document.getElementById('admin-password').value;
            
            if (loginAdmin(username, password)) {
                mostrarPagina('admin-panel');
                formLoginAdmin.reset();
                document.getElementById('login-error').textContent = '';
            } else {
                document.getElementById('login-error').textContent = 'Usuário ou senha incorretos.';
            }
        });
    }
    
    // Configurar o botão de logout
    const btnLogout = document.getElementById('btn-logout');
    if (btnLogout) {
        btnLogout.addEventListener('click', () => {
            logoutAdmin();
            mostrarPagina('home');
            alert('Você saiu da área administrativa.');
        });
    }
    
    // Configurar o formulário de adição de carros
    const formCarro = document.getElementById('form-carro');
    if (formCarro) {
        formCarro.addEventListener('submit', (e) => {
            e.preventDefault();
            
            // Verificar se o admin está logado
            if (!isAdminLoggedIn) {
                alert('Você precisa estar logado como administrador para adicionar carros.');
                mostrarPagina('login-admin');
                return;
            }
            
            const novoCarro = {
                marca: document.getElementById('marca').value,
                modelo: document.getElementById('modelo').value,
                ano: parseInt(document.getElementById('ano').value),
                carro_nome: document.getElementById('nome').value,
                categoria: document.getElementById('categoria').value,
                preco_inicial: parseFloat(document.getElementById('preco').value),
                lance_atual: parseFloat(document.getElementById('preco').value)
            };
            
            // Adicionar o carro
            const carroAdicionado = adicionarCarro(novoCarro);
            
            // Atualizar a interface
            adicionarCardAdmin(carroAdicionado, document.getElementById('lista-admin-carros'));
            
            // Recarregar a lista de carros na home
            carregarLeiloes();
            
            alert(`Carro adicionado: ${novoCarro.carro_nome || `${novoCarro.marca} ${novoCarro.modelo}`}`);
            formCarro.reset();
        });
    }
});