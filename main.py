import os
from datetime import date
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = FastAPI(title="Macro Tracker API")

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dieta.mandetalucas.workers.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], # Permitir todos os headers para aceitar o x-user-id
)

# Configuração do Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Modelos de dados
class DadosMetas(BaseModel):
    peso_kg: float
    altura_cm: float
    idade_anos: int
    sexo: str
    nivel_atividade: str
    objetivo: str

class RegistroAlimento(BaseModel):
    alimento_id: int
    quantidade_gramas: float

# --- ROTAS ---

@app.get("/consumo-hoje")
def obter_consumo_hoje(x_user_id: str = Header(...)):
    try:
        hoje = date.today().isoformat()
        # Filtro adicionado: .eq("user_id", x_user_id)
        resultado = supabase.table("registros_consumo") \
            .select("id, quantidade, tabela_taco(*)") \
            .gte("created_at", hoje) \
            .eq("user_id", x_user_id) \
            .execute()
        return resultado.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/buscar-alimento")
def buscar_alimento(nome: str):
    # Esta rota é de busca pública na tabela taco, não precisa de x_user_id
    try:
        resultado = supabase.table("tabela_taco") \
            .select("*") \
            .ilike("nome_alimento", f"%{nome}%") \
            .execute()
        return resultado.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/registrar-alimento")
def registrar_alimento(dados: RegistroAlimento, x_user_id: str = Header(...)):
    try:
        # Inserção com o user_id para garantir que o dado pertença ao usuário
        resultado = supabase.table("registros_consumo").insert({
            "alimento_id": dados.alimento_id,
            "quantidade": dados.quantidade_gramas,
            "user_id": x_user_id
        }).execute()
        return {"status": "sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calcular-restante")
def calcular_restante(dados: DadosMetas, x_user_id: str = Header(...)):
    # Cálculos TMB e Metas
    s = 5 if dados.sexo == "Masculino" else -161
    tmb = (10 * dados.peso_kg) + (6.25 * dados.altura_cm) - (5 * dados.idade_anos) + s
    
    multiplicadores = {"Sedentário": 1.2, "Leve": 1.375, "Moderado": 1.55, "Muito Ativo": 1.725}
    tdee = tmb * multiplicadores.get(dados.nivel_atividade, 1.2)
    
    ajustes = {"Hipertrofia": 300, "Secagem": -500, "Manter": 0}
    meta_calorica = tdee + ajustes.get(dados.objetivo, 0)
    
    meta_prot = dados.peso_kg * 2
    meta_fat = dados.peso_kg * 1
    meta_carb = (meta_calorica - (meta_prot * 4) - (meta_fat * 9)) / 4

    # Calcular consumo atual (filtrado pelo x_user_id)
    hoje = date.today().isoformat()
    try:
        registros = supabase.table("registros_consumo") \
            .select("quantidade, tabela_taco(*)") \
            .gte("created_at", hoje) \
            .eq("user_id", x_user_id) \
            .execute()
        
        tot_kcal, tot_prot, tot_carb, tot_fat = 0, 0, 0, 0
        
        for item in registros.data:
            q = item['quantidade'] / 100
            alimento = item['tabela_taco']
            tot_kcal += (alimento.get('energia_kcal', 0) * q)
            tot_prot += (alimento.get('proteinas_g', 0) * q)
            tot_carb += (alimento.get('carboidratos_g', 0) * q)
            tot_fat += (alimento.get('lipideos_g', 0) * q)
            
    except Exception:
        tot_kcal, tot_prot, tot_carb, tot_fat = 0, 0, 0, 0

    return {
        "consumido_hoje": {
            "total_kcal": round(tot_kcal, 2),
            "total_prot": round(tot_prot, 2),
            "total_carb": round(tot_carb, 2),
            "total_fat": round(tot_fat, 2)
        },
        "restante_hoje": {
            "calorias": round(meta_calorica - tot_kcal, 2),
            "proteinas_g": round(meta_prot - tot_prot, 2),
            "carboidratos_g": round(meta_carb - tot_carb, 2),
            "gorduras_g": round(meta_fat - tot_fat, 2)
        }
    }

@app.delete("/limpar-consumo")
def limpar_consumo(x_user_id: str = Header(...)):
    hoje = date.today().isoformat()
    try:
        # Filtro de segurança para deletar apenas os dados do usuário atual
        supabase.table("registros_consumo") \
            .delete() \
            .gte("created_at", hoje) \
            .eq("user_id", x_user_id) \
            .execute()
        return {"status": "sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/deletar-alimento/{registro_id}")
def deletar_alimento(registro_id: str, x_user_id: str = Header(...)):
    try:
        # Filtro de segurança: deleta apenas se o ID do registro bater E o user_id também
        supabase.table("registros_consumo") \
            .delete() \
            .eq("id", registro_id) \
            .eq("user_id", x_user_id) \
            .execute()
        return {"status": "sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))