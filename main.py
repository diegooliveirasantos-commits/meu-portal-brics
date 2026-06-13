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

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="BRICSVAULT PORTAL SMC",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dicionário de tradução simplificado
txt = {
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
    "compra_forte": "🟢 COMPRA FORTE",
    "venda_forte": "🔴 VENDA FORTE",
    "neutro": "🟡 NEUTRO",
    "erro_dados": "Dados históricos insuficientes. Escolha outro Ativo ou reduza o Tempo Gráfico.",
    "ctx_desconto": "Ativo em Zona de Desconto de Fibonacci.",
    "ctx_premium": "Ativo em Zona Premium de Fibonacci.",
    "ctx_neutro": "Preço em zona neutra de equilíbrio.",
    "ultima_atualizacao": "Última Atualização",
    "proximo_refresh": "Próximo refresh em",
    "segundos": "segundos",
    "pontos_compra": "Pontos de Compra",
    "pontos_venda": "Pontos de Venda",
    "grafico_titulo": "📈 Gráfico de Preço com Indicadores SMC",
}

def formatar_preco(valor, prefixo="$ "):
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

# Conexão com Exchange
@st.cache_resource
def inicializar_exchange():
    return ccxt.gate({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})

gateio_client = inicializar_exchange()

@st.cache_data(ttl=3600)
def obter_todos_pares_usdt():
    try:
        mercados = gateio_client.load_markets()
        return sorted([s for s in mercados.keys() if s.endswith('/USDT')])
    except Exception:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]

# Função aprimorada para obter Market Cap
@st.cache_data(ttl=300)
def obter_market_cap_para_simbolo(simbolo_usdt):
    """
    Obtém o market cap usando a API da CoinGecko.
    Primeiro tenta pelo nome da moeda, depois faz uma busca geral.
    """
    try:
        moeda_base = simbolo_usdt.split('/')[0].lower()
        
        # Método 1: Buscar lista de moedas e encontrar o ID correto
        url_lista = "https://api.coingecko.com/api/v3/coins/list"
        response_lista = requests.get(url_lista, timeout=10)
        
        if response_lista.status_code == 200:
            lista_moedas = response_lista.json()
            
            # Procurar pelo símbolo exato
            coin_id = None
            for moeda in lista_moedas:
                if moeda['symbol'].lower() == moeda_base:
                    coin_id = moeda['id']
                    break
            
            if coin_id:
                # Método 2: Obter dados detalhados da moeda
                url_dados = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&community_data=false&developer_data=false"
                response_dados = requests.get(url_dados, timeout=10)
                
                if response_dados.status_code == 200:
                    dados = response_dados.json()
                    market_cap = dados.get('market_data', {}).get('market_cap', {}).get('usd')
                    if market_cap:
                        return market_cap
        
        # Método 3: Tentar busca direta por symbol
        url_busca = f"https://api.coingecko.com/api/v3/search?query={moeda_base}"
        response_busca = requests.get(url_busca, timeout=10)
        
        if response_busca.status_code == 200:
            dados_busca = response_busca.json()
            coins = dados_busca.get('coins', [])
            
            for coin in coins:
                if coin['symbol'].lower() == moeda_base:
                    coin_id = coin['id']
                    url_dados = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&community_data=false&developer_data=false"
                    response_dados = requests.get(url_dados, timeout=10)
                    
                    if response_dados.status_code == 200:
                        dados = response_dados.json()
                        market_cap = dados.get('market_data', {}).get('market_cap', {}).get('usd')
                        if market_cap:
                            return market_cap
        
        return None
        
    except Exception as e:
        return None

# Indicadores
def calcular_rsi(df, col, periodo=14):
    delta = df[col].diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    ma_ganho = ganho.ewm(span=periodo, adjust=False).mean()
    ma_perda = perda.ewm(span=periodo, adjust=False).mean()
    return 100 - (100 / (1 + (ma_ganho / ma_perda.replace(0, 1e-10))))

def calcular_macd(df, col):
    ema_rapida = df[col].ewm(span=12, adjust=False).mean()
    ema_lenta = df[col].ewm(span=26, adjust=False).mean()
    macd = ema_rapida - ema_lenta
    sinal = macd.ewm(span=9, adjust=False).mean()
    return macd, sinal, macd - sinal

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
    tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
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

