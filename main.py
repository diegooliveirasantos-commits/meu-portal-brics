import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import time
import requests
import math
from decimal import Decimal
import json
import re
from bs4 import BeautifulSoup
from streamlit_lightweight_charts import renderLightweightCharts

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="BRICSVAULT PORTAL SMC",
    page_icon=" 🏦 ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sistema completo de tradução multilíngue
DICIONARIO_LINGUAS = {
    "Português (BR)": {
        "titulo": " 🏦  BRICSVAULT PORTAL - Motor de Smart Money Concepts (SMC)",
        "config_globais": " ⚙️  Configurações Globais",
        "selecione_cripto": "Selecione Qualquer Criptomoeda (/USDT):",
        "tempo_grafico": "Tempo Gráfico:",
        "modo_vivo": "Ativar Monitoramento em Tempo Real",
        "intervalo_refresh": "Intervalo de Atualização (Segundos):",
        "preco_spot": "Preço Spot Real",
        "variacao_24h": "Variação 24h (Exchange)",
        "market_cap": "Market Cap (USD)",
        "stop_atr": "Preço Stop ATR",
        "compra_forte": " 🟢  COMPRA FORTE (SMC + FIBONACCI ALINHADOS)",
        "venda_forte": " 🔴  VENDA FORTE (SMC + FIBONACCI ALINHADOS)",
        "neutro": " 🟡  NEUTRO (AGUARDAR SMC)",
        "erro_dados": "Dados históricos insuficientes nesta Exchange para calcular a confluência estrutural SMC. Escolha outro Ativo ou reduza o Tempo Gráfico.",
        "ctx_desconto": "Ativo posicionado em Zona de Desconto de Fibonacci (Excelente risco/retorno para Institucionais).",
        "ctx_premium": "Ativo posicionado em Zona Premium de Fibonacci (Preço esticado, propício para realização de lucro).",
        "ctx_neutro": "Preço em zona neutra de equilíbrio de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Última Atualização",
        "proximo_refresh": "Próximo refresh em",
        "segundos": "segundos",
        "pontos_compra": "Pontos de Compra",
        "pontos_venda": "Pontos de Venda",
        "grafico_titulo": " 📈  Gráfico de Preço Interativo (TradingView Engine)",
        "buscando_marketcap": " 🔍  Buscando Market Cap em USD...",
        "marketcap_nao_disponivel": "Não disponível",
        "idioma_label": " 🌐  Language / Idioma / Langue / Sprache / Lingua / Язык /  语言  /  भाषा ",
        "idioma_selecao": "Selecione o idioma da interface:",
    },
    "English (EN)": {
        "titulo": " 🏦  BRICSVAULT PORTAL - Smart Money Concepts (SMC) Engine",
        "config_globais": " ⚙️  Global Settings",
        "selecione_cripto": "Select Any Cryptocurrency (/USDT):",
        "tempo_grafico": "Timeframe:",
        "modo_vivo": "Enable Real-Time Monitoring",
        "intervalo_refresh": "Refresh Interval (Seconds):",
        "preco_spot": "Real Spot Price",
        "variacao_24h": "24h Variation (Exchange)",
        "market_cap": "Market Cap (USD)",
        "stop_atr": "ATR Stop Price",
        "compra_forte": " 🟢  STRONG BUY (SMC + FIBONACCI ALIGNED)",
        "venda_forte": " 🔴  STRONG SELL (SMC + FIBONACCI ALIGNED)",
        "neutro": " 🟡  NEUTRAL (AWAIT SMC)",
        "erro_dados": "Insufficient historical data on this Exchange to calculate SMC structural confluence. Choose another Asset or reduce the Timeframe.",
        "ctx_desconto": "Asset positioned in Fibonacci Discount Zone (Excellent risk/reward for Institutionals).",
        "ctx_premium": "Asset positioned in Fibonacci Premium Zone (Price stretched, suitable for profit-taking).",
        "ctx_neutro": "Price in neutral Fibonacci equilibrium zone (Fair Value Zone).",
        "ultima_atualizacao": "Last Update",
        "proximo_refresh": "Next refresh in",
        "segundos": "seconds",
        "pontos_compra": "Buy Points",
        "pontos_venda": "Sell Points",
        "grafico_titulo": " 📈  Interactive Price Chart (TradingView Engine)",
        "buscando_marketcap": " 🔍  Searching Market Cap in USD...",
        "marketcap_nao_disponivel": "Not available",
        "idioma_label": " 🌐  Language / Idioma / Langue / Sprache / Lingua / Язык /  语言  /  भाषा ",
        "idioma_selecao": "Select Interface Language:",
    }
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
    else:
        return f"{prefixo}{valor:,.2f}"


def formatar_market_cap(valor):
    if valor is None:
        return "$ —"
    if isinstance(valor, str):
        try:
            valor = float(valor.replace('$', '').replace(',', '').replace(' ', '').strip())
        except:
            return "$ —"
    if valor <= 0:
        return "$ —"
    if valor >= 1_000_000_000_000:
        return f"$ {valor / 1_000_000_000_000:.2f}T"
    elif valor >= 1_000_000_000:
        return f"$ {valor / 1_000_000_000:.2f}B"
    elif valor >= 1_000_000:
        return f"$ {valor / 1_000_000:.2f}M"
    elif valor >= 1_000:
        return f"$ {valor / 1_000:.2f}K"
    else:
        return f"$ {valor:,.2f}"


@st.cache_resource
def inicializar_exchange():
    return ccxt.gate({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})


gateio_client = inicializar_exchange()


# CORREÇÃO: Removido @st.cache_data para evitar UnhashableParamError com ccxt
def obter_todos_pares_usdt():
    try:
        mercados = gateio_client.load_markets()
        return sorted([s for s in mercados.keys() if s.endswith('/USDT')])
    except Exception:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]


