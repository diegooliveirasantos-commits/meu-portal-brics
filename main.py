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
        "spike_alta": "🚀  SPIKE DE ALTA DETECTADO (Volume + OBV + Range)",
        "spike_baixa": "💥  SPIKE DE BAIXA DETECTADO (Volume + OBV + Range)",
        "erro_dados": "Dados históricos insuficientes nesta Exchange. Escolha outro ativo ou reduza o Tempo Gráfico.",
        "ctx_desconto": "Ativo em Zona de Desconto de Fibonacci (Excelente risco/retorno para Institucionais).",
        "ctx_premium": "Ativo em Zona Premium de Fibonacci (Preço esticado, propício para realização de lucro).",
        "ctx_neutro": "Preço em zona neutra de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Última Atualização",
        "proximo_refresh": "Próximo refresh em",
        "segundos": "segundos",
        "pontos_compra": "Pontos de Compra",
        "pontos_venda": "Pontos de Venda",
        "sinal_spike": "Spike Volatilidade",
        "grafico_titulo": "📈  Gráfico de Preço Interativo",
        "buscando_marketcap": "🔍  Buscando Market Cap...",
        "marketcap_nao_disponivel": "Não disponível",
        "idioma_label": "🌐  Idioma / Language",
        "idioma_selecao": "Selecione o idioma da interface:",
        "aviso_aquecimento": "⚠️ Velas de aquecimento usadas no cálculo",
        "backtest_titulo": "📊 Backtesting — Últimos 100 Sinais",
        "backtest_compra": "Compra",
        "backtest_venda": "Venda",
        "backtest_total": "Total Sinais",
        "backtest_acertos": "Acertos",
        "backtest_taxa": "Taxa de Acerto",
        "backtest_historico": "Histórico de Sinais Recentes",
        "backtest_data": "Data/Hora",
        "backtest_sinal": "Sinal",
        "backtest_preco": "Preço Entrada",
        "backtest_resultado": "Resultado",
        "backtest_acerto": "✅ Acerto",
        "backtest_erro": "❌ Erro",
        "poc_label": "POC (Point of Control)",
        "vah_label": "VAH (Value Area High)",
        "val_label": "VAL (Value Area Low)",
        "fear_greed_label": "😱 Fear & Greed Index",
        "medo_extremo": "Medo Extremo",
        "medo": "Medo",
        "neutro_fg": "Neutro",
        "ganancia": "Ganância",
        "ganancia_extrema": "Ganância Extrema",
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
        "spike_alta": "🚀  UPSIDE SPIKE DETECTED (Volume + OBV + Range)",
        "spike_baixa": "💥  DOWNSIDE SPIKE DETECTED (Volume + OBV + Range)",
        "erro_dados": "Insufficient historical data on this Exchange. Choose another asset or reduce the Timeframe.",
        "ctx_desconto": "Asset in Fibonacci Discount Zone (Excellent risk/reward for Institutionals).",
        "ctx_premium": "Asset in Fibonacci Premium Zone (Price stretched, suitable for profit-taking).",
        "ctx_neutro": "Price in neutral Fibonacci zone (Fair Value Zone).",
        "ultima_atualizacao": "Last Update",
        "proximo_refresh": "Next refresh in",
        "segundos": "seconds",
        "pontos_compra": "Buy Points",
        "pontos_venda": "Sell Points",
        "sinal_spike": "Volatility Spike",
        "grafico_titulo": "📈  Interactive Price Chart",
        "buscando_marketcap": "🔍  Fetching Market Cap...",
        "marketcap_nao_disponivel": "Not available",
        "idioma_label": "🌐  Language / Idioma",
        "idioma_selecao": "Select Interface Language:",
        "aviso_aquecimento": "⚠️ Warm-up candles used in calculation",
        "backtest_titulo": "📊 Backtesting — Last 100 Signals",
        "backtest_compra": "Buy",
        "backtest_venda": "Sell",
        "backtest_total": "Total Signals",
        "backtest_acertos": "Hits",
        "backtest_taxa": "Hit Rate",
        "backtest_historico": "Recent Signal History",
        "backtest_data": "Date/Time",
        "backtest_sinal": "Signal",
        "backtest_preco": "Entry Price",
        "backtest_resultado": "Result",
        "backtest_acerto": "✅ Hit",
        "backtest_erro": "❌ Miss",
        "poc_label": "POC (Point of Control)",
        "vah_label": "VAH (Value Area High)",
        "val_label": "VAL (Value Area Low)",
        "fear_greed_label": "😱 Fear & Greed Index",
        "medo_extremo": "Extreme Fear",
        "medo": "Fear",
        "neutro_fg": "Neutral",
        "ganancia": "Greed",
        "ganancia_extrema": "Extreme Greed",
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
# FEAR & GREED INDEX (alternative.me — API gratuita, sem chave)
@st.cache_data(ttl=3600)
def obter_fear_greed_index():
    """
    Busca o Fear & Greed Index da API pública alternative.me.
    Retorna: (valor, classificação_texto)
    Ex: (25, "Fear") ou (75, "Greed")
    """
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            dados = response.json()
            if dados.get("data") and len(dados["data"]) > 0:
                valor = int(dados["data"][0]["value"])
                classificacao = dados["data"][0]["value_classification"]
                return valor, classificacao
        return None, None
    except Exception:
        return None, None


