import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import math
from decimal import Decimal
import plotly.graph_objects as go
from datetime import datetime
import asyncio
import ccxt.async_support as ccxt_async
import requests
from functools import partial

st.set_page_config(
    page_title="BRICSVAULT PORTAL SMC PRO",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
VELAS_TOTAL = 500
PERIODO_AQUECIMENTO = 100
PERIODO_SWING_DEFAULT = 50

# ─────────────────────────────────────────────────────────────────────────────
# DICIONÁRIO DE IDIOMAS (completo – igual ao original, omitido por brevidade)
# Mantenha o mesmo dicionário DICIONARIO_LINGUAS que você já tem.
# (Apenas para não alongar, assuma que ele está aqui exatamente como antes)
DICIONARIO_LINGUAS = {
    "Português (BR)": { ... },  # Coloque o dicionário completo aqui
    # ... todos os idiomas
}

# ─────────────────────────────────────────────────────────────────────────────
# FORMATAÇÃO (sem alterações)
def formatar_preco(valor, prefixo="$ "):
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return f"{prefixo}—"
    if valor <= 0:
        return f"{prefixo}0.00"
    if valor < 0.001:
        d = Decimal(str(valor))
        s = f"{d:.20f}".rstrip("0")
        partes = s.split(".")
        if len(partes) != 2:
            return f"{prefixo}{valor}"
        parte_decimal = partes[1]
        n_zeros = len(parte_decimal) - len(parte_decimal.lstrip("0"))
        digitos_sig = parte_decimal.lstrip("0")
        return f"{prefixo}0.0{n_zeros}x{digitos_sig}"
    elif valor < 1:
        return f"{prefixo}{valor:.6f}"
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
        return "$ 0.00"
    if valor >= 1_000_000_000_000:
        return f"$ {valor / 1_000_000_000_000:.2f}T"
    elif valor >= 1_000_000_000:
        return f"$ {valor / 1_000_000_000:.2f}B"
    elif valor >= 1_000_000:
        return f"$ {valor / 1_000_000:.2f}M"
    else:
        return f"$ {valor:,.2f}"

# ─────────────────────────────────────────────────────────────────────────────
# GERENCIADOR DE EXCHANGES (ASYNC) – mantido com @st.cache_resource
class ExchangeManager:
    EXCHANGES = {
        "Gate.io": {
            "class": ccxt_async.gate,
            "config": {"enableRateLimit": True, "options": {"defaultType": "spot"}},
            "separator": "/",
            "has_volume_usd": False
        },
        "Kraken": {
            "class": ccxt_async.kraken,
            "config": {"enableRateLimit": True},
            "separator": "/",
            "has_volume_usd": False
        },
        "MEXC": {
            "class": ccxt_async.mexc,
            "config": {"enableRateLimit": True},
            "separator": "",
            "has_volume_usd": True
        },
        "KuCoin": {
            "class": ccxt_async.kucoin,
            "config": {"enableRateLimit": True},
            "separator": "-",
            "has_volume_usd": True
        }
    }
    PRIORITY = ["Gate.io", "Kraken", "MEXC", "KuCoin"]

    def __init__(self):
        self.clients = {}
        self._init_clients()

    def _init_clients(self):
        for name, config in self.EXCHANGES.items():
            try:
                self.clients[name] = config["class"](config["config"])
            except Exception:
                pass

    async def get_client(self, exchange_name):
        return self.clients.get(exchange_name)

    def get_separator(self, exchange_name):
        return self.EXCHANGES.get(exchange_name, {}).get("separator", "/")

    def get_symbol_format(self, exchange_name, symbol):
        if exchange_name == "MEXC":
            return symbol.replace("/", "")
        elif exchange_name == "KuCoin":
            return symbol.replace("/", "-")
        else:
            return symbol

@st.cache_resource
def get_exchange_manager():
    return ExchangeManager()

# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÕES ASSÍNCRONAS (sem cache) – implementam a lógica de rede
async def obter_todos_pares_usdt_async():
    manager = get_exchange_manager()
    client = await manager.get_client("Gate.io")
    if not client:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]
    try:
        markets = await client.load_markets()
        pairs = [s for s in markets.keys() if s.endswith("/USDT")]
        await client.close()
        return sorted(pairs)
    except Exception:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]
    finally:
        if client:
            await client.close()

