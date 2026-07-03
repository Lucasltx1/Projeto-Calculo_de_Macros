from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

# Consulta os 5 primeiros registros da tabela
response = supabase.table("tabela_taco").select("*").limit(5).execute()

print("Dados recuperados com sucesso:")
for item in response.data:
    print(item)