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

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False
    st.warning("Para a aba de ações, instale yfinance: pip install yfinance")

st.set_page_config(
    page_title="BRICSVAULT PORTAL SMC",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
VELAS_TOTAL = 500
PERIODO_AQUECIMENTO = 100

# ─────────────────────────────────────────────────────────────────────────────
# DICIONÁRIO DE IDIOMAS – 15 idiomas
DICIONARIO_LINGUAS = {
    "Português (BR)": {
        "titulo": "🏦  BRICSVAULT PORTAL - Motor SMC",
        "aba_cripto": "🪙 Criptomoedas",
        "aba_acoes": "📈 Ações (Bolsas)",
        "config_globais": "⚙️  Configurações Globais",
        "selecione_cripto": "Selecione Criptomoeda (/USDT):",
        "selecione_corretora_acoes": "Selecione a Corretora (Bolsa):",
        "ticker_acoes": "Digite o Ticker (ex: AAPL, PETR4.SA):",
        "tempo_grafico": "Tempo Gráfico:",
        "modo_vivo": "Ativar Monitoramento em Tempo Real",
        "intervalo_refresh": "Intervalo de Atualização (Segundos):",
        "preco_spot": "Preço Spot Real",
        "variacao_24h": "Variação 24h",
        "volume_24h": "Volume 24h (USDT)",
        "market_cap": "Market Cap (USD)",
        "stop_atr": "Preço Stop ATR",
        "compra_forte": "🟢  COMPRA FORTE (SMC + FIBONACCI ALINHADOS)",
        "venda_forte": "🔴  VENDA FORTE (SMC + FIBONACCI ALINHADOS)",
        "neutro": "🟡  NEUTRO (AGUARDAR SMC)",
        "erro_dados": "Dados insuficientes. Tente outro ativo ou reduza o Tempo Gráfico.",
        "ctx_desconto": "Ativo em Zona de Desconto de Fibonacci (Excelente risco/retorno).",
        "ctx_premium": "Ativo em Zona Premium de Fibonacci (Preço esticado, propício para lucro).",
        "ctx_neutro": "Preço em zona neutra de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Última Atualização",
        "proximo_refresh": "Próximo refresh em",
        "segundos": "segundos",
        "pontos_compra": "Pontos de Compra",
        "pontos_venda": "Pontos de Venda",
        "grafico_titulo": "📈  Gráfico Interativo",
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
        "titulo": "🏦  BRICSVAULT PORTAL - SMC Engine",
        "aba_cripto": "🪙 Cryptocurrencies",
        "aba_acoes": "📈 Stocks (Exchanges)",
        "config_globais": "⚙️  Global Settings",
        "selecione_cripto": "Select Cryptocurrency (/USDT):",
        "selecione_corretora_acoes": "Select Broker (Exchange):",
        "ticker_acoes": "Enter Ticker (e.g., AAPL, PETR4.SA):",
        "tempo_grafico": "Timeframe:",
        "modo_vivo": "Enable Real-Time Monitoring",
        "intervalo_refresh": "Refresh Interval (Seconds):",
        "preco_spot": "Spot Price",
        "variacao_24h": "24h Change",
        "volume_24h": "24h Volume (USD)",
        "market_cap": "Market Cap (USD)",
        "stop_atr": "ATR Stop Price",
        "compra_forte": "🟢  STRONG BUY (SMC + FIBONACCI ALIGNED)",
        "venda_forte": "🔴  STRONG SELL (SMC + FIBONACCI ALIGNED)",
        "neutro": "🟡  NEUTRAL (AWAIT SMC)",
        "erro_dados": "Insufficient data. Try another asset or reduce the Timeframe.",
        "ctx_desconto": "Asset in Fibonacci Discount Zone (Excellent risk/reward).",
        "ctx_premium": "Asset in Fibonacci Premium Zone (Price stretched, suitable for profit-taking).",
        "ctx_neutro": "Price in neutral Fibonacci zone (Fair Value Zone).",
        "ultima_atualizacao": "Last Update",
        "proximo_refresh": "Next refresh in",
        "segundos": "seconds",
        "pontos_compra": "Buy Points",
        "pontos_venda": "Sell Points",
        "grafico_titulo": "📈  Interactive Chart",
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
    # Demais idiomas (Espanhol, Francês, Alemão, Italiano, Russo, Japonês, Chinês, Hindi, Bengali, Árabe, Coreano, Vietnamita, Turco)
    # devem ser incluídos com as mesmas chaves, apenas com os textos traduzidos.
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
        return f"$ {valor:,.2f}"


def formatar_volume_usdt(valor):
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return "—"
    if valor >= 1_000_000_000_000:
        return f"$ {valor / 1_000_000_000_000:.2f}T"
    elif valor >= 1_000_000_000:
        return f"$ {valor / 1_000_000_000:.2f}B"
    elif valor >= 1_000_000:
        return f"$ {valor / 1_000_000:.2f}M"
    else:
        return f"$ {valor:,.2f}"


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
        return (txt["compra_forte"], "#00cc66",
                f"{contexto_fib} SMC + PPO Order Flow Bullish.",
                pontos_alta, pontos_baixa)
    elif pontos_baixa >= 8.5:
        return (txt["venda_forte"], "#ff3333",
                f"{contexto_fib} SMC + PPO Order Flow Bearish.",
                pontos_alta, pontos_baixa)
    else:
        return txt["neutro"], "#ffcc00", contexto_fib, pontos_alta, pontos_baixa


def renderizar_grafico_plotly(df, titulo, nome_ativo):
    df_graf = df.iloc[PERIODO_AQUECIMENTO:].copy()
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df_graf['time'],
        open=df_graf['open'],
        high=df_graf['high'],
        low=df_graf['low'],
        close=df_graf['close'],
        name=nome_ativo,
        increasing_line_color='#10b981',
        decreasing_line_color='#ef4444'
    ))
    fig.add_trace(go.Scatter(
        x=df_graf['time'],
        y=df_graf['SSL_Baseline'],
        mode='lines',
        name='SMC Baseline (SSL)',
        line=dict(color='#00aaff', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=df_graf['time'],
        y=df_graf['ATR_Stop'],
        mode='lines',
        name='ATR Trailing Stop',
        line=dict(color='#ffaa00', width=1, dash='dash')
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
    st.plotly_chart(fig, width='stretch')


# ─────────────────────────────────────────────────────────────────────────────
# PARTE 1 – CRIPTOMOEDAS
class ExchangeManagerCrypto:
    EXCHANGES = {
        "Gate.io": {"class": ccxt.gate, "config": {"enableRateLimit": True, "options": {"defaultType": "spot"}}, "separator": "/"},
        "Kraken": {"class": ccxt.kraken, "config": {"enableRateLimit": True}, "separator": "/"},
        "MEXC": {"class": ccxt.mexc, "config": {"enableRateLimit": True}, "separator": ""},
        "KuCoin": {"class": ccxt.kucoin, "config": {"enableRateLimit": True}, "separator": "-"}
    }
    PRIORITY = ["Gate.io", "Kraken", "MEXC", "KuCoin"]

    def __init__(self):
        self.clients = {}
        for name, cfg in self.EXCHANGES.items():
            try:
                self.clients[name] = cfg["class"](cfg["config"])
            except:
                pass

    def get_client(self, name):
        return self.clients.get(name)

    def get_symbol(self, name, symbol):
        sep = self.EXCHANGES[name]["separator"]
        if name == "MEXC":
            return symbol.replace("/", "")
        elif name == "KuCoin":
            return symbol.replace("/", "-")
        return symbol


def obter_pares_usdt():
    manager = ExchangeManagerCrypto()
    client = manager.get_client("Gate.io")
    if not client:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]
    try:
        markets = client.load_markets()
        pairs = [s for s in markets.keys() if s.endswith('/USDT')]
        return sorted(pairs)
    except:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]


def obter_dados_24h_crypto(symbol):
    manager = ExchangeManagerCrypto()
    for name in manager.PRIORITY:
        client = manager.get_client(name)
        if not client:
            continue
        try:
            s = manager.get_symbol(name, symbol)
            ticker = client.fetch_ticker(s)
            if ticker and ticker.get('last'):
                return {
                    "last": ticker.get('last'),
                    "change": ticker.get('percentage'),
                    "volume": ticker.get('quoteVolume') or ticker.get('baseVolume'),
                    "high": ticker.get('high'),
                    "low": ticker.get('low'),
                    "bid": ticker.get('bid'),
                    "ask": ticker.get('ask')
                }
        except:
            continue
    return None


def carregar_dados_crypto(symbol, timeframe):
    manager = ExchangeManagerCrypto()
    for name in manager.PRIORITY:
        client = manager.get_client(name)
        if not client:
            continue
        try:
            s = manager.get_symbol(name, symbol)
            candles = client.fetch_ohlcv(s, timeframe=timeframe, limit=VELAS_TOTAL)
            if candles and len(candles) >= PERIODO_AQUECIMENTO + 50:
                df = pd.DataFrame(candles, columns=['timestamp','open','high','low','close','volume'])
                df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
                df['RSI_14'] = calcular_rsi(df['close'], 14)
                macd, sig, hist = calcular_macd(df['close'])
                df['MACD'] = macd
                df['MACD_SIGNAL'] = sig
                df['MACD_HIST'] = hist
                df['MFI'] = calcular_mfi(df)
                df = calcular_ssl_hybrid(df)
                df = calcular_atr_stop(df)
                df = calcular_ppo(df)
                df['SSL_Baseline'] = df['SSL_Baseline'].ffill()
                df['ATR_Stop'] = df['ATR_Stop'].replace(0, np.nan).ffill()
                return df.dropna(subset=['close']).reset_index(drop=True)
        except:
            continue
    return None


# ─────────────────────────────────────────────────────────────────────────────
# PARTE 2 – AÇÕES
def obter_dados_acoes(ticker, timeframe, periodo_dias=500):
    try:
        if '.SA' in ticker.upper():
            return obter_dados_brapi(ticker, periodo_dias)
        else:
            return obter_dados_yahoo(ticker, periodo_dias)
    except Exception as e:
        st.error(f"Erro ao buscar dados para {ticker}: {e}")
        return None


def obter_dados_yahoo(ticker, periodo_dias):
    if not YF_AVAILABLE:
        st.error("yfinance não instalado. Execute: pip install yfinance")
        return None
    try:
        interval_map = {
            '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '1h', '4h': '1h',
            '1d': '1d', '1w': '1wk'
        }
        interval = interval_map.get(timeframe, '1d')
        if timeframe == '4h':
            interval = '1h'
        data = yf.download(ticker, period='max', interval=interval, progress=False)
        if data.empty:
            return None
        data = data.tail(VELAS_TOTAL)
        data = data.reset_index()
        data.rename(columns={
            'Datetime': 'timestamp',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }, inplace=True)
        data['time'] = pd.to_datetime(data['timestamp'])
        if 'timestamp' not in data.columns:
            data = data.reset_index()
            data['time'] = pd.to_datetime(data['Date'] if 'Date' in data.columns else data['index'])
        if len(data) < PERIODO_AQUECIMENTO + 50:
            return None
        data['RSI_14'] = calcular_rsi(data['close'], 14)
        macd, sig, hist = calcular_macd(data['close'])
        data['MACD'] = macd
        data['MACD_SIGNAL'] = sig
        data['MACD_HIST'] = hist
        data['MFI'] = calcular_mfi(data)
        data = calcular_ssl_hybrid(data)
        data = calcular_atr_stop(data)
        data = calcular_ppo(data)
        data['SSL_Baseline'] = data['SSL_Baseline'].ffill()
        data['ATR_Stop'] = data['ATR_Stop'].replace(0, np.nan).ffill()
        return data.dropna(subset=['close']).reset_index(drop=True)
    except Exception as e:
        st.error(f"Erro no Yahoo Finance: {e}")
        return None


def obter_dados_brapi(ticker, periodo_dias):
    try:
        if periodo_dias <= 5:
            rng = '5d'
        elif periodo_dias <= 30:
            rng = '1mo'
        elif periodo_dias <= 180:
            rng = '6mo'
        elif periodo_dias <= 365:
            rng = '1y'
        else:
            rng = '5y'
        url = f"https://brapi.dev/api/quote/{ticker}?interval=1d&range={rng}"
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data.get('results'):
            return None
        results = data['results'][0]
        hist = results.get('historicalDataPrice', [])
        if not hist:
            return None
        df = pd.DataFrame(hist)
        df.rename(columns={
            'date': 'timestamp',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        }, inplace=True)
        df['time'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('time')
        df = df.tail(VELAS_TOTAL)
        if len(df) < PERIODO_AQUECIMENTO + 50:
            return None
        df['RSI_14'] = calcular_rsi(df['close'], 14)
        macd, sig, hist = calcular_macd(df['close'])
        df['MACD'] = macd
        df['MACD_SIGNAL'] = sig
        df['MACD_HIST'] = hist
        df['MFI'] = calcular_mfi(df)
        df = calcular_ssl_hybrid(df)
        df = calcular_atr_stop(df)
        df = calcular_ppo(df)
        df['SSL_Baseline'] = df['SSL_Baseline'].ffill()
        df['ATR_Stop'] = df['ATR_Stop'].replace(0, np.nan).ffill()
        return df.dropna(subset=['close']).reset_index(drop=True)
    except Exception as e:
        st.error(f"Erro no Brapi: {e}")
        return None


def obter_info_acao_yahoo(ticker):
    if not YF_AVAILABLE:
        return None
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if not info:
            return None
        current_price = info.get('regularMarketPrice') or info.get('currentPrice')
        if not current_price:
            return None
        change = info.get('regularMarketChangePercent')
        volume = info.get('regularMarketVolume')
        market_cap = info.get('marketCap')
        return {
            "last": current_price,
            "change": change,
            "volume": volume,
            "market_cap": market_cap
        }
    except:
        return None


def obter_info_acao_brapi(ticker):
    try:
        url = f"https://brapi.dev/api/quote/{ticker}"
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if not data.get('results'):
            return None
        res = data['results'][0]
        return {
            "last": res.get('regularMarketPrice'),
            "change": res.get('regularMarketChangePercent'),
            "volume": res.get('regularMarketVolume'),
            "market_cap": res.get('marketCap')
        }
    except:
        return None


def obter_info_acao(ticker):
    if '.SA' in ticker.upper():
        info = obter_info_acao_brapi(ticker)
        if info:
            return info
    return obter_info_acao_yahoo(ticker)


# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÃO PARA NOME EXTENSO DA CRIPTO
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
# MARKET CAP PARA CRIPTO (definido ANTES de ser chamado)
@st.cache_data(ttl=600)
def obter_market_cap_coingecko(simbolo):
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
                coin_id = coin.get("id")
                break
        else:
            if coins:
                coin_id = coins[0].get("id")
            else:
                return None
        url2 = "https://api.coingecko.com/api/v3/coins/markets"
        params2 = {
            "vs_currency": "usd",
            "ids": coin_id,
            "order": "market_cap_desc",
            "per_page": 1,
            "page": 1,
            "sparkline": "false"
        }
        resp2 = requests.get(url2, params=params2, headers=headers, timeout=10)
        if resp2.status_code == 200:
            dados = resp2.json()
            if dados and len(dados) > 0:
                mc = dados[0].get("market_cap")
                if mc and float(mc) > 1_000_000:
                    return float(mc)
        return None
    except:
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
    except:
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
# SIDEBAR
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

timeframes = txt["intervalos"]
timeframe_escolhido = st.sidebar.selectbox(
    txt["tempo_grafico"],
    list(timeframes.keys()),
    index=5
)
timeframe = timeframes[timeframe_escolhido]

st.sidebar.markdown("---")
modo_vivo = st.sidebar.toggle(txt["modo_vivo"], value=False)
intervalo_refresh = st.sidebar.slider(
    txt["intervalo_refresh"], min_value=15, max_value=120, value=30
)

# ─────────────────────────────────────────────────────────────────────────────
# ABAS
tab1, tab2 = st.tabs([txt["aba_cripto"], txt["aba_acoes"]])

with tab1:
    st.header(txt["aba_cripto"])
    lista_criptos = obter_pares_usdt()
    if not lista_criptos:
        lista_criptos = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]
    simbolo_id = st.selectbox(
        txt["selecione_cripto"],
        lista_criptos,
        index=lista_criptos.index("SOL/USDT") if "SOL/USDT" in lista_criptos else 0
    )

    @st.fragment(run_every=intervalo_refresh if modo_vivo else None)
    def painel_cripto():
        df_dados = carregar_dados_crypto(simbolo_id, timeframe)
        if df_dados is None or df_dados.empty:
            st.warning(txt["erro_dados"])
            return

        dados_24h = obter_dados_24h_crypto(simbolo_id)
        if dados_24h:
            preco = dados_24h.get("last")
            variacao = dados_24h.get("change")
            volume = dados_24h.get("volume")
        else:
            preco = variacao = volume = None

        market_cap = obter_market_cap_robusto(simbolo_id)

        recomendacao, cor_sinal, analise, pontos_alta, pontos_baixa = analisar_confluencia(df_dados, txt)

        st.markdown(f"""
        <div style="background:{cor_sinal}22;padding:20px;border-radius:10px;
                    border:2px solid {cor_sinal};margin-bottom:20px;">
        <h2 style="margin:0;color:{cor_sinal};">{recomendacao}</h2>
        <p style="margin:8px 0 0 0;color:#ddd;">{analise}</p>
        </div>
        """, unsafe_allow_html=True)

        nome_extenso = obter_nome_extenso_cripto(simbolo_id)
        label_preco = f"{nome_extenso} | {txt['preco_spot']}"

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric(label_preco, formatar_preco(preco) if preco else "—")
        m2.metric(txt["variacao_24h"], f"{variacao:+.2f}%" if variacao is not None else "—")
        m3.metric(txt["volume_24h"], formatar_volume_usdt(volume) if volume else "—")
        if market_cap is not None:
            m4.metric(txt["market_cap"], formatar_market_cap(market_cap))
        else:
            m4.metric(txt["market_cap"], txt["marketcap_nao_disponivel"])
        m5.metric(txt["pontos_compra"], f"{pontos_alta:.1f}")
        m6.metric(txt["pontos_venda"], f"{pontos_baixa:.1f}")

        ultimo_reg = df_dados.iloc[-1]
        st.markdown(
            f"**{txt['stop_atr']}:** {formatar_preco(ultimo_reg['ATR_Stop'])}"
            f"  |  RSI: **{ultimo_reg['RSI_14']:.1f}**"
            f"  |  MFI: **{ultimo_reg['MFI']:.1f}**"
        )

        st.markdown(f"### {txt['grafico_titulo']}")
        renderizar_grafico_plotly(df_dados, txt["grafico_titulo"], simbolo_id)

        hora_atual = pd.Timestamp.now().strftime("%H:%M:%S")
        n_velas = len(df_dados.iloc[PERIODO_AQUECIMENTO:])
        st.info(
            f"{'🟢' if modo_vivo else '⏸'} {txt['ultima_atualizacao']}: {hora_atual} | "
            f"{txt['proximo_refresh']} {intervalo_refresh} {txt['segundos']} | "
            f"{txt['aviso_aquecimento']}: {PERIODO_AQUECIMENTO} | Velas: {n_velas}"
        )

    painel_cripto()

with tab2:
    st.header(txt["aba_acoes"])

    @st.fragment(run_every=intervalo_refresh if modo_vivo else None)
    def painel_acoes():
        if "corretora_acoes" not in st.session_state:
            st.session_state.corretora_acoes = "Charles Schwab (EUA)"
        if "ticker_acoes" not in st.session_state:
            st.session_state.ticker_acoes = "AAPL"

        corretora = st.session_state.corretora_acoes
        ticker = st.session_state.ticker_acoes

        df_acoes = obter_dados_acoes(ticker, timeframe)
        if df_acoes is None or df_acoes.empty:
            st.warning(txt["erro_dados"])
            return

        info = obter_info_acao(ticker)
        preco = info.get("last") if info else None
        variacao = info.get("change") if info else None
        volume = info.get("volume") if info else None
        market_cap = info.get("market_cap") if info else None

        recomendacao, cor_sinal, analise, pontos_alta, pontos_baixa = analisar_confluencia(df_acoes, txt)

        st.markdown(f"""
        <div style="background:{cor_sinal}22;padding:20px;border-radius:10px;
                    border:2px solid {cor_sinal};margin-bottom:20px;">
        <h2 style="margin:0;color:{cor_sinal};">{recomendacao}</h2>
        <p style="margin:8px 0 0 0;color:#ddd;">{analise}</p>
        </div>
        """, unsafe_allow_html=True)

        label_preco = f"{ticker.upper()} | {txt['preco_spot']}"

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric(label_preco, formatar_preco(preco) if preco else "—")
        m2.metric(txt["variacao_24h"], f"{variacao:+.2f}%" if variacao is not None else "—")
        m3.metric(txt["volume_24h"], formatar_volume_usdt(volume) if volume else "—")
        m4.metric(txt["market_cap"], formatar_market_cap(market_cap) if market_cap else txt["marketcap_nao_disponivel"])
        m5.metric(txt["pontos_compra"], f"{pontos_alta:.1f}")
        m6.metric(txt["pontos_venda"], f"{pontos_baixa:.1f}")

        ultimo_reg = df_acoes.iloc[-1]
        st.markdown(
            f"**{txt['stop_atr']}:** {formatar_preco(ultimo_reg['ATR_Stop'])}"
            f"  |  RSI: **{ultimo_reg['RSI_14']:.1f}**"
            f"  |  MFI: **{ultimo_reg['MFI']:.1f}**"
        )

        st.markdown(f"### {txt['grafico_titulo']}")
        renderizar_grafico_plotly(df_acoes, txt["grafico_titulo"], ticker)

        hora_atual = pd.Timestamp.now().strftime("%H:%M:%S")
        n_velas = len(df_acoes.iloc[PERIODO_AQUECIMENTO:])
        st.info(
            f"{'🟢' if modo_vivo else '⏸'} {txt['ultima_atualizacao']}: {hora_atual} | "
            f"{txt['proximo_refresh']} {intervalo_refresh} {txt['segundos']} | "
            f"{txt['aviso_aquecimento']}: {PERIODO_AQUECIMENTO} | Velas: {n_velas}"
        )

    col1, col2 = st.columns(2)
    with col1:
        corretora_sel = st.selectbox(
            txt["selecione_corretora_acoes"],
            ["Charles Schwab (EUA)", "IC Markets (Austrália)", "DMM Securities (Japão)", "XP Investimentos (Brasil)", "Chapel Hill Denham (Nigéria)"],
            index=0,
            key="corretora_acoes"
        )
    with col2:
        exemplos_map = {
            "Charles Schwab (EUA)": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
            "IC Markets (Austrália)": ["BHP.AX", "CBA.AX", "CSL.AX", "WBC.AX"],
            "DMM Securities (Japão)": ["7203.T", "9984.T", "6758.T", "8306.T"],
            "XP Investimentos (Brasil)": ["PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA"],
            "Chapel Hill Denham (Nigéria)": ["GTCO.NG", "ZENITHBANK.NG", "DANGOTE.NG", "MTNN.NG"]
        }
        exemplos = exemplos_map.get(corretora_sel, ["AAPL"])
        ticker_padrao = exemplos[0]
        ticker = st.text_input(txt["ticker_acoes"], value=ticker_padrao, key="ticker_acoes")

    painel_acoes()
