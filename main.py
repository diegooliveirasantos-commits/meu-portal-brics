import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import requests
import math
from decimal import Decimal

# ─────────────────────────────────────────────────────────────
# FORMATACAO DE PRECO
# ─────────────────────────────────────────────────────────────
def formatar_preco(valor: float, prefixo: str = "$ ") -> str:
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return f"{prefixo}—"
    if valor <= 0:
        return f"{prefixo}{valor}"
    if valor < 0.001:
        d = Decimal(str(valor))
        s = f"{d:.20f}".rstrip("0")
        partes = s.split(".")
        if len(partes) != 2:
            return f"{prefixo}{valor:.8f}"
        parte_decimal = partes[1]
        n_zeros = len(parte_decimal) - len(parte_decimal.lstrip("0"))
        digitos_sig = parte_decimal.lstrip("0")
        return f"{prefixo}0.0{n_zeros}x{digitos_sig}"
    elif valor < 1:
        return f"{prefixo}{valor:.6f}"
    elif valor < 10:
        return f"{prefixo}{valor:.4f}"
    elif valor < 1000:
        return f"{prefixo}{valor:,.2f}"
    else:
        return f"{prefixo}{valor:,.2f}"

def formatar_market_cap(valor):
    if valor is None:
        return "N/A"
    if valor >= 1_000_000_000_000:
        return f"$ {valor/1_000_000_000_000:.2f}T"
    elif valor >= 1_000_000_000:
        return f"$ {valor/1_000_000_000:.2f}B"
    elif valor >= 1_000_000:
        return f"$ {valor/1_000_000:.2f}M"
    elif valor >= 1_000:
        return f"$ {valor/1_000:.2f}K"
    else:
        return f"$ {valor:.2f}"

