import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import os

# Configuração da Página do Streamlit (Deve ser a primeira linha de código Streamlit)
st.set_page_config(
    page_title="BRICSVAULT PORTAL",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização do cliente Gate.io via CCXT
@st.cache_resource
def inicializar_exchange():
    return ccxt.gateio({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })

gateio_client = inicializar_exchange()

# --- FUNÇÕES DE CÁLCULO MATEMÁTICO NATIVO (Substitutos estáveis para o pandas-ta) ---
def calcular_ema(df, col, periodo):
    return df[col].ewm(span=periodo, adjust=False).mean()

def calcular_rsi(df, col, periodo=14):
    delta = df[col].diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    
    # Média móvel exponencial para o RSI
    ma_ganho = ganho.ewm(com=periodo-1, adjust=False).mean()
    ma_perda = perda.ewm(com=periodo-1, adjust=False).mean()
    
    rs = ma_ganho / ma_perda.replace(0, 0.00001)
    return 100 - (100 / (1 + rs))

def calcular_macd(df, col):
    ema_rapida = df[col].ewm(span=12, adjust=False).mean()
    ema_lenta = df[col].ewm(span=26, adjust=False).mean()
    macd = ema_rapida - ema_lenta
    sinal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - sinal
    return macd, sinal, hist

# --- CARREGAMENTO SEGURO DE DADOS DA EXCHANGE ---
@st.cache_data(ttl=15)
def carregar_dados_bricsvault(simbolo_id, timeframe, intervalo_escolhido):
    try:
        if timeframe == "1d" and intervalo_escolhido == "1 Mês (Longo Prazo)":
            velas = gateio_client.fetch_ohlcv(simbolo_id, timeframe='1d', limit=1000)
        else:
            limite_velas = 500 if timeframe in ['1m', '5m', '15m'] else 300
            velas = gateio_client.fetch_ohlcv(simbolo_id, timeframe=timeframe, limit=limite_velas)
            
        if not velas: 
            return None
            
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        if timeframe == "1d" and intervalo_escolhido == "1 Mês (Longo Prazo)":
            df.set_index('time', inplace=True)
            df = df.resample('ME').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})
            df.reset_index(inplace=True)
        
        # Cálculos de indicadores nativos e blindados (Evita o erro de Python 3.14)
        df['EMA_9']   = calcular_ema(df, 'close', 9)
        df['EMA_21']  = calcular_ema(df, 'close', 21)
        df['EMA_55']  = calcular_ema(df, 'close', 55)
        df['EMA_200'] = calcular_ema(df, 'close', 200) if len(df) >= 200 else df['EMA_55']
        df['RSI_14']  = calcular_rsi(df, 'close', 14)
        
        macd, sinal, hist = calcular_macd(df, 'close')
        df['MACD'] = macd
        df['MACD_SIGNAL'] = sinal
        df['MACD_HIST'] = hist

        return df.dropna(subset=['close', 'EMA_9'])
    except Exception as e:
        st.error(f"Erro ao buscar dados do mercado: {e}")
        return None

# --- INTERFACE DO USUÁRIO (DASHBOARD) ---
st.title("🏦 BRICSVAULT PORTAL - Sistema de Análise Financeira")
st.subheader("Painel de Monitoramento de Criptoativos com Indicadores Avançados")

# Barra Lateral (Sidebar) de Controle
st.sidebar.header("⚙️ Configurações do Portal")

# Seleção de Criptomoedas
pares_brics = {
    "Bitcoin (BTC/USDT)": "BTC/USDT",
    "Ethereum (ETH/USDT)": "ETH/USDT",
    "Solana (SOL/USDT)": "SOL/USDT",
    "Ripple (XRP/USDT)": "XRP/USDT",
    "Binance Coin (BNB/USDT)": "BNB/USDT"
}
par_selecionado = st.sidebar.selectbox("Escolha o Ativo para Análise:", list(pares_brics.keys()))
simbolo_id = pares_brics[par_selecionado]

