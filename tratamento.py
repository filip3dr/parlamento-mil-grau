import pandas as pd
import plotly.express as px

def gerar_grafico_despesas(df):
    """
    Recebe as notas fiscais, soma por categoria e desenha o gráfico de rosca.
    Também identifica as 3 faturas mais caras.
    """
    # Se o DataFrame estiver vazio, devolve None para o app.py mostrar o aviso
    if df is None or df.empty or 'tipoDespesa' not in df.columns:
        return None, None
    
    # 1. PREPARAR DADOS PARA O GRÁFICO (Somar tudo por Categoria)
    # Ex: Combustível: 15.000€, Passagens: 8.000€
    df_agrupado = df.groupby('tipoDespesa')['valorLiquido'].sum().reset_index()
    df_agrupado = df_agrupado[df_agrupado['valorLiquido'] > 0] # Remove categorias zeradas
    
    if df_agrupado.empty:
        return None, None

    # 2. GERAR O GRÁFICO DE ROSCA (DONUT)
    # Usamos uma paleta verde/azul para manter a identidade visual
    fig = px.pie(
        df_agrupado, 
        values='valorLiquido', 
        names='tipoDespesa', 
        hole=0.45, # Transforma a tarte num donut
        color_discrete_sequence=px.colors.sequential.Teal
    )
    
    # Ocultar a legenda gigante e focar na informação diretamente nas fatias
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        showlegend=False, 
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    # 3. IDENTIFICAR O TOP 3 DE GASTOS (As 3 maiores notas fiscais individuais)
    top_3 = df.nlargest(3, 'valorLiquido')[['tipoDespesa', 'valorLiquido', 'dataDocumento', 'nomeFornecedor']]
    
    return fig, top_3