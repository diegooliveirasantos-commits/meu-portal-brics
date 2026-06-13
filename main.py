import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="BRICSVAULT PORTAL PRO",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização segura do cliente Gate.io via CCXT
@st.cache_resource
def inicializar_exchange():
    return ccxt.gate({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })

gateio_client = inicializar_exchange()

# Carregamento dinâmico de TODOS os pares USDT disponíveis na exchange
@st.cache_data(ttl=3600)
def obter_todos_pares_usdt():
    try:
        mercados = gateio_client.load_markets()
        pares_usdt = [simbolo for simbolo in mercados.keys() if simbolo.endswith('/USDT')]
        return sorted(pares_usdt)
    except Exception:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]

# --- FUNÇÕES DE CÁLCULO MATEMÁTICO NATIVO ---
def calcular_rsi(df, col, periodo=14):
    delta = df[col].diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
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

def calcular_ssl_hybrid(df, periodo=20):
    sma_high = df['high'].rolling(window=periodo).mean()
    sma_low = df['low'].rolling(window=periodo).mean()
    
    ssl_direction = []
    current_dir = 1
    
    for idx in range(len(df)):
        close = df['close'].iloc[idx]
        h = sma_high.iloc[idx]
        l = sma_low.iloc[idx]
        
        if pd.isna(h) or pd.isna(l):
            ssl_direction.append(current_dir)
            continue
            
        if close > h:
            current_dir = 1
        elif close < l:
            current_dir = -1
        ssl_direction.append(current_dir)
        
    df['ssl_dir'] = ssl_direction
    df['SSL_High'] = sma_high
    df['SSL_Low'] = sma_low
    df['SSL_Baseline'] = df.apply(lambda row: row['SSL_High'] if row['ssl_dir'] == 1 else row['SSL_Low'], axis=1)
    return df

def calcular_atr_stop(df, periodo=14, multiplicador=3.0):
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(span=periodo, adjust=False).mean()
    
    atr_stop = np.zeros(len(df))
    tendencia = np.zeros(len(df))
    
    for i in range(1, len(df)):
        preco_fechamento = close.iloc[i]
        atr_atual = atr.iloc[i]
        
        if i == 1:
            atr_stop[i] = preco_fechamento - (atr_atual * multiplicador)
            tendencia[i] = 1
            continue
            
        stop_anterior = atr_stop[i-1]
        tendencia_anterior = tendencia[i-1]
        
        if tendencia_anterior == 1:
            if preco_fechamento < stop_anterior:
                tendencia[i] = -1
                atr_stop[i] = preco_fechamento + (atr_atual * multiplicador)
            else:
                tendencia[i] = 1
                valor_calculado = preco_fechamento - (atr_atual * multiplicador)
                atr_stop[i] = max(stop_anterior, valor_calculado)
        else:
            if preco_fechamento > stop_anterior:
                tendencia[i] = 1
                atr_stop[i] = preco_fechamento - (atr_atual * multiplicador)
            else:
                tendencia[i] = -1
                valor_calculado = preco_fechamento + (atr_atual * multiplicador)
                atr_stop[i] = min(stop_anterior, valor_calculado)
                
    df['ATR_Stop'] = atr_stop
    df['atr_dir'] = tendencia
    return df

# --- SISTEMA DE SINALIZAÇÃO DE AÇÃO CONFLUENTE (SSL + ATR STOP + RSI + MACD) ---
def calcular_sinal_BRICS(df):
    ultimo = df.iloc[-1]
    rsi = ultimo['RSI_14']
    macd_hist = ultimo['MACD_HIST']
    close = ultimo['close']
    ssl_dir = ultimo['ssl_dir']
    atr_dir = ultimo['atr_dir']
    
    ponto_compra = 0
    ponto_venda = 0
    
    if ssl_dir == 1: ponto_compra += 1.5
    else: ponto_venda += 1.5
        
    if atr_dir == 1: ponto_compra += 1.5
    else: ponto_venda += 1.5
    
    if rsi < 45: ponto_compra += 1
    elif rsi > 55: ponto_venda += 1
    
    if macd_hist > 0: ponto_compra += 1
    else: ponto_venda += 1
    
    if ponto_compra >= 4:
        return "🟢 COMPRA FORTE", "#00cc66", close * 1.05, "Tendência Confluente: Preço trabalhando acima do SSL Baseline e validado pelo Stop ATR."
    elif ponto_venda >= 4:
        return "🔴 VENDA FORTE", "#ff3333", close * 0.95, "Tendência de Baixa: Preço abaixo do SSL Baseline e rompido pelo Stop ATR."
    else:
        return "🟡 NEUTRO (AGUARDAR)", "#ffcc00", close, "Indicadores sem consenso macro absoluto. Aguarde o alinhamento das bandas."

