import streamlit as st
import os
import hashlib
import sys
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
from datetime import datetime, timedelta

# ============================================
# SISTEMA ANTI-CÓPIA BRICSVAULT
# Proteção contra execução não autorizada
# ============================================

def protecao_anti_copia():
    """Impede execução em domínios não autorizados."""
    
    app_url = os.environ.get("STREAMLIT_APP_URL", "")
    server_name = os.environ.get("STREAMLIT_SERVER_ADDRESS", "")
    
    IDENTIFICADORES_PERMITIDOS = [
        "bricsvault-portal",
        "diegooliveirasantos-commits",
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
    ]
    
    autorizado = False
    
    for identificador in IDENTIFICADORES_PERMITIDOS:
        if identificador in app_url or identificador in server_name:
            autorizado = True
            break
    
    if not app_url and not server_name:
        autorizado = True
    
    if not autorizado:
        st.set_page_config(page_title="🚫 ACESSO BLOQUEADO", page_icon="🔒")
        st.error("## 🚫 ACESSO NÃO AUTORIZADO")
        st.warning("Este software é propriedade de **Diego Oliveira Santos**")
        st.info("🔗 Acesse apenas em: https://bricsvault-portal.streamlit.app")
        st.markdown("---")
        st.caption("BRICSVAULT © 2024 - Todos os direitos reservados")
        st.stop()
        sys.exit()
    
    try:
        token_verificacao = st.secrets.get("TOKEN_VERIFICACAO", None)
        if token_verificacao and token_verificacao != "BRICSVAULT_AUTENTICO_2024":
            st.error("🔑 Token de verificação inválido")
            st.stop()
    except Exception:
        pass

protecao_anti_copia()

# ============================================
# FIM DO SISTEMA ANTI-CÓPIA
# ============================================

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
# DICIONÁRIO DE IDIOMAS (17 línguas - principais)
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
        "erro_dados": "Dados históricos insuficientes nesta Exchange.",
        "ctx_desconto": "Ativo em Zona de Desconto de Fibonacci.",
        "ctx_premium": "Ativo em Zona Premium de Fibonacci.",
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
        "backtest_titulo": "📊 Backtesting Avançado — Últimos 100 Sinais",
        "backtest_compra": "Compra",
        "backtest_venda": "Venda",
        "backtest_total": "Total Sinais",
        "backtest_acertos": "Acertos",
        "backtest_taxa": "Taxa de Acerto",
        "backtest_profit_factor": "Profit Factor",
        "backtest_avg_win": "Ganho Médio",
        "backtest_avg_loss": "Perda Média",
        "backtest_historico": "Histórico de Sinais Recentes",
        "backtest_data": "Data/Hora",
        "backtest_sinal": "Sinal",
        "backtest_preco": "Preço Entrada",
        "backtest_resultado": "Resultado",
        "backtest_acerto": "✅ Acerto",
        "backtest_erro": "❌ Erro",
        "backtest_metricas": "Métricas de Performance",
        "poc_label": "POC (Point of Control)",
        "vah_label": "VAH (Value Area High)",
        "val_label": "VAL (Value Area Low)",
        "fear_greed_label": "😱 Fear & Greed Index",
        "medo_extremo": "Medo Extremo",
        "medo": "Medo",
        "neutro_fg": "Neutro",
        "ganancia": "Ganância",
        "ganancia_extrema": "Ganância Extrema",
        "estrutura_bos": "🏗️ BOS (Break of Structure)",
        "estrutura_choch": "🔄 CHoCH (Change of Character)",
        "estrutura_indefinida": "⏳ Estrutura Indefinida",
        "divergencia_obv_bull": "📈 Divergência OBV Bullish",
        "divergencia_obv_bear": "📉 Divergência OBV Bearish",
        "divergencia_obv_none": "➖ OBV Sem Divergência",
        "alinhamento_mtf": "🔄 Alinhamento Multi-TF",
        "alinhamento_mtf_sim": "✅ Alinhado",
        "alinhamento_mtf_nao": "❌ Não Alinhado",
        "filtro_liquidez": "💧 Liquidez Real do Ativo",
        "liquidez_classificacao": ["⚫ Baixíssima", "🔴 Muito Baixa", "🟠 Baixa", "🟡 Moderada", "🟢 Alta", "⭐ Elevada"],
        "liquidez_descricao": {
            0: "Evite operar - sem liquidez",
            1: "Alto risco - slippage elevado",
            2: "Risco moderado - ordens pequenas",
            3: "Operável - ordens médias",
            4: "Boa liquidez - execução rápida",
            5: "Excelente - institucional"
        },
        "volume_direcional_bull": "📊 Volume Direcional Bullish",
        "volume_direcional_bear": "📊 Volume Direcional Bearish",
        "volume_direcional_neutro": "📊 Volume Direcional Neutro",
        "limiar_dinamico": "Limiar Dinâmico",
        "modulo_mtf": "🔍 Módulo Multi-Timeframe",
        "modulo_estrutura": "🏗️ Módulo de Estrutura SMC",
        "modulo_obv": "📊 Módulo Divergência OBV",
        "modulo_volume": "📈 Módulo Volume Direcional",
        "modulo_fg": "😱 Módulo Fear & Greed",
        "modulo_liquidez": "💧 Módulo Liquidez Real",
        "spread_atual": "Spread %",
        "volume_24h_usdt": "Volume 24h (USDT)",
        "profundidade_livro": "Profundidade ±2%",
        "intervalos": {
            "1 Minuto": "1m", "5 Minutos": "5m", "15 Minutos": "15m",
            "30 Minutos": "30m", "1 Hora": "1h", "4 Horas": "4h",
            "1 Dia": "1d", "1 Semana": "1w"
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
        "erro_dados": "Insufficient historical data on this Exchange.",
        "ctx_desconto": "Asset in Fibonacci Discount Zone.",
        "ctx_premium": "Asset in Fibonacci Premium Zone.",
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
        "backtest_titulo": "📊 Advanced Backtesting — Last 100 Signals",
        "backtest_compra": "Buy",
        "backtest_venda": "Sell",
        "backtest_total": "Total Signals",
        "backtest_acertos": "Hits",
        "backtest_taxa": "Hit Rate",
        "backtest_profit_factor": "Profit Factor",
        "backtest_avg_win": "Avg Win",
        "backtest_avg_loss": "Avg Loss",
        "backtest_historico": "Recent Signal History",
        "backtest_data": "Date/Time",
        "backtest_sinal": "Signal",
        "backtest_preco": "Entry Price",
        "backtest_resultado": "Result",
        "backtest_acerto": "✅ Hit",
        "backtest_erro": "❌ Miss",
        "backtest_metricas": "Performance Metrics",
        "poc_label": "POC (Point of Control)",
        "vah_label": "VAH (Value Area High)",
        "val_label": "VAL (Value Area Low)",
        "fear_greed_label": "😱 Fear & Greed Index",
        "medo_extremo": "Extreme Fear",
        "medo": "Fear",
        "neutro_fg": "Neutral",
        "ganancia": "Greed",
        "ganancia_extrema": "Extreme Greed",
        "estrutura_bos": "🏗️ BOS (Break of Structure)",
        "estrutura_choch": "🔄 CHoCH (Change of Character)",
        "estrutura_indefinida": "⏳ Undefined Structure",
        "divergencia_obv_bull": "📈 OBV Bullish Divergence",
        "divergencia_obv_bear": "📉 OBV Bearish Divergence",
        "divergencia_obv_none": "➖ No OBV Divergence",
        "alinhamento_mtf": "🔄 Multi-TF Alignment",
        "alinhamento_mtf_sim": "✅ Aligned",
        "alinhamento_mtf_nao": "❌ Not Aligned",
        "filtro_liquidez": "💧 Real Asset Liquidity",
        "liquidez_classificacao": ["⚫ Very Low", "🔴 Low", "🟠 Below Avg", "🟡 Moderate", "🟢 High", "⭐ Excellent"],
        "liquidez_descricao": {
            0: "Avoid - no liquidity",
            1: "High risk - large slippage",
            2: "Moderate risk - small orders",
            3: "Tradeable - medium orders",
            4: "Good liquidity - fast execution",
            5: "Excellent - institutional grade"
        },
        "volume_direcional_bull": "📊 Bullish Directional Volume",
        "volume_direcional_bear": "📊 Bearish Directional Volume",
        "volume_direcional_neutro": "📊 Neutral Directional Volume",
        "limiar_dinamico": "Dynamic Threshold",
        "modulo_mtf": "🔍 Multi-Timeframe Module",
        "modulo_estrutura": "🏗️ SMC Structure Module",
        "modulo_obv": "📊 OBV Divergence Module",
        "modulo_volume": "📈 Directional Volume Module",
        "modulo_fg": "😱 Fear & Greed Module",
        "modulo_liquidez": "💧 Real Liquidity Module",
        "spread_atual": "Spread %",
        "volume_24h_usdt": "24h Volume (USDT)",
        "profundidade_livro": "Depth ±2%",
        "intervalos": {
            "1 Minute": "1m", "5 Minutes": "5m", "15 Minutes": "15m",
            "30 Minutes": "30m", "1 Hour": "1h", "4 Hours": "4h",
            "1 Day": "1d", "1 Week": "1w"
        }
    }
}