# ─────────────────────────────────────────────────────────────────────────────
# MARKET CAP — CoinGecko (endpoint /coins/markets com busca por símbolo)
@st.cache_data(ttl=600)
def obter_market_cap_coingecko(simbolo):
    """
    Busca market cap via endpoint /coins/markets do CoinGecko.
    Usa o parâmetro 'symbols' para busca direta por símbolo (ex: 'jellyjelly', 'zec').
    Não depende de ID map — funciona para QUALQUER cripto listada no CoinGecko.
    """
    try:
        # Método 1: busca por símbolo direto (funciona para JELLYJELLY, ZEC, etc.)
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "symbols": simbolo.lower(),
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
                if mc and float(mc) > 1_000_000:
                    return float(mc)
        elif response.status_code == 429:
            return None

        # Método 2 (fallback): busca por ID se o símbolo estiver no mapa
        coin_id_map = {
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
        coin_id = coin_id_map.get(simbolo.upper())
        if coin_id:
            params2 = {
                "vs_currency": "usd",
                "ids": coin_id,
                "order": "market_cap_desc",
                "per_page": 1,
                "page": 1,
                "sparkline": "false"
            }
            resp2 = requests.get(url, params=params2, headers=headers, timeout=10)
            if resp2.status_code == 200:
                dados2 = resp2.json()
                if dados2 and len(dados2) > 0:
                    mc2 = dados2[0].get("market_cap")
                    if mc2 and float(mc2) > 1_000_000:
                        return float(mc2)
        return None
    except Exception:
        return None


def obter_market_cap_robusto(simbolo_id):
    """
    Tenta obter market cap do CoinGecko.
    Usa busca por símbolo direto + fallback por ID.
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
    delta = serie.diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    ma_ganho = ganho.ewm(span=periodo, adjust=False).mean()
    ma_perda = perda.ewm(span=periodo, adjust=False).mean()
    return 100 - (100 / (1 + (ma_ganho / ma_perda.replace(0, 1e-10))))


def calcular_macd(serie):
    ema12 = serie.ewm(span=12, adjust=False).mean()
    ema26 = serie.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    sinal = macd.ewm(span=9, adjust=False).mean()
    return macd, sinal, macd - sinal


def calcular_obv(df):
    """
    On-Balance Volume (OBV) — indicador leading que antecede movimentos de preço.
    OBV sobe quando o preço fecha acima do anterior (volume é adicionado).
    OBV desce quando o preço fecha abaixo do anterior (volume é subtraído).
    Divergência OBV/preço é sinal antecipado de reversão ou continuação.
    """
    obv = [0]
    for i in range(1, len(df)):
        if df['close'].iloc[i] > df['close'].iloc[i-1]:
            obv.append(obv[-1] + df['volume'].iloc[i])
        elif df['close'].iloc[i] < df['close'].iloc[i-1]:
            obv.append(obv[-1] - df['volume'].iloc[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index)


def calcular_obv_aceleracao(obv_series, periodo=5):
    """
    Aceleração do OBV: taxa de variação do OBV nos últimos 'periodo' candles.
    Valores altos positivos → forte pressão compradora (spike de alta).
    Valores altos negativos → forte pressão vendedora (spike de baixa).
    """
    return obv_series.diff(periodo) / periodo


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
    df = df.copy()
    df['ssl_dir'] = ssl_dir
    df['SSL_Baseline'] = np.where(ssl_dir == 1, sma_high, sma_low)
    return df


def calcular_atr_stop(df, periodo=14, multiplicador=3.0):
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
    ema_rapida = df[col].ewm(span=rapido, adjust=False).mean()
    ema_lenta = df[col].ewm(span=lento, adjust=False).mean()
    df = df.copy()
    df['PPO'] = ((ema_rapida - ema_lenta) / ema_lenta) * 100
    df['PPO_Signal'] = df['PPO'].ewm(span=sinal_periodo, adjust=False).mean()
    return df


# ─────────────────────────────────────────────────────────────────────────────
# VOLUME PROFILE (POC/VAH/VAL)
def calcular_volume_profile(df, num_bins=50, value_area_pct=0.70):
    """
    Calcula Volume Profile diretamente dos dados OHLCV.
    Retorna:
    - POC (Point of Control): nível de preço com maior volume
    - VAH (Value Area High): topo da área de valor (70% do volume)
    - VAL (Value Area Low): fundo da área de valor (70% do volume)
    """
    if df.empty:
        return None, None, None

    preco_min = df['low'].min()
    preco_max = df['high'].max()
    if preco_max == preco_min:
        return preco_max, preco_max, preco_max

    bins = np.linspace(preco_min, preco_max, num_bins + 1)
    volume_por_nivel = np.zeros(num_bins)

    for i in range(len(df)):
        low = df['low'].iloc[i]
        high = df['high'].iloc[i]
        volume = df['volume'].iloc[i]
        if high == low:
            idx = np.digitize(low, bins) - 1
            idx = min(max(idx, 0), num_bins - 1)
            volume_por_nivel[idx] += volume
        else:
            volume_por_unidade = volume / (high - low)
            for j in range(num_bins):
                bin_low = bins[j]
                bin_high = bins[j + 1]
                overlap_low = max(low, bin_low)
                overlap_high = min(high, bin_high)
                if overlap_high > overlap_low:
                    volume_por_nivel[j] += (overlap_high - overlap_low) * volume_por_unidade

    # POC: nível com maior volume
    poc_idx = np.argmax(volume_por_nivel)
    poc = (bins[poc_idx] + bins[poc_idx + 1]) / 2

    # Value Area (70% do volume total)
    volume_total = volume_por_nivel.sum()
    volume_alvo = volume_total * value_area_pct

    # Ordenar níveis por volume (decrescente)
    indices_ordenados = np.argsort(volume_por_nivel)[::-1]
    volume_acumulado = 0
    niveis_value_area = []
    for idx in indices_ordenados:
        volume_acumulado += volume_por_nivel[idx]
        niveis_value_area.append(idx)
        if volume_acumulado >= volume_alvo:
            break

    if niveis_value_area:
        vah_idx = max(niveis_value_area)
        val_idx = min(niveis_value_area)
        vah = (bins[vah_idx] + bins[vah_idx + 1]) / 2 if vah_idx + 1 < len(bins) else bins[vah_idx]
        val = (bins[val_idx] + bins[val_idx + 1]) / 2 if val_idx + 1 < len(bins) else bins[val_idx]
    else:
        vah = poc
        val = poc

    return poc, vah, val


# ─────────────────────────────────────────────────────────────────────────────
# DETECTOR DE SPIKE DE VOLATILIDADE (Variação Intraday Brusca)
def detectar_spike_volatilidade(df_analise):
    """
    Detecta spikes de volatilidade intraday baseado em:
    1. Range intraday (High - Low) / Open > limiar
    2. Aceleração do OBV (variação do OBV nos últimos 5 períodos)
    3. Volume atual > 2x média de volume (20 períodos)

    Retorna: "ALTA", "BAIXA", ou None
    """
    if len(df_analise) < 25:
        return None

    u = df_analise.iloc[-1]

    # 1. Range intraday vs Open
    range_pct = ((u['high'] - u['low']) / u['open']) * 100 if u['open'] > 0 else 0

    # 2. Volume anômalo vs média 20 períodos
    vol_medio = df_analise['volume'].iloc[-21:-1].mean()
    vol_atual = u['volume']
    vol_ratio = vol_atual / vol_medio if vol_medio > 0 else 1

    # 3. Aceleração do OBV
    obv_acel = u.get('OBV_Aceleracao', 0)

    # Fechamento vs Abertura (direção do movimento)
    direcao = 1 if u['close'] > u['open'] else -1

    # Critérios de spike
    spike_range = range_pct > 5.0  # Range > 5% do preço
    spike_volume = vol_ratio > 2.0  # Volume > 2x média
    spike_obv = abs(obv_acel) > (df_analise['OBV_Aceleracao'].abs().mean() * 2.5 if len(df_analise) > 25 else 0)

    # Pontuação de spike
    score = 0
    if spike_range:
        score += 1
    if spike_volume:
        score += 1
    if spike_obv and not (np.isnan(obv_acel) or np.isinf(obv_acel)):
        score += 1

    # Spike confirmado se 2 de 3 critérios atendidos
    if score >= 2:
        if direcao > 0:
            return "ALTA"
        else:
            return "BAIXA"

    return None


# ─────────────────────────────────────────────────────────────────────────────
# FIBONACCI
def calcular_retracao_fibonacci(df_analise):
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

        # Indicadores tradicionais
        df['RSI_14'] = calcular_rsi(df['close'], 14)
        macd, sinal, hist = calcular_macd(df['close'])
        df['MACD'] = macd
        df['MACD_SIGNAL'] = sinal
        df['MACD_HIST'] = hist
        df['MFI'] = calcular_mfi(df)
        df = calcular_ssl_hybrid(df)
        df = calcular_atr_stop(df)
        df = calcular_ppo(df)

        # OBV (On-Balance Volume) — indicador leading
        df['OBV'] = calcular_obv(df)

        # Aceleração do OBV (5 períodos)
        df['OBV_Aceleracao'] = calcular_obv_aceleracao(df['OBV'], periodo=5)

        # Volume Ratio (volume atual vs média 20 períodos)
        df['Volume_Ratio'] = df['volume'] / df['volume'].rolling(20).mean()

        # Preenchimento de NaN residuais
        df['SSL_Baseline'] = df['SSL_Baseline'].ffill()
        df['ATR_Stop'] = df['ATR_Stop'].replace(0, np.nan).ffill()

        return df.dropna(subset=['close']).reset_index(drop=True)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None


def obter_variacao_24h(simbolo_id):
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
    df_analise = df_completo.iloc[PERIODO_AQUECIMENTO:].copy()

    if df_analise.empty:
        return txt["neutro"], "#ffcc00", txt["ctx_neutro"], 0.0, 0.0, None, None, None, None

    u = df_analise.iloc[-1]
    preco_atual = u['close']

    fib_niveis = calcular_retracao_fibonacci(df_analise)

    # Volume Profile (POC/VAH/VAL)
    poc, vah, val = calcular_volume_profile(df_analise)

    pontos_alta = 0.0
    pontos_baixa = 0.0

    # RSI(14)
    rsi_val = u['RSI_14']
    if not math.isnan(rsi_val):
        if rsi_val < 40:
            pontos_alta += 2
        elif rsi_val > 60:
            pontos_baixa += 2

    # MACD + OBV combinados
    macd_hist = u['MACD_HIST']
    if not math.isnan(macd_hist):
        if macd_hist > 0:
            pontos_alta += 2
        else:
            pontos_baixa += 2

    # OBV: confirmação ou divergência
    obv_acel = u.get('OBV_Aceleracao', 0)
    if not (np.isnan(obv_acel) or np.isinf(obv_acel)):
        if obv_acel > 0:
            pontos_alta += 1.5  # OBV acelerando → pressão compradora
        else:
            pontos_baixa += 1.5

    # Volume anômalo: confirma força do movimento
    vol_ratio = u.get('Volume_Ratio', 1)
    if vol_ratio > 2.0:
        if macd_hist > 0:
            pontos_alta += 1  # Volume alto confirma alta
        else:
            pontos_baixa += 1

    # MFI
    mfi_val = u['MFI']
    if not math.isnan(mfi_val):
        if mfi_val > 50:
            pontos_alta += 1
        else:
            pontos_baixa += 1

    # SSL Hybrid
    if u['ssl_dir'] == 1:
        pontos_alta += 1
    else:
        pontos_baixa += 1

    # ATR Trailing Stop
    if u['atr_dir'] == 1:
        pontos_alta += 1
    else:
        pontos_baixa += 1

    # PPO
    ppo_val = u['PPO']
    ppo_sig = u['PPO_Signal']
    if not (math.isnan(ppo_val) or math.isnan(ppo_sig)):
        if ppo_val > ppo_sig:
            pontos_alta += 1.5
        else:
            pontos_baixa += 1.5

    # Volume Profile: posição do preço
    volume_profile_pontos = 0.0
    if poc is not None and vah is not None and val is not None:
        if preco_atual <= val:
            # Abaixo do VAL → zona de acumulação → +confluência compra
            pontos_alta += 1.5
            volume_profile_pontos = 1.5
        elif preco_atual >= vah:
            # Acima do VAH → zona de distribuição → +confluência venda
            pontos_baixa += 1.5
            volume_profile_pontos = -1.5
        # Perto do POC (entre VAL e VAH) → equilíbrio → neutro

    # Fibonacci
    if preco_atual >= fib_niveis['fib_382']:
        pontos_baixa += 2.0
        contexto_fib = txt["ctx_premium"]
    elif preco_atual <= fib_niveis['fib_618']:
        pontos_alta += 2.0
        contexto_fib = txt["ctx_desconto"]
    else:
        contexto_fib = txt["ctx_neutro"]

    # Detectar spike de volatilidade
    spike = detectar_spike_volatilidade(df_analise)

    if pontos_alta >= 8.5:
        return (
            txt["compra_forte"], "#00cc66",
            f"{contexto_fib} SMC + PPO Order Flow Bullish.",
            pontos_alta, pontos_baixa, spike, poc, vah, val
        )
    elif pontos_baixa >= 8.5:
        return (
            txt["venda_forte"], "#ff3333",
            f"{contexto_fib} SMC + PPO Order Flow Bearish.",
            pontos_alta, pontos_baixa, spike, poc, vah, val
        )
    else:
        return txt["neutro"], "#ffcc00", contexto_fib, pontos_alta, pontos_baixa, spike, poc, vah, val


# ─────────────────────────────────────────────────────────────────────────────
# BACKTESTING SIMPLES
def executar_backtesting(df_completo, txt):
    """
    Backtesting simples dos últimos 100 sinais históricos.
    Avalia se os sinais de compra/venda foram seguidos por movimento favorável.
    Critério de acerto:
    - Compra: preço 5 velas depois > preço de entrada + 0.5%
    - Venda: preço 5 velas depois < preço de entrada - 0.5%
    """
    df_analise = df_completo.iloc[PERIODO_AQUECIMENTO:].copy()
    if len(df_analise) < 150:
        return None, None, None, None, []

    sinais_compra = 0
    sinais_venda = 0
    acertos_compra = 0
    acertos_venda = 0
    historico = []

    # Janela de backtesting: últimos 100 candles (mais 5 para verificação futura)
    inicio = max(0, len(df_analise) - 105)
    for i in range(inicio, len(df_analise) - 5):
        janela = df_analise.iloc[:i+1]
        if len(janela) < PERIODO_AQUECIMENTO:
            continue

        # Recriar análise para este ponto no tempo
        u = janela.iloc[-1]
        preco_entrada = u['close']

        # Classificação simplificada
        rsi_val = u['RSI_14']
        macd_hist = u['MACD_HIST']
        ssl_dir = u.get('ssl_dir', 0)
        atr_dir = u.get('atr_dir', 0)

        score_alta = 0
        score_baixa = 0
        if not math.isnan(rsi_val):
            if rsi_val < 40: score_alta += 2
            elif rsi_val > 60: score_baixa += 2
        if not math.isnan(macd_hist):
            if macd_hist > 0: score_alta += 2
            else: score_baixa += 2
        if ssl_dir == 1: score_alta += 1
        else: score_baixa += 1
        if atr_dir == 1: score_alta += 1
        else: score_baixa += 1

        tipo_sinal = None
        if score_alta >= 4:
            tipo_sinal = "COMPRA"
            sinais_compra += 1
        elif score_baixa >= 4:
            tipo_sinal = "VENDA"
            sinais_venda += 1

        if tipo_sinal:
            # Verificar resultado 5 candles depois
            preco_futuro = df_analise.iloc[i + 5]['close']
            variacao = ((preco_futuro - preco_entrada) / preco_entrada) * 100

            acerto = False
            if tipo_sinal == "COMPRA" and variacao > 0.5:
                acerto = True
                acertos_compra += 1
            elif tipo_sinal == "VENDA" and variacao < -0.5:
                acerto = True
                acertos_venda += 1

            historico.append({
                'data': df_analise.iloc[i]['time'],
                'sinal': tipo_sinal,
                'preco_entrada': preco_entrada,
                'variacao': variacao,
                'acerto': acerto
            })

    total_sinais = sinais_compra + sinais_venda
    total_acertos = acertos_compra + acertos_venda
    taxa_acerto = (total_acertos / total_sinais * 100) if total_sinais > 0 else 0

    return sinais_compra, sinais_venda, total_acertos, taxa_acerto, historico


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO COM VOLUME PROFILE
def renderizar_grafico_plotly(df_completo, simbolo_id, poc, vah, val, txt):
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

    # Volume Profile — linhas horizontais
    if poc is not None:
        fig.add_hline(
            y=poc,
            line_dash="dash",
            line_color="#ffdd57",
            annotation_text=f"{txt.get('poc_label', 'POC')}: {formatar_preco(poc)}",
            annotation_position="bottom right",
            annotation_font=dict(color="#ffdd57", size=10)
        )
    if vah is not None:
        fig.add_hline(
            y=vah,
            line_dash="dot",
            line_color="#ff6b6b",
            annotation_text=f"{txt.get('vah_label', 'VAH')}: {formatar_preco(vah)}",
            annotation_position="bottom right",
            annotation_font=dict(color="#ff6b6b", size=10)
        )
    if val is not None:
        fig.add_hline(
            y=val,
            line_dash="dot",
            line_color="#51cf66",
            annotation_text=f"{txt.get('val_label', 'VAL')}: {formatar_preco(val)}",
            annotation_position="bottom right",
            annotation_font=dict(color="#51cf66", size=10)
        )

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

    df_analise = df_dados.iloc[PERIODO_AQUECIMENTO:]
    if df_analise.empty:
        st.warning(txt["erro_dados"])
        return

    ultimo_reg = df_analise.iloc[-1]
    preco_atual = ultimo_reg['close']

    variacao_24h = obter_variacao_24h(simbolo_id)
    market_cap = obter_market_cap_robusto(simbolo_id)

    # Fear & Greed Index
    fg_valor, fg_classificacao = obter_fear_greed_index()

    # Análise SMC
    recomendacao, cor_sinal, analise, pontos_alta, pontos_baixa, spike, poc, vah, val = analisar_confluencia(
        df_dados, txt
    )

    # Banner de sinal principal
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

    # Métricas principais
    nome_completo_ativo = obter_nome_extenso_cripto(simbolo_id)
    label_preco = f"{nome_completo_ativo} | {txt['preco_spot']}"

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(label_preco, formatar_preco(preco_atual))
    m2.metric(txt["variacao_24h"], f"{variacao_24h:+.2f}%")

    if market_cap is not None:
        m3.metric(txt["market_cap"], formatar_market_cap(market_cap))
    else:
        m3.metric(txt["market_cap"], txt["marketcap_nao_disponivel"])

    # Coluna 4: Spike de Volatilidade ou Pontos de Compra
    if spike == "ALTA":
        m4.metric(txt["sinal_spike"], f"🚀 {txt['spike_alta']}")
    elif spike == "BAIXA":
        m4.metric(txt["sinal_spike"], f"💥 {txt['spike_baixa']}")
    else:
        m4.metric(txt["pontos_compra"], f"{pontos_alta:.1f}")

    m5.metric(txt["pontos_venda"], f"{pontos_baixa:.1f}")

    # Linha adicional: Fear & Greed + Volume Profile + OBV
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if fg_valor is not None:
            fg_emoji = ""
            if fg_valor <= 25:
                fg_emoji = "😱"
            elif fg_valor <= 45:
                fg_emoji = "😟"
            elif fg_valor <= 55:
                fg_emoji = "😐"
            elif fg_valor <= 75:
                fg_emoji = "😀"
            else:
                fg_emoji = "🤩"
            st.metric(
                txt["fear_greed_label"],
                f"{fg_emoji} {fg_valor}/100",
                delta=fg_classificacao,
                delta_color="off"
            )
        else:
            st.metric(txt["fear_greed_label"], "—")

    with col2:
        st.metric("POC (Volume Profile)", formatar_preco(poc) if poc else "—")

    with col3:
        obv_val = ultimo_reg.get('OBV', 0)
        obv_acel = ultimo_reg.get('OBV_Aceleracao', 0)
        if not (np.isnan(obv_acel) or np.isinf(obv_acel)):
            st.metric("OBV Aceleração", f"{obv_acel:,.0f}")
        else:
            st.metric("OBV Aceleração", "—")

    with col4:
        vol_ratio = ultimo_reg.get('Volume_Ratio', 1)
        if not np.isnan(vol_ratio):
            st.metric("Volume Ratio", f"{vol_ratio:.2f}x")
        else:
            st.metric("Volume Ratio", "—")

    # Stop ATR + indicadores
    atr_stop_val = ultimo_reg['ATR_Stop']
    st.markdown(
        f"**{txt['stop_atr']}:** {formatar_preco(atr_stop_val)}"
        f"  |  RSI: **{ultimo_reg['RSI_14']:.1f}**"
        f"  |  MFI: **{ultimo_reg['MFI']:.1f}**"
        f"  |  MACD Hist: **{ultimo_reg['MACD_HIST']:.6f}**"
    )

    # Gráfico
    st.markdown(f"### {txt['grafico_titulo']}")
    renderizar_grafico_plotly(df_dados, simbolo_id, poc, vah, val, txt)

    # Volume Profile Info
    if poc is not None:
        st.caption(
            f"📊 **Volume Profile:** POC = {formatar_preco(poc)} | "
            f"VAH = {formatar_preco(vah)} | "
            f"VAL = {formatar_preco(val)} | "
            f"Preço atual: {'🟡 Equilíbrio (perto do POC)' if val <= preco_atual <= vah else ('🔴 Distribuição (acima do VAH)' if preco_atual > vah else '🟢 Acumulação (abaixo do VAL)')}"
        )

    # ─────────────────────────────────────────────────────────────────────────
    # BACKTESTING
    st.markdown("---")
    st.markdown(f"### {txt['backtest_titulo']}")

    sinais_compra, sinais_venda, total_acertos, taxa_acerto, historico = executar_backtesting(df_dados, txt)

    if sinais_compra is not None and sinais_venda is not None:
        bt1, bt2, bt3, bt4, bt5 = st.columns(5)
        bt1.metric(txt["backtest_compra"], sinais_compra)
        bt2.metric(txt["backtest_venda"], sinais_venda)
        bt3.metric(txt["backtest_total"], sinais_compra + sinais_venda)
        bt4.metric(txt["backtest_acertos"], total_acertos)
        bt5.metric(txt["backtest_taxa"], f"{taxa_acerto:.1f}%")

        # Exibir últimos 10 sinais
        if historico:
            st.markdown(f"**{txt['backtest_historico']}**")
            hist_df = pd.DataFrame(historico[-10:][::-1])
            hist_df['Resultado'] = hist_df['acerto'].apply(
                lambda x: txt["backtest_acerto"] if x else txt["backtest_erro"]
            )
            hist_df['Preço'] = hist_df['preco_entrada'].apply(lambda x: formatar_preco(x))
            hist_df['Var %'] = hist_df['variacao'].apply(lambda x: f"{x:+.2f}%")
            hist_df_display = hist_df[['data', 'sinal', 'Preço', 'Var %', 'Resultado']].copy()
            hist_df_display.columns = [
                txt["backtest_data"], txt["backtest_sinal"],
                txt["backtest_preco"], 'Var %', txt["backtest_resultado"]
            ]
            st.dataframe(hist_df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Backtesting requer mais dados históricos. Aguarde mais candles.")

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
