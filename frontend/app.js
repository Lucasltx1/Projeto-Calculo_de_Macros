const BASE_URL = 'https://projeto-calculo-de-macros.onrender.com';

function getUserId() {
    let userId = localStorage.getItem('user_id');
    if (!userId) {
        userId = crypto.randomUUID();
        localStorage.setItem('user_id', userId);
    }
    return userId;
}

// --- BUSCA DE ALIMENTOS ---
const inputBusca = document.getElementById('alimento-busca');
const listaSugestoes = document.getElementById('sugestoes-lista');
const inputIdSelecionado = document.getElementById('alimento-id-selecionado');

inputBusca.addEventListener('input', async (e) => {
    const termo = e.target.value;
    if (termo.length < 2) {
        listaSugestoes.innerHTML = '';
        return;
    }

    // Certifique-se que seu backend tem a rota GET /alimentos?q=...
    const response = await fetch(`${BASE_URL}/alimentos?q=${encodeURIComponent(termo)}`);
    const alimentos = await response.json();

    listaSugestoes.innerHTML = '';
    alimentos.forEach(alimento => {
        const li = document.createElement('li');
        li.textContent = alimento.nome;
        li.onclick = () => {
            inputBusca.value = alimento.nome;
            inputIdSelecionado.value = alimento.id; // Guarda o ID oculto
            listaSugestoes.innerHTML = '';
        };
        listaSugestoes.appendChild(li);
    });
});

// --- REGISTRAR ALIMENTO ---
document.getElementById('btn-adicionar').addEventListener('click', async () => {
    const id = inputIdSelecionado.value;
    const qtd = document.getElementById('quantidade-gramas').value;

    if (!id || !qtd) {
        alert('Selecione um alimento e informe a quantidade!');
        return;
    }

    await registrarAlimento(id, qtd);
    alert('Alimento registrado!');
    location.reload(); // Atualiza a página para ver o novo consumo
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

// --- OUTRAS FUNÇÕES ---
async function carregarConsumo() {
    const response = await fetch(`${BASE_URL}/consumo-hoje`, {
        method: 'GET',
        headers: { 'x-user-id': getUserId() }
    });
    return await response.json();
}

async function deletarAlimento(registro_id) {
    const response = await fetch(`${BASE_URL}/deletar-alimento/${registro_id}`, {
        method: 'DELETE',
        headers: { 'x-user-id': getUserId() }
    });
    return await response.json();
}