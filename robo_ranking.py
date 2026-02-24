import requests
import pandas as pd
import datetime
import time

print("🤖 Iniciando o Robô Mil Grau (Modo Minerador Bi-anual)...")
ano_atual = datetime.date.today().year
anos_busca = [ano_atual - 1, ano_atual] # Pega 2025 e 2026 juntos!

print("📋 Buscando a lista de todos os 513 deputados...")
url_dep = "https://dadosabertos.camara.leg.br/api/v2/deputados"
try:
    resp_dep = requests.get(url_dep).json()
    deputados = resp_dep['dados']
except Exception as e:
    print(f"❌ Erro ao conectar com a Câmara: {e}")
    exit()

ranking = []

print(f"⏳ Minerando gastos para os anos de {anos_busca[0]} e {anos_busca[1]}...")
print("⚠️ Atenção: Como estamos puxando mais de 12 meses de notas para 513 deputados, isso vai levar alguns minutos a mais.")
print("Pode ir pegar um café, o robô está trabalhando para você! ☕\n")

for i, dep in enumerate(deputados):
    id_dep = dep['id']
    nome = dep['nome']
    partido = dep['siglaPartido']
    uf = dep['siglaUf']
    
    # Mostra o progresso no terminal a cada 50 deputados para você ver que não travou
    if (i + 1) % 50 == 0:
        print(f"   -> Já processamos {i + 1} de {len(deputados)} parlamentares...")
        
    url_despesas = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_dep}/despesas"
    
    total_gasto = 0.0
    pagina = 1
    
    # Loop de paginação: busca todas as notas do deputado nesses dois anos
    while True:
        # A API da Câmara aceita uma lista de anos! Ela vai devolver tudo misturado.
        params = {'ano': anos_busca, 'itens': 100, 'pagina': pagina}
        try:
            resp_desp = requests.get(url_despesas, params=params, timeout=10)
            if resp_desp.status_code == 200:
                despesas = resp_desp.json().get('dados', [])
                if not despesas:
                    break # Acabaram as notas fiscais deste deputado
                
                # Soma os valores da página atual
                for d in despesas:
                    valor = d.get('valorLiquido', 0)
                    if valor:
                        total_gasto += float(valor)
                
                pagina += 1
            else:
                break
        except:
            break # Em caso de falha de conexão, pula para o próximo
            
    # Se o deputado gastou mais de zero reais, entra no ranking
    if total_gasto > 0:
        ranking.append({
            'ideCadastro': id_dep,
            'txNomeParlamentar': nome,
            'sgPartido': partido,
            'sgUF': uf,
            'vlrLiquido': total_gasto
        })
        
    # Pausa de 0.1s para não sobrecarregar o firewall do governo
    time.sleep(0.1) 

print("\n🧮 Consolidando a matemática...")
df_ranking = pd.DataFrame(ranking)

# Ordena os gastadores e salva a base COMPLETA
if not df_ranking.empty:
    df_ranking = df_ranking.sort_values(by='vlrLiquido', ascending=False)
    
    df_ranking.to_csv("ranking_completo.csv", index=False)
    print("✅ Sucesso Absoluto! Arquivo 'ranking_completo.csv' gerado (Dados de 2025 e 2026).")
    print("🚀 Pode recarregar sua página inicial agora!")
else:
    print("⚠️ Nenhum gasto foi encontrado.")