def carregar_dados(simbolo_id, timeframe_selecionado):
    try:
        velas = gateio_client.fetch_ohlcv(simbolo_id, timeframe=timeframe_selecionado, limit=200)
        if not velas:
            return None
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['RSI_14'] = calcular_rsi(df, 'close', 14)
        macd, sinal, hist = calcular_macd(df, 'close')
        df['MACD'] = macd
        df['MACD_SIGNAL'] = sinal
        df['MACD_HIST'] = hist
        df['MFI'] = calcular_mfi(df)
        df = calcular_ssl_hybrid(df)
        df = calcular_atr_stop(df)
        return df.dropna(subset=['close', 'SSL_Baseline'])
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

def obter_variacao_24h(simbolo_id):
    try:
        dados_24h = gateio_client.fetch_ohlcv(simbolo_id, timeframe='1d', limit=2)
        if dados_24h and len(dados_24h) >= 2:
            close_hoje = dados_24h[-1][4]
            close_ontem = dados_24h[-2][4]
            return ((close_hoje - close_ontem) / close_ontem) * 100
    except Exception:
        pass
    return 0.0

def analisar_confluencia(df, fib_niveis):
    u = df.iloc[-1]
    preco_atual = u['close']
    pontos_alta = 0.0
    pontos_baixa = 0.0
    
    if u['RSI_14'] < 40:
        pontos_alta += 2
    elif u['RSI_14'] > 60:
        pontos_baixa += 2
    
    if u['MACD_HIST'] > 0:
        pontos_alta += 2
    else:
        pontos_baixa += 2
    
    if u['MFI'] > 50:
        pontos_alta += 1
    else:
        pontos_baixa += 1
    
    if u['ssl_dir'] == 1:
        pontos_alta += 1
    else:
        pontos_baixa += 1
    
    if u['atr_dir'] == 1:
        pontos_alta += 1
    else:
        pontos_baixa += 1
    
    if preco_atual <= fib_niveis['fib_618']:
        pontos_alta += 2.0
        contexto_fib = txt["ctx_desconto"]
    elif preco_atual >= fib_niveis['fib_382']:
        pontos_baixa += 2.0
        contexto_fib = txt["ctx_premium"]
    else:
        contexto_fib = txt["ctx_neutro"]
    
    if pontos_alta >= 7.5:
        return txt["compra_forte"], "#00cc66", f"{contexto_fib} Estrutura Bullish.", pontos_alta, pontos_baixa
    elif pontos_baixa >= 7.5:
        return txt["venda_forte"], "#ff3333", f"{contexto_fib} Estrutura Bearish.", pontos_alta, pontos_baixa
    else:
        return txt["neutro"], "#ffcc00", contexto_fib, pontos_alta, pontos_baixa

def construir_grafico(df, fib_niveis, simbolo_id):
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.5, 0.25, 0.25],
        vertical_spacing=0.05,
        subplot_titles=(f"{simbolo_id} - Preço", "RSI", "MACD")
    )
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name="OHLC"
    ), row=1, col=1)
    
    # SSL Baseline
    ssl_colors = df['ssl_dir'].apply(lambda d: '#00aaff' if d == 1 else '#ff6600')
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['SSL_Baseline'],
        mode='lines', line=dict(width=1.5),
        marker=dict(color=ssl_colors), name="SSL"
    ), row=1, col=1)
    
    # ATR Stop
    atr_colors = df['atr_dir'].apply(lambda d: '#00cc66' if d == 1 else '#ff3333')
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['ATR_Stop'],
        mode='markers', marker=dict(color=atr_colors, size=3),
        name="ATR Stop"
    ), row=1, col=1)
    
    # Fibonacci
    for chave, cor in [('fib_0', 'red'), ('fib_236', 'orange'), ('fib_382', 'yellow'),
                        ('fib_500', 'gray'), ('fib_618', 'green'), ('fib_786', 'blue'), ('fib_100', 'purple')]:
        fig.add_hline(y=fib_niveis[chave], line_dash="dot", line_color=cor, line_width=1, row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['RSI_14'],
        line=dict(color='yellow', width=1.5), name="RSI 14"
    ), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", line_width=0.8, row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", line_width=0.8, row=2, col=1)
    
    # MACD
    hist_colors = df['MACD_HIST'].apply(lambda v: 'green' if v >= 0 else 'red')
    fig.add_trace(go.Bar(
        x=df['time'], y=df['MACD_HIST'],
        marker_color=hist_colors, name="MACD Hist"
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['MACD'],
        line=dict(color='blue', width=1), name="MACD"
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['MACD_SIGNAL'],
        line=dict(color='orange', width=1), name="Signal"
    ), row=3, col=1)
    
    fig.update_layout(
        height=800,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        margin=dict(l=60, r=60, t=40, b=20)
    )
    
    return fig