# ─────────────────────────────────────────────────────────────
# CONFIGURACAO DA PAGINA
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BRICSVAULT PORTAL SMC",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────
# DICIONARIO DE TRADUCAO
# ─────────────────────────────────────────────────────────────
DICIONARIO_LINGUAS = {
    "Português (BR)": {
        "titulo": "🏦 BRICSVAULT PORTAL - Motor de Smart Money Concepts (SMC)",
        "config_globais": "⚙️ Configurações Globais",
        "selecione_cripto": "Selecione Qualquer Criptomoeda (/USDT):",
        "tempo_grafico": "Tempo Gráfico:",
        "modo_vivo": "Ativar Monitoramento em Tempo Real",
        "intervalo_refresh": "Intervalo de Atualização (Segundos):",
        "preco_spot": "Preço Spot Real",
        "variacao_24h": "Variação 24h (Exchange)",
        "market_cap": "Market Cap",
        "stop_atr": "Preço Stop ATR",
        "fib_niveis_titulo": "📐 Níveis Críticos de Retração de Fibonacci (Ciclo Atual)",
        "matriz_detalhada": "📊 Matriz Detalhada de Momentum e Exaustão",
        "compra_forte": "🟢 COMPRA FORTE (SMC + FIBONACCI ALINHADOS)",
        "venda_forte": "🔴 VENDA FORTE (SMC + FIBONACCI ALINHADOS)",
        "neutro": "🟡 NEUTRO (AGUARDAR SMC)",
        "erro_dados": "Dados históricos insuficientes nesta Exchange para calcular a confluência estrutural SMC. Escolha outro Ativo ou reduza o Tempo Gráfico.",
        "fib_nomes": ["0.0% (MÁXIMA)", "23.6%", "38.2% (Fronteira Premium)", "50.0% (Equilíbrio)", "61.8% (Golden Ratio / Desconto)", "78.6%", "100.0% (MÍNIMA)"],
        "fib_posicoes": ["Topo do Ciclo", "Retração Rasa", "Zona de Carga Vendedora", "Preço Justo", "Zona de Compra Institucional", "Retração Profunda", "Fundo do Ciclo"],
        "ctx_desconto": "Ativo posicionado em Zona de Desconto de Fibonacci (Excelente risco/retorno para Institucionais).",
        "ctx_premium": "Ativo posicionado em Zona Premium de Fibonacci (Preço esticado, propício para realização de lucro).",
        "ctx_neutro": "Preço em zona neutra de equilíbrio de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Última Atualização",
        "proximo_refresh": "Próximo refresh em",
        "segundos": "segundos",
        "indicadores_smc": "🧠 Indicadores SMC",
        "bos": "BOS (Break of Structure)",
        "choch": "CHoCH (Change of Character)",
        "fvg": "FVG (Fair Value Gap)",
        "ssl": "SSL Hybrid",
        "macd_hist": "MACD Histograma",
        "cmf": "CMF (Chaikin Money Flow)",
        "wt": "WaveTrend WT1 vs WT2",
        "rsi": "RSI (14)",
        "stoch_rsi_k": "Stoch RSI %K",
        "stoch_rsi_d": "Stoch RSI %D",
        "mfi": "MFI (14)",
        "alta": "ALTA",
        "baixa": "BAIXA",
        "neutro_curto": "NEUTRO",
        "resumo_confluencia": "Resumo de Confluência",
        "pontos_compra": "Pontos de Compra",
        "pontos_venda": "Pontos de Venda",
        "grafico_titulo": "📈 Gráfico de Preço com Indicadores SMC",
        "sem_dados": "Nenhum dado disponível. Verifique a conexão.",
    },
    "Inglés (EN)": {
        "titulo": "🏦 BRICSVAULT PORTAL - Smart Money Concepts (SMC) Engine",
        "config_globais": "⚙️ Global Settings",
        "selecione_cripto": "Select Any Cryptocurrency (/USDT):",
        "tempo_grafico": "Timeframe:",
        "modo_vivo": "Enable Real-Time Monitoring",
        "intervalo_refresh": "Refresh Interval (Seconds):",
        "preco_spot": "Real Spot Price",
        "variacao_24h": "24h Variation (Exchange)",
        "market_cap": "Market Cap",
        "stop_atr": "ATR Stop Price",
        "fib_niveis_titulo": "📐 Critical Fibonacci Retraction Levels (Current Cycle)",
        "matriz_detalhada": "📊 Detailed Momentum & Exhaustion Matrix",
        "compra_forte": "🟢 STRONG BUY (SMC + FIBONACCI ALIGNED)",
        "venda_forte": "🔴 STRONG SELL (SMC + FIBONACCI ALIGNED)",
        "neutro": "🟡 NEUTRAL (AWAIT SMC)",
        "erro_dados": "Insufficient historical data on this Exchange to calculate SMC structural confluence. Choose another Asset or reduce the Timeframe.",
        "fib_nomes": ["0.0% (MAXIMUM)", "23.6%", "38.2% (Premium Frontier)", "50.0% (Equilibrium)", "61.8% (Golden Ratio / Discount)", "78.6%", "100.0% (MINIMUM)"],
        "fib_posicoes": ["Cycle Top", "Shallow Retraction", "Seller Load Zone", "Fair Price", "Institutional Buy Zone", "Deep Retraction", "Cycle Bottom"],
        "ctx_desconto": "Asset positioned in Fibonacci Discount Zone (Excellent risk/reward for Institutionals).",
        "ctx_premium": "Asset positioned in Fibonacci Premium Zone (Price stretched, suitable for profit-taking).",
        "ctx_neutro": "Price in neutral Fibonacci equilibrium zone (Fair Value Zone).",
        "ultima_atualizacao": "Last Update",
        "proximo_refresh": "Next refresh in",
        "segundos": "seconds",
        "indicadores_smc": "🧠 SMC Indicators",
        "bos": "BOS (Break of Structure)",
        "choch": "CHoCH (Change of Character)",
        "fvg": "FVG (Fair Value Gap)",
        "ssl": "SSL Hybrid",
        "macd_hist": "MACD Histogram",
        "cmf": "CMF (Chaikin Money Flow)",
        "wt": "WaveTrend WT1 vs WT2",
        "rsi": "RSI (14)",
        "stoch_rsi_k": "Stoch RSI %K",
        "stoch_rsi_d": "Stoch RSI %D",
        "mfi": "MFI (14)",
        "alta": "BULLISH",
        "baixa": "BEARISH",
        "neutro_curto": "NEUTRAL",
        "resumo_confluencia": "Confluence Summary",
        "pontos_compra": "Buy Points",
        "pontos_venda": "Sell Points",
        "grafico_titulo": "📈 Price Chart with SMC Indicators",
        "sem_dados": "No data available. Check connection.",
    },
    "Español (ESP)": {
        "titulo": "🏦 BRICSVAULT PORTAL - Motor de Smart Money Concepts (SMC)",
        "config_globais": "⚙️ Configuraciones Globales",
        "selecione_cripto": "Seleccione Cualquier Criptomoneda (/USDT):",
        "tempo_grafico": "Período de Tiempo:",
        "modo_vivo": "Activar Monitoreo en Tiempo Real",
        "intervalo_refresh": "Intervalo de Actualización (Segundos):",
        "preco_spot": "Precio Spot Real",
        "variacao_24h": "Variación 24h (Exchange)",
        "market_cap": "Cap. de Mercado",
        "stop_atr": "Precio Stop ATR",
        "fib_niveis_titulo": "📐 Niveles Críticos de Retracción de Fibonacci (Ciclo Actual)",
        "matriz_detalhada": "📊 Matriz Detallada de Momentum y Agotamiento",
        "compra_forte": "🟢 COMPRA FUERTE (SMC + FIBONACCI ALINEADOS)",
        "venda_forte": "🔴 VENTA FUERTE (SMC + FIBONACCI ALINEADOS)",
        "neutro": "🟡 NEUTRO (ESPERAR SMC)",
        "erro_dados": "Datos históricos insuficientes en esta Exchange para calcular la confluencia estructural SMC. Elija otro Activo o reduzca el Tiempo Gráfico.",
        "fib_nomes": ["0.0% (MÁXIMA)", "23.6%", "38.2% (Frontera Premium)", "50.0% (Equilibrio)", "61.8% (Golden Ratio / Descuento)", "78.6%", "100.0% (MÍNIMA)"],
        "fib_posicoes": ["Techo del Ciclo", "Retracción Superficial", "Zona de Carga Vendedora", "Precio Justo", "Zona de Compra Institucional", "Retracción Profunda", "Fondo del Ciclo"],
        "ctx_desconto": "Activo posicionado en Zona de Descuento de Fibonacci (Excelente riesgo/beneficio para Institucionales).",
        "ctx_premium": "Activo posicionado en Zona Premium de Fibonacci (Precio estirado, propicio para toma de ganancias).",
        "ctx_neutro": "Precio en zona neutral de equilibrio de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Última Actualización",
        "proximo_refresh": "Próximo refresh en",
        "segundos": "segundos",
        "indicadores_smc": "🧠 Indicadores SMC",
        "bos": "BOS (Ruptura de Estructura)",
        "choch": "CHoCH (Cambio de Carácter)",
        "fvg": "FVG (Gap de Valor Justo)",
        "ssl": "SSL Hybrid",
        "macd_hist": "Histograma MACD",
        "cmf": "CMF (Flujo de Dinero Chaikin)",
        "wt": "WaveTrend WT1 vs WT2",
        "rsi": "RSI (14)",
        "stoch_rsi_k": "Stoch RSI %K",
        "stoch_rsi_d": "Stoch RSI %D",
        "mfi": "MFI (14)",
        "alta": "ALCISTA",
        "baixa": "BAJISTA",
        "neutro_curto": "NEUTRAL",
        "resumo_confluencia": "Resumen de Confluencia",
        "pontos_compra": "Puntos de Compra",
        "pontos_venda": "Puntos de Venta",
        "grafico_titulo": "📈 Gráfico de Precio con Indicadores SMC",
        "sem_dados": "Sin datos disponibles. Verifique la conexión.",
    }
}

