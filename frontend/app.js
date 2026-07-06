const BASE_URL = 'https://projeto-calculo-de-macros.onrender.com';

// --- CONFIGURAÇÕES E SELETORES ---
function getUserId() {
    let userId = localStorage.getItem('user_id');
    if (!userId) {
        userId = crypto.randomUUID();
        localStorage.setItem('user_id', userId);
    }
    return userId;
}

const inputBusca = document.getElementById('alimento-busca');
const listaSugestoes = document.getElementById('sugestoes-lista');
const inputIdSelecionado = document.getElementById('alimento-id-selecionado');
const listaConsumo = document.getElementById('lista-consumo'); // Certifique-se que o ID no HTML seja esse
const btnAdicionar = document.getElementById('btn-adicionar');

// --- BUSCA DE ALIMENTOS ---
inputBusca.addEventListener('input', async (e) => {
    const termo = e.target.value;
    if (termo.length < 2) {
        listaSugestoes.innerHTML = '';
        return;
    }

    try {
        const response = await fetch(`${BASE_URL}/alimentos?q=${encodeURIComponent(termo)}`);
        const alimentos = await response.json();

        listaSugestoes.innerHTML = '';
        
        alimentos.forEach(alimento => {
            const li = document.createElement('li');
            li.textContent = alimento.nome_alimento; 
            
            li.onclick = () => {
                inputBusca.value = alimento.nome_alimento;
                inputIdSelecionado.value = alimento.id;
                listaSugestoes.innerHTML = '';
            };
            listaSugestoes.appendChild(li);
        });
    } catch (error) {
        console.error("Erro na busca de alimentos:", error);
    }
});

// --- REGISTRAR ALIMENTO ---
btnAdicionar.addEventListener('click', async () => {
    const id = inputIdSelecionado.value;
    const qtd = document.getElementById('quantidade-gramas').value;

    if (!id || !qtd) {
        alert('Selecione um alimento e informe a quantidade!');
        return;
    }

    await registrarAlimento(id, qtd);
    alert('Alimento registrado!');
    location.reload(); // Recarrega para atualizar a lista
});

async function registrarAlimento(alimento_id, quantidade_gramas) {
    const payload = { alimento_id, quantidade_gramas };
    try {
        const response = await fetch(`${BASE_URL}/registrar-alimento`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-user-id': getUserId()
            },
            body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error('Erro ao registrar');
        return await response.json();
    } catch (error) {
        console.error('Erro:', error);
    }
}

// --- CARREGAR CONSUMO ---
// --- CARREGAR CONSUMO COM BOTÃO DE DELETAR ---
async function carregarConsumo() {
    try {
        const response = await fetch(`${BASE_URL}/consumo-hoje`, {
            method: 'GET',
            headers: { 'x-user-id': getUserId() }
        });
        
        if (!response.ok) throw new Error('Erro ao buscar consumo');
        
        const dados = await response.json();
        listaConsumo.innerHTML = ''; 
        
        dados.forEach(item => {
            const li = document.createElement('li');
            const nome = item.tabela_taco ? item.tabela_taco.nome_alimento : "Alimento desconhecido";
            
            // Texto do item
            li.textContent = `${nome} - ${item.quantidade}g `;

            // Botão de deletar (o "X")
            const btnDelete = document.createElement('button');
            btnDelete.textContent = 'X';
            btnDelete.style.marginLeft = '10px';
            btnDelete.style.color = 'red';
            btnDelete.style.cursor = 'pointer';
            
            // Ação ao clicar no botão
            btnDelete.onclick = async () => {
                if (!confirm(`Deseja remover ${nome}?`)) return;

                try {
                    const res = await fetch(`${BASE_URL}/deletar-alimento/${item.id}`, {
                        method: 'DELETE',
                        headers: { 'x-user-id': getUserId() }
                    });

                    if (res.ok) {
                        location.reload(); // Recarrega para sumir com o item
                    } else {
                        alert('Erro ao deletar item.');
                    }
                } catch (err) {
                    console.error('Erro ao deletar:', err);
                }
            };

            li.appendChild(btnDelete);
            listaConsumo.appendChild(li);
        });
    } catch (e) {
        console.error("Erro ao carregar consumo:", e);
    }
}
// --- LIMPAR CONSUMO ---
document.getElementById('btn-limpar').addEventListener('click', async () => {
    if (!confirm('Tem certeza que deseja apagar todo o consumo de hoje?')) return;

    try {
        const response = await fetch(`${BASE_URL}/limpar-consumo`, {
            method: 'DELETE',
            headers: {
                'x-user-id': getUserId()
            }
        });

        if (response.ok) {
            alert('Consumo limpo com sucesso!');
            location.reload(); // Recarrega a página para limpar a lista visualmente
        } else {
            alert('Erro ao limpar consumo.');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao conectar com o servidor.');
    }
});
// --- INICIALIZAÇÃO ---
document.addEventListener('DOMContentLoaded', () => {
    console.log("Página carregada, buscando consumo...");
    carregarConsumo();
});