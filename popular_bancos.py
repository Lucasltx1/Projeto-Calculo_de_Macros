import pandas as pd
import numpy as np
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

# Carrega o CSV
df = pd.read_csv('taco_AG.csv')

# Mapeamento exato das colunas do seu arquivo
mapeamento = {
    'Descrição dos alimentos': 'nome_alimento',
    'Energia..kcal.': 'energia_kcal',
    'Proteína..g.': 'proteinas_g',
    'Carboidrato..g.': 'carboidratos_g',
    'Lipídeos..g.': 'lipideos_g'
}

# 1. Filtra o DataFrame apenas com as colunas que nos interessam
df_final = df[list(mapeamento.keys())].copy()

# 2. Renomeia para o formato do banco de dados
df_final = df_final.rename(columns=mapeamento)

# 3. Limpeza de dados:
# Remove NaN/Infinitos e garante que sejam números
cols_num = ['energia_kcal', 'proteinas_g', 'carboidratos_g', 'lipideos_g']
df_final[cols_num] = df_final[cols_num].replace([np.nan, np.inf, -np.inf], 0.0)
df_final[cols_num] = df_final[cols_num].apply(pd.to_numeric, errors='coerce').fillna(0.0)

# 4. Envio para o Supabase
dados = df_final.to_dict(orient='records')

try:
    # Insere em lotes pequenos para evitar erro de payload muito grande
    # Se der erro de tamanho, podemos dividir em partes menores
    supabase.table("tabela_taco").insert(dados).execute()
    print(f"Sucesso! {len(dados)} alimentos inseridos.")
except Exception as e:
    print(f"Erro ao inserir dados: {e}")