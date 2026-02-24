import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
from api import carregar_votacoes_nominais, carregar_votos, carregar_detalhes_votacao, carregar_ranking_gastos, carregar_resumo_geral

# ==========================================
# CONFIGURAÇÃO E IDENTIDADE VISUAL
# ==========================================
st.set_page_config(page_title="Parlamento Mil Grau", page_icon="🏛️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F0F2F6; }
    
    .photo-container {
        width: 150px;
        height: 200px;
        background-color: #eee;
        border-radius: 10px;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .photo-container img { object-fit: cover; width: 100%; height: 100%; }

    [data-testid="stVerticalBlockBorderWrapper"]:has(.highlight-marker) {
        border-left: 10px solid #d32f2f !important;
        background-color: white !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
        border-radius: 15px !important;
    }
    
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 12px !important;
        border: 1px solid #E6E9EF !important;
        background-color: white !important;
    }

    .main-header { text-align: center; margin-top: -30px; margin-bottom: 20px; }
    
    .date-tag { font-size: 1rem; color: #666; font-weight: normal; vertical-align: middle; margin-left: 8px; }
    
    /* Placar Gigante */
    .total-card {
        background-color: white; 
        border-radius: 12px; 
        border: 1px solid #E6E9EF; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05); 
        padding: 30px; 
        text-align: center; 
        margin-bottom: 30px; 
        border-top: 8px solid #003399;
    }
    .total-title { margin: 0; font-size: 1.1rem; color: #666; font-weight: bold; text-transform: uppercase; }
    .total-value { margin: 0; font-size: 4rem; color: #d32f2f; font-weight: 900; letter-spacing: -2px; line-height: 1.2; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# CÁLCULO AUTOMÁTICO DO PERÍODO
# ==========================================
meses_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
hoje = datetime.date.today()
# ==========================================
# CÁLCULO AUTOMÁTICO DO PERÍODO
# ==========================================
hoje = datetime.date.today()
meses_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}

# Atualizamos a tag para refletir o Acumulado de 2025 + 2026
ano_passado = hoje.year - 1
periodo_apuracao = f"{ano_passado} a {meses_pt[hoje.month]}/{hoje.year}"
# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    c1, c_logo, c2 = st.columns([1, 1.5, 1])
    with c_logo:
        try: st.image("logo2.png", use_container_width=True)
        except: st.warning("⚠️ logo2.png não encontrado")
    st.markdown("<h4 style='text-align: center; color: #003399;'>Monitoramento</h4>", unsafe_allow_html=True)

# ==========================================
# HEADER
# ==========================================
st.markdown('<div class="main-header">', unsafe_allow_html=True)
c1, c_mid, c2 = st.columns([2, 1, 2])
with c_mid:
    try: st.image("logo.png", use_container_width=True)
    except: st.error("⚠️ logo.png não encontrado.")
st.markdown("<p style='text-align: center; color: #666;'>O extrato real do dinheiro público em Brasília.</p>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 📊 1. PLACAR GERAL E PARTIDOS
# ==========================================
total_gasto, df_partidos = carregar_resumo_geral()

if total_gasto > 0:
    total_formatado = f"R$ {total_gasto:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    
    # Placar Gigante da Câmara com o Rodapé Explicativo
    st.markdown(f'''
        <div class="total-card" style="padding-bottom: 20px;">
            <p class="total-title">Total Gasto pela Câmara dos Deputados ({periodo_apuracao})</p>
            <h1 class="total-value" style="margin-bottom: 5px;">{total_formatado}</h1>
            <p style="color: #888; font-size: 0.85rem; margin: 0;"><em>*Valor referente exclusivamente à Cota Parlamentar (notas fiscais). Não inclui a folha de pagamento de salários.</em></p>
        </div>
    ''', unsafe_allow_html=True)
    
    # Gráfico de Gastos por Partido
    with st.container(border=True):
        st.markdown(f"#### 🏛️ Ranking de Gastos por Partido <span class='date-tag'>({periodo_apuracao})</span>", unsafe_allow_html=True)
        # Exibe o Top 15 partidos para não poluir
        fig_partido = px.bar(df_partidos.head(15), x='Partido', y='Gasto (R$)', text_auto='.2s', 
                             color='Gasto (R$)', color_continuous_scale='Reds')
        fig_partido.update_layout(xaxis_title="", yaxis_title="", height=300, 
                                  margin=dict(l=0, r=0, t=10, b=0), showlegend=False,
                                  paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_partido, use_container_width=True)

# ==========================================
# 🏆 2. DESTAQUE: CAMPEÃO DE GASTOS
# ==========================================
st.write("")
ranking = carregar_ranking_gastos()

if not ranking.empty:
    top_1 = ranking.iloc[0]
    
    with st.container(border=True):
        st.markdown('<div class="highlight-marker"></div>', unsafe_allow_html=True)
        col_foto, col_info = st.columns([1, 3])
        
        with col_foto:
            url_oficial = top_1.get('urlFoto', '')
            st.markdown(f'''
                <div class="photo-container">
                    <img src="{url_oficial}" alt="Foto de {top_1['Deputado']}">
                </div>
            ''', unsafe_allow_html=True)
            
        with col_info:
            st.markdown(f"<h3 style='margin:0; color:#d32f2f;'>⚠️ MAIOR GASTO INDIVIDUAL REGISTRADO</h3>", unsafe_allow_html=True)
            st.markdown(f"## {top_1['Deputado']}")
            st.markdown(f"**{top_1['Partido']} - {top_1['UF']}**")
            
            # O valor gigante
            st.markdown(f"Total: <span style='font-size:2.2rem; color:#d32f2f; font-weight:bold;'>{top_1['Gasto_Formatado']}</span>", unsafe_allow_html=True)
            
            # A explicação exata para calar os críticos (usando a nossa variável automática)
            st.markdown(f"<p style='color: #666; font-size: 0.9rem; margin-top: -10px;'><em>*Refere-se exclusivamente à soma de todas as notas fiscais declaradas de {periodo_apuracao}. Não inclui salários oficiais.</em></p>", unsafe_allow_html=True)

    # ==========================================
    # 3. GRID INFERIOR (OUTROS GASTADORES E VOTAÇÕES)
    # ==========================================
    st.write("")
    col_esq, col_dir = st.columns(2, gap="large")

    with col_esq:
        with st.container(border=True):
            st.markdown(f"### 💸 Próximos no Ranking", unsafe_allow_html=True)
            
            if len(ranking) > 1:
                outros = ranking.iloc[1:6].copy()
                outros['Nome_Exibicao'] = outros['Deputado'] + ' (' + outros['Partido'] + '-' + outros['UF'] + ')'
                outros = outros.sort_values(by='Gasto (R$)', ascending=True)
                
                fig = px.bar(outros, x="Gasto (R$)", y="Nome_Exibicao", orientation='h',
                             color_discrete_sequence=['#00875F'], text_auto='.2s')
                
                fig.update_layout(yaxis={'title': ''}, xaxis={'visible': False}, height=280, 
                                  margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            
            if st.button("🔎 Abrir Extrato Detalhado do Parlamentar"):
                st.switch_page("pages/1_Extrato_Detalhado.py")

    with col_dir:
        with st.container(border=True):
            st.markdown("### 🎯 Placar de Votações")
            df_v = carregar_votacoes_nominais()
            
            if not df_v.empty:
                df_v['nome_exibir'] = df_v['descricao'].apply(lambda x: x.split(" Sim:")[0][:70] + "..." if " Sim:" in str(x) else str(x)[:70])
                selecao = st.selectbox("Últimas 10 votações nominais:", df_v['nome_exibir'].tolist())
                v_row = df_v[df_v['nome_exibir'] == selecao].iloc[0]
                
                with st.expander("📄 Ver Resumo da Votação", expanded=True):
                    detalhes = carregar_detalhes_votacao(v_row['id'])
                    if isinstance(detalhes, dict) and detalhes.get('ementa'):
                        st.write(detalhes['ementa'])
                    else:
                        st.write(v_row['descricao'].split(" Sim:")[0])

                st.info(f"Resultado Oficial: {'✅ APROVADA' if v_row['aprovacao'] == 1 else '❌ REJEITADA'}")
                
                votos = carregar_votos(v_row['id'])
                if not votos.empty:
                    cont = votos['tipoVoto'].value_counts().reset_index()
                    cols = st.columns(len(cont))
                    for i, row in cont.iterrows():
                        cols[i].metric(label=row['tipoVoto'].upper(), value=row['count'])
                        
                    fig_v = px.bar(cont, x='tipoVoto', y='count', color='tipoVoto',
                                   color_discrete_map={'Sim': '#00C853', 'Não': '#D50000', 'Abstenção': '#FFAB00'})
                    fig_v.update_layout(height=180, showlegend=False, margin=dict(l=0, r=0, t=10, b=0),
                                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_v, use_container_width=True)
                else:
                    st.warning("⚠️ **Votação Simbólica:** Não houve registro no painel eletrônico.")