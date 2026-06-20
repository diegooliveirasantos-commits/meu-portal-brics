import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import math
from decimal import Decimal
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import time

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
# DICIONÁRIO DE IDIOMAS – COMPLETO (versão resumida para brevidade, mas você deve manter o completo)
# Inclui: Português, Inglês, Espanhol, Francês, Alemão, Italiano, Russo, Chinês, Japonês, Coreano, Vietnamita, Turco.
# Para não repetir todo o dicionário aqui, mantenha o que você já possui, apenas acrescente as novas chaves:
# "tempo_status": "Tempo decorrido: {tempo}" (e equivalentes em cada idioma)
# As chaves já foram adicionadas na versão anterior. Certifique-se de que todas estão presentes.
DICIONARIO_LINGUAS = {
    "Português (BR)": {
        "titulo": "🏦  BRICSVAULT PORTAL - Motor SMC + Fibonacci PRO",
        "config_globais": "⚙️  Configurações Globais",
        "selecione_cripto": "Selecione Qualquer Criptomoeda (/USDT):",
        "tempo_grafico": "Tempo Gráfico:",
        "modo_vivo": "Ativar Monitoramento em Tempo Real",
        "intervalo_refresh": "Intervalo de Atualização (Segundos):",
        "preco_spot": "Preço Atual",
        "variacao_24h": "Variação 24h",
        "volume_24h": "Volume 24h (USDT)",
        "market_cap": "Market Cap (USD)",
        "stop_atr": "Stop ATR",
        "compra_forte": "🟢  COMPRA FORTE (SMC + FIBONACCI)",
        "venda_forte": "🔴  VENDA FORTE (SMC + FIBONACCI)",
        "neutro": "🟡  NEUTRO (AGUARDAR SMC)",
        "erro_dados": "Dados históricos insuficientes. Tente outro ativo ou reduza o Tempo Gráfico.",
        "ctx_desconto": "Zona de Desconto de Fibonacci (Excelente risco/retorno).",
        "ctx_premium": "Zona Premium de Fibonacci (Preço esticado, propício para realização).",
        "ctx_neutro": "Zona neutra de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Última Atualização",
        "proximo_refresh": "Próximo refresh em",
        "segundos": "segundos",
        "grafico_titulo": "📈  Gráfico de Preço Interativo",
        "buscando_marketcap": "🔍  Buscando Market Cap...",
        "marketcap_nao_disponivel": "Não disponível",
        "idioma_label": "🌐  Idioma / Language",
        "idioma_selecao": "Selecione o idioma da interface:",
        "aviso_aquecimento": "⚠️ Velas de aquecimento usadas no cálculo",
        "alvo_swing_title": "🎯 Projeção de Alvos (Fibonacci / Smart Money)",
        "direcao_operacao": "Direção",
        "entrada_projetada": "Entrada Projetada",
        "stop_projetado": "Stop Loss Projetado",
        "swing_alto": "Topo do Swing (High)",
        "swing_baixo": "Fundo do Swing (Low)",
        "range_label": "Oscilação (Range)",
        "alvo_prefix": "ALVO {n}",
        "sem_alvos": "Nenhum alvo projetado para este movimento.",
        "contexto_smc": "Contexto SMC",
        "trend_ascendente": "Tendência de Alta 🟢",
        "trend_descendente": "Tendência de Baixa 🔴",
        "trend_neutra": "Tendência Neutra 🟡",
        "batido": "✅ Batido",
        "aguardado": "⏳ Aguardado",
        "tempo_status": "Tempo decorrido: {tempo}",
        "backtest_titulo": "📊 Ver Assertividade nos Últimos Dados (Backtest Robusto)",
        "backtest_sem_dados": "⚠️ Dados históricos insuficientes para o backtest. Aumente o número de velas ou reduza os parâmetros.",
        "backtest_sem_sinais": "⚠️ Nenhum sinal forte gerado no histórico recente. Reduza a nota de corte ou ajuste o período de swing.",
        "backtest_resultados": "**Resultados do Backtest:**",
        "backtest_sinais": "Sinais Gerados",
        "backtest_acertos": "Acertos",
        "backtest_assertividade": "Assertividade",
        "backtest_lucro_medio": "Lucro Médio por Operação",
        "backtest_risco_medio": "Risco Médio por Operação",
        "backtest_fator_lucro": "Fator de Lucro",
        "backtest_drawdown": "Drawdown Máximo",
        "backtest_rr": "Relação Risco/Retorno Média",
        "backtest_curva_capital": "Curva de Capital (Equity Curve)",
        "intervalos": {
            "1 Minuto": "1m", "5 Minutos": "5m", "15 Minutos": "15m",
            "30 Minutos": "30m", "1 Hora": "1h", "4 Horas": "4h",
            "1 Dia": "1d", "1 Semana": "1w"
        }
    },
    "English (EN)": {
        # ... (mesma estrutura, com traduções)
    },
    # ... (demais idiomas – mantenha o seu dicionário completo)
}