@st.cache_data(ttl=3600)
def obter_nome_extenso_cripto(simbolo_id):
    """Busca o nome real por extenso da moeda através da API do Gate.io"""
    try:
        base_currency = simbolo_id.split('/')[0]
        url = "https://api.gateio.ws/api/v4/spot/currencies"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            dados = response.json()
            for moeda in dados:
                if moeda.get('currency', '').upper() == base_currency.upper():
                    return moeda.get('name', base_currency).upper()
        return base_currency
    except Exception:
        return simbolo_id.split('/')[0]


@st.cache_data(ttl=300)
def obter_market_cap_coingecko(simbolo):
    try:
        url_lista = "https://api.coingecko.com/api/v3/coins/list"
        response = requests.get(url_lista, timeout=15)
        if response.status_code == 200:
            moedas = response.json()
            simbolo_lower = simbolo.lower()
            coin_id = next((m['id'] for m in moedas if m.get('symbol', '') == simbolo_lower), None)
            if coin_id:
                url_dados = (
                    f"https://api.coingecko.com/api/v3/coins/{coin_id}"
                    f"?localization=false&tickers=false&community_data=false&developer_data=false"
                )
                res = requests.get(url_dados, timeout=15)
                if res.status_code == 200:
                    return float(res.json().get('market_data', {}).get('market_cap', {}).get('usd', 0))
        return None
    except:
        return None


@st.cache_data(ttl=300)
def obter_market_cap_coinmarketcap(simbolo):
    # CORREÇÃO: Headers mais robustos para evitar bloqueio 403
    try:
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept-Language': 'en-US,en;q=0.9',
        }
        url = f"https://coinmarketcap.com/currencies/{simbolo.lower()}/"
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup.find_all('script'):
                if script.string and 'marketCap' in script.string:
                    match = re.search(r'"marketCap":(\d+\.?\d*)', script.string)
                    if match:
                        return float(match.group(1))
        return None
    except:
        return None


def obter_market_cap_robusto(simbolo_id):
    simbolo = simbolo_id.split('/')[0]
    for funcao in [obter_market_cap_coingecko, obter_market_cap_coinmarketcap]:
        res = funcao(simbolo)
        if res and res > 0:
            return float(res)
    # Fallback: usar ticker 24h da exchange
    try:
        ticker = gateio_client.fetch_ticker(simbolo_id)
        if ticker and ticker.get('quoteVolume', 0) > 0:
            return float(ticker.get('quoteVolume') * 500)
    except:
        pass
    return None


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
    high = df['high']
    low = df['low']
    close = df['close']
    tr = pd.concat(
        [high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()],
        axis=1
    ).max(axis=1)
    atr = tr.ewm(span=periodo, adjust=False).mean()
    atr_stop = np.zeros(len(df))
    tendencia = np.zeros(len(df), dtype=int)
    close_arr = close.values
    atr_arr = atr.values

    # CORREÇÃO: Inicialização correta do estado da primeira vela
    if len(df) > 0:
        atr_stop[0] = close_arr[0] - (atr_arr[0] * multiplicador) if not np.isnan(atr_arr[0]) else close_arr[0]
        tendencia[0] = 1

    for i in range(1, len(df)):
        if np.isnan(atr_arr[i]):
            atr_stop[i] = atr_stop[i - 1]
            tendencia[i] = tendencia[i - 1]
            continue
        if tendencia[i - 1] == 1:
            if close_arr[i] < atr_stop[i - 1]:
                tendencia[i] = -1
                atr_stop[i] = close_arr[i] + (atr_arr[i] * multiplicador)
            else:
                tendencia[i] = 1
                atr_stop[i] = max(atr_stop[i - 1], close_arr[i] - (atr_arr[i] * multiplicador))
        else:
            if close_arr[i] > atr_stop[i - 1]:
                tendencia[i] = 1
                atr_stop[i] = close_arr[i] - (atr_arr[i] * multiplicador)
            else:
                tendencia[i] = -1
                atr_stop[i] = min(atr_stop[i - 1], close_arr[i] + (atr_arr[i] * multiplicador))

    df['ATR_Stop'] = atr_stop
    df['atr_dir'] = tendencia
    return df


