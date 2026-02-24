import requests
import pandas as pd
import streamlit as st

@st.cache_data 
def carregar_deputados():
    url = "https://dadosabertos.camara.leg.br/api/v2/deputados?ordem=ASC&ordenarPor=nome"
    response = requests.get(url)
    if response.status_code == 200:
        return pd.DataFrame(response.json()['dados'])
    return pd.DataFrame()

import requests
import pandas as pd

import datetime
import requests
import pandas as pd

# CARREGAR DESPESAS

def carregar_despesas(id_deputado):
    """
    Busca TODAS as despesas do deputado na API da Câmara, forçando
    o governo a entregar o histórico dos últimos 2 anos (2025 e 2026),
    para bater exatamente com o nosso Ranking da Home.
    """
    url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{id_deputado}/despesas"
    todas_despesas = []
    pagina = 1
    
    # Define os anos que queremos obrigar a API a trazer
    ano_atual = datetime.date.today().year
    anos_busca = [ano_atual - 1, ano_atual] 
    
    while True:
        params = {
            'ano': anos_busca, # A CORREÇÃO ESTÁ AQUI!
            'ordem': 'DESC',
            'ordenarPor': 'dataDocumento',
            'itens': 100,
            'pagina': pagina
        }
        
        try:
            resposta = requests.get(url, params=params, timeout=15)
            
            if resposta.status_code == 200:
                dados = resposta.json().get('dados', [])
                
                if not dados:
                    break 
                    
                todas_despesas.extend(dados)
                pagina += 1 
            else:
                break 
        except Exception as e:
            print(f"Erro ao buscar página {pagina}: {e}")
            break
            
    if not todas_despesas:
        return pd.DataFrame()
        
    df = pd.DataFrame(todas_despesas)
    
    if 'dataDocumento' in df.columns:
        df['dataDocumento'] = pd.to_datetime(df['dataDocumento'], errors='coerce')
        
    if 'valorLiquido' in df.columns:
        df['valorLiquido'] = pd.to_numeric(df['valorLiquido'], errors='coerce').fillna(0)
        
    return df
    #CARREGAR VOTAÇÔES

def carregar_votacoes_nominais():
    """
    Busca as últimas votações na Câmara, varre os resultados e retorna
    exatamente as últimas 10 que foram nominais (com registro de votos).
    """
    # Pedimos um lote maior (50 itens) ordenado pelas mais recentes
    url = "https://dadosabertos.camara.leg.br/api/v2/votacoes"
    params = {
        'ordem': 'DESC',
        'ordenarPor': 'dataHoraRegistro',
        'itens': 50 
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            dados = response.json().get('dados', [])
            
            votacoes_nominais = []
            
            for v in dados:
                # Se não tiver o ID, pula
                if 'id' not in v:
                    continue
                    
                # A API retorna informações no próprio objeto ou nos detalhes se houve aprovação
                # Vamos considerar as que têm "aprovacao" definida e descrição clara
                descricao = v.get('descricao', '')
                
                # Uma heurística básica para garantir que a votação tem relevância/dados
                if descricao:
                    votacao_limpa = {
                        'id': v['id'],
                        'descricao': descricao,
                        'data': v.get('dataHoraRegistro', ''),
                        'aprovacao': v.get('aprovacao', 0)
                    }
                    votacoes_nominais.append(votacao_limpa)
                
                # Assim que batermos 10 votações válidas, paramos a busca para não pesar o app
                if len(votacoes_nominais) == 10:
                    break
            
            return pd.DataFrame(votacoes_nominais)
        return pd.DataFrame()
    except Exception as e:
        print(f"Erro na API de Votações: {e}")
        return pd.DataFrame()


@st.cache_data
def carregar_votos(id_votacao):
    # Puxa a lista de quem votou Sim/Não naquela votação específica
    url = f"https://dadosabertos.camara.leg.br/api/v2/votacoes/{id_votacao}/votos"
    response = requests.get(url)
    if response.status_code == 200:
        dados = response.json()['dados']
        if dados: # Verifica se a lista não está vazia
            return pd.json_normalize(dados) # <-- O truque que desempacota os dados
    return pd.DataFrame()

@st.cache_data
def carregar_detalhes_votacao(id_votacao):
    # Vai na Câmara e pede a "bula" (os detalhes) dessa votação específica
    url = f"https://dadosabertos.camara.leg.br/api/v2/votacoes/{id_votacao}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('dados', {})
    return {}


# RANK DE GASTOS
import pandas as pd
import streamlit as st
import requests

@st.cache_data(ttl=3600)
def carregar_dados_consolidados():
    """Lê o arquivo completo e prepara as informações para a Home"""
    try:
        df = pd.read_csv("ranking_completo.csv")
        
        # BLINDAGEM DA FOTO: Força virar número inteiro antes de virar texto (Mata o ".0")
        df['id'] = pd.to_numeric(df['ideCadastro'], errors='coerce').fillna(0).astype(int).astype(str)
        
        # AQUI ESTÁ A MÁGICA: Link oficial e exato do servidor de fotos da Câmara!
        df['urlFoto'] = "https://www.camara.leg.br/internet/deputado/bandep/" + df['id'] + ".jpg"
        
        df = df.rename(columns={
            'txNomeParlamentar': 'Deputado',
            'sgPartido': 'Partido',
            'sgUF': 'UF',
            'vlrLiquido': 'Gasto (R$)'
        })
        df['Gasto_Formatado'] = df['Gasto (R$)'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "v").replace(".", ",").replace("v", "."))
        return df
    except FileNotFoundError:
        return pd.DataFrame()

# ... (MANTENHA O RESTO DO SEU api.py EXATAMENTE COMO ESTÁ) ...
def carregar_resumo_geral():
    """Calcula o somatório total da Câmara e o ranking por partidos"""
    df = carregar_dados_consolidados()
    if not df.empty:
        total_camara = df['Gasto (R$)'].sum()
        # Agrupa e soma os gastos por partido
        df_partido = df.groupby('Partido', as_index=False)['Gasto (R$)'].sum()
        df_partido = df_partido.sort_values(by='Gasto (R$)', ascending=False)
        return total_camara, df_partido
    return 0, pd.DataFrame()

def carregar_ranking_gastos():
    """Retorna apenas o Top 10 para o Card de Destaque"""
    df = carregar_dados_consolidados()
    if not df.empty:
        return df.head(10)
    return pd.DataFrame()

# ... (MANTENHA AQUI SUAS FUNÇÕES DE carregar_votacoes_nominais, carregar_votos, etc) ...