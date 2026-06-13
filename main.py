import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import math
from decimal import Decimal

# ─────────────────────────────────────────────────────────────
# FORMATACAO DE PRECO — notacao compacta para valores micro
# ─────────────────────────────────────────────────────────────
def formatar_preco(valor: float, prefixo: str = "$ ") -> str:
    """
    Formatacao inteligente de precos de criptomoedas.
    Valores micro (< 0.001) usam notacao compacta: 0.0{N_zeros}x{digitos_significativos}
    """
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
    else:
        return f"{prefixo}{valor:,.2f}"

def formatar_marketcap(valor: float) -> str:
    """Formatador para bilhoes (B), milhoes (M) ou milhares (K)"""
    if valor is None or math.isnan(valor) or valor == 0:
        return "$ —"
    if valor >= 1_000_000_000_000:
        return f"$ {valor / 1_000_000_000_000:.2f} T"
    elif valor >= 1_000_000_000:
        return f"$ {valor / 1_000_000_000:.2f} B"
    elif valor >= 1_000_000:
        return f"$ {valor / 1_000_000:.2f} M"
    else:
        return f"$ {valor:,.2f}"

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="BRICSVAULT PORTAL SMC",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- REPOSITÓRIO INTERNO DE TRADUÇÃO (i18n) ---
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
        "fib_nomes": ["0.0% (MAXIMUM)", "23.6%", "38.2% (Premium Frontier)", "50.0% (Equilíbrio)", "61.8% (Golden Ratio / Discount)", "78.6%", "100.0% (MINIMUM)"],
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
    }
}

st.sidebar.markdown("### 🌐 Language / Idioma / Langue")
idioma_selecionado = st.sidebar.selectbox(
    "Select Interface Language:",
    options=list(DICIONARIO_LINGUAS.keys()),
    index=0
)
txt = DICIONARIO_LINGUAS[idioma_selecionado]

# ─────────────────────────────────────────────────────────────
# CONEXÃO COM EXCHANGE
# ─────────────────────────────────────────────────────────────
@st.cache_resource
def inicializar_exchange():
    return ccxt.gate({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })

gateio_client = inicializar_exchange()

@st.cache_data(ttl="1h")
def obter_todos_pares_usdt():
    try:
        mercados = gateio_client.load_markets()
        return sorted([s for s in mercados.keys() if s.endswith('/USDT')])
    except Exception:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]

# ─────────────────────────────────────────────────────────────
# FUNÇÕES DE INDICADORES (Vetorizadas)
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
    ema_lenta  = df[col].ewm(span=26, adjust=False).mean()
    macd       = ema_rapida - ema_lenta
    sinal      = macd.ewm(span=9, adjust=False).mean()
    return macd, sinal, macd - sinal

def calcular_chaikin_money_flow(df, periodo=20):
    rng = (df['high'] - df['low']).replace(0, 1e-10)
    mfm = ((df['close'] - df['low']) - (df['high'] - df['close'])) / rng
    mfv = mfm * df['volume']
    vol_sum = df['volume'].rolling(window=periodo).sum().replace(0, 1e-10)
    df['CMF'] = mfv.rolling(window=periodo).sum() / vol_sum
    return df

def calcular_wavetrend_oscillator(df, n1=10, n2=21):
    ap  = (df['high'] + df['low'] + df['close']) / 3
    esa = ap.ewm(span=n1, adjust=False).mean()
    d   = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
    close_val = 0.015 * d.replace(0, 1e-10)
    ci  = (ap - esa) / close_val
    df['WT1'] = ci.ewm(span=n2, adjust=False).mean()
    df['WT2'] = df['WT1'].rolling(window=4).mean().bfill()
    return df

def calcular_mfi(df, periodo=14):
    tp  = (df['high'] + df['low'] + df['close']) / 3
    rmf = tp * df['volume']
    tp_shift = tp.shift(1)
    pos_flow = rmf.where(tp > tp_shift, 0.0)
    neg_flow = rmf.where(tp < tp_shift, 0.0)
    pos_sum  = pos_flow.rolling(window=periodo).sum()
    neg_sum  = neg_flow.rolling(window=periodo).sum().replace(0, 1e-10)
    return 100 - (100 / (1 + pos_sum / neg_sum))