# --- CARREGAMENTO E TRATAMENTO DE DADOS COM AGREGADOR TEMPORAL REAL ---
def carregar_dados_bricsvault(simbolo_id, timeframe_selecionado):
    try:
        limite = 500
        timeframe_fetch = timeframe_selecionado
        agrupar_meses = None
        
        # Consolidação matemática exata para tempos gráficos não nativos da API
        if timeframe_selecionado == "3M":
            timeframe_fetch = "1M"
            agrupar_meses = 3
        elif timeframe_selecionado == "6M":
            timeframe_fetch = "1M"
            agrupar_meses = 6
        elif timeframe_selecionado == "1Y":
            timeframe_fetch = "1M"
            agrupar_meses = 12

        velas = gateio_client.fetch_ohlcv(simbolo_id, timeframe=timeframe_fetch, limit=limite)
        if not velas: return None
            
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        if agrupar_meses:
            df.set_index('time', inplace=True)
            df = df.resample(f'{agrupar_meses}ME').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna().reset_index()
        
        if len(df) < 20:
            return None
            
        df['RSI_14'] = calcular_rsi(df, 'close', 14)
        macd, sinal, hist = calcular_macd(df, 'close')
        df['MACD'] = macd
        df['MACD_SIGNAL'] = sinal
        df['MACD_HIST'] = hist
        
        df = calcular_ssl_hybrid(df, periodo=20)
        df = calcular_atr_stop(df, periodo=14, multiplicador=3.0)

        return df.dropna(subset=['close', 'SSL_Baseline', 'ATR_Stop'])
    except Exception as e:
        st.error(f"Erro na extração de dados: {e}")
        return None

# --- INTERFACE DO PORTAL ---
st.title("🏦 BRICSVAULT PORTAL - Análise de Precisão de Mercado")

st.sidebar.header("⚙️ Configurações Globais")

lista_criptos = obter_todos_pares_usdt()
simbolo_id = st.sidebar.selectbox("Selecione Qualquer Criptomoeda (/USDT):", lista_criptos, index=lista_criptos.index("SOL/USDT") if "SOL/USDT" in lista_criptos else 0)

intervalos = {
    "1 Minuto": "1m",
    "5 Minutos": "5m",
    "1 Hora": "1h",
    "4 Horas": "4h",
    "8 Horas": "8h",
    "12 Horas": "12h",
    "1 Dia": "1d",
    "1 Semana": "1w",
    "1 Mês": "1M",
    "3 Meses": "3M",
    "6 Meses": "6M",
    "1 Ano": "1Y"
}
intervalo_escolhido = st.sidebar.selectbox("Tempo Gráfico:", list(intervalos.keys()))
timeframe = intervalos[intervalo_escolhido]

st.sidebar.markdown("---")
st.sidebar.subheader("🔄 Controle de Transmissão Live")
modo_vivo = st.sidebar.toggle("Ativar Monitoramento em Tempo Real", value=True)
intervalo_refresh = st.sidebar.slider("Intervalo de Atualização (Segundos):", min_value=3, max_value=30, value=5)

executar_botao = st.sidebar.button("🚀 EXECUTAR ANÁLISE COMPLETA (GO)", use_container_width=True)

if "execucao_inicializada" not in st.session_state:
    st.session_state["execucao_inicializada"] = True

