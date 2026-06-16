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
from datetime import datetime

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
        "selecione_exchange": "Selecione a Exchange de Dados:",
        "tempo_grafico": "Tempo Gráfico:",
        "modo_vivo": "Ativar Monitoramento em Tempo Real",
        "intervalo_refresh": "Intervalo de Atualização (Segundos):",
        "preco_spot": "Preço Spot Real",
        "variacao_24h": "Variação 24h",
        "volume_24h": "Volume 24h",
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
        "fonte_dados": "Fonte dos Dados",
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
        "selecione_exchange": "Select Data Exchange:",
        "tempo_grafico": "Timeframe:",
        "modo_vivo": "Enable Real-Time Monitoring",
        "intervalo_refresh": "Refresh Interval (Seconds):",
        "preco_spot": "Real Spot Price",
        "variacao_24h": "24h Variation",
        "volume_24h": "24h Volume",
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
        "fonte_dados": "Data Source",
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


def formatar_volume(valor):
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return "—"
    if valor >= 1_000_000_000:
        return f"{valor / 1_000_000_000:.2f}B"
    elif valor >= 1_000_000:
        return f"{valor / 1_000_000:.2f}M"
    elif valor >= 1_000:
        return f"{valor / 1_000:.2f}K"
    else:
        return f"{valor:.2f}"


# ─────────────────────────────────────────────────────────────────────────────
# GERENCIADOR DE EXCHANGES
class ExchangeManager:
    """Gerencia múltiplas exchanges com fallback e cache."""
    
    EXCHANGES = {
        "Gate.io": {
            "class": ccxt.gate,
            "config": {"enableRateLimit": True, "options": {"defaultType": "spot"}},
            "base_url": "https://api.gateio.ws/api/v4",
            "pair_separator": "/",
            "ticker_endpoint": "spot/tickers",
            "has_volume_usd": False
        },
        "Kraken": {
            "class": ccxt.kraken,
            "config": {"enableRateLimit": True},
            "base_url": "https://api.kraken.com/0/public",
            "pair_separator": "/",
            "ticker_endpoint": "Ticker",
            "has_volume_usd": False
        },
        "MEXC": {
            "class": ccxt.mexc,
            "config": {"enableRateLimit": True},
            "base_url": "https://api.mexc.com/api/v3",
            "pair_separator": "",
            "ticker_endpoint": "ticker/24hr",
            "has_volume_usd": True,  # quoteVolume disponível
        },
        "KuCoin": {
            "class": ccxt.kucoin,
            "config": {"enableRateLimit": True},
            "base_url": "https://api.kucoin.com/api/v1",
            "pair_separator": "-",
            "ticker_endpoint": "market/stats",
            "has_volume_usd": True,  # volValue disponível
        },
        "Robinhood": {
            "class": ccxt.robinhood,
            "config": {"enableRateLimit": True},
            "base_url": "https://api.robinhood.com/crypto",
            "pair_separator": "/",
            "ticker_endpoint": "market/best-price",
            "has_volume_usd": False
        }
    }
    
    def __init__(self):
        self.clients = {}
        self._init_clients()
    
    def _init_clients(self):
        for name, config in self.EXCHANGES.items():
            try:
                self.clients[name] = config["class"](config["config"])
            except Exception as e:
                st.warning(f"Erro ao inicializar {name}: {e}")
    
    def get_client(self, exchange_name):
        return self.clients.get(exchange_name)
    
    def get_exchange_names(self):
        return list(self.EXCHANGES.keys())
    
    def get_pair_separator(self, exchange_name):
        return self.EXCHANGES.get(exchange_name, {}).get("pair_separator", "/")
    
    def has_volume_usd(self, exchange_name):
        return self.EXCHANGES.get(exchange_name, {}).get("has_volume_usd", False)


# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÕES DE MERCADO POR EXCHANGE