# ========== INTERFACE PRINCIPAL ==========
st.title(txt["titulo"])

# Sidebar
st.sidebar.header(txt["config_globais"])
lista_criptos = obter_todos_pares_usdt()
simbolo_id = st.sidebar.selectbox(
    txt["selecione_cripto"],
    lista_criptos,
    index=lista_criptos.index("SOL/USDT") if "SOL/USDT" in lista_criptos else 0
)

intervalos = {
    "1 Minuto": "1m", "5 Minutos": "5m", "15 Minutos": "15m",
    "30 Minutos": "30m", "1 Hora": "1h", "4 Horas": "4h",
    "1 Dia": "1d", "1 Semana": "1w"
}
intervalo_escolhido = st.sidebar.selectbox(txt["tempo_grafico"], list(intervalos.keys()), index=5)
timeframe = intervalos[intervalo_escolhido]

st.sidebar.markdown("---")
modo_vivo = st.sidebar.toggle(txt["modo_vivo"], value=False)
intervalo_refresh = st.sidebar.slider(txt["intervalo_refresh"], min_value=5, max_value=60, value=15)

# Carregar dados
status_placeholder = st.empty()
df_dados = carregar_dados(simbolo_id, timeframe)

if df_dados is None or df_dados.empty:
    st.warning(txt["erro_dados"])
else:
    ultimo_reg = df_dados.iloc[-1]
    preco_atual = ultimo_reg['close']
    fib_niveis = calcular_retracao_fibonacci(df_dados)
    variacao_24h = obter_variacao_24h(simbolo_id)
    
    # Mostrar spinner enquanto carrega o market cap
    with st.spinner('Carregando Market Cap...'):
        market_cap = obter_market_cap_para_simbolo(simbolo_id)
    
    recomendacao, cor_sinal, analise, pontos_alta, pontos_baixa = analisar_confluencia(df_dados, fib_niveis)
    
    # Painel de recomendação
    st.markdown(f"""
    <div style="background:{cor_sinal}22;padding:20px;border-radius:10px;border:2px solid {cor_sinal};margin-bottom:20px;">
        <h2 style="margin:0;color:{cor_sinal};">{recomendacao}</h2>
        <p style="margin:8px 0 0 0;color:#ddd;">{analise}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(txt["preco_spot"], formatar_preco(preco_atual))
    m2.metric(txt["variacao_24h"], f"{variacao_24h:+.2f}%")
    m3.metric(txt["market_cap"], formatar_market_cap(market_cap))
    m4.metric(txt["pontos_compra"], f"{pontos_alta:.1f}")
    m5.metric(txt["pontos_venda"], f"{pontos_baixa:.1f}")
    
    # Gráfico
    st.markdown(f"### {txt['grafico_titulo']}")
    fig = construir_grafico(df_dados, fib_niveis, simbolo_id)
    st.plotly_chart(fig, use_container_width=True)
    
    # Status
    hora_atual = pd.Timestamp.now().strftime("%H:%M:%S")
    if modo_vivo:
        status_placeholder.info(f"🟢 {txt['ultima_atualizacao']}: {hora_atual} | {txt['proximo_refresh']} {intervalo_refresh} {txt['segundos']}")
        time.sleep(intervalo_refresh)
        st.rerun()
    else:
        status_placeholder.info(f"⏸ {txt['ultima_atualizacao']}: {hora_atual}")
