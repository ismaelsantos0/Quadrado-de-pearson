from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

app = FastAPI(title="Calculadora de Ração Educacional - Rostagno")

# ---------------------------------------------------------
# 1. BASE DE DADOS (Extraída dos PDFs fornecidos)
# ---------------------------------------------------------
TABELA_INGREDIENTES = {
    "milho_grao": {
        "nome": "Milho, Grão (Média)", 
        [span_3](start_span)"pb": 7.81,            # Proteína Bruta (%)[span_3](end_span)
        [span_4](start_span)"em_aves": 3364,       # Energia Metabolizável Aves (kcal/kg)[span_4](end_span)
        [span_5](start_span)"ca": 0.02,            # Cálcio Total (%)[span_5](end_span)
        [span_6](start_span)"p_disp": 0.05,        # Fósforo Disponível (%)[span_6](end_span)
        [span_7](start_span)"lisina": 0.25,        # Lisina Total (%)[span_7](end_span)
        [span_8](start_span)"metionina": 0.16      # Metionina Total (%)[span_8](end_span)
    },
    "amendoim_farelo": {
        "nome": "Amendoim, Farelo", 
        [span_9](start_span)"pb": 48.20,           # Proteína Bruta (%)[span_9](end_span)
        "em_aves": 2680,       # (Valor hipotético preenchido para lógica, usar tabela real)
        "ca": 0.20,            # (Valor hipotético preenchido para lógica, usar tabela real)
        "p_disp": 0.21,        # (Valor hipotético preenchido para lógica, usar tabela real)
        [span_10](start_span)"lisina": 1.58,        # Lisina Total (%)[span_10](end_span)
        [span_11](start_span)"metionina": 0.52      # Metionina Total (%)[span_11](end_span)
    },
    # A Soja precisaria de ser extraída da sua tabela completa para entrar aqui
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
# 2. MODELOS DE ENTRADA (Payload do Lovable)
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
# 3. LÓGICA DE NEGÓCIO E ENDPOINT
# ---------------------------------------------------------
@app.post("/api/calcular-racao/passo-basal")
def calcular_mistura_basal(req: RequisicaoCalculo):
    passos_educacionais = []
    
    # PASSO 1: Calcular o que já está ocupado (Espaço e Proteína)
    peso_ocupado = req.espaco_reservado_pct
    pb_fornecida = 0.0
    
    detalhes_fixos = []
    for fixo in req.inclusoes_fixas:
        ingrediente = TABELA_INGREDIENTES.get(fixo.id_ingrediente)
        if not ingrediente:
            raise HTTPException(status_code=404, detail=f"Ingrediente {fixo.id_ingrediente} não encontrado.")
        
        peso_ocupado += fixo.quantidade_kg
        pb_aporte = (fixo.quantidade_kg * ingrediente["pb"]) / 100
        pb_fornecida += pb_aporte
        
        detalhes_fixos.append(f"{fixo.quantidade_kg}kg de {ingrediente['nome']} fornece {pb_aporte:.2f}% de PB.")

    espaco_livre = 100.0 - peso_ocupado
    
    passos_educacionais.append({
        "titulo": "1. Análise do Espaço e Proteína Prévia",
        "narrativa": f"Ao reservar {req.espaco_reservado_pct}% de espaço e adicionar os ingredientes fixos, ocupámos {peso_ocupado:.1f}kg do total.",
        "detalhes_calculo": detalhes_fixos,
        "conclusao": f"Restam {espaco_livre:.1f}kg de espaço livre na misturadora e já temos garantidos {pb_fornecida:.2f}% de Proteína Bruta."
    })

    # PASSO 2: Ajuste da Meta para as Equações Simultâneas
    pb_faltante = req.meta_pb - pb_fornecida
    meta_ajustada = (pb_faltante * 100) / espaco_livre
    
    passos_educacionais.append({
        "titulo": "2. Ajuste da Meta de Proteína",
        "narrativa": f"Como já temos {pb_fornecida:.2f}% de PB providenciados, faltam {pb_faltante:.2f}% para atingir a meta geral de {req.meta_pb}%.",
        "detalhes_calculo": [
            f"Fórmula: ({pb_faltante:.2f} * 100) / {espaco_livre:.1f}kg restantes = {meta_ajustada:.2f}%"
        ],
        "conclusao": f"A nossa nova meta temporária para a mistura basal é de {meta_ajustada:.2f}% de PB."
    })

    # PASSO 3: Balanceamento Base (Método de Pearson/Equações)
    energetico = TABELA_INGREDIENTES[req.id_energetico_base]
    proteico = TABELA_INGREDIENTES[req.id_proteico_base]
    
    # Validação Matemática de Exceção
    if meta_ajustada <= energetico["pb"] or meta_ajustada >= proteico["pb"]:
         raise HTTPException(status_code=400, detail="Cálculo impossível! A meta de proteína ajustada deve estar entre a proteína do ingrediente energético e a do proteico.")

    # Diagonais de Pearson
    partes_proteico = abs(meta_ajustada - energetico["pb"])
    partes_energetico = abs(proteico["pb"] - meta_ajustada)
    total_partes = partes_proteico + partes_energetico

    kg_energetico = (partes_energetico / total_partes) * espaco_livre
    kg_proteico = (partes_proteico / total_partes) * espaco_livre

    passos_educacionais.append({
        "titulo": f"3. Balanceamento: {energetico['nome']} e {proteico['nome']}",
        "narrativa": "Utilizando o método do Quadrado de Pearson para cruzar as exigências com a concentração real de cada ingrediente (de acordo com as Tabelas Brasileiras).",
        "detalhes_calculo": [
            f"Partes de {energetico['nome']}: {proteico['pb']} - {meta_ajustada:.2f} = {partes_energetico:.2f}",
            f"Partes de {proteico['nome']}: {meta_ajustada:.2f} - {energetico['pb']} = {partes_proteico:.2f}",
            f"Total de Partes: {total_partes:.2f}"
        ],
        "conclusao": f"Precisaremos de {kg_energetico:.2f}kg de {energetico['nome']} e {kg_proteico:.2f}kg de {proteico['nome']}."
    })

    # PASSO 4: Preparação para as Cascatas de Minerais e Aminoácidos
    # A API calcula logo os níveis de Cálcio e Fósforo que estes ingredientes base já forneceram.
    ca_fornecido_base = ((kg_energetico * energetico["ca"]) / 100) + ((kg_proteico * proteico["ca"]) / 100)
    p_fornecido_base = ((kg_energetico * energetico["p_disp"]) / 100) + ((kg_proteico * proteico["p_disp"]) / 100)

    passos_educacionais.append({
        "titulo": "4. Resumo de Minerais Fornecidos pela Base",
        "narrativa": "Antes de adicionar o calcário ou o fosfato, o sistema contabiliza o que o milho e a fonte proteica já trouxeram naturalmente para a mistura.",
        "detalhes_calculo": [
            f"Cálcio Base: {ca_fornecido_base:.3f} kg",
            f"Fósforo Disponível Base: {p_fornecido_base:.3f} kg"
        ],
        "conclusao": "Estes valores serão abatidos das exigências nutricionais finais do animal no próximo passo de cálculo (Cascata Mineral)."
    })

    return {
        "status": "sucesso",
        "resultados_parciais": {
            "espaco_livre": round(espaco_livre, 3),
            "kg_energetico": round(kg_energetico, 3),
            "kg_proteico": round(kg_proteico, 3),
            "ca_base": round(ca_fornecido_base, 4),
            "p_disp_base": round(p_fornecido_base, 4)
        },
        "passos_educacionais": passos_educacionais
    }
