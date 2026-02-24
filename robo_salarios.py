import pandas as pd
import requests

print("🤖 Iniciando o Robô da Folha de Pagamento (Modo Custo Base Legal)...")

# Valores EXATOS do salário dos deputados definidos por lei em cada ano
# (Considerando 12 meses + 13º salário)
salario_2023 = 41650.92 * 13 # R$ 541.461,96
salario_2024 = 44008.52 * 13 # R$ 572.110,76
salario_2025 = 46366.19 * 13 # R$ 602.760,47
salario_2026 = 46366.19 * 2  # Apenas Jan e Fev (ainda sem 13º) -> R$ 92.732,38

custo_total_mandato = salario_2023 + salario_2024 + salario_2025 + salario_2026

print("📋 Buscando a lista atualizada de deputados...")
url_dep = "https://dadosabertos.camara.leg.br/api/v2/deputados"

try:
    resp_dep = requests.get(url_dep).json()
    deputados = resp_dep['dados']
    
    lista_salarios = []
    
    print("🧮 Aplicando o cálculo do Custo Fixo de Mandato (2023 - Fev/2026)...")
    for dep in deputados:
        lista_salarios.append({
            'id_deputado': str(dep['id']),
            'nome': dep['nome'],
            'salario_mandato': custo_total_mandato
        })
        
    df_salarios = pd.DataFrame(lista_salarios)
    
    # Salva o arquivo localmente
    df_salarios.to_csv("salarios_mandato.csv", index=False)
    
    # Formatação apenas para exibir no terminal
    valor_tela = f"R$ {custo_total_mandato:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    print(f"✅ Sucesso Absoluto! Arquivo gerado.")
    print(f"💰 Custo Salarial Base por Deputado no Mandato: {valor_tela}")

except Exception as e:
    print(f"❌ Erro ao processar os salários: {e}")