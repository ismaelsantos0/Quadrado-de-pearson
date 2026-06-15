from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Calculadora de Ração Educacional - Rostagno")

# Configuração de CORS para permitir acesso do Lovable
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# BASE DE DADOS (Dados reais das Tabelas Brasileiras 2026)
# ---------------------------------------------------------
TABELA_INGREDIENTES = {
    "milho_grao": {
        "nome": "Milho, Grão (Média)", 
        "pb": 7.81, 
        "em_aves": 3364, 
        "ca": 0.02, 
        "p_disp": 0.05, 
        "lisina": 0.25, 
        "metionina": 0.16
    },
    "amendoim_farelo": {
        "nome": "Amendoim, Farelo", 
        "pb": 48.20, 
        "em_aves": 2680, 
        "ca": 0.20, 
        "p_disp": 0.21, 
        "lisina": 1.58, 
        "metionina": 0.52
    },
    "soja_farelo_45": {
        "nome": "Farelo de Soja (45%)", 
        "pb": 45.60,
        "em_aves": 2270,
        "ca": 0.30,
        "p_disp": 0.22,
        "lisina": 2.75,
        "metionina": 0.62
    }
}

# ---------------------------------------------------------
# MODELOS
# ---------------------------------------------------------
class InclusaoFixa(BaseModel):
    id_ingrediente: str
    quantidade_kg: float

class RequisicaoCalculo(BaseModel):
    meta_pb: float
    espaco_reservado_pct: float
    inclusoes_fixas: List[InclusaoFixa]
    id_energetico_base: str
    id_proteico_base: str

# ---------------------------------------------------------
# ROTAS
# ---------------------------------------------------------
@app.get("/api/ingredientes")
def listar_ingredientes():
    lista = []
    for id_ing, dados in TABELA_INGREDIENTES.items():
        lista.append({
            "id": id_ing,
            "nome": dados["nome"],
            "pb": dados["pb"],
            "em_aves": dados.get("em_aves", 0)
        })
    return sorted(lista, key=lambda x: x["nome"])

@app.post("/api/calcular-racao/passo-basal")
def calcular_mistura_basal(req: RequisicaoCalculo):
    passos_educacionais = []
    
    # Passo 1: Espaço ocupado
    peso_ocupado = req.espaco_reservado_pct
    pb_fornecida = 0.0
    detalhes_fixos = []
    
    for fixo in req.inclusoes_fixas:
        ing = TABELA_INGREDIENTES.get(fixo.id_ingrediente)
        if not ing:
            raise HTTPException(status_code=404, detail=f"Ingrediente {fixo.id_ingrediente} não encontrado.")
        peso_ocupado += fixo.quantidade_kg
        pb_aporte = (fixo.quantidade_kg * ing["pb"]) / 100
        pb_fornecida += pb_aporte
        detalhes_fixos.append(f"{fixo.quantidade_kg}kg de {ing['nome']} fornece {pb_aporte:.2f}% de PB.")

    espaco_livre = 100.0 - peso_ocupado
    passos_educacionais.append({
        "titulo": "1. Análise de Espaço",
        "narrativa": f"Ocupamos {peso_ocupado:.1f}kg com fixos e reserva. Restam {espaco_livre:.1f}kg de espaço livre.",
        "detalhes_calculo": detalhes_fixos,
        "conclusao": f"PB já garantida: {pb_fornecida:.2f}%."
    })

    # Passo 2: Meta ajustada
    pb_faltante = req.meta_pb - pb_fornecida
    meta_ajustada = (pb_faltante * 100) / espaco_livre
    passos_educacionais.append({
        "titulo": "2. Ajuste de Meta",
        "narrativa": f"Precisamos de {pb_faltante:.2f}% de PB nos {espaco_livre:.1f}kg restantes.",
        "detalhes_calculo": [f"({pb_faltante:.2f} * 100) / {espaco_livre:.1f} = {meta_ajustada:.2f}%"],
        "conclusao": f"Meta ajustada para o Pearson: {meta_ajustada:.2f}%."
    })

    # Passo 3: Pearson
    ene = TABELA_INGREDIENTES[req.id_energetico_base]
    pro = TABELA_INGREDIENTES[req.id_proteico_base]
    
    partes_pro = abs(meta_ajustada - ene["pb"])
    partes_ene = abs(pro["pb"] - meta_ajustada)
    total = partes_pro + partes_ene
    
    kg_ene = (partes_ene / total) * espaco_livre
    kg_pro = (partes_pro / total) * espaco_livre
    
    passos_educacionais.append({
        "titulo": "3. Cálculo de Balanceamento",
        "narrativa": f"Cruzando {ene['nome']} e {pro['nome']} para a meta de {meta_ajustada:.2f}%.",
        "detalhes_calculo": [f"Milho: {partes_ene:.2f} partes", f"Soja: {partes_pro:.2f} partes"],
        "conclusao": f"Resultados: {kg_ene:.2f}kg de {ene['nome']} e {kg_pro:.2f}kg de {pro['nome']}."
    })

    return {
        "status": "sucesso",
        "passos_educacionais": passos_educacionais,
        "resultados_parciais": {
            "kg_energetico": round(kg_ene, 3),
            "kg_proteico": round(kg_pro, 3)
        }
    }