# Seleção de Períodos de Tempo (Timeframes)
intervalos = {
    "1 Minuto (Scalping)": "1m",
    "5 Minutos (Day Trade)": "5m",
    "15 Minutos (Day Trade)": "15m",
    "1 Hora (Swing Trade)": "1h",
    "4 Horas (Swing Trade)": "4h",
    "1 Dia (Posição)": "1d",
    "1 Mês (Longo Prazo)": "1d"
}
intervalo_escolhido = st.sidebar.selectbox("Selecione o Tempo Gráfico:", list(intervalos.keys()))
timeframe = intervalos[intervalo_escolhido]

# Carregar os dados processados
with st.spinner("Conectando à API Global do Mercado e calculando indicadores..."):
    df_dados = carregar_dados_bricsvault(simbolo_id, timeframe, intervalo_escolhido)

if df_dados is not None and not df_dados.empty:
    # Capturar últimos valores para os Cards Informativos
    ultimo_registro = df_dados.iloc[-1]
    preco_atual = ultimo_registro['close']
    rsi_atual = ultimo_registro['RSI_14']
    macd_atual = ultimo_registro['MACD']
    
    # Calcular variação percentual simples do período exibido
    preco_inicial = df_dados.iloc[0]['close']
    variacao_percentual = ((preco_atual - preco_inicial) / preco_inicial) * 100

    # Layout de Cards/Métricas
    col1, col2, col3 = st.columns(3)
    col1.metric("Preço Atual", f"$ {preco_atual:,.2f}", f"{variacao_percentual:+.2f}%")
    col2.metric("Índice de Força Relativa (RSI 14)", f"{rsi_atual:.2f}", "Zona Neutra" if 30 <= rsi_atual <= 70 else ("Sobrevendido" if rsi_atual < 30 else "Sobrecomprado"))
    col3.metric("Indicador MACD", f"{macd_atual:.4f}")

    # --- CONSTRUÇÃO DO GRÁFICO PROFISSIONAL (Subplots Plotly) ---
    fig = make_subplots(
        rows=3, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05, 
        subplot_titles=(f'Gráfico de Velas (Candlestick) - {simbolo_id}', 'Índice de Força Relativa (RSI)', 'Histograma MACD'),
        row_width=[0.2, 0.2, 0.6]
    )

    # 1. Gráfico Principal (Candlestick + EMAs)
    fig.add_trace(go.Candlestick(
        x=df_dados['time'], open=df_dados['open'], high=df_dados['high'],
        low=df_dados['low'], close=df_dados['close'], name="Preço"
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['EMA_9'], line=dict(color='yellow', width=1.5), name="EMA 9"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['EMA_21'], line=dict(color='orange', width=1.5), name="EMA 21"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['EMA_55'], line=dict(color='red', width=1.5), name="EMA 55"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['EMA_200'], line=dict(color='blue', width=1.5), name="EMA 200"), row=1, col=1)

    # 2. Gráfico do RSI
    fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['RSI_14'], line=dict(color='purple', width=2), name="RSI (14)"), row=2, col=1)
    # Linhas de referência do RSI (30 e 70)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    # 3. Gráfico do MACD
    fig.add_trace(go.Bar(x=df_dados['time'], y=df_dados['MACD_HIST'], name="Histograma MACD", marker_color='gray'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['MACD'], line=dict(color='blue', width=1.5), name="MACD Line"), row=3, col=1)
    fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['MACD_SIGNAL'], line=dict(color='orange', width=1.5), name="Signal Line"), row=3, col=1)

    # Customizações Estéticas do Layout do Gráfico
    fig.update_layout(
        height=800,
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    # Exibir o gráfico no portal
    st.plotly_chart(fig, use_container_width=True)

    # Tabela com dados históricos em tempo real para auditoria secundária
    st.markdown("### 📋 Tabela de Dados Estruturados Recentes")
    st.dataframe(df_dados.tail(20)[['time', 'open', 'high', 'low', 'close', 'volume', 'RSI_14']].sort_values(by='time', ascending=False), use_container_width=True)

else:
    st.warning("Não foi possível processar ou renderizar os dados para as configurações selecionadas. Tente outro ativo ou período.")
