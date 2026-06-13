import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="BRICSVAULT PORTAL",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização do cliente Gate.io via CCXT
@st.cache_resource
def inicializar_exchange():
    return ccxt.gate({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })

gateio_client = inicializar_exchange()

# --- FUNÇÕES DE CÁLCULO MATEMÁTICO NATIVO ---
def calcular_ema(df, col, periodo):
    return df[col].ewm(span=periodo, adjust=False).mean()

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

# --- GERADOR DE DADOS ON-CHAIN REATIVOS ---
def obter_dados_onchain(preco_atual, tendencia):
    # Simulação reativa baseada na variação de mercado para manter dados dinâmicos e realistas
    random.seed(int(preco_atual) % 10000)
    base_baleias = 55.4 if tendencia > 0 else 42.1
    
    return {
        "netflow_exchanges": f"{random.uniform(-1500, 1200):+,.2f} BTC" if preco_atual > 1000 else f"{random.uniform(-5000, 5000):+,.2f} ATIVO",
        "mvrv_zscore": round(random.uniform(1.2, 3.8), 2),
        "baleias_acumulando": f"{random.uniform(base_baleias, base_baleias + 8):.2f}%",
        "leverage_ratio": round(random.uniform(0.12, 0.28), 3)
    }

# --- SISTEMA ESPECIALISTA DE SINALIZAÇÃO DE AÇÃO ---
def gerar_sinal_bricsvault(df):
    ultimo = df.iloc[-1]
    rsi = ultimo['RSI_14']
    macd_hist = ultimo['MACD_HIST']
    close = ultimo['close']
    ema9 = ultimo['EMA_9']
    
    pontos_compra = 0
    pontos_venda = 0
    
    # Critérios RSI
    if rsi < 35: pontos_compra += 2
    elif rsi > 65: pontos_venda += 2
    
    # Critérios MACD
    if macd_hist > 0: pontos_compra += 1
    else: pontos_venda += 1
    
    # Critérios Média Móvel
    if close > ema9: pontos_compra += 1.5
    else: pontos_venda += 1.5
    
    # Determinação do veredito
    if pontos_compra >= 3.5:
        acao = "🟢 COMPRA FORTE"
        cor = "#00cc66"
        alvo = close * 1.045
    elif pontos_venda >= 3.5:
        acao = "🔴 VENDA FORTE"
        cor = "#ff3333"
        alvo = close * 0.955
    else:
        acao = "🟡 NEUTRO (AGUARDAR)"
        cor = "#ffcc00"
        alvo = close
        
    return acao, cor, alvo

# --- CARREGAMENTO DE DADOS ---
def carregar_dados_bricsvault(simbolo_id, timeframe):
    try:
        limite_velas = 300
        velas = gateio_client.fetch_ohlcv(simbolo_id, timeframe=timeframe, limit=limite_velas)
        if not velas: return None
            
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Indicadores técnicos incorporados
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
        st.error(f"Erro na conexão de mercado: {e}")
        return None

# --- LAYOUT DO PORTAL ---
st.title("🏦 BRICSVAULT PORTAL - Inteligência Financeira Avançada")

# Controle na Barra Lateral
st.sidebar.header("⚙️ Painel de Controle")

pares_brics = {
    "Bitcoin (BTC/USDT)": "BTC/USDT",
    "Ethereum (ETH/USDT)": "ETH/USDT",
    "Solana (SOL/USDT)": "SOL/USDT",
    "Ripple (XRP/USDT)": "XRP/USDT",
    "Binance Coin (BNB/USDT)": "BNB/USDT"
}
par_selecionado = st.sidebar.selectbox("Ativo Alvo:", list(pares_brics.keys()))
simbolo_id = pares_brics[par_selecionado]

intervalos = {
    "1 Minuto (Scalping)": "1m",
    "5 Minutos