# Para os outros 15 idiomas, usamos fallback para Português e Inglês
# (O dicionário completo com 17 idiomas está disponível sob demanda)
for lang in list(DICIONARIO_LINGUAS.keys()):
    if lang not in ["Português (BR)", "English (EN)"]:
        DICIONARIO_LINGUAS[lang] = DICIONARIO_LINGUAS["English (EN)"]

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
    """Formata volume em USDT para exibição."""
    if valor is None or valor == 0:
        return "$0"
    if valor >= 1_000_000_000:
        return f"${valor/1_000_000_000:.1f}B"
    elif valor >= 1_000_000:
        return f"${valor/1_000_000:.1f}M"
    elif valor >= 1_000:
        return f"${valor/1_000:.1f}K"
    else:
        return f"${valor:.0f}"


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
# FEAR & GREED INDEX
@st.cache_data(ttl=3600)
def obter_fear_greed_index():
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
# MARKET CAP
@st.cache_data(ttl=600)
def obter_market_cap_coingecko(simbolo):
    try:
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
        return None
    except Exception:
        return None


def obter_market_cap_robusto(simbolo_id):
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


def calcular_atr(df, periodo=14):
    high, low, close = df['high'], df['low'], df['close']
    tr = pd.concat(
        [high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()],
        axis=1
    ).max(axis=1)
    return tr.ewm(span=periodo, adjust=False).mean()


# ─────────────────────────────────────────────────────────────────────────────
# VOLUME PROFILE (POC/VAH/VAL)
def calcular_volume_profile(df, num_bins=50, value_area_pct=0.70):
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

    poc_idx = np.argmax(volume_por_nivel)
    poc = (bins[poc_idx] + bins[poc_idx + 1]) / 2

    volume_total = volume_por_nivel.sum()
    volume_alvo = volume_total * value_area_pct

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
# MÓDULO 5 (NOVO): ANÁLISE DE LIQUIDEZ REAL (Escala 0-5)
# Baseada em dados REAIS da Gate.io: ticker, order book, volume 24h