async def obter_volume_usd_direto_async(exchange_name, simbolo):
    try:
        if exchange_name == "MEXC":
            pair = simbolo.replace("/", "")
            url = f"https://api.mexc.com/api/v3/ticker/24hr?symbol={pair}"
            resp = await asyncio.to_thread(requests.get, url, timeout=10)
            if resp.status_code == 200:
                return float(resp.json().get("quoteVolume", 0))
        elif exchange_name == "KuCoin":
            pair = simbolo.replace("/", "-")
            url = f"https://api.kucoin.com/api/v1/market/stats?symbol={pair}"
            resp = await asyncio.to_thread(requests.get, url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "200000":
                    return float(data.get("data", {}).get("volValue", 0))
        elif exchange_name == "Gate.io":
            pair = simbolo.replace("/", "_")
            url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={pair}"
            resp = await asyncio.to_thread(requests.get, url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    return float(data[0].get("quote_volume", 0))
    except Exception:
        pass
    return None

async def fetch_from_exchange_24h(exchange_name, manager, simbolo):
    client = None
    try:
        client = await manager.get_client(exchange_name)
        if not client:
            return None
        symbol = manager.get_symbol_format(exchange_name, simbolo)
        ticker = await client.fetch_ticker(symbol)
        if ticker:
            result = {
                "last": ticker.get("last"),
                "change": ticker.get("percentage"),
                "volume": ticker.get("quoteVolume") or ticker.get("baseVolume"),
                "high": ticker.get("high"),
                "low": ticker.get("low"),
                "bid": ticker.get("bid"),
                "ask": ticker.get("ask")
            }
            if not result["volume"]:
                result["volume"] = await obter_volume_usd_direto_async(exchange_name, simbolo)
            if result["last"] is not None:
                return result
    except Exception:
        pass
    finally:
        if client:
            await client.close()
    return None

async def obter_dados_24h_async(simbolo):
    manager = get_exchange_manager()
    tasks = []
    for exchange_name in manager.PRIORITY:
        fetch_func = partial(
            fetch_from_exchange_24h,
            exchange_name=exchange_name,
            manager=manager,
            simbolo=simbolo
        )
        tasks.append(asyncio.create_task(fetch_func()))
    
    for future in asyncio.as_completed(tasks):
        result = await future
        if result:
            return result
    return None

async def obter_nome_extenso_cripto_async(simbolo_id):
    try:
        base_currency = simbolo_id.split("/")[0]
        url = "https://api.gateio.ws/api/v4/spot/currencies"
        response = await asyncio.to_thread(requests.get, url, timeout=10)
        if response.status_code == 200:
            dados = response.json()
            for moeda in dados:
                if moeda.get("currency", "").upper() == base_currency.upper():
                    return moeda.get("name", base_currency).upper()
        return base_currency
    except Exception:
        return simbolo_id.split("/")[0]

async def obter_id_coingecko_async(simbolo):
    try:
        url = "https://api.coingecko.com/api/v3/search"
        params = {"query": simbolo}
        headers = {"Accept": "application/json"}
        resp = await asyncio.to_thread(requests.get, url, params=params, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        coins = data.get("coins", [])
        simbolo_upper = simbolo.upper()
        for coin in coins:
            if coin.get("symbol", "").upper() == simbolo_upper:
                return coin.get("id")
        if coins:
            return coins[0].get("id")
        return None
    except Exception:
        return None

async def obter_market_cap_coingecko_async(simbolo):
    coin_id = await obter_id_coingecko_async(simbolo)
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
        resp = await asyncio.to_thread(requests.get, url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            dados = resp.json()
            if dados and len(dados) > 0:
                mc = dados[0].get("market_cap")
                if mc and float(mc) > 1_000_000:
                    return float(mc)
        return None
    except Exception:
        return None

async def obter_market_cap_coincap_async(simbolo):
    try:
        asset_id = simbolo.lower()
        url = f"https://api.coincap.io/v2/assets/{asset_id}"
        resp = await asyncio.to_thread(requests.get, url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            mc = data.get("data", {}).get("marketCapUsd")
            if mc:
                mc_float = float(mc)
                if mc_float > 1_000_000:
                    return mc_float
        url_list = "https://api.coincap.io/v2/assets"
        params = {"limit": 2000}
        resp = await asyncio.to_thread(requests.get, url_list, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("data", []):
                if item.get("symbol", "").upper() == simbolo.upper():
                    mc = item.get("marketCapUsd")
                    if mc:
                        mc_float = float(mc)
                        if mc_float > 1_000_000:
                            return mc_float
        return None
    except Exception:
        return None

async def obter_market_cap_robusto_async(simbolo_id):
    simbolo = simbolo_id.split("/")[0]
    mc_cg = await obter_market_cap_coingecko_async(simbolo)
    mc_cc = await obter_market_cap_coincap_async(simbolo)
    
    if isinstance(mc_cg, Exception): mc_cg = None
    if isinstance(mc_cc, Exception): mc_cc = None
    
    valores = [v for v in (mc_cg, mc_cc) if v is not None and v > 0]
    if len(valores) == 2:
        return sum(valores) / len(valores)
    elif len(valores) == 1:
        return valores[0]
    else:
        return None

# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÕES SÍNCRONAS COM CACHE – chamam as assíncronas via asyncio.run
@st.cache_data(ttl=3600)
def obter_todos_pares_usdt():
    return asyncio.run(obter_todos_pares_usdt_async())

@st.cache_data(ttl=60)  # cache curto para dados de 24h
def obter_dados_24h(simbolo):
    return asyncio.run(obter_dados_24h_async(simbolo))

@st.cache_data(ttl=3600)
def obter_nome_extenso_cripto(simbolo_id):
    return asyncio.run(obter_nome_extenso_cripto_async(simbolo_id))

@st.cache_data(ttl=600)
def obter_market_cap_robusto(simbolo_id):
    return asyncio.run(obter_market_cap_robusto_async(simbolo_id))

# ─────────────────────────────────────────────────────────────────────────────
# CARREGAMENTO DE DADOS OHLCV (async, com cache manual no session_state)
async def carregar_dados_async(simbolo_id, timeframe_selecionado):
    manager = get_exchange_manager()
    
    if 'ohlcv_data' not in st.session_state:
        st.session_state.ohlcv_data = {}
    if simbolo_id not in st.session_state.ohlcv_data:
        st.session_state.ohlcv_data[simbolo_id] = {}
    if timeframe_selecionado not in st.session_state.ohlcv_data[simbolo_id]:
        st.session_state.ohlcv_data[simbolo_id][timeframe_selecionado] = pd.DataFrame()

    df_cached = st.session_state.ohlcv_data[simbolo_id][timeframe_selecionado]
    
    since_timestamp = None
    if not df_cached.empty:
        since_timestamp = int(df_cached['timestamp'].iloc[-1]) + 1 

    velas_novas = []
    for exchange_name in manager.PRIORITY:
        client = None
        try:
            client = await manager.get_client(exchange_name)
            if not client:
                continue
            symbol = manager.get_symbol_format(exchange_name, simbolo_id)
            
            limit_fetch = VELAS_TOTAL - len(df_cached) if not df_cached.empty else VELAS_TOTAL
            if limit_fetch <= 0:
                limit_fetch = 1

            velas = await client.fetch_ohlcv(
                symbol,
                timeframe=timeframe_selecionado,
                limit=limit_fetch,
                since=since_timestamp
            )
            if velas:
                velas_novas.extend(velas)
                break
        except Exception:
            continue
        finally:
            if client:
                await client.close()
    
    if not velas_novas and df_cached.empty:
        return None

    df_novas = pd.DataFrame(
        velas_novas,
        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
    )
    df_novas['time'] = pd.to_datetime(df_novas['timestamp'], unit='ms')
    df_novas = df_novas.drop_duplicates(subset=['timestamp'])

    df_combinado = pd.concat([df_cached, df_novas]).drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
    
    if len(df_combinado) > VELAS_TOTAL:
        df_combinado = df_combinado.iloc[-VELAS_TOTAL:].reset_index(drop=True)

    if len(df_combinado) < PERIODO_AQUECIMENTO + 50:
        return None

    # Calcular indicadores (funções síncronas)
    df_combinado['RSI_14'] = calcular_rsi(df_combinado['close'], 14)
    macd, sinal, hist = calcular_macd(df_combinado['close'])
    df_combinado['MACD'] = macd
    df_combinado['MACD_SIGNAL'] = sinal
    df_combinado['MACD_HIST'] = hist
    df_combinado['MFI'] = calcular_mfi(df_combinado)
    df_combinado = calcular_ssl_hybrid(df_combinado)
    df_combinado = calcular_atr_stop(df_combinado)
    df_combinado = calcular_ppo(df_combinado)

    df_combinado['SSL_Baseline'] = df_combinado['SSL_Baseline'].ffill()
    df_combinado['ATR_Stop'] = df_combinado['ATR_Stop'].replace(0, np.nan).ffill()

    st.session_state.ohlcv_data[simbolo_id][timeframe_selecionado] = df_combinado.dropna(subset=['close']).reset_index(drop=True)
    
    return st.session_state.ohlcv_data[simbolo_id][timeframe_selecionado]

# ─────────────────────────────────────────────────────────────────────────────
# INDICADORES TÉCNICOS (síncronos – sem alterações)
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
# SMC AVANÇADO E LÓGICA DE SINAIS (síncronos)
def identificar_fractais(df, window=2):
    df['fractal_high'] = df['high'].rolling(window=window*2+1, center=True).apply(
        lambda x: x.iloc[window] if x.iloc[window] == x.max() else np.nan, raw=False
    )
    df['fractal_low'] = df['low'].rolling(window=window*2+1, center=True).apply(
        lambda x: x.iloc[window] if x.iloc[window] == x.min() else np.nan, raw=False
    )
    return df

def identificar_swing_smc(df_ohlcv, periodo_minimo_swing=10):
    df = df_ohlcv.copy()
    df = identificar_fractais(df, window=2)
    swing_highs = df[df['fractal_high'].notna()]['high']
    swing_lows = df[df['fractal_low'].notna()]['low']
    if swing_highs.empty or swing_lows.empty:
        return None
    last_high_idx = swing_highs.index[-1] if not swing_highs.empty else None
    last_low_idx = swing_lows.index[-1] if not swing_lows.empty else None
    if last_high_idx is None and last_low_idx is None:
        return None
    if last_high_idx is not None and (last_low_idx is None or last_high_idx > last_low_idx):
        current_swing_high = df.loc[last_high_idx, 'high']
        prev_low_candidates = swing_lows[swing_lows.index < last_high_idx]
        if not prev_low_candidates.empty:
            current_swing_low = prev_low_candidates.iloc[-1]
            current_swing_low_idx = prev_low_candidates.index[-1]
        else:
            current_swing_low = df['low'].min()
            current_swing_low_idx = df['low'].idxmin()
        return {
            'swing_high': current_swing_high,
            'swing_low': current_swing_low,
            'swing_high_idx': last_high_idx,
            'swing_low_idx': current_swing_low_idx,
            'direction_from_swing': 'SHORT'
        }
    elif last_low_idx is not None and (last_high_idx is None or last_low_idx > last_high_idx):
        current_swing_low = df.loc[last_low_idx, 'low']
        prev_high_candidates = swing_highs[swing_highs.index < last_low_idx]
        if not prev_high_candidates.empty:
            current_swing_high = prev_high_candidates.iloc[-1]
            current_swing_high_idx = prev_high_candidates.index[-1]
        else:
            current_swing_high = df['high'].max()
            current_swing_high_idx = df['high'].idxmax()
        return {
            'swing_high': current_swing_high,
            'swing_low': current_swing_low,
            'swing_high_idx': current_swing_high_idx,
            'swing_low_idx': last_low_idx,
            'direction_from_swing': 'LONG'
        }
    return None

def calcular_retracao_fibonacci_smc(swing_high, swing_low):
    diff = swing_high - swing_low
    return {
        'fib_0':   swing_high,
        'fib_236': swing_high - 0.236 * diff,
        'fib_382': swing_high - 0.382 * diff,
        'fib_500': swing_high - 0.500 * diff,
        'fib_618': swing_high - 0.618 * diff,
        'fib_786': swing_high - 0.786 * diff,
        'fib_100': swing_low
    }

def gerar_sinal_fibonacci(df_completo, direcao_smc, multiplicadores, periodo_swing):
    swing_info = identificar_swing_smc(df_completo.iloc[PERIODO_AQUECIMENTO:])
    if not swing_info:
        swing_high = df_completo['high'].max()
        swing_low = df_completo['low'].min()
        entrada_projetada = df_completo['close'].iloc[-1]
        stop_projetado = swing_low if direcao_smc == "LONG" else swing_high
        return {
            'direcao': direcao_smc,
            'entrada': entrada_projetada,
            'stop': stop_projetado,
            'swing_high': swing_high,
            'swing_low': swing_low,
            'alvos': []
        }
    swing_high = swing_info['swing_high']
    swing_low = swing_info['swing_low']
    preco_atual = df_completo['close'].iloc[-1]
    if direcao_smc == "LONG":
        entrada_projetada = calcular_retracao_fibonacci_smc(swing_high, swing_low)['fib_618']
        stop_projetado = swing_low
        if preco_atual < entrada_projetada:
            entrada_projetada = preco_atual
        risco = entrada_projetada - stop_projetado
        alvos = [entrada_projetada + mult * risco for mult in multiplicadores]
        alvos_validos = [a for a in alvos if a > entrada_projetada]
    else:  # SHORT
        entrada_projetada = calcular_retracao_fibonacci_smc(swing_high, swing_low)['fib_382']
        stop_projetado = swing_high
        if preco_atual > entrada_projetada:
            entrada_projetada = preco_atual
        risco = stop_projetado - entrada_projetada
        alvos = [entrada_projetada - mult * risco for mult in multiplicadores]
        alvos_validos = [a for a in alvos if a < entrada_projetada]
    alvos_finais = alvos_validos[:8]
    if direcao_smc == "SHORT":
        alvos_finais.sort(reverse=True)
    else:
        alvos_finais.sort()
    return {
        "direcao": direcao_smc,
        "swing_high": swing_high,
        "swing_low": swing_low,
        "entrada": entrada_projetada,
        "stop": stop_projetado,
        "risco": risco,
        "alvos": alvos_finais,
        "multiplicadores": multiplicadores[:len(alvos_finais)]
    }

def analisar_confluencia(df_completo, txt, limiar_sinal=9.0, periodo_aquecimento=100):
    df_analise = df_completo.iloc[periodo_aquecimento:].copy()
    if df_analise.empty:
        return txt["neutro"], "#ffcc00", txt["erro_dados"], 0.0, 0.0, "NEUTRO"
    ultimo_reg = df_analise.iloc[-1]
    preco_atual = ultimo_reg["close"]
    pontos_alta = 0.0
    pontos_baixa = 0.0
    contexto_fib = txt["ctx_neutro"]
    swing_info = identificar_swing_smc(df_completo)
    if swing_info:
        swing_high = swing_info['swing_high']
        swing_low = swing_info['swing_low']
        fib_niveis_smc = calcular_retracao_fibonacci_smc(swing_high, swing_low)
        if preco_atual >= fib_niveis_smc['fib_382'] and preco_atual <= fib_niveis_smc['fib_0']:
            pontos_baixa += 2.5
            contexto_fib = txt["ctx_premium"]
        elif preco_atual <= fib_niveis_smc['fib_618'] and preco_atual >= fib_niveis_smc['fib_100']:
            pontos_alta += 2.5
            contexto_fib = txt["ctx_desconto"]
        else:
            contexto_fib = txt["ctx_neutro"]
        if swing_info['direction_from_swing'] == 'LONG':
            pontos_alta += 1.0
        elif swing_info['direction_from_swing'] == 'SHORT':
            pontos_baixa += 1.0
    rsi_val = ultimo_reg["RSI_14"]
    if not math.isnan(rsi_val):
        if rsi_val < 40: 
            pontos_alta += 2.5
        elif rsi_val > 60: 
            pontos_baixa += 2.5
    macd_hist = ultimo_reg["MACD_HIST"]
    if not math.isnan(macd_hist):
        if macd_hist > 0:
            pontos_alta += 2
        else:
            pontos_baixa += 2
    mfi_val = ultimo_reg["MFI"]
    if not math.isnan(mfi_val):
        if mfi_val < 40: 
            pontos_alta += 1.5
        elif mfi_val > 60: 
            pontos_baixa += 1.5
    if ultimo_reg["ssl_dir"] == 1:
        pontos_alta += 1.5
    else:
        pontos_baixa += 1.5
    if ultimo_reg["atr_dir"] == 1:
        pontos_alta += 1.5
    else:
        pontos_baixa += 1.5
    ppo_val = ultimo_reg["PPO"]
    ppo_sig = ultimo_reg["PPO_Signal"]
    if not (math.isnan(ppo_val) or math.isnan(ppo_sig)):
        if ppo_val > ppo_sig: 
            pontos_alta += 2
        else: 
            pontos_baixa += 2
    direcao = "NEUTRO"
    if pontos_alta >= limiar_sinal and pontos_alta > pontos_baixa:
        direcao = "LONG"
        return (txt["compra_forte"], "#00cc66",
                f"{contexto_fib} SMC + Confluência de Indicadores Bullish.",
                pontos_alta, pontos_baixa, direcao)
    elif pontos_baixa >= limiar_sinal and pontos_baixa > pontos_alta:
        direcao = "SHORT"
        return (txt["venda_forte"], "#ff3333",
                f"{contexto_fib} SMC + Confluência de Indicadores Bearish.",
                pontos_alta, pontos_baixa, direcao)
    else:
        media_50 = df_analise['close'].rolling(50).mean().iloc[-1]
        if preco_atual > media_50:
            direcao = "LONG"
        else:
            direcao = "SHORT"
        return txt["neutro"], "#ffcc00", contexto_fib, pontos_alta, pontos_baixa, direcao

# ─────────────────────────────────────────────────────────────────────────────
# BACKTEST
def calcular_assertividade_historica_robusta(df, limiar, periodo_aquecimento, txt, 
                                            target_profit_pct=1.0, look_ahead_candles=5):
    acertos = 0
    total_sinais = 0
    total_lucro_pct = 0.0
    total_risco_pct = 0.0
    operacoes_registradas = []
    if len(df) < periodo_aquecimento + PERIODO_SWING_DEFAULT + look_ahead_candles:
        return "Dados históricos insuficientes para testar a assertividade robusta.", {}
    inicio_backtest = periodo_aquecimento + PERIODO_SWING_DEFAULT
    for i in range(inicio_backtest, len(df) - look_ahead_candles):
        df_contexto = df.iloc[:i+1].copy()
        try:
            _, _, _, pontos_alta, pontos_baixa, direcao = analisar_confluencia(
                df_contexto, txt, limiar, periodo_aquecimento
            )
            sinal_fib = gerar_sinal_fibonacci(df_contexto, direcao, [1.0], PERIODO_SWING_DEFAULT)
            entrada = sinal_fib['entrada']
            stop_loss = sinal_fib['stop']
            if direcao == "LONG" and pontos_alta >= limiar:
                total_sinais += 1
                risco_pct = ((entrada - stop_loss) / entrada) * 100 if entrada > 0 else 0
                futuros = df.iloc[i+1 : i+1+look_ahead_candles]
                if not futuros.empty:
                    alvo_preco = entrada * (1 + target_profit_pct / 100)
                    if futuros['high'].max() >= alvo_preco:
                        acertos += 1
                        lucro_realizado = target_profit_pct
                    else:
                        lucro_realizado = ((futuros['close'].iloc[-1] - entrada) / entrada) * 100
                    total_lucro_pct += lucro_realizado
                    total_risco_pct += risco_pct
                    operacoes_registradas.append({
                        'timestamp': df_contexto['timestamp'].iloc[-1],
                        'direcao': 'LONG',
                        'entrada': entrada,
                        'stop_loss': stop_loss,
                        'alvo_preco': alvo_preco,
                        'lucro_realizado_pct': lucro_realizado,
                        'risco_pct': risco_pct,
                        'acerto': (futuros['high'].max() >= alvo_preco)
                    })
            elif direcao == "SHORT" and pontos_baixa >= limiar:
                total_sinais += 1
                risco_pct = ((stop_loss - entrada) / entrada) * 100 if entrada > 0 else 0
                futuros = df.iloc[i+1 : i+1+look_ahead_candles]
                if not futuros.empty:
                    alvo_preco = entrada * (1 - target_profit_pct / 100)
                    if futuros['low'].min() <= alvo_preco:
                        acertos += 1
                        lucro_realizado = target_profit_pct
                    else:
                        lucro_realizado = ((entrada - futuros['close'].iloc[-1]) / entrada) * 100
                    total_lucro_pct += lucro_realizado
                    total_risco_pct += risco_pct
                    operacoes_registradas.append({
                        'timestamp': df_contexto['timestamp'].iloc[-1],
                        'direcao': 'SHORT',
                        'entrada': entrada,
                        'stop_loss': stop_loss,
                        'alvo_preco': alvo_preco,
                        'lucro_realizado_pct': lucro_realizado,
                        'risco_pct': risco_pct,
                        'acerto': (futuros['low'].min() <= alvo_preco)
                    })
        except Exception:
            continue
    if total_sinais == 0:
        return "Nenhum sinal forte gerado no histórico recente para backtest. Tente reduzir a nota de corte ou ajustar o período de swing.", {}
    assertividade = (acertos / total_sinais) * 100
    lucro_medio_por_operacao = total_lucro_pct / total_sinais if total_sinais > 0 else 0
    risco_medio_por_operacao = total_risco_pct / total_sinais if total_sinais > 0 else 0
    ganhos = sum([op['lucro_realizado_pct'] for op in operacoes_registradas if op['lucro_realizado_pct'] > 0])
    perdas = sum([abs(op['lucro_realizado_pct']) for op in operacoes_registradas if op['lucro_realizado_pct'] < 0])
    fator_lucro = ganhos / perdas if perdas > 0 else (ganhos / 1e-10 if ganhos > 0 else 0)
    equity_curve = [100]
    max_drawdown = 0
    peak = 100
    for op in operacoes_registradas:
        equity_curve.append(equity_curve[-1] * (1 + op['lucro_realizado_pct'] / 100))
        if equity_curve[-1] > peak:
            peak = equity_curve[-1]
        drawdown = (peak - equity_curve[-1]) / peak * 100
        if drawdown > max_drawdown:
            max_drawdown = drawdown
    resultado_str = f"""
    **Resultados do Backtest:**
    - Sinais Gerados: {total_sinais}
    - Acertos: {acertos}
    - Assertividade: {assertividade:.1f}%
    - Lucro Médio por Operação: {lucro_medio_por_operacao:.2f}%
    - Risco Médio por Operação: {risco_medio_por_operacao:.2f}%
    - Fator de Lucro: {fator_lucro:.2f}
    - Drawdown Máximo: {max_drawdown:.2f}%
    - Relação Risco/Retorno Média: {lucro_medio_por_operacao / risco_medio_por_operacao if risco_medio_por_operacao > 0 else 0:.2f}:1
    """
    return resultado_str, {'equity_curve': equity_curve, 'operacoes': operacoes_registradas}

# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO
def renderizar_grafico_plotly(df_completo, simbolo_id, look_ahead_candles, operacoes_backtest=None):
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
    if operacoes_backtest:
        diff_mean = df_grafico['time'].diff().mean()
        if pd.notna(diff_mean):
            delta_tempo = diff_mean * look_ahead_candles
        else:
            delta_tempo = pd.Timedelta(minutes=5)
        for op in operacoes_backtest:
            if op['direcao'] == 'LONG':
                fig.add_trace(go.Scatter(
                    x=[pd.to_datetime(op['timestamp'], unit='ms')],
                    y=[op['entrada']],
                    mode='markers',
                    marker=dict(symbol='triangle-up', size=10, color='green'),
                    name='Entrada LONG',
                    showlegend=False
                ))
                if op['acerto']:
                    fig.add_trace(go.Scatter(
                        x=[pd.to_datetime(op['timestamp'], unit='ms') + delta_tempo],
                        y=[op['alvo_preco']],
                        mode='markers',
                        marker=dict(symbol='star', size=10, color='lime'),
                        name='Alvo LONG Atingido',
                        showlegend=False
                    ))
                fig.add_trace(go.Scatter(
                    x=[pd.to_datetime(op['timestamp'], unit='ms')],
                    y=[op['stop_loss']],
                    mode='markers',
                    marker=dict(symbol='x', size=10, color='red'),
                    name='Stop LONG',
                    showlegend=False
                ))
            elif op['direcao'] == 'SHORT':
                fig.add_trace(go.Scatter(
                    x=[pd.to_datetime(op['timestamp'], unit='ms')],
                    y=[op['entrada']],
                    mode='markers',
                    marker=dict(symbol='triangle-down', size=10, color='red'),
                    name='Entrada SHORT',
                    showlegend=False
                ))
                if op['acerto']:
                    fig.add_trace(go.Scatter(
                        x=[pd.to_datetime(op['timestamp'], unit='ms') + delta_tempo],
                        y=[op['alvo_preco']],
                        mode='markers',
                        marker=dict(symbol='star', size=10, color='orange'),
                        name='Alvo SHORT Atingido',
                        showlegend=False
                    ))
                fig.add_trace(go.Scatter(
                    x=[pd.to_datetime(op['timestamp'], unit='ms')],
                    y=[op['stop_loss']],
                    mode='markers',
                    marker=dict(symbol='x', size=10, color='green'),
                    name='Stop SHORT',
                    showlegend=False
                ))
    fig.update_layout(
        paper_bgcolor='#0b0f19',
        plot_bgcolor='#0b0f19',
        font=dict(color='#e2e8f0'),
        xaxis=dict(gridcolor='#1e293b', showgrid=True, rangeslider=dict(visible=False)),
        yaxis=dict(gridcolor='#1e293b', showgrid=True),
        legend=dict(bgcolor='#1e293b', bordercolor='#475569', borderwidth=1),
        margin=dict(l=10, r=10, t=30, b=10),
        height=520
    )
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN (UI)
async def main():
    idiomas_disponiveis = list(DICIONARIO_LINGUAS.keys())
    st.sidebar.markdown(f"### {DICIONARIO_LINGUAS['Português (BR)']['idioma_label']}")
    idioma_selecionado = st.sidebar.selectbox(
        DICIONARIO_LINGUAS['Português (BR)']['idioma_selecao'],
        options=idiomas_disponiveis,
        index=0
    )
    txt = DICIONARIO_LINGUAS[idioma_selecionado]
    st.title(txt["titulo"])
    st.sidebar.header(txt["config_globais"])
    
    # Chamada síncrona com cache
    lista_criptos = obter_todos_pares_usdt()
    if not lista_criptos:
        lista_criptos = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]
    
    simbolo_id = st.sidebar.selectbox(
        txt["selecione_cripto"],
        lista_criptos,
        index=lista_criptos.index("SOL/USDT") if "SOL/USDT" in lista_criptos else 0
    )
    
    intervalos = txt["intervalos"]
    intervalo_escolhido = st.sidebar.selectbox(
        txt["tempo_grafico"],
        list(intervalos.keys()),
        index=5
    )
    timeframe = intervalos[intervalo_escolhido]
    
    st.sidebar.markdown("---")
    modo_vivo = st.sidebar.toggle(txt["modo_vivo"], value=False)
    intervalo_refresh = st.sidebar.slider(
        txt["intervalo_refresh"], min_value=15, max_value=120, value=30
    )
    
    st.sidebar.markdown("### 🎯 Configuração dos Alvos")
    multiplicadores_padrao = [0.236, 0.5, 0.786, 1.272, 2.236, 3.618, 5.0, 8.0]
    multiplicadores_str = st.sidebar.text_input(
        "Multiplicadores (separados por vírgula):",
        value=",".join(map(str, multiplicadores_padrao))
    )
    try:
        multiplicadores = [float(x.strip()) for x in multiplicadores_str.split(",") if x.strip()]
        if not multiplicadores:
            multiplicadores = multiplicadores_padrao
    except:
        multiplicadores = multiplicadores_padrao
    
    periodo_swing = st.sidebar.slider(
        "Período do Swing (velas):",
        min_value=10, max_value=200, value=PERIODO_SWING_DEFAULT
    )
    
    st.sidebar.markdown("### ⚙️ Ajuste de Assertividade")
    limiar_sinal = st.sidebar.slider(
        "Nota de corte para sinal forte (padrão 9.0):",
        min_value=5.0, max_value=12.0, value=9.0, step=0.5,
        help="Quanto maior, mais rigoroso. Para 1h, 9.0 é um bom equilíbrio entre filtro e oportunidades."
    )
    periodo_aquecimento_ui = st.sidebar.slider(
        "Velas de aquecimento (padrão 100):",
        min_value=50, max_value=300, value=100, step=10,
        help="Define quantas velas iniciais são ignoradas no cálculo. Para 1h, 100 velas = 4 dias."
    )

    target_profit_pct_ui = st.sidebar.slider(
        "Alvo de Lucro para Backtest (%):",
        min_value=0.5, max_value=5.0, value=1.0, step=0.1,
        help="Percentual de lucro considerado um 'acerto' no backtest."
    )
    look_ahead_candles_ui = st.sidebar.slider(
        "Velas para Buscar Alvo no Backtest:",
        min_value=3, max_value=20, value=5, step=1,
        help="Número de velas futuras para verificar se o alvo de lucro foi atingido."
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**BRICSVAULT PORTAL SMC PRO**")
    st.sidebar.markdown("Versão: 2.0 (Aprimorada com SMC e Async)")

    # PAINEL PRINCIPAL
    @st.fragment(run_every=intervalo_refresh if modo_vivo else None)
    async def painel_principal_fragment(simbolo_id, timeframe, txt, modo_vivo, intervalo_refresh,
                                        multiplicadores, periodo_swing, limiar_sinal, periodo_aquecimento_ui,
                                        target_profit_pct_ui, look_ahead_candles_ui):
        df_dados = await carregar_dados_async(simbolo_id, timeframe)
        if df_dados is None or df_dados.empty:
            st.warning(txt["erro_dados"])
            return
        df_analise = df_dados.iloc[periodo_aquecimento_ui:]
        if df_analise.empty:
            st.warning(txt["erro_dados"])
            return
        ultimo_reg = df_analise.iloc[-1]
        preco_atual = ultimo_reg['close']
        st.markdown("---")
        col_preco1, col_preco2, col_preco3 = st.columns([1, 2, 1])
        with col_preco2:
            nome_curto = simbolo_id.split('/')[0]
            st.markdown(
                f"""
                <div style="text-align: center; padding: 15px; background: #1e293b; border-radius: 12px; border: 1px solid #475569;">
                    <span style="font-size: 32px; font-weight: bold; color: #e2e8f0;">
                        {formatar_preco(preco_atual)}
                    </span>
                    <br>
                    <span style="font-size: 16px; color: #94a3b8;">
                        {nome_curto} / USDT – {txt['preco_spot']}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )
        st.markdown("---")

        # Dados 24h e market cap – chamadas síncronas com cache
        dados_24h = obter_dados_24h(simbolo_id)
        variacao_24h = dados_24h.get("change") if dados_24h else 0.0
        volume_24h = dados_24h.get("volume") if dados_24h else None
        market_cap = obter_market_cap_robusto(simbolo_id)

        recomendacao, cor_sinal, analise, pontos_alta, pontos_baixa, direcao = analisar_confluencia(
            df_dados, txt, limiar_sinal, periodo_aquecimento_ui
        )

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

        sinal_fib = gerar_sinal_fibonacci(df_dados, direcao, multiplicadores, periodo_swing)

        st.markdown(f"### {txt['alvo_swing_title']}")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric(txt["direcao_operacao"], f"{sinal_fib['direcao']} 🚀")
        col2.metric(txt["entrada_projetada"], formatar_preco(sinal_fib['entrada']))
        col3.metric(txt["stop_projetado"], formatar_preco(sinal_fib['stop']), 
                    delta=f"{((sinal_fib['stop'] - sinal_fib['entrada'])/sinal_fib['entrada']*100):+.2f}%")
        col4.metric(txt["swing_alto"], formatar_preco(sinal_fib['swing_high']))
        col5.metric(txt["swing_baixo"], formatar_preco(sinal_fib['swing_low']))

        if sinal_fib['alvos']:
            alvos = sinal_fib['alvos']
            st.markdown("**🎯 Projeção dos Alvos:**")
            cols_alvos = st.columns(4)
            for i, preco_alvo in enumerate(alvos):
                label = txt["alvo_prefix"].format(n=i+1)
                if sinal_fib['direcao'] == "LONG":
                    pct = ((preco_alvo - sinal_fib['entrada']) / sinal_fib['entrada']) * 100
                else:
                    pct = ((sinal_fib['entrada'] - preco_alvo) / sinal_fib['entrada']) * 100
                cols_alvos[i % 4].metric(label, formatar_preco(preco_alvo), delta=f"{pct:+.2f}%")
        else:
            st.info(txt["sem_alvos"])

        st.divider()

        with st.expander("📊 Ver Assertividade nos Últimos Dados (Backtest Robusto)"):
            resultado_backtest = calcular_assertividade_historica_robusta(
                df_dados, limiar_sinal, periodo_aquecimento_ui, txt, 
                target_profit_pct=target_profit_pct_ui, look_ahead_candles=look_ahead_candles_ui
            )
            if isinstance(resultado_backtest, tuple):
                resultado_backtest_str, backtest_metrics = resultado_backtest
                st.markdown(resultado_backtest_str)
                st.caption("💡 Quanto maior a porcentagem, mais confiável a configuração atual para o ativo e timeframe escolhidos.")
                if 'equity_curve' in backtest_metrics and len(backtest_metrics['equity_curve']) > 1:
                    st.subheader("Curva de Capital (Equity Curve)")
                    fig_equity = go.Figure(data=go.Scatter(y=backtest_metrics['equity_curve'], mode='lines'))
                    fig_equity.update_layout(
                        title='Equity Curve',
                        xaxis_title='Número de Operações',
                        yaxis_title='Capital (%)',
                        paper_bgcolor='#0b0f19',
                        plot_bgcolor='#0b0f19',
                        font=dict(color='#e2e8f0')
                    )
                    st.plotly_chart(fig_equity, use_container_width=True)
            else:
                st.markdown(resultado_backtest)
                backtest_metrics = {}

        nome_extenso = obter_nome_extenso_cripto(simbolo_id)
        label_market_cap = f"{txt['market_cap']}"
        if market_cap is None:
            market_cap_display = txt['marketcap_nao_disponivel']
        else:
            market_cap_display = formatar_market_cap(market_cap)

        st.markdown(f"### {txt['grafico_titulo']}")
        renderizar_grafico_plotly(df_dados, simbolo_id, look_ahead_candles_ui, 
                                  operacoes_backtest=backtest_metrics.get('operacoes') if isinstance(backtest_metrics, dict) else None)

        st.markdown("---")
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric(txt["preco_spot"], formatar_preco(preco_atual))
        with col_info2:
            st.metric(txt["variacao_24h"], f"{variacao_24h:.2f}%", delta=f"{variacao_24h:.2f}%")
        with col_info3:
            st.metric(txt["volume_24h"], formatar_market_cap(volume_24h))
        st.metric(label_market_cap, market_cap_display)

        if modo_vivo:
            st.markdown(f"<p style='text-align: right; color: #94a3b8;'>{txt['ultima_atualizacao']}: {datetime.now().strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: right; color: #94a3b8;'>{txt['proximo_refresh']} {intervalo_refresh} {txt['segundos']}</p>", unsafe_allow_html=True)

    await painel_principal_fragment(simbolo_id, timeframe, txt, modo_vivo, intervalo_refresh,
                                    multiplicadores, periodo_swing, limiar_sinal, periodo_aquecimento_ui,
                                    target_profit_pct_ui, look_ahead_candles_ui)

if __name__ == "__main__":
    asyncio.run(main())