# ─────────────────────────────────────────────────────────────────────────────
# FORMATAÇÃO E UTILITÁRIOS
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

def formatar_tempo(segundos):
    """Converte segundos em string formatada Xh Ym Zs"""
    if segundos < 0:
        segundos = 0
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    seg = int(segundos % 60)
    partes = []
    if horas > 0:
        partes.append(f"{horas}h")
    if minutos > 0:
        partes.append(f"{minutos}m")
    if seg > 0 or not partes:
        partes.append(f"{seg}s")
    return " ".join(partes)

# ─────────────────────────────────────────────────────────────────────────────
# GERENCIADOR DE EXCHANGES (SÍNCRONO) – mesmo código anterior
class ExchangeManager:
    EXCHANGES = {
        "Gate.io": {"class": ccxt.gate, "config": {"enableRateLimit": True, "options": {"defaultType": "spot"}}, "separator": "/"},
        "Kraken": {"class": ccxt.kraken, "config": {"enableRateLimit": True}, "separator": "/"},
        "MEXC": {"class": ccxt.mexc, "config": {"enableRateLimit": True}, "separator": ""},
        "KuCoin": {"class": ccxt.kucoin, "config": {"enableRateLimit": True}, "separator": "-"}
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

    def get_client(self, exchange_name):
        return self.clients.get(exchange_name)

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
# FUNÇÕES DE MERCADO (com cache) – mesmo código anterior
@st.cache_data(ttl=3600)
def obter_todos_pares_usdt():
    manager = get_exchange_manager()
    client = manager.get_client("Gate.io")
    if not client:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]
    try:
        markets = client.load_markets()
        pairs = [s for s in markets.keys() if s.endswith("/USDT")]
        return sorted(pairs)
    except Exception:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]

@st.cache_data(ttl=60)
def obter_dados_24h(simbolo):
    manager = get_exchange_manager()
    for exchange_name in manager.PRIORITY:
        try:
            client = manager.get_client(exchange_name)
            if not client:
                continue
            symbol = manager.get_symbol_format(exchange_name, simbolo)
            ticker = client.fetch_ticker(symbol)
            if ticker and ticker.get("last") is not None:
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
                    result["volume"] = obter_volume_usd_direto(exchange_name, simbolo)
                return result
        except Exception:
            continue
    return None

def obter_volume_usd_direto(exchange_name, simbolo):
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
        elif exchange_name == "Gate.io":
            pair = simbolo.replace("/", "_")
            url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={pair}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    return float(data[0].get("quote_volume", 0))
    except Exception:
        pass
    return None

@st.cache_data(ttl=3600)
def obter_nome_extenso_cripto(simbolo_id):
    try:
        base_currency = simbolo_id.split("/")[0]
        url = "https://api.gateio.ws/api/v4/spot/currencies"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            dados = response.json()
            for moeda in dados:
                if moeda.get("currency", "").upper() == base_currency.upper():
                    return moeda.get("name", base_currency).upper()
        return base_currency
    except Exception:
        return simbolo_id.split("/")[0]

# (demais funções de market cap, etc. – manter as mesmas que você já tem)