# ─────────────────────────────────────────────────────────────
# SELETOR DE IDIOMA
# ─────────────────────────────────────────────────────────────
st.sidebar.markdown("### 🌐 Language / Idioma / Langue")
idioma_selecionado = st.sidebar.selectbox(
    "Select Interface Language:",
    options=list(DICIONARIO_LINGUAS.keys()),
    index=0
)
txt = DICIONARIO_LINGUAS[idioma_selecionado]

# ─────────────────────────────────────────────────────────────
# CONEXAO COM EXCHANGE
# ─────────────────────────────────────────────────────────────
@st.cache_resource
def inicializar_exchange():
    return ccxt.gate({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })

gateio_client = inicializar_exchange()

@st.cache_data(ttl=3600)
def obter_todos_pares_usdt():
    try:
        mercados = gateio_client.load_markets()
        return sorted([s for s in mercados.keys() if s.endswith('/USDT')])
    except Exception:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]

# ─────────────────────────────────────────────────────────────
# FUNCAO PARA OBTER MARKET CAP (CoinGecko)
# ─────────────────────────────────────────────────────────────
MAPEAMENTO_COINGECKO = {
    'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana', 'XRP': 'ripple',
    'BNB': 'binancecoin', 'ADA': 'cardano', 'DOGE': 'dogecoin', 'DOT': 'polkadot',
    'MATIC': 'matic-network', 'AVAX': 'avalanche-2', 'LINK': 'chainlink',
    'UNI': 'uniswap', 'LTC': 'litecoin', 'ATOM': 'cosmos', 'ETC': 'ethereum-classic',
    'XLM': 'stellar', 'VET': 'vechain', 'FIL': 'filecoin', 'TRX': 'tron',
    'NEAR': 'near', 'APT': 'aptos', 'ARB': 'arbitrum', 'OP': 'optimism',
    'SUI': 'sui', 'PEPE': 'pepe', 'SHIB': 'shiba-inu', 'BONK': 'bonk',
    'WIF': 'dogwifcoin', 'JUP': 'jupiter-exchange-solana', 'PYTH': 'pyth-network',
    'TIA': 'celestia', 'SEI': 'sei-network', 'INJ': 'injective-protocol',
    'RUNE': 'thorchain', 'AAVE': 'aave', 'GRT': 'the-graph', 'FTM': 'fantom',
    'ALGO': 'algorand', 'SAND': 'the-sandbox', 'MANA': 'decentraland',
    'AXS': 'axie-infinity', 'EGLD': 'elrond-erd-2', 'EOS': 'eos', 'FLOW': 'flow',
    'CHZ': 'chiliz', 'CRV': 'curve-dao-token', 'SNX': 'havven', 'SUSHI': 'sushi',
    '1INCH': '1inch', 'ZRX': '0x', 'ENJ': 'enjincoin', 'ICP': 'internet-computer',
    'XTZ': 'tezos', 'XMR': 'monero', 'CAKE': 'pancakeswap-token', 'RAY': 'raydium',
    'ORCA': 'orca', 'EGLD': 'elrond-erd-2', 'KLAY': 'klay-token'
}