def calcular_ssl_hybrid(df, periodo=20):
    sma_high = df['high'].rolling(window=periodo).mean()
    sma_low  = df['low'].rolling(window=periodo).mean()
    close_arr  = df['close'].values
    sma_h_arr  = sma_high.values
    sma_l_arr  = sma_low.values
    ssl_dir    = np.ones(len(df), dtype=int)
    current    = 1
    for i in range(len(df)):
        if np.isnan(sma_h_arr[i]) or np.isnan(sma_l_arr[i]):
            ssl_dir[i] = current
            continue
        if   close_arr[i] > sma_h_arr[i]: current = 1
        elif close_arr[i] < sma_l_arr[i]: current = -1
        ssl_dir[i] = current
    df['ssl_dir']      = ssl_dir
    df['SSL_Baseline'] = np.where(df['ssl_dir'] == 1, sma_high, sma_low)
    return df

def calcular_atr_stop(df, periodo=14, multiplicador=3.0):
    high, low, close = df['high'], df['low'], df['close']
    tr  = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low  - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    atr = tr.ewm(span=periodo, adjust=False).mean()
    atr_stop  = np.zeros(len(df))
    tendencia = np.zeros(len(df), dtype=int)
    close_arr = close.values
    atr_arr   = atr.values
    for i in range(1, len(df)):
        if i == 1:
            atr_stop[i]  = close_arr[i] - (atr_arr[i] * multiplicador)
            tendencia[i] = 1
            continue
        if tendencia[i-1] == 1:
            if close_arr[i] < atr_stop[i-1]:
                tendencia[i] = -1
                atr_stop[i]  = close_arr[i] + (atr_arr[i] * multiplicador)
            else:
                tendencia[i] = 1
                atr_stop[i]  = max(atr_stop[i-1], close_arr[i] - (atr_arr[i] * multiplicador))
        else:
            if close_arr[i] > atr_stop[i-1]:
                tendencia[i] = 1
                atr_stop[i]  = close_arr[i] - (atr_arr[i] * multiplicador)
            else:
                tendencia[i] = -1
                atr_stop[i]  = min(atr_stop[i-1], close_arr[i] + (atr_arr[i] * multiplicador))
    df['ATR_Stop'] = atr_stop
    df['atr_dir']  = tendencia
    return df

def calcular_alpha_trend(df, periodo=14, coeff=1.0):
    high, low, close = df['high'], df['low'], df['close']
    tr  = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low  - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    atr    = tr.rolling(window=periodo).mean()
    up_t   = low  - coeff * atr
    down_t = high + coeff * atr
    mfi    = df['MFI'].values
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
    maximas     = df['high'].values
    minimas     = df['low'].values
    bos_detectado   = 0
    choch_detectado = 0
    fvg_pendente    = 0
    for i in range(len(df) - 3, len(df) - 1):
        if minimas[i+1] > maximas[i-1]:
            fvg_pendente = 1
        elif maximas[i+1] < minimas[i-1]:
            fvg_pendente = -1
    topo_local  = np.max(fechamentos[-15:-2])
    fundo_local = np.min(fechamentos[-15:-2])
    if   fechamentos[-1] > topo_local: bos_detectado  = 1
    elif fechamentos[-1] < fundo_local: bos_detectado  = -1
    if   fechamentos[-1] > topo_local  and fechamentos[-2] <= topo_local: choch_detectado = 1
    elif fechamentos[-1] < fundo_local and fechamentos[-2] >= fundo_local: choch_detectado = -1
    df['SMC_BOS']   = bos_detectado
    df['SMC_CHOCH'] = choch_detectado
    df['SMC_FVG']   = fvg_pendente
    return df