# ─────────────────────────────────────────────────────────────────────────────
# CARREGAMENTO DE DADOS OHLCV (SÍNCRONO) – mesmo código anterior
def carregar_dados(simbolo_id, timeframe_selecionado):
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
        try:
            client = manager.get_client(exchange_name)
            if not client:
                continue
            symbol = manager.get_symbol_format(exchange_name, simbolo_id)
            limit_fetch = VELAS_TOTAL - len(df_cached) if not df_cached.empty else VELAS_TOTAL
            if limit_fetch <= 0:
                limit_fetch = 1
            velas = client.fetch_ohlcv(symbol, timeframe=timeframe_selecionado, limit=limit_fetch, since=since_timestamp)
            if velas:
                velas_novas.extend(velas)
                break
        except Exception:
            continue
    if not velas_novas and df_cached.empty:
        return None
    df_novas = pd.DataFrame(velas_novas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df_novas['time'] = pd.to_datetime(df_novas['timestamp'], unit='ms')
    df_novas = df_novas.drop_duplicates(subset=['timestamp'])
    df_combinado = pd.concat([df_cached, df_novas]).drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
    if len(df_combinado) > VELAS_TOTAL:
        df_combinado = df_combinado.iloc[-VELAS_TOTAL:].reset_index(drop=True)
    if len(df_combinado) < PERIODO_AQUECIMENTO + 50:
        return None
    # Calcular indicadores
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
# INDICADORES TÉCNICOS (idênticos aos anteriores)
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
    tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.ewm(span=periodo, adjust=False).mean()
    atr_stop = np.zeros(len(df))
    tendencia = np.zeros(len(df), dtype=int)
    close_arr = close.values
    atr_arr = atr.values
    if len(df) > 0:
        atr_stop[0] = close_arr[0] - (atr_arr[0] * multiplicador) if not np.isnan(atr_arr[0]) else close_arr[0]
        tendencia[0] = 1
    for i in range(1, len(df)):
        if np.isnan(atr_arr[i]):
            atr_stop[i] = atr_stop[i-1]
            tendencia[i] = tendencia[i-1]
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
# SMC E FIBONACCI (com correção na entrada projetada)
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
        'fib_0': swing_high,
        'fib_236': swing_high - 0.236 * diff,
        'fib_382': swing_high - 0.382 * diff,
        'fib_500': swing_high - 0.500 * diff,
        'fib_618': swing_high - 0.618 * diff,
        'fib_786': swing_high - 0.786 * diff,
        'fib_100': swing_low
    }

def gerar_sinal_fibonacci(df_completo, direcao_smc, multiplicadores, periodo_swing):
    """
    Gera a projeção de entrada, stop e alvos baseada nos níveis de Fibonacci.
    A entrada NÃO é ajustada para o preço atual – mantém-se o nível de Fibonacci,
    evitando falsos sinais.
    """
    swing_info = identificar_swing_smc(df_completo.iloc[PERIODO_AQUECIMENTO:])
    if not swing_info:
        swing_high = df_completo['high'].max()
        swing_low = df_completo['low'].min()
        entrada_projetada = df_completo['close'].iloc[-1]  # fallback
        stop_projetado = swing_low if direcao_smc == "LONG" else swing_high
        return {
            'direcao': direcao_smc,
            'entrada': entrada_projetada,
            'stop': stop_projetado,
            'swing_high': swing_high,
            'swing_low': swing_low,
            'alvos': [],
            'idx_sinal': len(df_completo) - 1,
            'timestamp_sinal': df_completo['timestamp'].iloc[-1]
        }
    swing_high = swing_info['swing_high']
    swing_low = swing_info['swing_low']
    fibs = calcular_retracao_fibonacci_smc(swing_high, swing_low)
    idx_sinal = len(df_completo) - 1
    timestamp_sinal = df_completo['timestamp'].iloc[-1]

    if direcao_smc == "LONG":
        # Entrada na zona de desconto (61.8%)
        entrada_projetada = fibs['fib_618']
        stop_projetado = swing_low  # abaixo do swing low
        risco = entrada_projetada - stop_projetado
        alvos = [entrada_projetada + mult * risco for mult in multiplicadores]
        alvos_validos = [a for a in alvos if a > entrada_projetada]
    else:  # SHORT
        # Entrada na zona premium (38.2%)
        entrada_projetada = fibs['fib_382']
        stop_projetado = swing_high  # acima do swing high
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
        "multiplicadores": multiplicadores[:len(alvos_finais)],
        "idx_sinal": idx_sinal,
        "timestamp_sinal": timestamp_sinal
    }