@st.cache_data(ttl=3600)
def obter_pares_exchange(exchange_name):
    """Obtém todos os pares USDT de uma exchange específica."""
    manager = ExchangeManager()
    client = manager.get_client(exchange_name)
    if not client:
        return []
    try:
        markets = client.load_markets()
        separator = manager.get_pair_separator(exchange_name)
        # Filtra pares que terminam com USDT
        pairs = [s for s in markets.keys() if s.endswith('/USDT')]
        if not pairs:
            # Tenta com separador diferente (ex: MEXC usa BTCUSDT sem "/")
            pairs = [s for s in markets.keys() if s.endswith('USDT') and '/' not in s]
        return sorted(pairs)
    except Exception:
        return []


@st.cache_data(ttl=60)
def obter_dados_24h(exchange_name, simbolo):
    """
    Obtém dados de 24h (preço, variação, volume) via API REST direta,
    aproveitando endpoints específicos de cada exchange.
    """
    manager = ExchangeManager()
    client = manager.get_client(exchange_name)
    if not client:
        return None
    
    try:
        # Tenta via ccxt primeiro (mais genérico)
        ticker = client.fetch_ticker(simbolo)
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
            # Se não tem volume em USD, tenta via API específica
            if not result["volume"] and manager.has_volume_usd(exchange_name):
                result["volume"] = obter_volume_usd_direto(exchange_name, simbolo)
            return result
    except Exception:
        pass
    
    # Fallback: chamada REST direta para exchanges que têm endpoints específicos
    return obter_dados_24h_direto(exchange_name, simbolo)


def obter_dados_24h_direto(exchange_name, simbolo):
    """Chamadas REST diretas para endpoints específicos de cada exchange."""
    try:
        if exchange_name == "Gate.io":
            # /api/v4/spot/tickers?currency_pair=BTC_USDT
            pair = simbolo.replace("/", "_")
            url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={pair}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    d = data[0]
                    return {
                        "last": float(d.get("last", 0)),
                        "change": float(d.get("change_percentage", 0)),
                        "volume": float(d.get("quote_volume", 0)),
                        "high": float(d.get("high_24h", 0)),
                        "low": float(d.get("low_24h", 0)),
                        "bid": float(d.get("highest_bid", 0)),
                        "ask": float(d.get("lowest_ask", 0))
                    }
        
        elif exchange_name == "Kraken":
            # /0/public/Ticker?pair=XXBTZUSD
            pair_map = {
                "BTC/USDT": "XXBTZUSD", "ETH/USDT": "XETHZUSD", "SOL/USDT": "SOLUSD",
                "XRP/USDT": "XXRPZUSD", "BNB/USDT": "BNBUSD", "ADA/USDT": "ADAUSD"
            }
            kraken_pair = pair_map.get(simbolo, simbolo.replace("/", ""))
            url = f"https://api.kraken.com/0/public/Ticker?pair={kraken_pair}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("error") or not data.get("result"):
                    return None
                for key, d in data["result"].items():
                    return {
                        "last": float(d.get("c", [0])[0]),
                        "change": float(d.get("p", [0, 0])[1]) if d.get("p") else 0,
                        "volume": float(d.get("v", [0, 0])[1]),
                        "high": float(d.get("h", [0, 0])[1]),
                        "low": float(d.get("l", [0, 0])[1]),
                        "bid": float(d.get("b", [0])[0]),
                        "ask": float(d.get("a", [0])[0])
                    }
        
        elif exchange_name == "MEXC":
            # /api/v3/ticker/24hr?symbol=BTCUSDT
            pair = simbolo.replace("/", "")
            url = f"https://api.mexc.com/api/v3/ticker/24hr?symbol={pair}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                d = resp.json()
                return {
                    "last": float(d.get("lastPrice", 0)),
                    "change": float(d.get("priceChangePercent", 0)),
                    "volume": float(d.get("quoteVolume", 0)) or float(d.get("volume", 0)),
                    "high": float(d.get("highPrice", 0)),
                    "low": float(d.get("lowPrice", 0)),
                    "bid": float(d.get("bidPrice", 0)),
                    "ask": float(d.get("askPrice", 0))
                }
        
        elif exchange_name == "KuCoin":
            # /api/v1/market/stats?symbol=BTC-USDT
            pair = simbolo.replace("/", "-")
            url = f"https://api.kucoin.com/api/v1/market/stats?symbol={pair}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "200000":
                    d = data.get("data", {})
                    return {
                        "last": float(d.get("last", 0)),
                        "change": float(d.get("changeRate", 0)) * 100,
                        "volume": float(d.get("volValue", 0)),
                        "high": float(d.get("high", 0)),
                        "low": float(d.get("low", 0)),
                        "bid": float(d.get("buy", 0)),
                        "ask": float(d.get("sell", 0))
                    }
        
        elif exchange_name == "Robinhood":
            # /crypto/market/best-price?symbol=BTCUSD
            pair = simbolo.replace("/", "")
            url = f"https://api.robinhood.com/crypto/market/best-price?symbol={pair}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                d = resp.json()
                return {
                    "last": float(d.get("price", 0)),
                    "change": None,  # Robinhood não fornece variação via este endpoint
                    "volume": None,
                    "high": None,
                    "low": None,
                    "bid": float(d.get("bid_price", 0)),
                    "ask": float(d.get("ask_price", 0))
                }
    except Exception as e:
        pass
    return None