def calcular_ppo(df, col='close', rapido=12, lento=26, sinal_periodo=9):
    ema_rapida = df[col].ewm(span=rapido, adjust=False).mean()
    ema_lenta = df[col].ewm(span=lento, adjust=False).mean()
    df['PPO'] = ((ema_rapida - ema_lenta) / ema_lenta) * 100
    df['PPO_Signal'] = df['PPO'].ewm(span=sinal_periodo, adjust=False).mean()
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
        df = calcular_ppo(df)
        # CORREÇÃO: dropna aplicado apenas na coluna 'close'; SSL_Baseline pode ter NaN
        # nas primeiras linhas por causa do rolling, preenchemos com forward fill
        df['SSL_Baseline'] = df['SSL_Baseline'].ffill()
        df['ATR_Stop'] = df['ATR_Stop'].replace(0, np.nan).ffill()
        return df.dropna(subset=['close'])
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None


def obter_variacao_24h(simbolo_id):
    # CORREÇÃO: Fallback ao ticker 24h quando OHLCV diário é insuficiente
    try:
        dados_24h = gateio_client.fetch_ohlcv(simbolo_id, timeframe='1d', limit=2)
        if dados_24h and len(dados_24h) >= 2:
            return ((dados_24h[-1][4] - dados_24h[-2][4]) / dados_24h[-2][4]) * 100
    except:
        pass
    try:
        ticker = gateio_client.fetch_ticker(simbolo_id)
        if ticker and ticker.get('percentage') is not None:
            return float(ticker['percentage'])
    except:
        pass
    return 0.0


def analisar_confluencia(df, fib_niveis, txt):
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

    if u['PPO'] > u['PPO_Signal']:
        pontos_alta += 1.5
    else:
        pontos_baixa += 1.5

    if preco_atual <= fib_niveis['fib_618']:
        pontos_alta += 2.0
        contexto_fib = txt["ctx_desconto"]
    elif preco_atual >= fib_niveis['fib_382']:
        pontos_baixa += 2.0
        contexto_fib = txt["ctx_premium"]
    else:
        contexto_fib = txt["ctx_neutro"]

    if pontos_alta >= 8.5:
        return txt["compra_forte"], "#00cc66", f"{contexto_fib} SMC + PPO Order Flow Bullish.", pontos_alta, pontos_baixa
    elif pontos_baixa >= 8.5:
        return txt["venda_forte"], "#ff3333", f"{contexto_fib} SMC + PPO Order Flow Bearish.", pontos_alta, pontos_baixa
    else:
        return txt["neutro"], "#ffcc00", contexto_fib, pontos_alta, pontos_baixa


# ─────────────────────────────────────────────
# EXECUÇÃO DO PORTAL
# ─────────────────────────────────────────────
st.sidebar.markdown(f"### {DICIONARIO_LINGUAS['Português (BR)']['idioma_label']}")
idioma_selecionado = st.sidebar.selectbox(
    DICIONARIO_LINGUAS['Português (BR)']['idioma_selecao'],
    options=list(DICIONARIO_LINGUAS.keys()),
    index=0
)
txt = DICIONARIO_LINGUAS[idioma_selecionado]
st.title(txt["titulo"])
st.sidebar.header(txt["config_globais"])

lista_criptos = obter_todos_pares_usdt()
simbolo_id = st.sidebar.selectbox(
    txt["selecione_cripto"],
    lista_criptos,
    index=lista_criptos.index("SOL/USDT") if "SOL/USDT" in lista_criptos else 0
)

intervalos = {
    "1 Minuto": "1m",
    "5 Minutos": "5m",
    "15 Minutos": "15m",
    "30 Minutos": "30m",
    "1 Hora": "1h",
    "4 Horas": "4h",
    "1 Dia": "1d",
    "1 Semana": "1w"
}
intervalo_escolhido = st.sidebar.selectbox(txt["tempo_grafico"], list(intervalos.keys()), index=5)
timeframe = intervalos[intervalo_escolhido]
st.sidebar.markdown("---")
modo_vivo = st.sidebar.toggle(txt["modo_vivo"], value=False)
intervalo_refresh = st.sidebar.slider(txt["intervalo_refresh"], min_value=5, max_value=60, value=15)

