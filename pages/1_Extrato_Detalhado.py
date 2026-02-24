import streamlit as st
import pandas as pd
import datetime
from PIL import Image
from api import carregar_deputados, carregar_despesas
from tratamento import gerar_grafico_despesas

st.set_page_config(page_title="Extrato Detalhado | Mil Grau", page_icon="🔎", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F0F2F6; }
    
    .photo-container {
        width: 160px;
        height: 215px;
        background-color: #eee;
        border-radius: 12px;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .photo-container img { object-fit: cover; width: 100%; height: 100%; }

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
        border: 1px solid #E6E9EF !important;
        background-color: white !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    
    .title-header { color: #003399; font-weight: 800; font-size: 2.5rem; margin-bottom: 0;}
    .subtitle-header { color: #666; font-size: 1.1rem; margin-top: -10px; margin-bottom: 30px;}
    
    .expense-card {
        background-color: #FFF5F5;
        border-left: 6px solid #d32f2f;
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR E FILTROS ---
with st.sidebar:
    c1, c_logo, c2 = st.columns([1, 1.5, 1])
    with c_logo:
        try:
            img = Image.open("logo2.png")
            st.image(img, use_container_width=True)
        except Exception as e:
            st.warning(f"⚠️ logo2 não encontrado: {e}")
            
    st.markdown("<h4 style='text-align: center; color: #003399;'>Filtros de Auditoria</h4>", unsafe_allow_html=True)
    st.markdown("---")
    
    df_deputados = carregar_deputados()
    if df_deputados.empty:
        st.error("Erro ao conectar com a API da Câmara.")
        st.stop()

    estado = st.selectbox("📌 UF (Estado):", ["Todos"] + sorted(list(df_deputados['siglaUf'].unique())))
    if estado != "Todos":
        df_deputados = df_deputados[df_deputados['siglaUf'] == estado]

    lista_nomes = df_deputados['nome'].tolist()
    deputado_escolhido = st.selectbox("👤 Parlamentar:", lista_nomes)
    
    st.markdown("---")
    st.markdown("<p style='text-align:center; font-weight:bold; color:#666; margin-bottom: 0;'>📅 Recorte das Notas Fiscais</p>", unsafe_allow_html=True)
    
    opcoes_periodo = [
        "Visão Geral (Últimas Notas)",
        "Acumulado (2025 e 2026)",
        "Ano Vigente (2026)", 
        "Ano Anterior (2025)",
        "Últimos 30 Dias"
    ]
    periodo_escolhido = st.selectbox("Selecione o período do cartão:", opcoes_periodo)

# --- TELA PRINCIPAL ---
st.markdown('<p class="title-header">🔎 Extrato Detalhado</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-header">Auditoria de Custo: Salário Oficial + Notas Fiscais Declaradas.</p>', unsafe_allow_html=True)

dados_deputado = df_deputados[df_deputados['nome'] == deputado_escolhido].iloc[0]
id_parlamentar = str(dados_deputado['id'])

with st.container(border=True):
    col_foto, col_info = st.columns([1, 4])
    with col_foto:
        url_foto = dados_deputado.get('urlFoto', '')
        st.markdown(f'''
            <div class="photo-container"><img src="{url_foto}" alt="Foto de {dados_deputado['nome']}"></div>
        ''', unsafe_allow_html=True)

    with col_info:
        st.markdown(f"<h2 style='margin-bottom:0;'>{dados_deputado['nome']}</h2>", unsafe_allow_html=True)
        st.markdown(f"**Partido:** {dados_deputado['siglaPartido']} | **Estado:** {dados_deputado['siglaUf']}")
        st.caption(f"ID Parlamentar: {id_parlamentar}")

st.write("")
st.markdown(f"### 📊 Raio-X Financeiro", unsafe_allow_html=True)

with st.spinner("Cruzando salários e faturas no servidor..."):
    df_despesas = carregar_despesas(id_parlamentar)
    
    if not df_despesas.empty:
        hoje = pd.Timestamp.now()
        
        # Filtros matemáticos para as notas fiscais
        if periodo_escolhido == "Ano Vigente (2026)":
            df_despesas = df_despesas[df_despesas['dataDocumento'].dt.year == hoje.year]
        elif periodo_escolhido == "Ano Anterior (2025)":
            df_despesas = df_despesas[df_despesas['dataDocumento'].dt.year == (hoje.year - 1)]
        elif periodo_escolhido == "Acumulado (2025 e 2026)":
            df_despesas = df_despesas[df_despesas['dataDocumento'].dt.year >= (hoje.year - 1)]
        elif periodo_escolhido == "Últimos 30 Dias":
            df_despesas = df_despesas[df_despesas['dataDocumento'] >= (hoje - pd.Timedelta(days=30))]

    fig, top_3 = gerar_grafico_despesas(df_despesas)
    
    # ---------------------------------------------------
    # CÁLCULOS DO SUPER PAINEL (SALÁRIO + DESPESAS)
    # ---------------------------------------------------
    total_despesas = df_despesas['valorLiquido'].sum() if not df_despesas.empty else 0
    qtd_notas = len(df_despesas) if not df_despesas.empty else 0
    
    # Busca o salário exato deste deputado no CSV do robô
    try:
        df_sal = pd.read_csv("salarios_mandato.csv")
        df_sal['id_deputado'] = df_sal['id_deputado'].astype(str)
        linha_salario = df_sal[df_sal['id_deputado'] == id_parlamentar]
        
        if not linha_salario.empty:
            salario_mandato = float(linha_salario.iloc[0]['salario_mandato'])
        else:
            salario_mandato = 0
    except:
        salario_mandato = 0
        
    custo_absoluto = total_despesas + salario_mandato
    
    # Formatação da Moeda
    despesas_formatadas = f"R$ {total_despesas:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    salario_formatado = f"R$ {salario_mandato:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    absoluto_formatado = f"R$ {custo_absoluto:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    
    # Renderiza o Super Painel Triplo (Sem espaços no início para não quebrar o Markdown)
    st.markdown(f"""
<div style="background-color: white; border-radius: 12px; border: 1px solid #E6E9EF; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 30px; border-top: 8px solid #003399; display: flex; justify-content: space-around; padding: 20px;">
    <div style="text-align: center; border-right: 1px solid #eee; padding-right: 20px; flex: 1;">
        <p style="margin: 0; font-size: 0.9rem; color: #666; font-weight: bold; text-transform: uppercase;">Salários Oficiais<br>(Últimos 4 Anos)</p>
        <h2 style="margin: 0; color: #003399; font-weight: 800;">{salario_formatado}</h2>
    </div>
    <div style="text-align: center; border-right: 1px solid #eee; padding-right: 20px; padding-left: 20px; flex: 1;">
        <p style="margin: 0; font-size: 0.9rem; color: #666; font-weight: bold; text-transform: uppercase;">Notas Fiscais Declaradas<br>({periodo_escolhido})</p>
        <h2 style="margin: 0; color: #d32f2f; font-weight: 800;">{despesas_formatadas}</h2>
        <p style="margin: 0; font-size: 0.75rem; color: #999;">{qtd_notas} faturas mineradas</p>
    </div>
    <div style="text-align: center; padding-left: 20px; flex: 1;">
        <p style="margin: 0; font-size: 1.1rem; color: #111; font-weight: 900; text-transform: uppercase;">🔥 Custo Total Estimado</p>
        <h1 style="margin: 0; font-size: 2.5rem; color: #111; font-weight: 900; letter-spacing: -1px; line-height: 1.1;">{absoluto_formatado}</h1>
    </div>
</div>
    """, unsafe_allow_html=True)
    
    # ---------------------------------------------------
    # GRÁFICOS E NOTAS (Só exibe se houver notas fiscais)
    # ---------------------------------------------------
    if fig is not None and not df_despesas.empty:
        col_grafico, col_top = st.columns([1.5, 1], gap="large")
        
        with col_grafico:
            with st.container(border=True):
                st.markdown("#### Distribuição do Cartão")
                st.plotly_chart(fig, use_container_width=True)
        
        with col_top:
            with st.container(border=True):
                st.markdown("#### 🚨 Maiores Notas Fiscais")
                st.caption(f"Faturas individuais mais altas no recorte selecionado.")
                
                for i, row in top_3.iterrows():
                    valor_fat = f"R$ {row['valorLiquido']:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
                    fornecedor = str(row.get('nomeFornecedor', 'Não informado')).title()[:30]
                    
                    st.markdown(f'''
                        <div class="expense-card">
                            <span style="font-size: 0.85rem; color: #555; text-transform: uppercase;">{row['tipoDespesa']}</span><br>
                            <span style="font-size: 1.3rem; font-weight: bold; color: #d32f2f;">{valor_fat}</span><br>
                            <span style="font-size: 0.8rem; color: #888;">🏢 {fornecedor}</span>
                        </div>
                    ''', unsafe_allow_html=True)
    else:
        st.info(f"O Custo Total acima reflete apenas os salários, pois nenhuma nota fiscal foi registrada no recorte de tempo: **{periodo_escolhido}**.")