def obter_volume_usd_direto(exchange_name, simbolo):
    """Obtém volume em USD via endpoints específicos."""
    try:
        if exchange_name == "MEXC":
            pair = simbolo.replace("/", "")
            url = f"https://api.mexc.com/api/v3/ticker/24hr?symbol={pair}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return float(resp.json().get("quoteVolume", 0))
        elif exchange_name == "KuCoin":
            pair = simbolo.replace("/", "-")
            url = f"https://api.kucoin.com/api/v1/market/stats?symbol={pair}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "200000":
                    return float(data.get("data", {}).get("volValue", 0))
    except:
        pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# MARKET CAP — CoinGecko + CoinCap (fallback)

@st.cache_data(ttl=3600)
def obter_id_coingecko(simbolo):
    try:
        url = "https://api.coingecko.com/api/v3/search"
        params = {"query": simbolo}
        headers = {"Accept": "application/json"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
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


@st.cache_data(ttl=600)
def obter_market_cap_coingecko(simbolo):
    coin_id = obter_id_coingecko(simbolo)
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
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            dados = resp.json()
            if dados and len(dados) > 0:
                mc = dados[0].get("market_cap")
                if mc and float(mc) > 1_000_000:
                    return float(mc)
        return None
    except Exception:
        return None


@st.cache_data(ttl=600)
def obter_market_cap_coincap(simbolo):
    try:
        asset_id = simbolo.lower()
        url = f"https://api.coincap.io/v2/assets/{asset_id}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            mc = data.get("data", {}).get("marketCapUsd")
            if mc:
                mc_float = float(mc)
                if mc_float > 1_000_000:
                    return mc_float
        url_list = "https://api.coincap.io/v2/assets"
        params = {"limit": 2000}
        resp = requests.get(url_list, params=params, timeout=10)
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


def obter_market_cap_robusto(simbolo_id):
    simbolo = simbolo_id.split('/')[0]
    mc = obter_market_cap_coingecko(simbolo)
    if mc is not None:
        return mc
    mc = obter_market_cap_coincap(simbolo)
    if mc is not None:
        return mc
    return None


# ─────────────────────────────────────────────────────────────────────────────
# INDICADORES TÉCNICOS (mantidos do código original)

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
# CARREGAMENTO DE DADOS (multi-exchange)

@st.cache_data(ttl=60)
def carregar_dados(exchange_name, simbolo_id, timeframe_selecionado):
    """Carrega dados históricos da exchange selecionada."""
    manager = ExchangeManager()
    client = manager.get_client(exchange_name)
    if not client:
        return None
    
    try:
        # Ajusta o símbolo para o formato esperado pela exchange
        # Algumas exchanges (MEXC) não usam "/"
        if exchange_name == "MEXC":
            simbolo = simbolo_id.replace("/", "")
        else:
            simbolo = simbolo_id
        
        velas = client.fetch_ohlcv(
            simbolo,
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

        # Calcular indicadores
        df['RSI_14'] = calcular_rsi(df['close'], 14)
        macd, sinal, hist = calcular_macd(df['close'])
        df['MACD'] = macd
        df['MACD_SIGNAL'] = sinal
        df['MACD_HIST'] = hist
        df['MFI'] = calcular_mfi(df)
        df = calcular_ssl_hybrid(df)
        df = calcular_atr_stop(df)
        df = calcular_ppo(df)

        df['SSL_Baseline'] = df['SSL_Baseline'].ffill()
        df['ATR_Stop'] = df['ATR_Stop'].replace(0, np.nan).ffill()

        return df.dropna(subset=['close']).reset_index(drop=True)
    except Exception as e:
        st.error(f"Erro ao carregar dados da {exchange_name}: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# ANÁLISE DE CONFLUÊNCIA SMC
def analisar_confluencia(df_completo, txt):
    df_analise = df_completo.iloc[PERIODO_AQUECIMENTO:].copy()

    if df_analise.empty:
        return txt["neutro"], "#ffcc00", txt["ctx_neutro"], 0.0, 0.0

    u = df_analise.iloc[-1]
    preco_atual = u['close']
    fib_niveis = calcular_retracao_fibonacci(df_analise)

    pontos_alta = 0.0
    pontos_baixa = 0.0

    rsi_val = u['RSI_14']
    if not math.isnan(rsi_val):
        if rsi_val < 40:
            pontos_alta += 2
        elif rsi_val > 60:
            pontos_baixa += 2

    macd_hist = u['MACD_HIST']
    if not math.isnan(macd_hist):
        if macd_hist > 0:
            pontos_alta += 2
        else:
            pontos_baixa += 2

    mfi_val = u['MFI']
    if not math.isnan(mfi_val):
        if mfi_val > 50:
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

    ppo_val = u['PPO']
    ppo_sig = u['PPO_Signal']
    if not (math.isnan(ppo_val) or math.isnan(ppo_sig)):
        if ppo_val > ppo_sig:
            pontos_alta += 1.5
        else:
            pontos_baixa += 1.5

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
def renderizar_grafico_plotly(df_completo, simbolo_id, exchange_name):
    df_grafico = df_completo.iloc[PERIODO_AQUECIMENTO:].copy()

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df_grafico['time'],
        open=df_grafico['open'],
        high=df_grafico['high'],
        low=df_grafico['low'],
        close=df_grafico['close'],
        name=f"{simbolo_id} ({exchange_name})",
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

# Inicializa o gerenciador de exchanges
exchange_manager = ExchangeManager()
exchange_options = exchange_manager.get_exchange_names()

# Seleção da exchange
exchange_selecionada = st.sidebar.selectbox(
    txt["selecione_exchange"],
    exchange_options,
    index=0
)

# Obtém pares da exchange selecionada
lista_criptos = obter_pares_exchange(exchange_selecionada)
if not lista_criptos:
    st.sidebar.warning(f"Não foi possível carregar pares da {exchange_selecionada}. Usando lista padrão.")
    lista_criptos = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]

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
def painel_principal(exchange_name, simbolo_id, timeframe, txt, modo_vivo, intervalo_refresh):
    # Carrega dados históricos da exchange selecionada
    df_dados = carregar_dados(exchange_name, simbolo_id, timeframe)

    if df_dados is None or df_dados.empty:
        st.warning(txt["erro_dados"])
        return

    df_analise = df_dados.iloc[PERIODO_AQUECIMENTO:]
    if df_analise.empty:
        st.warning(txt["erro_dados"])
        return

    ultimo_reg = df_analise.iloc[-1]
    preco_atual = ultimo_reg['close']

    # Obtém dados de 24h da exchange
    dados_24h = obter_dados_24h(exchange_name, simbolo_id)
    variacao_24h = dados_24h.get("change") if dados_24h else 0.0
    volume_24h = dados_24h.get("volume") if dados_24h else None
    
    # Market Cap
    market_cap = obter_market_cap_robusto(simbolo_id)

    # Análise SMC
    recomendacao, cor_sinal, analise, pontos_alta, pontos_baixa = analisar_confluencia(
        df_dados, txt
    )

    ppo_line = ultimo_reg['PPO']
    ppo_sig = ultimo_reg['PPO_Signal']
    ppo_txt = (
        f"PPO: {ppo_line:.3f} / Signal: {ppo_sig:.3f}"
        if not (math.isnan(ppo_line) or math.isnan(ppo_sig))
        else "PPO: —"
    )
    
    # Exibe a exchange de origem dos dados
    st.markdown(f"**{txt['fonte_dados']}:** {exchange_name}")

    st.markdown(f"""
    <div style="background:{cor_sinal}22;padding:20px;border-radius:10px;
                border:2px solid {cor_sinal};margin-bottom:20px;">
    <h2 style="margin:0;color:{cor_sinal};">{recomendacao}</h2>
    <p style="margin:8px 0 0 0;color:#ddd;">{analise} | <b>{ppo_txt}</b></p>
    </div>
    """, unsafe_allow_html=True)

    # Métricas - agora com 6 colunas para incluir Volume 24h
    nome_completo_ativo = simbolo_id.split('/')[0]
    label_preco = f"{nome_completo_ativo} | {txt['preco_spot']}"

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric(label_preco, formatar_preco(preco_atual))
    m2.metric(txt["variacao_24h"], f"{variacao_24h:+.2f}%" if variacao_24h is not None else "—")
    m3.metric(txt["volume_24h"], formatar_volume(volume_24h) if volume_24h else "—")

    if market_cap is not None:
        m4.metric(txt["market_cap"], formatar_market_cap(market_cap))
    else:
        m4.metric(txt["market_cap"], txt["marketcap_nao_disponivel"])

    m5.metric(txt["pontos_compra"], f"{pontos_alta:.1f}")
    m6.metric(txt["pontos_venda"], f"{pontos_baixa:.1f}")

    # Stop ATR
    atr_stop_val = ultimo_reg['ATR_Stop']
    st.markdown(
        f"**{txt['stop_atr']}:** {formatar_preco(atr_stop_val)}"
        f"  |  RSI: **{ultimo_reg['RSI_14']:.1f}**"
        f"  |  MFI: **{ultimo_reg['MFI']:.1f}**"
    )

    # Gráfico
    st.markdown(f"### {txt['grafico_titulo']}")
    renderizar_grafico_plotly(df_dados, simbolo_id, exchange_name)

    # Status
    hora_atual = pd.Timestamp.now().strftime("%H:%M:%S")
    n_velas = len(df_analise)
    if modo_vivo:
        st.info(
            f"🟢 {txt['ultima_atualizacao']}: {hora_atual} | "
            f"{txt['proximo_refresh']} {intervalo_refresh} {txt['segundos']} | "
            f"{txt['aviso_aquecimento']}: {PERIODO_AQUECIMENTO} | "
            f"Velas analisadas: {n_velas} | Fonte: {exchange_name}"
        )
    else:
        st.info(
            f"⏸ {txt['ultima_atualizacao']}: {hora_atual} | "
            f"{txt['aviso_aquecimento']}: {PERIODO_AQUECIMENTO} | "
            f"Velas analisadas: {n_velas} | Fonte: {exchange_name}"
        )


painel_principal(exchange_selecionada, simbolo_id, timeframe, txt, modo_vivo, intervalo_refresh)
