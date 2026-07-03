import os
from datetime import date
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega as variáveis secretas do arquivo .env
load_dotenv()

# --- ADICIONE ESTAS LINHAS DE TESTE ---
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

print(f"DEBUG: URL lida: {url}") # Isso vai imprimir no seu terminal
print(f"DEBUG: KEY lida: {key}")

if not url:
    raise ValueError("ERRO: A variável SUPABASE_URL não foi encontrada no .env!")
# --- FIM DO TESTE ---

supabase: Client = create_client(url, key)

# Conexão segura com o cliente do Supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Inicialização da aplicação FastAPI
app = FastAPI(
    title="Macro Tracker & TMB API",
    description="API para cálculo de Metabolismo Basal e rastreamento diário de macros usando a tabela TACO.",
    version="1.0.0"
)

# --- MODELOS DE ENTRADA (Validação de Dados com Pydantic) ---

class DadosUsuario(BaseModel):
    peso_kg: float
    altura_cm: float
    idade_anos: int
    sexo: str             # 'M' ou 'F'
    nivel_atividade: str   # 'sedentario', 'leve', 'moderado', 'muito_ativo'

class RegistroAlimento(BaseModel):
    usuario_id: str
    alimento_id: int
    quantidade_gramas: float

# --- ROTAS DA API ---

@app.get("/")
def home():
    return {"mensagem": "API de Tracker de Macros ativa! Acesse /docs para testar as rotas."}

@app.post("/calcular-metabolismo")
def calcular_metabolismo(dados: DadosUsuario):
    """
    Calcula a Taxa de Metabolismo Basal (TMB) e o Gasto Energético Total (GET)
    com base na equação de Mifflin-St Jeor e no nível de atividade informado.
    """
    if dados.sexo.upper() == 'M':
        tmb = (10 * dados.peso_kg) + (6.25 * dados.altura_cm) - (5 * dados.idade_anos) + 5
    elif dados.sexo.upper() == 'F':
        tmb = (10 * dados.peso_kg) + (6.25 * dados.altura_cm) - (5 * dados.idade_anos) - 161
    else:
        raise HTTPException(status_code=400, detail="O campo sexo deve ser 'M' (Masculino) ou 'F' (Feminino).")

    fatores = {
        "sedentario": 1.2,
        "leve": 1.375,
        "moderado": 1.55,
        "muito_ativo": 1.725
    }
    
    fator = fatores.get(dados.nivel_atividade.lower(), 1.2)
    get = tmb * fator

    return {
        "tmb_kcal": round(tmb, 2),
        "gasto_energetico_total_kcal": round(get, 2),
        "classificacao_atividade": dados.nivel_atividade.lower()
    }

@app.post("/registrar-alimento")
def registrar_alimento(registro: RegistroAlimento):
    """
    Busca o alimento na base TACO do Supabase, calcula as proporções dos macros
    e realiza o somatório acumulativo no diário do usuário para a data atual.
    """
    resposta_taco = supabase.table("tabela_taco").select("*").eq("id", registro.alimento_id).execute()
    
    if not resposta_taco.data:
        raise HTTPException(status_code=404, detail="Alimento não encontrado na base de dados TACO.")
        
    alimento = resposta_taco.data[0]
    
    multiplicador = registro.quantidade_gramas / 100.0
    kcal_ingeridas = alimento["energia_kcal"] * multiplicador
    prot_ingeridas = alimento["proteinas_g"] * multiplicador
    carb_ingeridas = alimento["carboidratos_g"] * multiplicador
    fat_ingeridas = alimento["lipideos_g"] * multiplicador

    hoje = str(date.today())
    
    busca_diaria = supabase.table("consumo_diario").select("*").eq("usuario_id", registro.usuario_id).eq("data", hoje).execute()

    if busca_diaria.data:
        registro_atual = busca_diaria.data[0]
        dados_atualizados = {
            "total_kcal": round(registro_atual["total_kcal"] + kcal_ingeridas, 2),
            "total_prot": round(registro_atual["total_prot"] + prot_ingeridas, 2),
            "total_carb": round(registro_atual["total_carb"] + carb_ingeridas, 2),
            "total_fat": round(registro_atual["total_fat"] + fat_ingeridas, 2),
        }
        supabase.table("consumo_diario").update(dados_atualizados).eq("id", registro_atual["id"]).execute()
        mensagem_retorno = "Alimento adicionado! O total do seu dia foi atualizado com sucesso."
    else:
        dados_atualizados = {
            "usuario_id": registro.usuario_id,
            "data": hoje,
            "total_kcal": round(kcal_ingeridas, 2),
            "total_prot": round(prot_ingeridas, 2),
            "total_carb": round(carb_ingeridas, 2),
            "total_fat": round(fat_ingeridas, 2),
        }
        supabase.table("consumo_diario").insert(dados_atualizados).execute()
        mensagem_retorno = "Primeiro alimento do dia registrado! Diário iniciado."

    return {
        "status": "sucesso",
        "mensagem": mensagem_retorno,
        "totais_acumulados_do_dia": dados_atualizados
    }