@st.cache_data(ttl=300)
def obter_market_cap(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&community_data=false&developer_data=false"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            market_cap = data['market_data']['market_cap']['usd']
            return market_cap
        return None
    except Exception:
        return None

@st.cache_data(ttl=300)
def obter_market_cap_para_simbolo(simbolo_usdt):
    moeda_base = simbolo_usdt.split('/')[0]
    coin_id = MAPEAMENTO_COINGECKO.get(moeda_base)
    if coin_id:
        market_cap = obter_market_cap(coin_id)
        if market_cap:
            return market_cap
    return None

# ─────────────────────────────────────────────────────────────
# FUNCOES DE INDICADORES
# ─────────────────────────────────────────────────────────────
def calcular_rsi(df, col, periodo=14):
    delta = df[col].diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    ma_ganho = ganho.ewm(span=periodo, adjust=False).mean()
    ma_perda = perda.ewm(span=periodo, adjust=False).mean()
    return 100 - (100 / (1 + (ma_ganho / ma_perda.replace(0, 1e-10))))

def calcular_stoch_rsi(df, periodo=14, k_period=3, d_period=3):
    rsi = df['RSI_14']
    min_rsi = rsi.rolling(window=periodo).min()
    max_rsi = rsi.rolling(window=periodo).max()
    stoch_raw = (rsi - min_rsi) / (max_rsi - min_rsi).replace(0, 1e-10)
    df['StochRSI_K'] = stoch_raw.rolling(window=k_period).mean() * 100
    df['StochRSI_D'] = df['StochRSI_K'].rolling(window=d_period).mean()
    return df

def calcular_macd(df, col):
    ema_rapida = df[col].ewm(span=12, adjust=False).mean()
    ema_lenta = df[col].ewm(span=26, adjust=False).mean()
    macd = ema_rapida - ema_lenta
    sinal = macd.ewm(span=9, adjust=False).mean()
    return macd, sinal, macd - sinal

def calcular_chaikin_money_flow(df, periodo=20):
    rng = (df['high'] - df['low']).replace(0, 1e-10)
    mfm = ((df['close'] - df['low']) - (df['high'] - df['close'])) / rng
    mfv = mfm * df['volume']
    vol_sum = df['volume'].rolling(window=periodo).sum().replace(0, 1e-10)
    df['CMF'] = mfv.rolling(window=periodo).sum() / vol_sum
    return df

def calcular_wavetrend_oscillator(df, n1=10, n2=21):
    ap = (df['high'] + df['low'] + df['close']) / 3
    esa = ap.ewm(span=n1, adjust=False).mean()
    d = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
    ci = (ap - esa) / (0.015 * d.replace(0, 1e-10))
    df['WT1'] = ci.ewm(span=n2, adjust=False).mean()
    df['WT2'] = df['WT1'].rolling(window=4).mean().bfill()
    return df

def calcular_mfi(df, periodo=14):
    tp = (df['high'] + df['low'] + df['close']) / 3
    rmf = tp * df['volume']
    tp_shift = tp.shift(1)
    pos_flow = rmf.where(tp > tp_shift, 0.0)
    neg_flow = rmf.where(tp < tp_shift, 0.0)
    pos_sum = pos_flow.rolling(window=periodo).sum()
    neg_sum = neg_flow.rolling(window=periodo).sum().replace(0, 1e-10)
    return 100 - (100 / (1 + pos_sum / neg_sum))

def calcular_ssl_hybrid(df, periodo=20):
    sma_high = df['high'].rolling(window=periodo).mean()
    sma_low = df['low'].rolling(window=periodo).mean()
    close_arr = df['close'].values
    sma_h_arr = sma_high.values
    sma_l_arr = sma_low.values
    ssl_dir = np.ones(len(df), dtype=int)
    current = 1
    for i in range(len(df)):
        if np.isnan(sma_h_arr[i]) or np.isnan(sma_l_arr[i]):
            ssl_dir[i] = current
            continue
        if close_arr[i] > sma_h_arr[i]:
            current = 1
        elif close_arr[i] < sma_l_arr[i]:
            current = -1
        ssl_dir[i] = current
    df['ssl_dir'] = ssl_dir
    df['SSL_Baseline'] = np.where(df['ssl_dir'] == 1, sma_high, sma_low)
    return df

def calcular_atr_stop(df, periodo=14, multiplicador=3.0):
    high, low, close = df['high'], df['low'], df['close']
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    atr = tr.ewm(span=periodo, adjust=False).mean()
    atr_stop = np.zeros(len(df))
    tendencia = np.zeros(len(df), dtype=int)
    close_arr = close.values
    atr_arr = atr.values
    for i in range(1, len(df)):
        if i == 1:
            atr_stop[i] = close_arr[i] - (atr_arr[i] * multiplicador)
            tendencia[i] = 1
            continue
        if tendencia[i-1] == 1:
            if close_arr[i] < atr_stop[i-1]:
                tendencia[i] = -1
                atr_stop[i] = close_arr[i] + (atr_arr[i] * multiplicador)
            else:
                tendencia[i] = 1
                atr_stop[i] = max(atr_stop[i-1], close_arr[i] - (atr_arr[i] * multiplicador))
        else:
            if close_arr[i] > atr_stop[i-1]:
                tendencia[i] = 1
                atr_stop[i] = close_arr[i] - (atr_arr[i] * multiplicador)
            else:
                tendencia[i] = -1
                atr_stop[i] = min(atr_stop[i-1], close_arr[i] + (atr_arr[i] * multiplicador))
    df['ATR_Stop'] = atr_stop
    df['atr_dir'] = tendencia
    return df

def calcular_alpha_trend(df, periodo=14, coeff=1.0):
    high, low, close = df['high'], df['low'], df['close']
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(window=periodo).mean()
    up_t = low - coeff * atr
    down_t = high + coeff * atr
    mfi = df['MFI'].values
    alpha_trend = np.zeros(len(df))
    for i in range(len(df)):
        if i < periodo:
            alpha_trend[i] = close.iloc[i]
            continue
        if mfi[i] >= 50:
            alpha_trend[i] = max(up_t.iloc[i], alpha_trend[i-1])
        else:
            alpha_trend[i] = min(down_t.iloc[i], alpha_trend[i-1])
    df['AT_K1'] = alpha_trend
    return df

def mapear_estrutura_smc(df):
    fechamentos = df['close'].values
    maximas = df['high'].values
    minimas = df['low'].values
    bos_detectado = 0
    choch_detectado = 0
    fvg_pendente = 0
    for i in range(len(df) - 3, len(df) - 1):
        if minimas[i+1] > maximas[i-1]:
            fvg_pendente = 1
        elif maximas[i+1] < minimas[i-1]:
            fvg_pendente = -1
    topo_local = np.max(fechamentos[-15:-2])
    fundo_local = np.min(fechamentos[-15:-2])
    if fechamentos[-1] > topo_local:
        bos_detectado = 1
    elif fechamentos[-1] < fundo_local:
        bos_detectado = -1
    if fechamentos[-1] > topo_local and fechamentos[-2] <= topo_local:
        choch_detectado = 1
    elif fechamentos[-1] < fundo_local and fechamentos[-2] >= fundo_local:
        choch_detectado = -1
    df['SMC_BOS'] = bos_detectado
    df['SMC_CHOCH'] = choch_detectado
    df['SMC_FVG'] = fvg_pendente
    return df

def calcular_retracao_fibonacci(df):
    maxima = df['high'].max()
    minima = df['low'].min()
    diff = maxima - minima
    return {
        'fib_0': maxima,
        'fib_236': maxima - 0.236 * diff,
        'fib_382': maxima - 0.382 * diff,
        'fib_500': maxima - 0.500 * diff,
        'fib_618': maxima - 0.618 * diff,
        'fib_786': maxima - 0.786 * diff,
        'fib_100': minima
    }

# ─────────────────────────────────────────────────────────────
# CARREGAMENTO DE DADOS
# ─────────────────────────────────────────────────────────────
def carregar_dados_bricsvault_smc(simbolo_id, timeframe_selecionado):
    try:
        velas = gateio_client.fetch_ohlcv(simbolo_id, timeframe=timeframe_selecionado, limit=200)
        if not velas:
            return None
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['RSI_14'] = calcular_rsi(df, 'close', 14)
        df = calcular_stoch_rsi(df)
        macd, sinal, hist = calcular_macd(df, 'close')
        df['MACD'], df['MACD_SIGNAL'], df['MACD_HIST'] = macd, sinal, hist
        df['MFI'] = calcular_mfi(df)
        df = calcular_ssl_hybrid(df)
        df = calcular_atr_stop(df)
        df = calcular_alpha_trend(df)
        df = calcular_chaikin_money_flow(df)
        df = calcular_wavetrend_oscillator(df)
        df = mapear_estrutura_smc(df)
        return df.dropna(subset=['close', 'SSL_Baseline'])
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

def obter_variacao_24h_precisa(simbolo_id):
    try:
        dados_24h = gateio_client.fetch_ohlcv(simbolo_id, timeframe='1d', limit=2)
        if dados_24h and len(dados_24h) >= 2:
            close_hoje = dados_24h[-1][4]
            close_ontem = dados_24h[-2][4]
            return ((close_hoje - close_ontem) / close_ontem) * 100
    except Exception:
        pass
    return 0.0

# ─────────────────────────────────────────────────────────────
# CONFLUENCIA SMC
# ─────────────────────────────────────────────────────────────
def analisar_confluencia_smc_total(df, fib_niveis):
    u = df.iloc[-1]
    preco_atual = u['close']
    pontos_alta = 0.0
    pontos_baixa = 0.0
    
    if u['SMC_CHOCH'] == 1 or u['SMC_BOS'] == 1:
        pontos_alta += 3
    if u['SMC_CHOCH'] == -1 or u['SMC_BOS'] == -1:
        pontos_baixa += 3
    if u['SMC_FVG'] == 1:
        pontos_alta += 1
    if u['SMC_FVG'] == -1:
        pontos_baixa += 1
    
    if preco_atual <= fib_niveis['fib_618']:
        pontos_alta += 2.0
        contexto_fib = txt["ctx_desconto"]
    elif preco_atual >= fib_niveis['fib_382']:
        pontos_baixa += 2.0
        contexto_fib = txt["ctx_premium"]
    else:
        contexto_fib = txt["ctx_neutro"]
    
    if u['CMF'] > 0:
        pontos_alta += 1.5
    else:
        pontos_baixa += 1.5
    if u['WT1'] > u['WT2']:
        pontos_alta += 1
    else:
        pontos_baixa += 1
    if u['MACD_HIST'] > 0:
        pontos_alta += 1
    else:
        pontos_baixa += 1
    
    if pontos_alta >= 7.5:
        return txt["compra_forte"], "#00cc66", f"{contexto_fib} SMC Order Flow Bullish Structure.", pontos_alta, pontos_baixa
    elif pontos_baixa >= 7.5:
        return txt["venda_forte"], "#ff3333", f"{contexto_fib} SMC Order Flow Bearish Structure.", pontos_alta, pontos_baixa
    else:
        return txt["neutro"], "#ffcc00", contexto_fib, pontos_alta, pontos_baixa

# ─────────────────────────────────────────────────────────────
# GRAFICO PRINCIPAL
# ─────────────────────────────────────────────────────────────
def construir_grafico(df, fib_niveis, simbolo_id):
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        row_heights=[0.50, 0.17, 0.17, 0.16],
        vertical_spacing=0.03,
        subplot_titles=(
            f"{simbolo_id} — Candlestick + ATR Stop + SSL Hybrid",
            "MACD",
            "RSI / Stoch RSI",
            "CMF / WaveTrend"
        )
    )
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name="OHLC", increasing_line_color='#00cc66',
        decreasing_line_color='#ff3333'
    ), row=1, col=1)
    
    # ATR Stop
    atr_colors = df['atr_dir'].apply(lambda d: '#00cc66' if d == 1 else '#ff3333')
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['ATR_Stop'], mode='markers',
        marker=dict(color=atr_colors, size=3), name="ATR Stop"
    ), row=1, col=1)
    
    # SSL Hybrid
    ssl_colors = df['ssl_dir'].apply(lambda d: '#00aaff' if d == 1 else '#ff6600')
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['SSL_Baseline'], mode='lines',
        line=dict(width=1.5), marker=dict(color=ssl_colors), name="SSL Hybrid"
    ), row=1, col=1)
    
    # Alpha Trend
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['AT_K1'], mode='lines',
        line=dict(color='#aa44ff', width=1, dash='dot'), name="Alpha Trend"
    ), row=1, col=1)
    
    # Fibonacci levels
    fib_cores = {
        'fib_0': ('#ff4444', '0.0%'), 'fib_236': ('#ffaa00', '23.6%'),
        'fib_382': ('#ffdd00', '38.2%'), 'fib_500': ('#aaaaaa', '50.0%'),
        'fib_618': ('#00cc66', '61.8%'), 'fib_786': ('#00