def calcular_retracao_fibonacci(df):
    maxima = df['high'].max()
    minima = df['low'].min()
    diff   = maxima - minima
    return {
        'fib_0':   maxima,
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

def obter_marketcap_e_variacao(simbolo_id):
    """Busca dados atualizados do Ticker para extrair Variação e MarketCap"""
    var_24h = 0.0
    mcap = 0.0
    try:
        ticker = gateio_client.fetch_ticker(simbolo_id)
        if ticker:
            var_24h = ticker.get('percentage', 0.0)
            info_raw = ticker.get('info', {})
            # Gate.io retorna a capitalização como 'market_cap' ou 'marketCap' na estrutura interna 'info'
            mcap_bruto = info_raw.get('market_cap' if 'market_cap' in info_raw else 'marketCap', 0.0)
            mcap = float(mcap_bruto) if mcap_bruto else 0.0
    except Exception:
        pass
    return var_24h, mcap

# ─────────────────────────────────────────────────────────────
# CONFLUÊNCIA SMC
# ─────────────────────────────────────────────────────────────
def analisar_confluencia_smc_total(df, fib_niveis):
    u = df.iloc[-1]
    preco_atual  = u['close']
    pontos_alta  = 0.0
    pontos_baixa = 0.0
    
    if u['SMC_CHOCH'] == 1  or u['SMC_BOS'] == 1: pontos_alta  += 3
    if u['SMC_CHOCH'] == -1 or u['SMC_BOS'] == -1: pontos_baixa += 3
    if u['SMC_FVG'] == 1:   pontos_alta  += 1
    if u['SMC_FVG'] == -1: pontos_baixa += 1
    
    if preco_atual <= fib_niveis['fib_618']:
        pontos_alta  += 2.0
        contexto_fib  = txt["ctx_desconto"]
    elif preco_atual >= fib_niveis['fib_382']:
        pontos_baixa += 2.0
        contexto_fib  = txt["ctx_premium"]
    else:
        contexto_fib  = txt["ctx_neutro"]
        
    if u['CMF'] > 0:         pontos_alta  += 1.5
    else:                    pontos_baixa += 1.5
    if u['WT1'] > u['WT2']: pontos_alta  += 1
    else:                    pontos_baixa += 1
    if u['MACD_HIST'] > 0:  pontos_alta  += 1
    else:                    pontos_baixa += 1
    
    if pontos_alta >= 7.5:
        return txt["compra_forte"], "#00cc66", f"{contexto_fib} SMC Order Flow Bullish Structure.", pontos_alta, pontos_baixa
    elif pontos_baixa >= 7.5:
        return txt["venda_forte"], "#ff3333", f"{contexto_fib} SMC Order Flow Bearish Structure.", pontos_alta, pontos_baixa
    else:
        return txt["neutro"], "#ffcc00", contexto_fib, pontos_alta, pontos_baixa

# ─────────────────────────────────────────────────────────────
# GRÁFICO PRINCIPAL
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
    fig.add_trace(go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name="OHLC", increasing_line_color='#00cc66',
        decreasing_line_color='#ff3333'
    ), row=1, col=1)
    
    atr_colors = df['atr_dir'].apply(lambda d: '#00cc66' if d == 1 else '#ff3333')
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['ATR_Stop'], mode='markers',
        marker=dict(color=atr_colors, size=3), name="ATR Stop"
    ), row=1, col=1)
    
    ssl_colors = df['ssl_dir'].apply(lambda d: '#00aaff' if d == 1 else '#ff6600')
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['SSL_Baseline'], mode='lines',
        line=dict(width=1.5), marker=dict(color=ssl_colors), name="SSL Hybrid"
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['AT_K1'], mode='lines',
        line=dict(color='#aa44ff', width=1, dash='dot'), name="Alpha Trend"
    ), row=1, col=1)
    
    fib_cores = {
        'fib_0':   ('#ff4444', '0.0%'),  'fib_236': ('#ffaa00', '23.6%'),
        'fib_382': ('#ffdd00', '38.2%'), 'fib_500': ('#aaaaaa', '50.0%'),
        'fib_618': ('#00cc66', '61.8%'), 'fib_786': ('#00aaff', '78.6%'),
        'fib_100': ('#4444ff', '100%')
    }
    for chave, (cor, label) in fib_cores.items():
        fig.add_hline(
            y=fib_niveis[chave], line_dash="dot", line_color=cor,
            line_width=1, annotation_text=label,
            annotation_position="right", row=1, col=1
        )
        
    hist_colors = df['MACD_HIST'].apply(lambda v: '#00cc66' if v >= 0 else '#ff3333')
    fig.add_trace(go.Bar(x=df['time'], y=df['MACD_HIST'], marker_color=hist_colors, name="MACD Hist"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['MACD'], line=dict(color='#00aaff', width=1), name="MACD"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['MACD_SIGNAL'], line=dict(color='#ff6600', width=1), name="Signal"), row=2, col=1)
    
    fig.add_trace(go.Scatter(x=df['time'], y=df['RSI_14'], line=dict(color='#ffdd00', width=1.5), name="RSI 14"), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['StochRSI_K'], line=dict(color='#00cc66', width=1), name="Stoch K"), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['StochRSI_D'], line=dict(color='#ff4444', width=1), name="Stoch D"), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red",   line_width=0.8, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", line_width=0.8, row=3, col=1)
    
    cmf_colors = df['CMF'].apply(lambda v: '#00cc66' if v >= 0 else '#ff3333')
    fig.add_trace(go.Bar(x=df['time'], y=df['CMF'], marker_color=cmf_colors, name="CMF"), row=4, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['WT1'], line=dict(color='#00aaff', width=1), name="WT1"), row=4, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['WT2'], line=dict(color='#ffaa00', width=1), name="WT2"), row=4, col=1)
    
    fig.update_layout(
        height=800, paper_bgcolor='#0e1117', plot_bgcolor='#0e1117',
        font=dict(color='#ffffff', size=11), xaxis_rangeslider_visible=False,
        legend=dict(orientation='h', y=1.02, bgcolor='rgba(0,0,0,0)'),
        margin=dict(l=60, r=80, t=40, b=20)
    )
    fig.update_xaxes(gridcolor='#222', showgrid=True)
    fig.update_yaxes(gridcolor='#222', showgrid=True)
    return fig

