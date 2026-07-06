// --- 1. DEFINIÇÃO DE VARIÁVEIS ---
const inputBusca = document.getElementById('busca-alimento');
const listaSugestoes = document.getElementById('lista-sugestoes');
const inputIdSelecionado = document.getElementById('alimento_id_selecionado');
const inputQuantidade = document.getElementById('quantidade_gramas');
const btnAdicionar = document.getElementById('btn-adicionar');
const macroForm = document.getElementById('macro-form');
const listaConsumo = document.getElementById('lista-consumo');

// --- 2. FUNÇÃO AUXILIAR DE SELEÇÃO ---
function selecionar(id, nome) {
    inputIdSelecionado.value = id;
    inputBusca.value = nome;
    listaSugestoes.innerHTML = ''; 
}

// --- 3. AUTOCOMPLETE ---
inputBusca.addEventListener('input', async () => {
    const termo = inputBusca.value;
    if (termo.length < 2) { 
        listaSugestoes.innerHTML = ''; 
        return; 
    }

    try {
        const res = await fetch(`http://127.0.0.1:8000/buscar-alimento?nome=${encodeURIComponent(termo)}`);
        if (!res.ok) return;

        const lista = await res.json();

        if (lista.length > 0) {
            listaSugestoes.innerHTML = lista.map(item => `
                <li style="cursor:pointer; padding:8px; border-bottom:1px solid #eee; background: white;" 
                    onclick="selecionar(${item.id}, '${item.nome_alimento.replace(/'/g, "\\'")}')">
                    ${item.nome_alimento}
                </li>
            `).join('');
        } else {
            listaSugestoes.innerHTML = '<li style="padding:8px;">Nenhum alimento encontrado.</li>';
        }
    } catch (err) {
        console.error("Erro ao buscar alimentos:", err);
    }
});

// --- 4. REGISTRAR ALIMENTO ---
btnAdicionar.addEventListener('click', async () => {
    const dados = {
        alimento_id: parseInt(inputIdSelecionado.value),
        quantidade_gramas: parseFloat(inputQuantidade.value)
    };

    if (isNaN(dados.alimento_id) || isNaN(dados.quantidade_gramas)) {
        alert("Por favor, selecione um alimento da lista e informe a quantidade.");
        return;
    }

    try {
        const res = await fetch('http://127.0.0.1:8000/registrar-alimento', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });

        if (res.ok) {
            alert("Alimento registrado com sucesso!");
            inputBusca.value = '';
            inputQuantidade.value = '';
            inputIdSelecionado.value = '';
            await atualizarConsumoHoje(); 
            // Recalcula metas automaticamente
            macroForm.dispatchEvent(new Event('submit'));
        } else {
            alert("Erro ao registrar.");
        }
    } catch (err) {
        console.error("Erro de conexão:", err);
    }
});

// --- 5. CÁLCULO DE METAS ---
macroForm.addEventListener('submit', async (e) => {
    e.preventDefault(); 
    const payload = {
        peso_kg: parseFloat(document.getElementById('peso').value),
        altura_cm: parseFloat(document.getElementById('altura').value),
        idade_anos: parseInt(document.getElementById('idade').value),
        sexo: document.getElementById('sexo').value,
        nivel_atividade: document.getElementById('atividade').value,
        objetivo: document.getElementById('objetivo').value
    };

    try {
        const res = await fetch('http://127.0.0.1:8000/calcular-restante', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const dados = await res.json();
        if (res.ok) {
            const divConsumidos = document.getElementById('itens-consumidos');
            const c = dados.consumido_hoje;
            const r = dados.restante_hoje;
            divConsumidos.innerHTML = `
                <div style="background: #f9f9f9; padding: 10px; border-radius: 8px;">
                    <p><strong>Total Consumido:</strong> ${c.total_kcal} kcal | Prot: ${c.total_prot}g | Carb: ${c.total_carb}g | Fat: ${c.total_fat}g</p>
                    <hr>
                    <p><strong>Restante para a meta:</strong> ${r.calorias} kcal | Prot: ${r.proteinas_g}g | Carb: ${r.carboidratos_g}g | Fat: ${r.gorduras_g}g</p>
                </div>
            `;
        } else {
            alert("Erro ao calcular metas.");
        }
    } catch (err) {
        console.error("Erro de rede:", err);
    }
});

// --- 6. ATUALIZAR LISTA DE CONSUMO ---
async function atualizarConsumoHoje() {
    const response = await fetch('http://127.0.0.1:8000/consumo-hoje');
    const dados = await response.json();
    
    listaConsumo.innerHTML = ''; 

    dados.forEach(item => {
        const divItem = document.createElement('div');
        divItem.style.marginBottom = "5px";
        divItem.innerHTML = `
            ${item.tabela_taco.nome_alimento} - ${item.quantidade}g
            <button onclick="removerItem('${item.id}')" style="color: red; margin-left: 10px; cursor: pointer;">X</button>
        `;
        listaConsumo.appendChild(divItem);
    });
}

// --- 7. REMOVER ITEM INDIVIDUAL ---
async function removerItem(id) {
    if (!confirm("Remover este item?")) return;

    await fetch(`http://127.0.0.1:8000/deletar-alimento/${id}`, {
        method: 'DELETE'
    });
    
    await atualizarConsumoHoje();
    // Recalcula os macros automaticamente após remover o item
    macroForm.dispatchEvent(new Event('submit'));
}

// --- 8. LIMPAR TUDO ---
async function limparTudo() {
    if (!confirm("Tem certeza que deseja apagar todos os registros de hoje?")) return;

    try {
        const response = await fetch('http://127.0.0.1:8000/limpar-consumo', {
            method: 'DELETE'
        });

        if (response.ok) {
            await atualizarConsumoHoje();
            document.getElementById('itens-consumidos').innerHTML = '<p>Consumo limpo.</p>';
        } else {
            alert("Erro ao limpar tudo.");
        }
    } catch (error) {
        console.error("Erro:", error);
    }
}

// Inicialização
document.addEventListener('DOMContentLoaded', atualizarConsumoHoje);