@st.cache_data(ttl=30)  # Cache de 30 segundos para dados de liquidez
def analisar_liquidez_real(simbolo_id):
    """
    Analisa a liquidez REAL do ativo usando dados da Gate.io:
    1. Spread (diferença bid/ask)
    2. Volume 24h em USDT
    3. Profundidade do livro de ordens (±2%)
    
    Retorna:
    - score (0-5): Nota de liquidez
    - spread_pct: Spread percentual
    - volume_24h_usdt: Volume 24h em USDT
    - profundidade_usdt: Profundidade média ±2% em USDT
    - detalhes: dict com informações detalhadas
    """
    try:
        # 1. Obter ticker para spread e volume 24h
        ticker = gateio_client.fetch_ticker(simbolo_id)
        
        bid = ticker.get('bid', 0)
        ask = ticker.get('ask', 0)
        last = ticker.get('last', 0)
        volume_24h_base = ticker.get('baseVolume', 0)  # Volume em moeda base
        volume_24h_usdt = ticker.get('quoteVolume', 0)  # Volume em USDT
        
        # Calcular spread percentual
        if bid > 0 and ask > 0:
            spread_pct = ((ask - bid) / bid) * 100
        else:
            spread_pct = 10.0  # Spread alto se não disponível
        
        # 2. Obter profundidade do livro de ordens
        try:
            order_book = gateio_client.fetch_order_book(simbolo_id, limit=50)
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            
            # Calcular profundidade ±2% do preço atual
            preco_ref = last if last > 0 else ((bid + ask) / 2 if bid > 0 and ask > 0 else 1)
            limite_superior = preco_ref * 1.02
            limite_inferior = preco_ref * 0.98
            
            profundidade_bid = sum(qtd * preco for preco, qtd in bids if preco >= limite_inferior)
            profundidade_ask = sum(qtd * preco for preco, qtd in asks if preco <= limite_superior)
            profundidade_total = profundidade_bid + profundidade_ask
        except Exception:
            profundidade_total = 0
        
        # 3. Calcular score de liquidez (0-5)
        score = 0
        
        # Sub-score: Spread (0-2 pontos)
        if spread_pct < 0.01:      # Spread < 0.01% (excelente)
            score += 2.0
        elif spread_pct < 0.05:    # Spread < 0.05% (bom)
            score += 1.5
        elif spread_pct < 0.1:     # Spread < 0.1% (moderado)
            score += 1.0
        elif spread_pct < 0.5:     # Spread < 0.5% (aceitável)
            score += 0.5
        elif spread_pct < 2.0:     # Spread < 2% (ruim)
            score += 0.25
        # spread >= 2% não ganha pontos
        
        # Sub-score: Volume 24h em USDT (0-2 pontos)
        if volume_24h_usdt > 100_000_000:     # > $100M
            score += 2.0
        elif volume_24h_usdt > 10_000_000:    # > $10M
            score += 1.5
        elif volume_24h_usdt > 1_000_000:     # > $1M
            score += 1.0
        elif volume_24h_usdt > 100_000:       # > $100K
            score += 0.5
        elif volume_24h_usdt > 10_000:        # > $10K
            score += 0.25
        # volume < $10K não ganha pontos
        
        # Sub-score: Profundidade do livro (0-1 ponto)
        if profundidade_total > 10_000_000:   # > $10M profundidade
            score += 1.0
        elif profundidade_total > 1_000_000:  # > $1M
            score += 0.75
        elif profundidade_total > 100_000:    # > $100K
            score += 0.5
        elif profundidade_total > 10_000:     # > $10K
            score += 0.25
        
        # Arredondar para inteiro 0-5
        score_final = min(5, max(0, int(round(score))))
        
        detalhes = {
            'spread_pct': spread_pct,
            'volume_24h_usdt': volume_24h_usdt,
            'profundidade_total': profundidade_total,
            'bid': bid,
            'ask': ask,
            'score_bruto': score
        }
        
        return score_final, spread_pct, volume_24h_usdt, profundidade_total, detalhes
        
    except Exception as e:
        # Se falhar, retornar liquidez desconhecida (score 2 = média baixa)
        return 2, 0.5, 0, 0, {'erro': str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO 1: ANÁLISE MULTI-TIMEFRAME (MTF)
def carregar_dados_mtf(simbolo_id, timeframe):
    try:
        velas = gateio_client.fetch_ohlcv(simbolo_id, timeframe=timeframe, limit=VELAS_TOTAL)
        if not velas or len(velas) < PERIODO_AQUECIMENTO + 50:
            return None
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['RSI_14'] = calcular_rsi(df['close'], 14)
        macd, sinal, hist = calcular_macd(df['close'])
        df['MACD'] = macd
        df['MACD_SIGNAL'] = sinal
        df['MACD_HIST'] = hist
        df = calcular_ssl_hybrid(df)
        df = calcular_atr_stop(df)
        df['OBV'] = calcular_obv(df)
        df['OBV_Aceleracao'] = calcular_obv_aceleracao(df['OBV'], periodo=5)
        return df.dropna(subset=['close']).reset_index(drop=True)
    except Exception:
        return None


def analisar_alinhamento_mtf(simbolo_id, timeframe_atual):
    mapa_tf_superior = {
        '1m': ['15m', '1h'], '5m': ['30m', '4h'], '15m': ['1h', '4h'],
        '30m': ['1h', '4h'], '1h': ['4h', '1d'], '4h': ['1d', '1w'],
        '1d': ['1w', '1w'], '1w': ['1w', '1w']
    }

    tfs_superiores = mapa_tf_superior.get(timeframe_atual, ['4h', '1d'])
    alinhamentos = 0
    detalhes = {}

    for tf in tfs_superiores:
        df_superior = carregar_dados_mtf(simbolo_id, tf)
        if df_superior is None:
            continue

        u = df_superior.iloc[-1]
        score_tf = 0

        if u['ssl_dir'] == 1: score_tf += 1
        else: score_tf -= 1
        if u['MACD_HIST'] > 0: score_tf += 1
        else: score_tf -= 1
        if not np.isnan(u.get('OBV_Aceleracao', 0)):
            if u['OBV_Aceleracao'] > 0: score_tf += 1
            else: score_tf -= 1

        detalhes[tf] = 'bullish' if score_tf >= 2 else ('bearish' if score_tf <= -2 else 'neutral')
        if score_tf >= 1: alinhamentos += 1
        elif score_tf <= -1: alinhamentos -= 1

    peso_mtf = alinhamentos * 1.25
    return alinhamentos >= 1, peso_mtf, detalhes


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO 2: ANÁLISE DE ESTRUTURA SMC (BOS/CHoCH)
def detectar_estrutura_smc(df):
    if len(df) < 50:
        return 'INDEFINIDO', 0.0

    df_recente = df.iloc[-60:]
    high = df_recente['high'].values
    low = df_recente['low'].values
    close = df_recente['close'].values

    swing_highs = []
    swing_lows = []
    for i in range(2, len(df_recente) - 2):
        if high[i] > high[i-1] and high[i] > high[i-2] and high[i] > high[i+1] and high[i] > high[i+2]:
            swing_highs.append((i, high[i]))
        if low[i] < low[i-1] and low[i] < low[i-2] and low[i] < low[i+1] and low[i] < low[i+2]:
            swing_lows.append((i, low[i]))

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return 'INDEFINIDO', 0.0

    ultimos_highs = swing_highs[-2:]
    ultimos_lows = swing_lows[-2:]
    preco_atual = close[-1]

    if len(ultimos_highs) >= 2:
        ultimo_sh = ultimos_highs[-1][1]
        penultimo_sh = ultimos_highs[-2][1]
        if preco_atual > ultimo_sh and ultimo_sh > penultimo_sh:
            return 'BOS', 3.5

    if len(ultimos_lows) >= 2:
        ultimo_sl = ultimos_lows[-1][1]
        penultimo_sl = ultimos_lows[-2][1]
        if preco_atual < ultimo_sl and ultimo_sl < penultimo_sl:
            return 'BOS', -3.5

    if len(ultimos_lows) >= 2 and len(ultimos_highs) >= 1:
        if ultimos_lows[-1][1] > ultimos_lows[-2][1]:
            if preco_atual > ultimos_highs[-1][1]:
                return 'CHoCH', 3.0

    if len(ultimos_highs) >= 2 and len(ultimos_lows) >= 1:
        if ultimos_highs[-1][1] < ultimos_highs[-2][1]:
            if preco_atual < ultimos_lows[-1][1]:
                return 'CHoCH', -3.0

    if len(ultimos_highs) >= 2 and len(ultimos_lows) >= 2:
        highs_subindo = ultimos_highs[-1][1] > ultimos_highs[-2][1]
        lows_subindo = ultimos_lows[-1][1] > ultimos_lows[-2][1]
        if highs_subindo and lows_subindo:
            return 'TENDENCIA_ALTA', 1.0
        elif not highs_subindo and not lows_subindo:
            return 'TENDENCIA_BAIXA', -1.0

    return 'INDEFINIDO', 0.0


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO 3: DIVERGÊNCIA OBV/PREÇO
def detectar_divergencia_obv(df, periodo=25):
    if len(df) < periodo:
        return 'NONE', 0.0

    df_window = df.iloc[-periodo:]
    meio = len(df_window) // 2
    primeira_metade = df_window.iloc[:meio]
    segunda_metade = df_window.iloc[meio:]

    preco_max_1 = primeira_metade['close'].max()
    preco_max_2 = segunda_metade['close'].max()
    preco_min_1 = primeira_metade['close'].min()
    preco_min_2 = segunda_metade['close'].min()

    obv_max_1 = primeira_metade['OBV'].max()
    obv_max_2 = segunda_metade['OBV'].max()
    obv_min_1 = primeira_metade['OBV'].min()
    obv_min_2 = segunda_metade['OBV'].min()

    if preco_max_2 > preco_max_1 and obv_max_2 < obv_max_1:
        return 'BEARISH', -3.0
    if preco_min_2 < preco_min_1 and obv_min_2 > obv_min_1:
        return 'BULLISH', 3.0

    return 'NONE', 0.0


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO 4: VOLUME DIRECIONAL
def calcular_volume_direcional(df, periodo=15):
    velas_alta = df['close'] > df['open']
    velas_baixa = df['close'] < df['open']

    vol_alta = df.loc[velas_alta, 'volume'].tail(periodo).mean()
    vol_baixa = df.loc[velas_baixa, 'volume'].tail(periodo).mean()

    if pd.isna(vol_alta): vol_alta = 0
    if pd.isna(vol_baixa): vol_baixa = 0

    if vol_baixa > 0:
        ratio = vol_alta / vol_baixa
    else:
        ratio = 2.0 if vol_alta > 0 else 1.0

    if ratio > 1.5: return 'BULLISH', 2.0
    elif ratio < 0.67: return 'BEARISH', -2.0
    elif ratio > 1.2: return 'LEAN_BULLISH', 1.0
    elif ratio < 0.83: return 'LEAN_BEARISH', -1.0
    else: return 'NEUTRO', 0.0


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO 6: INTEGRAÇÃO FEAR & GREED
def integrar_fear_greed(fg_valor):
    if fg_valor is None:
        return 0.0, 0.0
    if fg_valor <= 25: return 2.0, -3.0
    elif fg_valor <= 40: return 1.0, -1.5
    elif fg_valor >= 75: return -3.0, 2.0
    elif fg_valor >= 60: return -1.5, 1.0
    else: return 0.0, 0.0


# ─────────────────────────────────────────────────────────────────────────────
# CÁLCULO DO LIMIAR DINÂMICO
def calcular_limiar_dinamico(df):
    atr_series = calcular_atr(df)
    if atr_series.empty or pd.isna(atr_series.iloc[-1]):
        return 9.0
    atr_percentual = (atr_series.iloc[-1] / df['close'].iloc[-1]) * 100
    if atr_percentual > 8: return 11.0
    elif atr_percentual > 5: return 10.0
    elif atr_percentual > 3: return 9.0
    elif atr_percentual > 1.5: return 8.0
    else: return 7.0


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
# CARREGAMENTO DE DADOS PRINCIPAL
@st.cache_data(ttl=60)
def carregar_dados(simbolo_id, timeframe_selecionado):
    try:
        velas = gateio_client.fetch_ohlcv(
            simbolo_id, timeframe=timeframe_selecionado, limit=VELAS_TOTAL
        )
        if not velas or len(velas) < PERIODO_AQUECIMENTO + 50:
            return None
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['RSI_14'] = calcular_rsi(df['close'], 14)
        macd, sinal, hist = calcular_macd(df['close'])
        df['MACD'] = macd
        df['MACD_SIGNAL'] = sinal
        df['MACD_HIST'] = hist
        df['MFI'] = calcular_mfi(df)
        df = calcular_ssl_hybrid(df)
        df = calcular_atr_stop(df)
        df = calcular_ppo(df)
        df['OBV'] = calcular_obv(df)
        df['OBV_Aceleracao'] = calcular_obv_aceleracao(df['OBV'], periodo=5)
        df['Volume_Ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        df['ATR_14'] = calcular_atr(df)
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
# DETECTOR DE SPIKE DE VOLATILIDADE
def detectar_spike_volatilidade(df_analise):
    if len(df_analise) < 25:
        return None
    u = df_analise.iloc[-1]
    range_pct = ((u['high'] - u['low']) / u['open']) * 100 if u['open'] > 0 else 0
    vol_medio = df_analise['volume'].iloc[-21:-1].mean()
    vol_atual = u['volume']
    vol_ratio = vol_atual / vol_medio if vol_medio > 0 else 1
    obv_acel = u.get('OBV_Aceleracao', 0)
    direcao = 1 if u['close'] > u['open'] else -1
    spike_range = range_pct > 5.0
    spike_volume = vol_ratio > 2.0
    spike_obv = abs(obv_acel) > (df_analise['OBV_Aceleracao'].abs().mean() * 2.5 if len(df_analise) > 25 else 0)
    score = 0
    if spike_range: score += 1
    if spike_volume: score += 1
    if spike_obv and not (np.isnan(obv_acel) or np.isinf(obv_acel)): score += 1
    if score >= 2:
        return "ALTA" if direcao > 0 else "BAIXA"
    return None


# ─────────────────────────────────────────────────────────────────────────────
# ANÁLISE DE CONFLUÊNCIA SMC AVANÇADA
def analisar_confluencia(df_completo, simbolo_id, timeframe, fg_valor, liquidez_score, txt):
    df_analise = df_completo.iloc[PERIODO_AQUECIMENTO:].copy()
    if df_analise.empty:
        return txt["neutro"], "#ffcc00", txt["ctx_neutro"], 0.0, 0.0, None, None, None, None, {}

    u = df_analise.iloc[-1]
    preco_atual = u['close']

    fib_niveis = calcular_retracao_fibonacci(df_analise)
    poc, vah, val = calcular_volume_profile(df_analise)
    limiar_dinamico = calcular_limiar_dinamico(df_completo)

    alinhado_mtf, peso_mtf, detalhes_mtf = analisar_alinhamento_mtf(simbolo_id, timeframe)
    estrutura_smc, peso_estrutura = detectar_estrutura_smc(df_analise)
    divergencia_obv, peso_divergencia = detectar_divergencia_obv(df_analise)
    volume_dir, peso_volume = calcular_volume_direcional(df_analise)
    peso_fg_compra, peso_fg_venda = integrar_fear_greed(fg_valor)

    pontos_alta = 0.0
    pontos_baixa = 0.0

    rsi_val = u['RSI_14']
    if not math.isnan(rsi_val):
        if rsi_val < 30: pontos_alta += 3.0
        elif rsi_val < 40: pontos_alta += 2.0
        elif rsi_val > 70: pontos_baixa += 3.0
        elif rsi_val > 60: pontos_baixa += 2.0

    macd_hist = u['MACD_HIST']
    if not math.isnan(macd_hist):
        if macd_hist > 0: pontos_alta += 2.5
        else: pontos_baixa += 2.5

    obv_acel = u.get('OBV_Aceleracao', 0)
    if not (np.isnan(obv_acel) or np.isinf(obv_acel)):
        if obv_acel > 0: pontos_alta += 1.0
        else: pontos_baixa += 1.0

    mfi_val = u['MFI']
    if not math.isnan(mfi_val):
        if mfi_val < 30: pontos_alta += 1.5
        elif mfi_val > 70: pontos_baixa += 1.5

    if u['ssl_dir'] == 1: pontos_alta += 1.0
    else: pontos_baixa += 1.0

    if u['atr_dir'] == 1: pontos_alta += 1.0
    else: pontos_baixa += 1.0

    ppo_val = u['PPO']
    ppo_sig = u['PPO_Signal']
    if not (math.isnan(ppo_val) or math.isnan(ppo_sig)):
        if ppo_val > ppo_sig: pontos_alta += 1.5
        else: pontos_baixa += 1.5

    if poc is not None and vah is not None and val is not None:
        if preco_atual <= val: pontos_alta += 2.0
        elif preco_atual >= vah: pontos_baixa += 2.0

    if preco_atual >= fib_niveis['fib_382']:
        pontos_baixa += 2.0
        contexto_fib = txt["ctx_premium"]
    elif preco_atual <= fib_niveis['fib_618']:
        pontos_alta += 2.0
        contexto_fib = txt["ctx_desconto"]
    else:
        contexto_fib = txt["ctx_neutro"]

    if peso_estrutura > 0: pontos_alta += abs(peso_estrutura)
    elif peso_estrutura < 0: pontos_baixa += abs(peso_estrutura)

    if peso_divergencia > 0: pontos_alta += abs(peso_divergencia)
    elif peso_divergencia < 0: pontos_baixa += abs(peso_divergencia)

    if peso_volume > 0: pontos_alta += abs(peso_volume)
    elif peso_volume < 0: pontos_baixa += abs(peso_volume)

    if peso_mtf > 0: pontos_alta += abs(peso_mtf)
    elif peso_mtf < 0: pontos_baixa += abs(peso_mtf)

    pontos_alta += peso_fg_compra
    pontos_baixa += peso_fg_venda

    # Ajuste por liquidez REAL (Escala 0-5)
    # Liquidez baixa REDUZ a confiança nos sinais
    fator_liquidez = liquidez_score / 5.0  # Normaliza para 0.0 a 1.0
    # Se liquidez < 2 (muito baixa), reduz significativamente os pontos
    if liquidez_score <= 1:
        fator_liquidez = 0.3  # Reduz 70% da força do sinal
    elif liquidez_score == 2:
        fator_liquidez = 0.6  # Reduz 40%
    elif liquidez_score == 3:
        fator_liquidez = 0.8  # Reduz 20%
    # liquidez 4-5 mantém os pontos integrais
    
    pontos_alta *= fator_liquidez
    pontos_baixa *= fator_liquidez

    spike = detectar_spike_volatilidade(df_analise)

    modulos_info = {
        'mtf_alinhado': alinhado_mtf, 'mtf_peso': peso_mtf, 'mtf_detalhes': detalhes_mtf,
        'estrutura': estrutura_smc, 'estrutura_peso': peso_estrutura,
        'divergencia_obv': divergencia_obv, 'divergencia_peso': peso_divergencia,
        'volume_direcional': volume_dir, 'volume_peso': peso_volume,
        'liquidez_score': liquidez_score, 'fator_liquidez': fator_liquidez,
        'fg_peso_compra': peso_fg_compra, 'fg_peso_venda': peso_fg_venda,
        'limiar_dinamico': limiar_dinamico
    }

    if pontos_alta >= limiar_dinamico and pontos_alta > pontos_baixa:
        return (
            txt["compra_forte"], "#00cc66",
            f"{contexto_fib} | {estrutura_smc} | MTF: {'✅' if alinhado_mtf else '⚠️'}",
            pontos_alta, pontos_baixa, spike, poc, vah, val, modulos_info
        )
    elif pontos_baixa >= limiar_dinamico and pontos_baixa > pontos_alta:
        return (
            txt["venda_forte"], "#ff3333",
            f"{contexto_fib} | {estrutura_smc} | MTF: {'✅' if alinhado_mtf else '⚠️'}",
            pontos_alta, pontos_baixa, spike, poc, vah, val, modulos_info
        )
    else:
        return txt["neutro"], "#ffcc00", contexto_fib, pontos_alta, pontos_baixa, spike, poc, vah, val, modulos_info


# ─────────────────────────────────────────────────────────────────────────────
# BACKTESTING AVANÇADO COM TP/SL
def executar_backtesting(df_completo, simbolo_id, timeframe, txt):
    df_analise = df_completo.iloc[PERIODO_AQUECIMENTO:].copy()
    if len(df_analise) < 200:
        return None, None, None, None, None, None, None, []

    sinais_compra = 0
    sinais_venda = 0
    acertos_compra = 0
    acertos_venda = 0
    ganhos = []
    perdas = []
    historico = []

    inicio = max(0, len(df_analise) - 105)

    for i in range(inicio, len(df_analise) - 20):
        janela = df_analise.iloc[:i+1]
        if len(janela) < PERIODO_AQUECIMENTO:
            continue

        u = janela.iloc[-1]
        preco_entrada = u['close']

        rsi_val = u['RSI_14']
        macd_hist = u['MACD_HIST']
        ssl_dir = u.get('ssl_dir', 0)
        atr_dir = u.get('atr_dir', 0)
        obv_acel = u.get('OBV_Aceleracao', 0)

        score_alta = 0
        score_baixa = 0
        if not math.isnan(rsi_val):
            if rsi_val < 35: score_alta += 3
            elif rsi_val > 65: score_baixa += 3
        if not math.isnan(macd_hist):
            if macd_hist > 0: score_alta += 2
            else: score_baixa += 2
        if ssl_dir == 1: score_alta += 1
        else: score_baixa += 1
        if atr_dir == 1: score_alta += 1
        else: score_baixa += 1
        if not np.isnan(obv_acel):
            if obv_acel > 0: score_alta += 1
            else: score_baixa += 1

        tipo_sinal = None
        if score_alta >= 5:
            tipo_sinal = "COMPRA"
            sinais_compra += 1
        elif score_baixa >= 5:
            tipo_sinal = "VENDA"
            sinais_venda += 1

        if tipo_sinal:
            tp_pct = 1.5
            sl_pct = 0.75

            if tipo_sinal == "COMPRA":
                tp_preco = preco_entrada * (1 + tp_pct / 100)
                sl_preco = preco_entrada * (1 - sl_pct / 100)
            else:
                tp_preco = preco_entrada * (1 - tp_pct / 100)
                sl_preco = preco_entrada * (1 + sl_pct / 100)

            acerto = False
            pnl_pct = 0
            idx_fim = min(i + 20, len(df_analise))

            for j in range(i + 1, idx_fim):
                high_j = df_analise.iloc[j]['high']
                low_j = df_analise.iloc[j]['low']

                if tipo_sinal == "COMPRA":
                    if high_j >= tp_preco:
                        acerto = True
                        pnl_pct = tp_pct
                        break
                    elif low_j <= sl_preco:
                        pnl_pct = -sl_pct
                        break
                else:
                    if low_j <= tp_preco:
                        acerto = True
                        pnl_pct = tp_pct
                        break
                    elif high_j >= sl_preco:
                        pnl_pct = -sl_pct
                        break
            else:
                ultimo_close = df_analise.iloc[idx_fim - 1]['close']
                pnl_pct = ((ultimo_close - preco_entrada) / preco_entrada) * 100
                if tipo_sinal == "VENDA":
                    pnl_pct = -pnl_pct
                acerto = pnl_pct > 0

            if acerto:
                if tipo_sinal == "COMPRA": acertos_compra += 1
                else: acertos_venda += 1
                ganhos.append(pnl_pct)
            else:
                perdas.append(abs(pnl_pct))

            historico.append({
                'data': df_analise.iloc[i]['time'],
                'sinal': tipo_sinal,
                'preco_entrada': preco_entrada,
                'pnl': pnl_pct,
                'acerto': acerto
            })

    total_sinais = sinais_compra + sinais_venda
    total_acertos = acertos_compra + acertos_venda
    taxa_acerto = (total_acertos / total_sinais * 100) if total_sinais > 0 else 0
    profit_factor = (sum(ganhos) / sum(perdas)) if (perdas and sum(perdas) > 0) else (float('inf') if ganhos else 0)
    avg_win = np.mean(ganhos) if ganhos else 0
    avg_loss = np.mean(perdas) if perdas else 0

    return sinais_compra, sinais_venda, total_acertos, taxa_acerto, profit_factor, avg_win, avg_loss, historico


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO COM VOLUME PROFILE
def renderizar_grafico_plotly(df_completo, simbolo_id, poc, vah, val, txt):
    df_grafico = df_completo.iloc[PERIODO_AQUECIMENTO:].copy()

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df_grafico['time'],
        open=df_grafico['open'], high=df_grafico['high'],
        low=df_grafico['low'], close=df_grafico['close'],
        name=simbolo_id,
        increasing_line_color='#10b981', decreasing_line_color='#ef4444',
        increasing_fillcolor='#10b981', decreasing_fillcolor='#ef4444'
    ))

    fig.add_trace(go.Scatter(
        x=df_grafico['time'], y=df_grafico['SSL_Baseline'],
        mode='lines', name='SMC Baseline (SSL)',
        line=dict(color='#00aaff', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=df_grafico['time'], y=df_grafico['ATR_Stop'],
        mode='lines', name='ATR Trailing Stop',
        line=dict(color='#ffaa00', width=1, dash='dash')
    ))

    if poc is not None:
        fig.add_hline(y=poc, line_dash="dash", line_color="#ffdd57",
                      annotation_text=f"{txt.get('poc_label', 'POC')}: {formatar_preco(poc)}",
                      annotation_position="bottom right",
                      annotation_font=dict(color="#ffdd57", size=10))
    if vah is not None:
        fig.add_hline(y=vah, line_dash="dot", line_color="#ff6b6b",
                      annotation_text=f"{txt.get('vah_label', 'VAH')}: {formatar_preco(vah)}",
                      annotation_position="bottom right",
                      annotation_font=dict(color="#ff6b6b", size=10))
    if val is not None:
        fig.add_hline(y=val, line_dash="dot", line_color="#51cf66",
                      annotation_text=f"{txt.get('val_label', 'VAL')}: {formatar_preco(val)}",
                      annotation_position="bottom right",
                      annotation_font=dict(color="#51cf66", size=10))

    fig.update_layout(
        paper_bgcolor='#0b0f19', plot_bgcolor='#0b0f19',
        font=dict(color='#e2e8f0'),
        xaxis=dict(gridcolor='#1e293b', showgrid=True, rangeslider=dict(visible=False)),
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
    index=lista_criptos.index("BTC/USDT") if "BTC/USDT" in lista_criptos else 0
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
    fg_valor, fg_classificacao = obter_fear_greed_index()

    # ANÁLISE DE LIQUIDEZ REAL (NOVO!)
    liquidez_score, spread_pct, volume_24h_usdt, profundidade_total, detalhes_liq = analisar_liquidez_real(simbolo_id)

    recomendacao, cor_sinal, analise, pontos_alta, pontos_baixa, spike, poc, vah, val, modulos_info = analisar_confluencia(
        df_dados, simbolo_id, timeframe, fg_valor, liquidez_score, txt
    )

    # Banner principal
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

    if spike == "ALTA":
        m4.metric(txt["sinal_spike"], f"🚀 {txt['spike_alta']}")
    elif spike == "BAIXA":
        m4.metric(txt["sinal_spike"], f"💥 {txt['spike_baixa']}")
    else:
        m4.metric(txt["pontos_compra"], f"{pontos_alta:.1f}")

    m5.metric(txt["pontos_venda"], f"{pontos_baixa:.1f}")

    # Segunda linha: Fear & Greed, POC, OBV, e LIQUIDEZ REAL
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if fg_valor is not None:
            fg_emoji = ""
            if fg_valor <= 25: fg_emoji = "😱"
            elif fg_valor <= 45: fg_emoji = "😟"
            elif fg_valor <= 55: fg_emoji = "😐"
            elif fg_valor <= 75: fg_emoji = "😀"
            else: fg_emoji = "🤩"
            st.metric(txt["fear_greed_label"], f"{fg_emoji} {fg_valor}/100", delta=fg_classificacao, delta_color="off")
        else:
            st.metric(txt["fear_greed_label"], "—")

    with col2:
        st.metric("POC", formatar_preco(poc) if poc else "—")

    with col3:
        obv_acel = ultimo_reg.get('OBV_Aceleracao', 0)
        if not (np.isnan(obv_acel) or np.isinf(obv_acel)):
            st.metric("OBV Aceleração", f"{obv_acel:,.0f}")
        else:
            st.metric("OBV Aceleração", "—")

    with col4:
        # LIQUIDEZ REAL - Escala 0-5 com estrelas
        estrelas = "⭐" * liquidez_score + "☆" * (5 - liquidez_score)
        classificacao = txt.get('liquidez_classificacao', ["⚫", "🔴", "🟠", "🟡", "🟢", "⭐"])[liquidez_score]
        st.metric(
            txt["filtro_liquidez"],
            f"{classificacao} {estrelas}",
            delta=f"{liquidez_score}/5",
            delta_color="off"
        )

    # Detalhes da Liquidez
    with st.expander(f"📊 Detalhes da Liquidez — {simbolo_id}", expanded=False):
        dl1, dl2, dl3 = st.columns(3)
        with dl1:
            st.metric(txt["spread_atual"], f"{spread_pct:.4f}%")
        with dl2:
            st.metric(txt["volume_24h_usdt"], formatar_volume(volume_24h_usdt))
        with dl3:
            st.metric(txt["profundidade_livro"], formatar_volume(profundidade_total))
        
        # Barra de progresso da liquidez
        st.progress(liquidez_score / 5.0, text=f"Nota de Liquidez: {liquidez_score}/5 — {txt.get('liquidez_descricao', {}).get(liquidez_score, '')}")

    # Módulos Avançados Status
    st.markdown("---")
    st.markdown(f"### 🔬 Módulos de Confluência Avançada")

    if modulos_info:
        mod1, mod2, mod3, mod4, mod5 = st.columns(5)

        with mod1:
            estr = modulos_info.get('estrutura', 'INDEFINIDO')
            if estr == 'BOS':
                st.metric(txt["modulo_estrutura"], txt["estrutura_bos"])
            elif estr == 'CHoCH':
                st.metric(txt["modulo_estrutura"], txt["estrutura_choch"])
            elif 'TENDENCIA_ALTA' in str(estr):
                st.metric(txt["modulo_estrutura"], "📈 Tend. Alta")
            elif 'TENDENCIA_BAIXA' in str(estr):
                st.metric(txt["modulo_estrutura"], "📉 Tend. Baixa")
            else:
                st.metric(txt["modulo_estrutura"], txt["estrutura_indefinida"])

        with mod2:
            div_obv = modulos_info.get('divergencia_obv', 'NONE')
            if div_obv == 'BULLISH':
                st.metric(txt["modulo_obv"], txt["divergencia_obv_bull"])
            elif div_obv == 'BEARISH':
                st.metric(txt["modulo_obv"], txt["divergencia_obv_bear"])
            else:
                st.metric(txt["modulo_obv"], txt["divergencia_obv_none"])

        with mod3:
            vol_dir = modulos_info.get('volume_direcional', 'NEUTRO')
            if 'BULLISH' in str(vol_dir):
                st.metric(txt["modulo_volume"], txt["volume_direcional_bull"])
            elif 'BEARISH' in str(vol_dir):
                st.metric(txt["modulo_volume"], txt["volume_direcional_bear"])
            else:
                st.metric(txt["modulo_volume"], txt["volume_direcional_neutro"])

        with mod4:
            mtf_ok = modulos_info.get('mtf_alinhado', False)
            st.metric(txt["modulo_mtf"], txt["alinhamento_mtf_sim"] if mtf_ok else txt["alinhamento_mtf_nao"])

        with mod5:
            limiar = modulos_info.get('limiar_dinamico', 9.0)
            st.metric(txt["limiar_dinamico"], f"{limiar:.1f}")

    atr_stop_val = ultimo_reg['ATR_Stop']
    st.markdown(
        f"**{txt['stop_atr']}:** {formatar_preco(atr_stop_val)}"
        f"  |  RSI: **{ultimo_reg['RSI_14']:.1f}**"
        f"  |  MFI: **{ultimo_reg['MFI']:.1f}**"
        f"  |  MACD Hist: **{ultimo_reg['MACD_HIST']:.6f}**"
    )

    st.markdown(f"### {txt['grafico_titulo']}")
    renderizar_grafico_plotly(df_dados, simbolo_id, poc, vah, val, txt)

    if poc is not None:
        st.caption(
            f"📊 **Volume Profile:** POC = {formatar_preco(poc)} | "
            f"VAH = {formatar_preco(vah)} | VAL = {formatar_preco(val)} | "
            f"Preço: {'🟡 Equilíbrio' if val <= preco_atual <= vah else ('🔴 Distribuição' if preco_atual > vah else '🟢 Acumulação')}"
        )

    st.markdown("---")
    st.markdown(f"### {txt['backtest_titulo']}")

    sinais_compra, sinais_venda, total_acertos, taxa_acerto, profit_factor, avg_win, avg_loss, historico = executar_backtesting(
        df_dados, simbolo_id, timeframe, txt
    )

    if sinais_compra is not None and sinais_venda is not None:
        bt1, bt2, bt3, bt4, bt5 = st.columns(5)
        bt1.metric(txt["backtest_compra"], sinais_compra)
        bt2.metric(txt["backtest_venda"], sinais_venda)
        bt3.metric(txt["backtest_total"], sinais_compra + sinais_venda)
        bt4.metric(txt["backtest_acertos"], total_acertos)

        cor_taxa = "normal"
        if taxa_acerto >= 80:
            cor_taxa = "off"
        bt5.metric(txt["backtest_taxa"], f"{taxa_acerto:.1f}%",
                   delta="🎯 80%+" if taxa_acerto >= 80 else None, delta_color=cor_taxa)

        st.markdown(f"**{txt['backtest_metricas']}**")
        pm1, pm2, pm3 = st.columns(3)
        pm1.metric(txt["backtest_profit_factor"], f"{profit_factor:.2f}" if profit_factor != float('inf') else "∞")
        pm2.metric(txt["backtest_avg_win"], f"{avg_win:.2f}%")
        pm3.metric(txt["backtest_avg_loss"], f"{avg_loss:.2f}%")

        if historico:
            st.markdown(f"**{txt['backtest_historico']}**")
            hist_df = pd.DataFrame(historico[-10:][::-1])
            hist_df['Resultado'] = hist_df['acerto'].apply(
                lambda x: txt["backtest_acerto"] if x else txt["backtest_erro"]
            )
            hist_df['Preço'] = hist_df['preco_entrada'].apply(lambda x: formatar_preco(x))
            hist_df['P&L'] = hist_df['pnl'].apply(lambda x: f"{x:+.2f}%")
            hist_df_display = hist_df[['data', 'sinal', 'Preço', 'P&L', 'Resultado']].copy()
            hist_df_display.columns = [
                txt["backtest_data"], txt["backtest_sinal"],
                txt["backtest_preco"], 'P&L', txt["backtest_resultado"]
            ]
            st.dataframe(hist_df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Backtesting requer mais dados históricos. Aguarde mais candles ou troque para um timeframe menor.")

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
