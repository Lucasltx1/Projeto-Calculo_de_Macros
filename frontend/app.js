const BASE_URL = 'https://projeto-calculo-de-macros.onrender.com';

function getUserId() {
    let userId = localStorage.getItem('user_id');
    if (!userId) {
        userId = crypto.randomUUID();
        localStorage.setItem('user_id', userId);
    }
    return userId;
}

// 1. GET: Consumo Hoje (Correto)
async function carregarConsumo() {
    const response = await fetch(`${BASE_URL}/consumo-hoje`, {
        method: 'GET',
        headers: { 'x-user-id': getUserId() }
    });
    return await response.json();
}

// 2. POST: Registrar Alimento (Corrigido para enviar alimento_id e quantidade)
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

// 3. DELETE: Deletar Alimento (Corrigido para usar Path Parameter)
async function deletarAlimento(registro_id) {
    try {
        // Agora passando o ID na URL: /deletar-alimento/123
        const response = await fetch(`${BASE_URL}/deletar-alimento/${registro_id}`, {
            method: 'DELETE',
            headers: {
                'x-user-id': getUserId()
            }
        });

        if (!response.ok) throw new Error('Erro ao deletar');
        return await response.json();
    } catch (error) {
        console.error('Erro ao deletar:', error);
    }
}

// 4. POST: Calcular Metas (Adicionado para completar o backend)
async function calcularMetas(dadosMetas) {
    const response = await fetch(`${BASE_URL}/calcular-restante`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'x-user-id': getUserId()
        },
        body: JSON.stringify(dadosMetas)
    });
    return await response.json();
}