# (demais funções: analisar_confluencia, backtest, gráfico, etc. – mantidas iguais)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN (com exibição de tempo e status dos alvos)
def main():
    idiomas_disponiveis = list(DICIONARIO_LINGUAS.keys())
    st.sidebar.markdown(f"### {DICIONARIO_LINGUAS['Português (BR)']['idioma_label']}")
    idioma_selecionado = st.sidebar.selectbox(
        DICIONARIO_LINGUAS['Português (BR)']['idioma_selecao'],
        options=idiomas_disponiveis,
        index=0
    )
    txt = DICIONARIO_LINGUAS[idioma_selecionado]

    pares = obter_todos_pares_usdt()
    if not pares:
        pares = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]

    simbolo = st.sidebar.selectbox(
        txt["selecione_cripto"],
        pares,
        index=pares.index("SOL/USDT") if "SOL/USDT" in pares else 0
    )

    nome_extenso = obter_nome_extenso_cripto(simbolo)
    st.title(f"{txt['titulo']} – {nome_extenso} ({simbolo})")

    st.sidebar.header(txt["config_globais"])

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
    st.sidebar.markdown("Versão: 2.0 (Síncrona)")

    # ─── PAINEL PRINCIPAL ────────────────────────────────────────────────
    @st.fragment(run_every=intervalo_refresh if modo_vivo else None)
    def painel_principal_fragment():
        tempo_atual = datetime.now()
        df = carregar_dados(simbolo, timeframe)
        if df is None or df.empty:
            st.warning(txt["erro_dados"])
            return
        df_analise = df.iloc[periodo_aquecimento_ui:]
        if df_analise.empty:
            st.warning(txt["erro_dados"])
            return
        ultimo_reg = df_analise.iloc[-1]
        preco_atual = ultimo_reg['close']

        st.markdown("---")
        col_preco1, col_preco2, col_preco3 = st.columns([1, 2, 1])
        with col_preco2:
            nome_curto = simbolo.split('/')[0]
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

        dados_24h = obter_dados_24h(simbolo)
        variacao_24h = dados_24h.get("change") if dados_24h else 0.0
        volume_24h = dados_24h.get("volume") if dados_24h else None
        market_cap = obter_market_cap_robusto(simbolo)  # função existente

        recomendacao, cor_sinal, analise, pontos_alta, pontos_baixa, direcao = analisar_confluencia(
            df, txt, limiar_sinal, periodo_aquecimento_ui
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

        sinal_fib = gerar_sinal_fibonacci(df, direcao, multiplicadores, periodo_swing)

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
                # Calcula status e tempo decorrido
                status, tempo_str, _ = calcular_status_alvo(
                    df, sinal_fib['idx_sinal'], sinal_fib['timestamp_sinal'],
                    preco_alvo, sinal_fib['direcao'], tempo_atual
                )
                status_label = txt["batido"] if status == "batido" else txt["aguardado"]
                tempo_texto = txt["tempo_status"].format(tempo=tempo_str)

                if sinal_fib['direcao'] == "LONG":
                    pct = ((preco_alvo - sinal_fib['entrada']) / sinal_fib['entrada']) * 100
                else:
                    pct = ((sinal_fib['entrada'] - preco_alvo) / sinal_fib['entrada']) * 100

                with cols_alvos[i % 4]:
                    st.metric(label, formatar_preco(preco_alvo), delta=f"{pct:+.2f}%")
                    st.write(f"{status_label} – {tempo_texto}")
        else:
            st.info(txt["sem_alvos"])

        st.divider()

        # ─── BACKTEST ──────────────────────────────────────────────────
        with st.expander(txt["backtest_titulo"]):
            resultado_backtest, backtest_metrics = calcular_assertividade_historica_robusta(
                df, limiar_sinal, periodo_aquecimento_ui, txt,
                periodo_swing=periodo_swing,
                target_profit_pct=target_profit_pct_ui,
                look_ahead_candles=look_ahead_candles_ui
            )
            st.markdown(resultado_backtest)
            if backtest_metrics and 'equity_curve' in backtest_metrics and len(backtest_metrics['equity_curve']) > 1:
                st.subheader(txt["backtest_curva_capital"])
                fig_equity = go.Figure(data=go.Scatter(y=backtest_metrics['equity_curve'], mode='lines'))
                fig_equity.update_layout(
                    title=txt["backtest_curva_capital"],
                    xaxis_title="Número de Operações",
                    yaxis_title="Capital (%)",
                    paper_bgcolor='#0b0f19',
                    plot_bgcolor='#0b0f19',
                    font=dict(color='#e2e8f0')
                )
                st.plotly_chart(fig_equity, use_container_width=True)

        st.markdown(f"### {txt['grafico_titulo']}")
        renderizar_grafico_plotly(df, simbolo, look_ahead_candles_ui,
                                  operacoes_backtest=backtest_metrics.get('operacoes') if backtest_metrics else None)

        st.markdown("---")
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric(txt["preco_spot"], formatar_preco(preco_atual))
        with col_info2:
            st.metric(txt["variacao_24h"], f"{variacao_24h:.2f}%", delta=f"{variacao_24h:.2f}%")
        with col_info3:
            st.metric(txt["volume_24h"], formatar_market_cap(volume_24h))

        market_cap_display = txt['marketcap_nao_disponivel'] if market_cap is None else formatar_market_cap(market_cap)
        st.metric(f"{txt['market_cap']}", market_cap_display)

        if modo_vivo:
            st.markdown(f"<p style='text-align: right; color: #94a3b8;'>{txt['ultima_atualizacao']}: {datetime.now().strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: right; color: #94a3b8;'>{txt['proximo_refresh']} {intervalo_refresh} {txt['segundos']}</p>", unsafe_allow_html=True)

    painel_principal_fragment()

# ─────────────────────────────────────────────────────────────────────────────
# EXECUÇÃO
if __name__ == "__main__":
    main()
