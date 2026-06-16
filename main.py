import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import time
import requests
import math
from decimal import Decimal
import re
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(
    page_title="BRICSVAULT PORTAL SMC",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES DE AQUECIMENTO
# Os indicadores técnicos precisam de um número mínimo de velas para "aquecer"
# antes de produzirem valores matematicamente corretos:
#   RSI(14)       → 14 períodos
#   MACD(12,26,9) → 26 + 9 = 35 períodos
#   SSL(20)       → 20 períodos
#   ATR(14)       → 14 períodos
#   PPO(12,26,9)  → 26 + 9 = 35 períodos
#   MFI(14)       → 14 períodos
# Usamos 100 como margem segura. Carregamos 500 velas e descartamos as
# primeiras 100 apenas para o cálculo do SINAL (não para o gráfico).
VELAS_TOTAL = 500
PERIODO_AQUECIMENTO = 100

# ─────────────────────────────────────────────────────────────────────────────
# DICIONÁRIO DE IDIOMAS
DICIONARIO_LINGUAS = {
    "Português (BR)": {
        "titulo": "🏦  BRICSVAULT PORTAL - Motor de Smart Money Concepts (SMC)",
        "config_globais": "⚙️  Configurações Globais",
        "selecione_cripto": "Selecione Qualquer Criptomoeda (/USDT):",
        "tempo_grafico": "Tempo Gráfico:",
        "modo_vivo": "Ativar Monitoramento em Tempo Real",
        "intervalo_refresh": "Intervalo de Atualização (Segundos):",
        "preco_spot": "Preço Spot Real",
        "variacao_24h": "Variação 24h (Exchange)",
        "market_cap": "Market Cap (USD)",
        "stop_atr": "Preço Stop ATR",
        "compra_forte": "🟢  COMPRA FORTE (SMC + FIBONACCI ALINHADOS)",
        "venda_forte": "🔴  VENDA FORTE (SMC + FIBONACCI ALINHADOS)",
        "neutro": "🟡  NEUTRO (AGUARDAR SMC)",
        "erro_dados": "Dados históricos insuficientes nesta Exchange. Escolha outro ativo ou reduza o Tempo Gráfico.",
        "ctx_desconto": "Ativo em Zona de Desconto de Fibonacci (Excelente risco/retorno para Institucionais).",
        "ctx_premium": "Ativo em Zona Premium de Fibonacci (Preço esticado, propício para realização de lucro).",
        "ctx_neutro": "Preço em zona neutra de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Última Atualização",
        "proximo_refresh": "Próximo refresh em",
        "segundos": "segundos",
        "pontos_compra": "Pontos de Compra",
        "pontos_venda": "Pontos de Venda",
        "grafico_titulo": "📈  Gráfico de Preço Interativo",
        "buscando_marketcap": "🔍  Buscando Market Cap...",
        "marketcap_nao_disponivel": "Não disponível",
        "idioma_label": "🌐  Idioma / Language",
        "idioma_selecao": "Selecione o idioma da interface:",
        "aviso_aquecimento": "⚠️ Velas de aquecimento usadas no cálculo",
        "intervalos": {
            "1 Minuto": "1m",
            "5 Minutos": "5m",
            "15 Minutos": "15m",
            "30 Minutos": "30m",
            "1 Hora": "1h",
            "4 Horas": "4h",
            "1 Dia": "1d",
            "1 Semana": "1w"
        }
    },
    "English (EN)": {
        "titulo": "🏦  BRICSVAULT PORTAL - Smart Money Concepts (SMC) Engine",
        "config_globais": "⚙️  Global Settings",
        "selecione_cripto": "Select Any Cryptocurrency (/USDT):",
        "tempo_grafico": "Timeframe:",
        "modo_vivo": "Enable Real-Time Monitoring",
        "intervalo_refresh": "Refresh Interval (Seconds):",
        "preco_spot": "Real Spot Price",
        "variacao_24h": "24h Variation (Exchange)",
        "market_cap": "Market Cap (USD)",
        "stop_atr": "ATR Stop Price",
        "compra_forte": "🟢  STRONG BUY (SMC + FIBONACCI ALIGNED)",
        "venda_forte": "🔴  STRONG SELL (SMC + FIBONACCI ALIGNED)",
        "neutro": "🟡  NEUTRAL (AWAIT SMC)",
        "erro_dados": "Insufficient historical data on this Exchange. Choose another asset or reduce the Timeframe.",
        "ctx_desconto": "Asset in Fibonacci Discount Zone (Excellent risk/reward for Institutionals).",
        "ctx_premium": "Asset in Fibonacci Premium Zone (Price stretched, suitable for profit-taking).",
        "ctx_neutro": "Price in neutral Fibonacci zone (Fair Value Zone).",
        "ultima_atualizacao": "Last Update",
        "proximo_refresh": "Next refresh in",
        "segundos": "seconds",
        "pontos_compra": "Buy Points",
        "pontos_venda": "Sell Points",
        "grafico_titulo": "📈  Interactive Price Chart",
        "buscando_marketcap": "🔍  Fetching Market Cap...",
        "marketcap_nao_disponivel": "Not available",
        "idioma_label": "🌐  Language / Idioma",
        "idioma_selecao": "Select Interface Language:",
        "aviso_aquecimento": "⚠️ Warm-up candles used in calculation",
        "intervalos": {
            "1 Minute": "1m",
            "5 Minutes": "5m",
            "15 Minutes": "15m",
            "30 Minutes": "30m",
            "1 Hour": "1h",
            "4 Hours": "4h",
            "1 Day": "1d",
            "1 Week": "1w"
        }
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# FORMATAÇÃO
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
    else:
        # Qualquer valor abaixo de $1M não é market cap real de cripto listada
        return "$ —"


# ─────────────────────────────────────────────────────────────────────────────
# EXCHANGE
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


@st.cache_data(ttl=3600)
def obter_nome_extenso_cripto(simbolo_id):
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


# ─────────────────────────────────────────────────────────────────────────────
# MARKET CAP — CoinGecko via endpoint /coins/markets
# Este endpoint retorna dados de mercado diretamente, sem precisar:
#   1. Baixar a lista completa de 10.000+ moedas (/coins/list)
#   2. Fazer uma segunda chamada para buscar detalhes (/coins/{id})
# Uma única chamada retorna price, market_cap, volume para até 250 moedas.
# Rate limit do plano gratuito: 10-30 chamadas/minuto. Com cache de 10min,
# isso representa ~6 chamadas/hora por símbolo — bem dentro do limite.

# Mapa de IDs canônicos para os símbolos mais negociados.
# Necessário porque o CoinGecko usa IDs únicos (ex: "solana"), não símbolos
# (ex: "sol"), e vários tokens diferentes partilham o mesmo símbolo.
COINGECKO_ID_MAP = {
    "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
    "BNB": "binancecoin", "XRP": "ripple", "ADA": "cardano",
    "DOGE": "dogecoin", "TRX": "tron", "DOT": "polkadot",
    "MATIC": "matic-network", "POL": "matic-network", "LTC": "litecoin",
    "AVAX": "avalanche-2", "LINK": "chainlink", "UNI": "uniswap",
    "ATOM": "cosmos", "XLM": "stellar", "ETC": "ethereum-classic",
    "FIL": "filecoin", "NEAR": "near", "APT": "aptos",
    "ARB": "arbitrum", "OP": "optimism", "SUI": "sui",
    "INJ": "injective-protocol", "SEI": "sei-network",
    "TON": "the-open-network", "PEPE": "pepe", "SHIB": "shiba-inu",
    "WIF": "dogwifcoin", "BONK": "bonk", "FET": "fetch-ai",
    "RENDER": "render-token", "TAO": "bittensor",
    "JUP": "jupiter-exchange-solana", "W": "wormhole",
    "PYTH": "pyth-network", "STRK": "starknet",
    "MANTA": "manta-network", "LIT": "litentry",
    "HBAR": "hedera-hashgraph", "VET": "vechain",
    "ALGO": "algorand", "SAND": "the-sandbox",
    "MANA": "decentraland", "AXS": "axie-infinity",
    "CRV": "curve-dao-token", "AAVE": "aave",
    "MKR": "maker", "SNX": "synthetix-network-token",
    "GRT": "the-graph", "LDO": "lido-dao",
    "IMX": "immutable-x", "RUNE": "thorchain",
    "FLOKI": "floki", "CFX": "conflux-token",
    "KAVA": "kava", "ZIL": "zilliqa",
    "BLUR": "blur", "MAGIC": "magic",
}


@st.cache_data(ttl=600)  # Cache de 10 minutos — respeita rate limit gratuito
def obter_market_cap_coingecko(simbolo):
    """
    Busca market cap via endpoint /coins/markets do CoinGecko.
    Vantagem: uma única chamada HTTP retorna dados completos.
    Sem necessidade de baixar lista de moedas ou fazer duas chamadas.
    """
    coin_id = COINGECKO_ID_MAP.get(simbolo.upper())
    if not coin_id:
        return None
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": coin_id,
            "order": "market_cap_desc",
            "per_page": 1,
            "page": 1,
            "sparkline": "false"
        }
        headers = {"Accept": "application/json"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            dados = response.json()
            if dados and len(dados) > 0:
                mc = dados[0].get("market_cap")
                # Validação: market cap real de qualquer cripto listada > $1M
                if mc and float(mc) > 1_000_000:
                    return float(mc)
        elif response.status_code == 429:
            # Rate limit atingido — retornar None sem crashar
            return None
        return None
    except Exception:
        return None


def obter_market_cap_robusto(simbolo_id):
    """
    Tenta obter market cap do CoinGecko.
    Se o símbolo não estiver no mapa ou a API falhar, exibe 'Não disponível'.
    Nunca inventa valores — prefere mostrar '—' a mostrar dado errado.
    """
    simbolo = simbolo_id.split('/')[0]
    resultado = obter_market_cap_coingecko(simbolo)
    if resultado and resultado > 1_000_000:
        return resultado
    return None


# ─────────────────────────────────────────────────────────────────────────────
# INDICADORES TÉCNICOS

def calcular_rsi(serie, periodo=14):
    """RSI calculado sobre série pandas. Requer período de aquecimento."""
    delta = serie.diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    ma_ganho = ganho.ewm(span=periodo, adjust=False).mean()
    ma_perda = perda.ewm(span=periodo, adjust=False).mean()
    return 100 - (100 / (1 + (ma_ganho / ma_perda.replace(0, 1e-10))))


def calcular_macd(serie):
    """MACD(12,26,9). Requer mínimo 35 períodos de aquecimento."""
    ema12 = serie.ewm(span=12, adjust=False).mean()
    ema26 = serie.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    sinal = macd.ewm(span=9, adjust=False).mean()
    return macd, sinal, macd - sinal


def calcular_mfi(df, periodo=14):
    """Money Flow Index. Requer período de aquecimento."""
    tp = (df['high'] + df['low'] + df['close']) / 3
    rmf = tp * df['volume']
    tp_shift = tp.shift(1)
    pos_flow = rmf.where(tp > tp_shift, 0.0)
    neg_flow = rmf.where(tp < tp_shift, 0.0)
    pos_sum = pos_flow.rolling(window=periodo).sum()
    neg_sum = neg_flow.rolling(window=periodo).sum().replace(0, 1e-10)
    return 100 - (100 / (1 + pos_sum / neg_sum))


def calcular_ssl_hybrid(df, periodo=20):
    """SSL Hybrid Baseline. Requer período de aquecimento."""
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
    df = df.copy()
    df['ssl_dir'] = ssl_dir
    df['SSL_Baseline'] = np.where(ssl_dir == 1, sma_high, sma_low)
    return df


def calcular_atr_stop(df, periodo=14, multiplicador=3.0):
    """ATR Trailing Stop. Requer período de aquecimento."""
    high, low, close = df['high'], df['low'], df['close']
    tr = pd.concat(
        [high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()],
        axis=1
    ).max(axis=1)
    atr = tr.ewm(span=periodo, adjust=False).mean()
    atr_stop = np.zeros(len(df))
    tendencia = np.zeros(len(df), dtype=int)
    close_arr = close.values
    atr_arr = atr.values

    if len(df) > 0:
        atr_stop[0] = (
            close_arr[0] - (atr_arr[0] * multiplicador)
            if not np.isnan(atr_arr[0]) else close_arr[0]
        )
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

    df = df.copy()
    df['ATR_Stop'] = atr_stop
    df['atr_dir'] = tendencia
    return df


def calcular_ppo(df, col='close', rapido=12, lento=26, sinal_periodo=9):
    """Percentage Price Oscillator. Requer período de aquecimento."""
    ema_rapida = df[col].ewm(span=rapido, adjust=False).mean()
    ema_lenta = df[col].ewm(span=lento, adjust=False).mean()
    df = df.copy()
    df['PPO'] = ((ema_rapida - ema_lenta) / ema_lenta) * 100
    df['PPO_Signal'] = df['PPO'].ewm(span=sinal_periodo, adjust=False).mean()
    return df


# ─────────────────────────────────────────────────────────────────────────────
# FIBONACCI
# Calculado sobre as últimas velas APÓS o período de aquecimento,
# representando a janela de análise real — não o histórico completo de 500 velas.
def calcular_retracao_fibonacci(df_analise):
    """
    Recebe apenas o DataFrame pós-aquecimento (janela de análise).
    Máxima e mínima representam o swing da janela analisada.
    """
    maxima = df_analise['high'].max()
    minima = df_analise['low'].min()
    diff = maxima - minima
    return {
        'fib_0':   maxima,
        'fib_236': maxima - 0.236 * diff,
        'fib_382': maxima - 0.382 * diff,
        'fib_500': maxima - 0.500 * diff,
        'fib_618': maxima - 0.618 * diff,
        'fib_786': maxima - 0.786 * diff,
        'fib_100': minima
    }


# ─────────────────────────────────────────────────────────────────────────────
# CARREGAMENTO DE DADOS
@st.cache_data(ttl=60)
def carregar_dados(simbolo_id, timeframe_selecionado):
    """
    Carrega VELAS_TOTAL velas para garantir aquecimento adequado dos indicadores.
    Retorna o DataFrame completo com todos os indicadores calculados.
    O período de aquecimento (primeiras PERIODO_AQUECIMENTO velas) é usado
    apenas internamente pelos algoritmos — o sinal final é extraído das velas
    posteriores, já com indicadores estabilizados.
    """
    try:
        velas = gateio_client.fetch_ohlcv(
            simbolo_id,
            timeframe=timeframe_selecionado,
            limit=VELAS_TOTAL
        )
        if not velas or len(velas) < PERIODO_AQUECIMENTO + 50:
            return None
        df = pd.DataFrame(
            velas,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Calcular todos os indicadores sobre o DataFrame completo (500 velas).
        # As primeiras PERIODO_AQUECIMENTO velas estabilizam os cálculos EWM/rolling.
        df['RSI_14'] = calcular_rsi(df['close'], 14)
        macd, sinal, hist = calcular_macd(df['close'])
        df['MACD'] = macd
        df['MACD_SIGNAL'] = sinal
        df['MACD_HIST'] = hist
        df['MFI'] = calcular_mfi(df)
        df = calcular_ssl_hybrid(df)
        df = calcular_atr_stop(df)
        df = calcular_ppo(df)

        # Preenchimento de NaN residuais (apenas nas primeiras velas do rolling)
        df['SSL_Baseline'] = df['SSL_Baseline'].ffill()
        df['ATR_Stop'] = df['ATR_Stop'].replace(0, np.nan).ffill()

        return df.dropna(subset=['close']).reset_index(drop=True)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None


def obter_variacao_24h(simbolo_id):
    """Variação 24h diretamente do ticker da Gate.io — fonte oficial."""
    try:
        ticker = gateio_client.fetch_ticker(simbolo_id)
        if ticker and ticker.get('percentage') is not None:
            return float(ticker['percentage'])
    except:
        pass
    try:
        dados_24h = gateio_client.fetch_ohlcv(simbolo_id, timeframe='1d', limit=2)
        if dados_24h and len(dados_24h) >= 2:
            return ((dados_24h[-1][4] - dados_24h[-2][4]) / dados_24h[-2][4]) * 100
    except:
        pass
    return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# ANÁLISE DE CONFLUÊNCIA SMC
def analisar_confluencia(df_completo, txt):
    """
    Análise de confluência feita sobre a janela pós-aquecimento.
    df_completo: DataFrame com 500 velas e indicadores calculados.
    A última linha (iloc[-1]) representa o candle atual com indicadores estáveis.
    Fibonacci calculado sobre as últimas 200 velas pós-aquecimento.
    """
    # Janela de análise: descarta o período de aquecimento
    df_analise = df_completo.iloc[PERIODO_AQUECIMENTO:].copy()

    if df_analise.empty:
        return txt["neutro"], "#ffcc00", txt["ctx_neutro"], 0.0, 0.0

    # Última vela com indicadores estabilizados
    u = df_analise.iloc[-1]
    preco_atual = u['close']

    # Fibonacci calculado sobre a janela de análise real
    fib_niveis = calcular_retracao_fibonacci(df_analise)

    pontos_alta = 0.0
    pontos_baixa = 0.0

    # RSI(14): sobrevendido < 40 → alta; sobrecomprado > 60 → baixa
    rsi_val = u['RSI_14']
    if not math.isnan(rsi_val):
        if rsi_val < 40:
            pontos_alta += 2
        elif rsi_val > 60:
            pontos_baixa += 2

    # MACD: histograma positivo → momentum de alta
    macd_hist = u['MACD_HIST']
    if not math.isnan(macd_hist):
        if macd_hist > 0:
            pontos_alta += 2
        else:
            pontos_baixa += 2

    # MFI: fluxo de dinheiro > 50 → pressão compradora
    mfi_val = u['MFI']
    if not math.isnan(mfi_val):
        if mfi_val > 50:
            pontos_alta += 1
        else:
            pontos_baixa += 1

    # SSL Hybrid: direção da baseline
    if u['ssl_dir'] == 1:
        pontos_alta += 1
    else:
        pontos_baixa += 1

    # ATR Trailing Stop: tendência do stop
    if u['atr_dir'] == 1:
        pontos_alta += 1
    else:
        pontos_baixa += 1

    # PPO: linha acima do sinal → momentum positivo
    ppo_val = u['PPO']
    ppo_sig = u['PPO_Signal']
    if not (math.isnan(ppo_val) or math.isnan(ppo_sig)):
        if ppo_val > ppo_sig:
            pontos_alta += 1.5
        else:
            pontos_baixa += 1.5

    # Fibonacci: posição do preço na grade de retração
    if preco_atual >= fib_niveis['fib_382']:
        pontos_baixa += 2.0
        contexto_fib = txt["ctx_premium"]
    elif preco_atual <= fib_niveis['fib_618']:
        pontos_alta += 2.0
        contexto_fib = txt["ctx_desconto"]
    else:
        contexto_fib = txt["ctx_neutro"]

    if pontos_alta >= 8.5:
        return (
            txt["compra_forte"], "#00cc66",
            f"{contexto_fib} SMC + PPO Order Flow Bullish.",
            pontos_alta, pontos_baixa
        )
    elif pontos_baixa >= 8.5:
        return (
            txt["venda_forte"], "#ff3333",
            f"{contexto_fib} SMC + PPO Order Flow Bearish.",
            pontos_alta, pontos_baixa
        )
    else:
        return txt["neutro"], "#ffcc00", contexto_fib, pontos_alta, pontos_baixa


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO
def renderizar_grafico_plotly(df_completo, simbolo_id):
    """
    Gráfico exibe as últimas 300 velas pós-aquecimento para melhor visualização.
    O período de aquecimento (primeiras 100 velas) é omitido do gráfico,
    pois seus valores de indicador ainda estão em estabilização.
    """
    df_grafico = df_completo.iloc[PERIODO_AQUECIMENTO:].copy()

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df_grafico['time'],
        open=df_grafico['open'],
        high=df_grafico['high'],
        low=df_grafico['low'],
        close=df_grafico['close'],
        name=simbolo_id,
        increasing_line_color='#10b981',
        decreasing_line_color='#ef4444',
        increasing_fillcolor='#10b981',
        decreasing_fillcolor='#ef4444'
    ))

    fig.add_trace(go.Scatter(
        x=df_grafico['time'],
        y=df_grafico['SSL_Baseline'],
        mode='lines',
        name='SMC Baseline (SSL)',
        line=dict(color='#00aaff', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=df_grafico['time'],
        y=df_grafico['ATR_Stop'],
        mode='lines',
        name='ATR Trailing Stop',
        line=dict(color='#ffaa00', width=1, dash='dash')
    ))

    fig.update_layout(
        paper_bgcolor='#0b0f19',
        plot_bgcolor='#0b0f19',
        font=dict(color='#e2e8f0'),
        xaxis=dict(
            gridcolor='#1e293b',
            showgrid=True,
            rangeslider=dict(visible=False)
        ),
        yaxis=dict(gridcolor='#1e293b', showgrid=True),
        legend=dict(bgcolor='#1e293b', bordercolor='#475569', borderwidth=1),
        margin=dict(l=10, r=10, t=30, b=10),
        height=520
    )

    # Corrigido: width='stretch' substitui use_container_width=True (depreciado)
    st.plotly_chart(fig, width='stretch')


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
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

intervalos = txt["intervalos"]
intervalo_escolhido = st.sidebar.selectbox(
    txt["tempo_grafico"], list(intervalos.keys()), index=5
)
timeframe = intervalos[intervalo_escolhido]

st.sidebar.markdown("---")
modo_vivo = st.sidebar.toggle(txt["modo_vivo"], value=False)
intervalo_refresh = st.sidebar.slider(
    txt["intervalo_refresh"], min_value=15, max_value=120, value=30
)


# ─────────────────────────────────────────────────────────────────────────────
# PAINEL PRINCIPAL
@st.fragment(run_every=intervalo_refresh if modo_vivo else None)
def painel_principal(simbolo_id, timeframe, txt, modo_vivo, intervalo_refresh):
    df_dados = carregar_dados(simbolo_id, timeframe)

    if df_dados is None or df_dados.empty:
        st.warning(txt["erro_dados"])
        return

    # Dados da última vela estabilizada (pós-aquecimento)
    df_analise = df_dados.iloc[PERIODO_AQUECIMENTO:]
    if df_analise.empty:
        st.warning(txt["erro_dados"])
        return

    ultimo_reg = df_analise.iloc[-1]
    preco_atual = ultimo_reg['close']

    # Variação 24h: fonte oficial Gate.io ticker
    variacao_24h = obter_variacao_24h(simbolo_id)

    # Market Cap: CoinGecko /coins/markets (uma chamada, cache 10min)
    market_cap = obter_market_cap_robusto(simbolo_id)

    # Análise SMC
    recomendacao, cor_sinal, analise, pontos_alta, pontos_baixa = analisar_confluencia(
        df_dados, txt
    )

    # Banner de sinal
    ppo_line = ultimo_reg['PPO']
    ppo_sig = ultimo_reg['PPO_Signal']
    ppo_txt = (
        f"PPO: {ppo_line:.3f} / Signal: {ppo_sig:.3f}"
        if not (math.isnan(ppo_line) or math.isnan(ppo_sig))
        else "PPO: —"
    )
    st.markdown(f"""
    <div style="background:{cor_sinal}22;padding:20px;border-radius:10px;
                border:2px solid {cor_sinal};margin-bottom:20px;">
    <h2 style="margin:0;color:{cor_sinal};">{recomendacao}</h2>
    <p style="margin:8px 0 0 0;color:#ddd;">{analise} | <b>{ppo_txt}</b></p>
    </div>
    """, unsafe_allow_html=True)

    # Métricas
    nome_completo_ativo = obter_nome_extenso_cripto(simbolo_id)
    label_preco = f"{nome_completo_ativo} | {txt['preco_spot']}"

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(label_preco, formatar_preco(preco_atual))
    m2.metric(txt["variacao_24h"], f"{variacao_24h:+.2f}%")

    if market_cap is not None:
        m3.metric(txt["market_cap"], formatar_market_cap(market_cap))
    else:
        m3.metric(txt["market_cap"], txt["marketcap_nao_disponivel"])

    m4.metric(txt["pontos_compra"], f"{pontos_alta:.1f}")
    m5.metric(txt["pontos_venda"], f"{pontos_baixa:.1f}")

    # Stop ATR
    atr_stop_val = ultimo_reg['ATR_Stop']
    st.markdown(
        f"**{txt['stop_atr']}:** {formatar_preco(atr_stop_val)}"
        f"  |  RSI: **{ultimo_reg['RSI_14']:.1f}**"
        f"  |  MFI: **{ultimo_reg['MFI']:.1f}**"
    )

    # Gráfico
    st.markdown(f"### {txt['grafico_titulo']}")
    renderizar_grafico_plotly(df_dados, simbolo_id)

    # Status
    hora_atual = pd.Timestamp.now().strftime("%H:%M:%S")
    n_velas = len(df_analise)
    if modo_vivo:
        st.info(
            f"🟢 {txt['ultima_atualizacao']}: {hora_atual} | "
            f"{txt['proximo_refresh']} {intervalo_refresh} {txt['segundos']} | "
            f"{txt['aviso_aquecimento']}: {PERIODO_AQUECIMENTO} | "
            f"Velas analisadas: {n_velas}"
        )
    else:
        st.info(
            f"⏸ {txt['ultima_atualizacao']}: {hora_atual} | "
            f"{txt['aviso_aquecimento']}: {PERIODO_AQUECIMENTO} | "
            f"Velas analisadas: {n_velas}"
        )


painel_principal(simbolo_id, timeframe, txt, modo_vivo, intervalo_refresh)