status_placeholder = st.empty()
df_dados = carregar_dados(simbolo_id, timeframe)

if df_dados is None or df_dados.empty:
    st.warning(txt["erro_dados"])
else:
    ultimo_reg = df_dados.iloc[-1]
    preco_atual = ultimo_reg['close']
    fib_niveis = calcular_retracao_fibonacci(df_dados)
    variacao_24h = obter_variacao_24h(simbolo_id)

    with st.spinner(txt["buscando_marketcap"]):
        market_cap = obter_market_cap_robusto(simbolo_id)

    recomendacao, cor_sinal, analise, pontos_alta, pontos_baixa = analisar_confluencia(df_dados, fib_niveis, txt)

    st.markdown(f"""
    <div style="background:{cor_sinal}22;padding:20px;border-radius:10px;border:2px solid {cor_sinal};margin-bottom:20px;">
    <h2 style="margin:0;color:{cor_sinal};">{recomendacao}</h2>
    <p style="margin:8px 0 0 0;color:#ddd;">{analise} | <b>PPO Check:</b> Line {ultimo_reg['PPO']:.3f} / Signal {ultimo_reg['PPO_Signal']:.3f}</p>
    </div>
    """, unsafe_allow_html=True)

    nome_completo_ativo = obter_nome_extenso_cripto(simbolo_id)
    label_customizado_preco = f"{nome_completo_ativo} | {txt['preco_spot']}"

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(label_customizado_preco, formatar_preco(preco_atual))
    m2.metric(txt["variacao_24h"], f"{variacao_24h:+.2f}%")

    if market_cap is not None:
        m3.metric(txt["market_cap"], formatar_market_cap(market_cap))
    else:
        m3.metric(txt["market_cap"], txt["marketcap_nao_disponivel"])

    m4.metric(txt["pontos_compra"], f"{pontos_alta:.1f}")
    m5.metric(txt["pontos_venda"], f"{pontos_baixa:.1f}")

    # GRÁFICO PROFISSIONAL INTERATIVO LIGHTWEIGHT CHARTS (TRADINGVIEW)
    st.markdown(f"### {txt['grafico_titulo']}")

    df_tv = df_dados.reset_index(drop=True)

    # CORREÇÃO: Lightweight Charts exige timestamps Unix em segundos (inteiros)
    df_tv['time_unix'] = (df_tv['timestamp'] // 1000).astype(int)

    velas_tv = df_tv[['time_unix', 'open', 'high', 'low', 'close']].rename(
        columns={'time_unix': 'time'}
    ).to_dict(orient='records')

    ssl_tv = df_tv[['time_unix', 'SSL_Baseline']].rename(
        columns={'time_unix': 'time', 'SSL_Baseline': 'value'}
    ).dropna().to_dict(orient='records')

    atr_tv = df_tv[['time_unix', 'ATR_Stop']].rename(
        columns={'time_unix': 'time', 'ATR_Stop': 'value'}
    ).dropna().to_dict(orient='records')

    config_visual_grafico = {
        "layout": {"textColor": '#e2e8f0', "background": {"type": 'solid', "color": '#0b0f19'}},
        "grid": {"vertLines": {"color": '#1e293b'}, "horzLines": {"color": '#1e293b'}},
        "crosshair": {"mode": 0},
        "priceScale": {"borderColor": '#475569'},
        "timeScale": {"borderColor": '#475569', "timeVisible": True}
    }

    camadas_do_grafico = [
        {
            "type": "Candlestick",
            "data": velas_tv,
            "options": {
                "upColor": '#10b981',
                "downColor": '#ef4444',
                "borderVisible": False,
                "wickUpColor": '#10b981',
                "wickDownColor": '#ef4444'
            }
        },
        {
            "type": "Line",
            "data": ssl_tv,
            "options": {"color": '#00aaff', "lineWidth": 2, "title": "SMC Baseline"}
        },
        {
            "type": "Line",
            "data": atr_tv,
            "options": {"color": '#ffaa00', "lineWidth": 1, "lineStyle": 2, "title": "ATR Trailing"}
        }
    ]

    renderLightweightCharts(
        [{"chart": config_visual_grafico, "series": camadas_do_grafico}],
        'bricsvault_tv_chart'
    )

    hora_atual = pd.Timestamp.now().strftime("%H:%M:%S")
    if modo_vivo:
        status_placeholder.info(
            f" 🟢  {txt['ultima_atualizacao']}: {hora_atual} | "
            f"{txt['proximo_refresh']} {intervalo_refresh} {txt['segundos']}"
        )
        time.sleep(intervalo_refresh)
        st.rerun()
    else:
        status_placeholder.info(f" ⏸  {txt['ultima_atualizacao']}: {hora_atual}")