if executar_botao:
    st.session_state["execucao_inicializada"] = True

if st.session_state["execucao_inicializada"]:
    df_dados = carregar_dados_bricsvault(simbolo_id, timeframe)
        
    if df_dados is not None and not df_dados.empty:
        ultimo_reg = df_dados.iloc[-1]
        preco_atual = ultimo_reg['close']
        
        variacao = ((preco_atual - df_dados.iloc[0]['close']) / df_dados.iloc[0]['close']) * 100
        recomendacao, cor_sinal, alvo_tecnico, justificativa = calcular_sinal_BRICS(df_dados)

        # 🚨 SEÇÃO 1: PAINEL DE CONFLUÊNCIA DE SINAIS 🚨
        st.markdown(f"""
        <div style="background-color: {cor_sinal}22; padding: 20px; border-radius: 10px; border: 2px solid {cor_sinal}; margin-bottom: 25px;">
            <h2 style="margin: 0; color: {cor_sinal}; font-size: 26px;">SINAL EMITIDO: {recomendacao}</h2>
            <p style="margin: 8px 0 0 0; font-size: 16px; color: #ffffff;"><b>Alvo Estimado:</b> $ {alvo_tecnico:,.4f} | <b>Stop ATR Atual:</b> $ {ultimo_reg['ATR_Stop']:,.4f}</p>
            <p style="margin: 5px 0 0 0; font-size: 14px; color: #bbbbbb;"><b>Filtro Confluente (SSL Hybrid + Stop ATR):</b> {justificativa}</p>
        </div>
        """, unsafe_allow_html=True)

        # SEÇÃO 2: CARD DE MÉTRICAS REAIS
        col1, col2, col3 = st.columns(3)
        col1.metric("Preço Spot Real", f"$ {preco_atual:,.4f}", f"{variacao:+.2f}%")
        col2.metric("RSI (14)", f"{ultimo_reg['RSI_14']:.2f}")
        col3.metric("Volume Histórico", f"{ultimo_reg['volume']:,.2f}")

        # SEÇÃO 3: GRÁFICO AVANÇADO SUBPLOTS
        fig = make_subplots(
            rows=3, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.06, 
            subplot_titles=(f'Candlesticks + SSL Hybrid + Stop ATR - {simbolo_id}', 'Índice de Força Relativa (RSI)', 'Histograma MACD'),
            row_width=[0.2, 0.2, 0.6]
        )

        fig.add_trace(go.Candlestick(
            x=df_dados['time'], open=df_dados['open'], high=df_dados['high'],
            low=df_dados['low'], close=df_dados['close'], name="Preço"
        ), row=1, col=1)
        
        # Linhas do SSL Hybrid
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['SSL_Baseline'], line=dict(color='#00ffff', width=2), name="SSL Baseline"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['SSL_High'], line=dict(color='#00cc66', width=1, dash='dot'), name="SSL Banda Alta"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['SSL_Low'], line=dict(color='#ff3333', width=1, dash='dot'), name="SSL Banda Baixa"), row=1, col=1)
        
        # Linha do Stop ATR
        cor_atr = '#00ffcc' if ultimo_reg['atr_dir'] == 1 else '#ff0055'
        fig.add_trace(go.Scatter(
            x=df_dados['time'], y=df_dados['ATR_Stop'], 
            line=dict(color=cor_atr, width=2.5, dash='solid'), 
            name="Stop ATR"
        ), row=1, col=1)

        # Subplots Auxiliares
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['RSI_14'], line=dict(color='purple', width=2), name="RSI"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        fig.add_trace(go.Bar(x=df_dados['time'], y=df_dados['MACD_HIST'], name="Hist MACD", marker_color='cyan'), row=3, col=1)

        fig.update_layout(height=720, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=40, r=40, t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)

        if modo_vivo:
            time.sleep(intervalo_refresh)
            st.rerun()
    else:
        st.error("Erro técnico: O histórico desta moeda na exchange é muito curto para calcular os indicadores neste tempo gráfico específico. Escolha um tempo menor ou outro ativo.")