# ─────────────────────────────────────────────────────────────
# MATRIZ DE INDICADORES
# ─────────────────────────────────────────────────────────────
def renderizar_matriz(df, txt):
    u = df.iloc[-1]
    st.markdown(f"### {txt['matriz_detalhada']}")
    
    def badge(condicao_alta, label_alta, label_baixa, valor_str=""):
        if condicao_alta:
            cor, sinal = "#00cc66", txt["alta"]
            label = label_alta
        else:
            cor, sinal = "#ff3333", txt["baixa"]
            label = label_baixa
        return f"""<span style='background:{cor}22;border:1px solid {cor};border-radius:6px;
            padding:3px 10px;color:{cor};font-size:13px;font-weight:600;'>{sinal}</span>
            &nbsp;<span style='color:#ccc;font-size:12px;'>{label} {valor_str}</span>"""

    def neutro_badge(label):
        return f"""<span style='background:#ffcc0022;border:1px solid #ffcc00;border-radius:6px;
            padding:3px 10px;color:#ffcc00;font-size:13px;font-weight:600;'>{txt['neutro_curto']}</span>
            &nbsp;<span style='color:#ccc;font-size:12px;'>{label}</span>"""

    b_bos = badge(u['SMC_BOS'] == 1, "Bullish Breakout", "Bearish Breakdown") if u['SMC_BOS'] != 0 else neutro_badge("Sem quebra recente")
    b_choch = badge(u['SMC_CHOCH'] == 1, "Mudança de Tendência (Alta)", "Mudança de Tendência (Baixa)") if u['SMC_CHOCH'] != 0 else neutro_badge("Sem alteração estrutural")
    b_fvg = badge(u['SMC_FVG'] == 1, "Gap de Alta Ativo", "Gap de Baixa Ativo") if u['SMC_FVG'] != 0 else neutro_badge("Gaps balanceados")
    b_ssl = badge(u['ssl_dir'] == 1, "Preço Acima da Baseline", "Preço Abaixo da Baseline")
    b_macd = badge(u['MACD_HIST'] >= 0, "Histograma Positivo", "Histograma Negativo", f"({u['MACD_HIST']:.4f})")
    b_cmf = badge(u['CMF'] >= 0, "Fluxo de Capital Comprador", "Fluxo de Capital Vendedor", f"({u['CMF']:.2f})")
    b_wt = badge(u['WT1'] > u['WT2'], "Gatilho WT Bullish Cross", "Gatilho WT Bearish Cross")
    b_rsi = badge(u['RSI_14'] < 70, "Abaixo de Sobrecompra", "Sobrecomprado (Risco)", f"({u['RSI_14']:.1f})")

    dados_matriz = {
        "Indicador / Mapeamento": [txt["bos"], txt["choch"], txt["fvg"], txt["ssl"], txt["macd_hist"], txt["cmf"], txt["wt"], txt["rsi"]],
        "Status Operacional": [b_bos, b_choch, b_fvg, b_ssl, b_macd, b_cmf, b_wt, b_rsi]
    }
    
    df_matriz = pd.DataFrame(dados_matriz)
    st.write(df_matriz.to_html(escape=False, index=False), unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# LOOP DE EXECUÇÃO PRINCIPAL (MAIN ENGINE)
# ─────────────────────────────────────────────────────────────
st.title(txt["titulo"])

st.sidebar.markdown(f"## {txt['config_globais']}")
todos_pares = obter_todos_pares_usdt()
par_selecionado = st.sidebar.selectbox(txt["selecione_cripto"], options=todos_pares, index=todos_pares.index("BTC/USDT") if "BTC/USDT" in todos_pares else 0)
timeframe = st.sidebar.selectbox(txt["tempo_grafico"], options=['1m', '5m', '15m', '1h', '4h', '1d'], index=3)
modo_live = st.sidebar.checkbox(txt["modo_vivo"], value=False)
intervalo = st.sidebar.slider(txt["intervalo_refresh"], min_value=5, max_value=60, value=10, step=5)

# Container fixo para renderizar dados sem acumular chaves ou clonar elementos na tela
placeholder_dashboard = st.container()

while True:
    df_dados = carregar_dados_bricsvault_smc(par_selecionado, timeframe)
    
    if df_dados is not None and not df_dados.empty:
        fib_niveis = calcular_retracao_fibonacci(df_dados)
        v24h, market_cap = obter_marketcap_e_variacao(par_selecionado)
        preco_atual = df_dados.iloc[-1]['close']
        stop_atr = df_dados.iloc[-1]['ATR_Stop']
        
        status, cor_status, desc_status, p_alta, p_baixa = analisar_confluencia_smc_total(df_dados, fib_niveis)
        
        # .empty() limpa o bloco inteiro antes de cada redesenho em tempo real
        with placeholder_dashboard:
            placeholder_dashboard.empty()
            
            # Métricas em 5 colunas estruturadas
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric(txt["preco_spot"], formatar_preco(preco_atual))
            c2.metric(txt["variacao_24h"], f"{v24h:+.2f}%")
            c3.metric(txt["market_cap"], formatar_marketcap(market_cap))
            c4.metric(txt["stop_atr"], formatar_preco(stop_atr))
            
            with c5:
                st.markdown(f"""
                <div style='background:{cor_status}15; border:2px solid {cor_status}; border-radius:10px; padding:12px; text-align:center;'>
                    <h4 style='margin:0; color:{cor_status}; font-size:14px;'>{txt['resumo_confluencia']}</h4>
                    <p style='margin:5px 0; font-size:16px; font-weight:bold; color:{cor_status};'>{status}</p>
                    <span style='font-size:11px; color:#aaa;'>🟢 +{p_alta:.1f} | 🔴 +{p_baixa:.1f}</span>
                </div>
                """, unsafe_allow_html=True)
                
            st.info(desc_status)
            
            figura_dinamica = construir_grafico(df_dados, fib_niveis, par_selecionado)
            
            # Adicionado timestamp int(time.time()) para forçar chaves únicas em cada ciclo do loop
            st.plotly_chart(figura_dinamica, key=f"chart_{par_selecionado}_{timeframe}_{int(time.time())}")
            
            col_esq, col_dir = st.columns([1, 1])
            
            with col_esq:
                st.markdown(f"### {txt['fib_niveis_titulo']}")
                dados_fib = {
                    "Nível": txt["fib_nomes"],
                    "Região Interna": txt["fib_posicoes"],
                    "Preço de Alvo": [formatar_preco(fib_niveis[k]) for k in ['fib_0', 'fib_236', 'fib_382', 'fib_500', 'fib_618', 'fib_786', 'fib_100']]
                }
                st.table(pd.DataFrame(dados_fib))
                
            with col_dir:
                renderizar_matriz(df_dados, txt)
                
            st.markdown(f"⏱️ *{txt['ultima_atualizacao']}: {time.strftime('%H:%M:%S')}*")
            
    else:
        st.error(txt["erro_dados"])
        
    if not modo_live:
        break
        
    time.sleep(intervalo)
