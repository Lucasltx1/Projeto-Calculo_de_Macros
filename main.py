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

# Configuração de CORS - CORRIGIDO O DOMÍNIO
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://frontend.mandetalucas.workers.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        resultado = supabase.table("registros_consumo") \
            .select("id, quantidade, tabela_taco(*)") \
            .gte("created_at", hoje) \
            .eq("user_id", x_user_id) \
            .execute()
        return resultado.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Rota adicionada para casar com o app.js
@app.get("/alimentos")
def buscar_alimentos(q: str):
    try:
        resultado = supabase.table("tabela_taco") \
            .select("*") \
            .ilike("nome_alimento", f"%{q}%") \
            .execute()
        return resultado.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/buscar-alimento")
def buscar_alimento(nome: str):
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
    s = 5 if dados.sexo == "Masculino" else -161
    tmb = (10 * dados.peso_kg) + (6.25 * dados.altura_cm) - (5 * dados.idade_anos) + s
    
    multiplicadores = {"Sedentário": 1.2, "Leve": 1.375, "Moderado": 1.55, "Muito Ativo": 1.725}
    tdee = tmb * multiplicadores.get(dados.nivel_atividade, 1.2)
    
    ajustes = {"Hipertrofia": 300, "Secagem": -500, "Manter": 0}
    meta_calorica = tdee + ajustes.get(dados.objetivo, 0)
    
    meta_prot = dados.peso_kg * 2
    meta_fat = dados.peso_kg * 1
    meta_carb = (meta_calorica - (meta_prot * 4) - (meta_fat * 9)) / 4

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
        supabase.table("registros_consumo") \
            .delete() \
            .eq("id", registro_id) \
            .eq("user_id", x_user_id) \
            .execute()
        return {"status": "sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))