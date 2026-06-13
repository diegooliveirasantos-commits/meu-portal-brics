import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

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
        "stop_atr": "Preço Stop ATR",
        "fib_niveis_titulo": "📐 Níveis Críticos de Retração de Fibonacci (Ciclo Atual)",
        "matriz_detalhada": "📊 Matriz Detallada de Momentum e Exaustão",
        "compra_forte": "🟢 COMPRA FORTE (SMC + FIBONACCI ALINHADOS)",
        "venda_forte": "🔴 VENDA FORTE (SMC + FIBONACCI ALINHADOS)",
        "neutro": "🟡 NEUTRO (AGUARDAR SMC)",
        "erro_dados": "Dados históricos insuficientes nesta Exchange para calcular a confluência estrutural SMC. Escolha outro Ativo ou reduza o Tempo Gráfico.",
        "fib_nomes": ["0.0% (MÁXIMA)", "23.6%", "38.2% (Fronteira Premium)", "50.0% (Equilíbrio)", "61.8% (Golden Ratio / Desconto)", "78.6%", "100.0% (MÍNIMA)"],
        "fib_posicoes": ["Topo do Ciclo", "Retração Rasa", "Zona de Carga Vendedora", "Preço Justo", "Zona de Compra Institucional", "Retração Profunda", "Fundo do Ciclo"],
        "ctx_desconto": "Ativo posicionado em Zona de Desconto de Fibonacci (Excelente risco/retorno para Institucionais).",
        "ctx_premium": "Ativo posicionado em Zona Premium de Fibonacci (Preço esticado, propício para realização de lucro).",
        "ctx_neutro": "Preço em zona neutra de equilíbrio de Fibonacci (Fair Value Zone)."
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
        "stop_atr": "ATR Stop Price",
        "fib_niveis_titulo": "📐 Critical Fibonacci Retraction Levels (Current Cycle)",
        "matriz_detalhada": "📊 Detailed Momentum & Exhaustion Matrix",
        "compra_forte": "🟢 STRONG BUY (SMC + FIBONACCI ALIGNED)",
        "venda_forte": "🔴 STRONG SELL (SMC + FIBONACCI ALIGNED)",
        "neutro": "🟡 NEUTRAL (AWAIT SMC)",
        "erro_dados": "Insufficient historical data on this Exchange to calculate SMC structural confluence. Choose another Asset or reduce the Timeframe.",
        "fib_nomes": ["0.0% (MAXIMUM)", "23.6%", "38.2% (Premium Frontier)", "50.0% (Equilibrium)", "61.8% (Golden Ratio / Discount)", "78.6%", "100.0% (MINIMUM)"],
        "fib_posicoes": ["Cycle Top", "Shallow Retraction", "Seller Load Zone", "Fair Price", "Institutional Buy Zone", "Deep Retraction", "Cycle Bottom"],
        "ctx_desconto": "Asset positioned in Fibonacci Discount Zone (Excellent risk/reward for Institutionals).",
        "ctx_premium": "Asset positioned in Fibonacci Premium Zone (Price stretched, suitable for profit-taking).",
        "ctx_neutro": "Price in neutral Fibonacci equilibrium zone (Fair Value Zone)."
    },
    "Español (ESP)": {
        "titulo": "🏦 BRICSVAULT PORTAL - Motor de Smart Money Concepts (SMC)",
        "config_globais": "⚙️ Configuraciones Globales",
        "selecione_cripto": "Seleccione Cualquier Criptomoneda (/USDT):",
        "tempo_grafico": "Período de Tiempo:",
        "modo_vivo": "Activar Monitoreo en Tiempo Real",
        "intervalo_refresh": "Intervalo de Actualización (Segundos):",
        "preco_spot": "Precio Spot Real",
        "variacao_24h": "Variación 24h (Exchange)",
        "stop_atr": "Precio Stop ATR",
        "fib_niveis_titulo": "📐 Niveles Críticos de Retracción de Fibonacci (Ciclo Actual)",
        "matriz_detalhada": "📊 Matriz Detallada de Momentum y Agotamiento",
        "compra_forte": "🟢 COMPRA FUERTE (SMC + FIBONACCI ALINEADOS)",
        "venda_forte": "🔴 VENTA FUERTE (SMC + FIBONACCI ALINEADOS)",
        "neutro": "🟡 NEUTRO (ESPERAR SMC)",
        "erro_dados": "Datos históricos insuficientes en esta Exchange para calcular la confluencia estructural SMC. Elija otro Activo o reduzca el Tiempo Gráfico.",
        "fib_nomes": ["0.0% (MÁXIMA)", "23.6%", "38.2% (Frontera Premium)", "50.0% (Equilibrio)", "61.8% (Golden Ratio / Descuento)", "78.6%", "100.0% (MÍNIMA)"],
        "fib_posicoes": ["Techo del Ciclo", "Retracción Superficial", "Zona de Carga Vendedora", "Precio Justo", "Zona de Compra Institucional", "Retracción Profunda", "Fondo del Ciclo"],
        "ctx_desconto": "Activo posicionado en Zona de Descuento de Fibonacci (Excelente riesgo/beneficio para Institucionales).",
        "ctx_premium": "Activo posicionado en Zona Premium de Fibonacci (Precio estirado, propicio para toma de ganancias).",
        "ctx_neutro": "Precio en zona neutral de equilibrio de Fibonacci (Fair Value Zone)."
    },
    "中文 (CH)": {
        "titulo": "🏦 BRICSVAULT 门户 - 聪明的钱概念 (SMC) 引擎",
        "config_globais": "⚙️ 全局设置",
        "selecione_cripto": "选择任何加密货币 (/USDT):",
        "tempo_grafico": "时间框架:",
        "modo_vivo": "启用实时监控",
        "intervalo_refresh": "刷新间隔（秒）:",
        "preco_spot": "实时现货价格",
        "variacao_24h": "24小时涨跌幅 (交易所)",
        "stop_atr": "ATR 止损价",
        "fib_niveis_titulo": "📐 关键斐波那契回撤水平（当前周期）",
        "matriz_detalhada": "📊 动量与衰竭详细矩阵",
        "compra_forte": "🟢 强力买入 (SMC + 斐波那契共振)",
        "venda_forte": "🔴 强力卖出 (SMC + 斐波那契共振)",
        "neutro": "🟡 中性 (等待 SMC 信号)",
        "erro_dados": "该交易所的历史数据不足，无法计算 SMC 结构共振。请选择其他资产或缩短时间框架。",
        "fib_nomes": ["0.0% (最高点)", "23.6%", "38.2% (溢价边界)", "50.0% (平衡点)", "61.8% (黄金分割 / 折扣区)", "78.6%", "100.0% (最低点)"],
        "fib_posicoes": ["周期顶部", "浅幅回撤", "卖家压盘区", "合理价格", "机构买入区", "深幅回撤", "周期底部"],
        "ctx_desconto": "资产处于斐波那契折扣区（对机构而言极佳 Risk/Reward）。",
        "ctx_premium": "资产处于斐波那契溢价区（价格拉升过高，适合获利了结）。",
        "ctx_neutro": "价格处于斐波那契中性平衡区 (Fair Value Zone)."
    },
    "Русский (RUS)": {
        "titulo": "🏦 BRICSVAULT ПОРТАЛ - Алгоритм Smart Money Concepts (SMC)",
        "config_globais": "⚙️ Глобальные настройки",
        "selecione_cripto": "Выберите криптовалюту (/USDT):",
        "tempo_grafico": "Таймфрейм:",
        "modo_vivo": "Включить мониторинг в реальном времени",
        "intervalo_refresh": "Интервал обновления (сек):",
        "preco_spot": "Текущая спотовая цена",
        "variacao_24h": "Изменение за 24ч (Exchange)",
        "stop_atr": "Цена ATR Stop",
        "fib_niveis_titulo": "📐 Критические уровни коррекции Фибоначчи (Текущий цикл)",
        "matriz_detalhada": "📊 Подробная матрица импульса и истощения",
        "compra_forte": "🟢 АКТИВНОЕ ПОКУПКА (SMC + ФИБОНАЧЧИ СОГЛАСОВАНЫ)",
        "venda_forte": "🔴 АКТИВНОЕ ПРОДАЖА (SMC + ФИБОНАЧЧИ СОГЛАСОВАНЫ)",
        "neutro": "🟡 НЕЙТРАЛЬНО (ОЖИДАНИЕ SMC)",
        "erro_dados": "Недостаточно исторических данных на этой бирже для расчета структурного слияния SMC. Выберите другой актив или уменьшите таймфрейм.",
        "fib_nomes": ["0.0% (МАКСИМУМ)", "23.6%", "38.2% (Премиум граница)", "50.0% (Равновесие)", "61.8% (Золотое сечение / Дисконт)", "78.6%", "100.0% (МИНИМУМ)"],
        "fib_posicoes": ["Пик цикла", "Мелкая коррекция", "Зона нагрузки продавцов", "Справедливая цена", "Институциональная зона покупки", "Глубокая коррекция", "Дно цикла"],
        "ctx_desconto": "Актив находится в дисконтной зоне Фибоначчи (Отличное соотношение риск/прибыль для крупных игроков).",
        "ctx_premium": "Актив находится в премиум-зоне Фибоначчи (Цена завышена, подходит для фиксации прибыли).",
        "ctx_neutro": "Цена находится в нейтральной зоне равновесия Фибоначчи (Fair Value Zone)."
    },
    "Français (FR)": {
        "titulo": "🏦 BRICSVAULT PORTAL - Moteur Smart Money Concepts (SMC)",
        "config_globais": "⚙️ Paramètres Globaux",
        "selecione_cripto": "Sélectionnez une Crypto-monnaie (/USDT):",
        "tempo_grafico": "Unités de Temps:",
        "modo_vivo": "Activer le Suivi en Temps Réel",
        "intervalo_refresh": "Intervalle de Rafraîchissement (Secondes):",
        "preco_spot": "Prix Spot Réel",
        "variacao_24h": "Variation 24h (Exchange)",
        "stop_atr": "Prix Stop ATR",
        "fib_niveis_titulo": "📐 Niveaux Critiques de Retracement de Fibonacci (Cycle Actuel)",
        "matriz_detalhada": "📊 Matrice Détaillée du Momentum & Épuisement",
        "compra_forte": "🟢 ACHAT FORT (SMC + FIBONACCI ALIGNÉS)",
        "venda_forte": "🔴 VENTE FORTE (SMC + FIBONACCI ALIGNÉS)",
        "neutro": "🟡 NEUTRE (ATTENTE SMC)",
        "erro_dados": "Données historiques insuffisantes sur cet Exchange pour calculer la confluence structurelle SMC. Choisissez un autre Actif ou réduisez l'unité de temps.",
        "fib_nomes": ["0.0% (MAXIMUM)", "23.6%", "38.2% (Zone Premium)", "50.0% (Équilibre)", "61.8% (Ratio d'or / Zone de Discount)", "78.6%", "100.0% (MINIMUM)"],
        "fib_posicoes": ["Sommet du Cycle", "Retracement Superficiel", "Zone de Vente Institutionnelle", "Prix Équitable", "Zone d'Achat Institutionnelle", "Retracement Profond", "Bas du Cycle"],
        "ctx_desconto": "Actif positionné dans la Zone de Discount de Fibonacci (Excellent rapport risque/rendement pour les Institutionnels).",
        "ctx_premium": "Actif positionné dans la Zone Premium de Fibonacci (Prix étiré, propice à la prise de bénéfices).",
        "ctx_neutro": "Prix dans la zone d'équilibre neutre de Fibonacci (Fair Value Zone)."
    }
}

# SELETOR DE IDIOMA CONFIGURADO NO MENU LATERAL
st.sidebar.markdown("### 🌐 Language / Idioma / Langue")
idioma_selecionado = st.sidebar.selectbox(
    "Select Interface Language:",
    options=list(DICIONARIO_LINGUAS.keys()),
    index=0
)

txt = DICIONARIO_LINGUAS[idioma_selecionado]

@st.cache_resource
def inicializar_exchange():
    return ccxt.gate({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })

gateio_client = inicializar_exchange()

@st.cache_data(ttl=3600)
def obter_todos_pares_usdt():
    try:
        mercados = gateio_client.load_markets()
        return sorted([simbolo for simbolo in mercados.keys() if simbolo.endswith('/USDT')])
    except Exception:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]

def calcular_rsi(df, col, periodo=14):
    delta = df[col].diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    ma_ganho = ganho.ewm(span=periodo, adjust=False).mean()
    ma_perda = perda.ewm(span=periodo, adjust=False).mean()
    return 100 - (100 / (1 + (ma_ganho / ma_perda.replace(0, 0.00001))))

def calcular_stoch_rsi(df, periodo=14, k_period=3, d_period=3):
    rsi = df['RSI_14']
    min_rsi = rsi.rolling(window=periodo).min()
    max_rsi = rsi.rolling(window=periodo).max()
    df['StochRSI_K'] = ((rsi - min_rsi) / (max_rsi - min_rsi).replace(0, 0.00001)).rolling(window=k_period).mean() * 100
    df['StochRSI_D'] = df['StochRSI_K'].rolling(window=d_period).mean()
    return df

def calcular_macd(df, col):
    ema_rapida = df[col].ewm(span=12, adjust=False).mean()
    ema_lenta = df[col].ewm(span=26, adjust=False).mean()
    macd = ema_rapida - ema_lenta
    return macd, macd.ewm(span=9, adjust=False).mean(), macd - macd.ewm(span=9, adjust=False).mean()

def calcular_chaikin_money_flow(df, periodo=20):
    mfv = (((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low']).replace(0, 0.00001)) * df['volume']
    df['CMF'] = mfv.rolling(window=periodo).sum() / df['volume'].rolling(window=periodo).sum().replace(0, 0.00001)
    return df

def calcular_wavetrend_oscillator(df, n1=10, n2=21):
    ap = (df['high'] + df['low'] + df['close']) / 3
    esa = ap.ewm(span=n1, adjust=False).mean()
    d = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
    df['WT1'] = ((ap - esa) / (0.015 * d).replace(0, 0.00001)).ewm(span=n2, adjust=False).mean()
    df['WT2'] = df['WT1'].rolling(window=4).mean().bfill()
    return df

def calcular_mfi(df, periodo=14):
    tp = (df['high'] + df['low'] + df['close']) / 3
    rmf = tp * df['volume']
    pos_flow, neg_flow = pd.Series(0.0, index=df.index), pd.Series(0.0, index=df.index)
    for i in range(1, len(df)):
        if tp.iloc[i] > tp.iloc[i-1]: pos_flow.iloc[i] = rmf.iloc[i]
        elif tp.iloc[i] < tp.iloc[i-1]: neg_flow.iloc[i] = rmf.iloc[i]
    return 100 - (100 / (1 + (pos_flow.rolling(window=periodo).sum() / neg_flow.rolling(window=periodo).sum().replace(0, 0.00001))))

def calcular_ssl_hybrid(df, periodo=20):
    sma_high = df['high'].rolling(window=periodo).mean()
    sma_low = df['low'].rolling(window=periodo).mean()
    ssl_direction, current_dir = [], 1
    for idx in range(len(df)):
        close = df['close'].iloc[idx]
        h, l = sma_high.iloc[idx], sma_low.iloc[idx]
        if pd.isna(h) or pd.isna(l): ssl_direction.append(current_dir); continue
        if close > h: current_dir = 1
        elif close < l: current_dir = -1
        ssl_direction.append(current_dir)
    df['ssl_dir'] = ssl_direction
    df['SSL_Baseline'] = df.apply(lambda r: sma_high.iloc[df.index.get_loc(r.name)] if r['ssl_dir'] == 1 else sma_low.iloc[df.index.get_loc(r.name)], axis=1)
    return df

def calcular_atr_stop(df, periodo=14, multiplicador=3.0):
    high, low, close = df['high'], df['low'], df['close']
    tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.ewm(span=periodo, adjust=False).mean()
    atr_stop, tendencia = np.zeros(len(df)), np.zeros(len(df))
    for i in range(1, len(df)):
        if i == 1: atr_stop[i] = close.iloc[i] - (atr.iloc[i] * multiplicador); tendencia[i] = 1; continue
        if tendencia[i-1] == 1:
            if close.iloc[i] < atr_stop[i-1]: tendencia[i] = -1; atr_stop[i] = close.iloc[i] + (atr.iloc[i] * multiplicador)
            else: tendencia[i] = 1; atr_stop[i] = max(atr_stop[i-1], close.iloc[i] - (atr.iloc[i] * multiplicador))
        else:
            if close.iloc[i] > atr_stop[i-1]: tendencia[i] = 1; atr_stop[i] = close.iloc[i] - (atr.iloc[i] * multiplicador)
            else: tendencia[i] = -1; atr_stop[i] = min(atr_stop[i-1], close.iloc[i] + (atr.iloc[i] * multiplicador))
    df['ATR_Stop'], df['atr_dir'] = atr_stop, tendencia
    return df

def calcular_alpha_trend(df, periodo=14, coeff=1.0):
    high, low, close = df['high'], df['low'], df['close']
    tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.rolling(window=periodo).mean()
    df['MFI'] = calcular_mfi(df, periodo)
    up_t = low - coeff * atr
    down_t = high + coeff * atr
    alpha_trend = np.zeros(len(df))
    for i in range(len(df)):
        if i < periodo: alpha_trend[i] = close.iloc[i]; continue
        if df['MFI'].iloc[i] >= 50: alpha_trend[i] = max(up_t.iloc[i], alpha_trend[i-1])
        else: alpha_trend[i] = min(down_t.iloc[i], alpha_trend[i-1])
    df['AT_K1'] = alpha_trend
    return df

def mapear_estrutura_smc(df):
    fechamentos, maximas, minimas = df['close'].values, df['high'].values, df['low'].values
    bos_detectado, choch_detectado, fvg_pendente = 0, 0, 0
    for i in range(len(df) - 3, len(df) - 1):
        if minimas[i+1] > maximas[i-1]: fvg_pendente = 1
        elif maximas[i+1] < minimas[i-1]: fvg_pendente = -1
    topo_local, fundo_local = np.max(fechamentos[-15:-2]), np.min(fechamentos[-15:-2])
    if fechamentos[-1] > topo_local: bos_detectado = 1
    elif fechamentos[-1] < fundo_local: bos_detectado = -1
    if fechamentos[-1] > topo_local and fechamentos[-2] <= topo_local: choch_detectado = 1
    elif fechamentos[-1] < fundo_local and fechamentos[-2] >= fundo_local: choch_detectado = -1
    df['SMC_BOS'], df['SMC_CHOCH'], df['SMC_FVG'] = bos_detectado, choch_detectado, fvg_pendente
    return df

def analisar_confluencia_smc_total(df, fib_niveis):
    u = df.iloc[-1]
    preco_atual = u['close']
    pontos_alta = 0
    pontos_baixa = 0
    
    if u['SMC_CHOCH'] == 1 or u['SMC_BOS'] == 1: pontos_alta += 3
    if u['SMC_CHOCH'] == -1 or u['SMC_BOS'] == -1: pontos_baixa += 3
    if u['SMC_FVG'] == 1: pontos_alta += 1
    if u['SMC_FVG'] == -1: pontos_baixa += 1
    
    if preco_atual <= fib_niveis['fib_618']:
        pontos_alta += 2.0
        contexto_fib = txt["ctx_desconto"]
    elif preco_atual >= fib_niveis['fib_382']:
        pontos_baixa += 2.0
        contexto_fib = txt["ctx_premium"]
    else:
        contexto_fib = txt["ctx_neutro"]

    if u['CMF'] > 0: pontos_alta += 1.5
    else: pontos_baixa += 1.5
    if u['WT1'] > u['WT2']: pontos_alta += 1
    else: pontos_baixa += 1
    if u['MACD_HIST'] > 0: pontos_alta += 1
    else: pontos_baixa += 1

    if pontos_alta >= 7.5:
        return txt["compra_forte"], "#00cc66", f"{contexto_fib} SMC Order Flow Bullish Structure."
    elif pontos_baixa >= 7.5:
        return txt["venda_forte"], "#ff3333", f"{contexto_fib} SMC Order Flow Bearish Structure."
    else:
        return txt["neutro"], "#ffcc00", f"{contexto_fib}"

def calcular_retracao_fibonacci(df):
    maxima_absoluta, minima_absoluta = df['high'].max(), df['low'].min()
    diff = maxima_absoluta - minima_absoluta
    return {
        'fib_0': maxima_absoluta, 'fib_236': maxima_absoluta - (0.236 * diff),
        'fib_382': maxima_absoluta - (0.382 * diff), 'fib_500': maxima_absoluta - (0.500 * diff),
        'fib_618': maxima_absoluta - (0.618 * diff), 'fib_786': maxima_absoluta - (0.786 * diff),
        'fib_100': minima_absoluta
    }

def carregar_dados_bricsvault_smc(simbolo_id, timeframe_selecionado):
    try:
        velas = gateio_client.fetch_ohlcv(simbolo_id, timeframe=timeframe_selecionado, limit=200)
        if not velas: return None
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        df['RSI_14'] = calcular_rsi(df, 'close', 14)
        df = calcular_stoch_rsi(df)
        macd, sinal, hist = calcular_macd(df, 'close')
        df['MACD'], df['MACD_SIGNAL'], df['MACD_HIST'] = macd, sinal, hist
        df = calcular_ssl_hybrid(df)
        df = calcular_atr_stop(df)
        df = calcular_alpha_trend(df)
        df = calcular_chaikin_money_flow(df)
        df = calcular_wavetrend_oscillator(df)
        df = mapear_estrutura_smc(df)
        return df.dropna(subset=['close', 'SSL_Baseline'])
    except Exception:
        return None

def obter_variacao_24h_precisa(simbolo_id):
    try:
        dados_24h = gateio_client.fetch_ohlcv(simbolo_id, timeframe='1d', limit=2)
        if dados_24h and len(dados_24h) >= 2:
            return ((dados_24h[-1][4] - dados_24h[-1][1]) / dados_24h[-1][1]) * 100
    except Exception:
        pass
    return 0.0

# --- INTERFACE DINÂMICA ---
st.title(txt["titulo"])

st.sidebar.header(txt["config_globais"])
lista_criptos = obter_todos_pares_usdt()
simbolo_id = st.sidebar.selectbox(txt["selecione_cripto"], lista_criptos, index=lista_criptos.index("SOL/USDT") if "SOL/USDT" in lista_criptos else 0)

intervalos = {"1m": "1m", "5m": "5m", "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w"}
timeframe = st.sidebar.selectbox(txt["tempo_grafico"], list(intervalos.keys()), index=2)

st.sidebar.markdown("---")
modo_vivo = st.sidebar.toggle(txt["modo_vivo"], value=True)
intervalo_refresh = st.sidebar.slider(txt["intervalo_refresh"], min_value=5, max_value=30, value=10)

df_dados = carregar_dados_bricsvault_smc(simbolo_id, timeframe)
    
if df_dados is not None and not df_dados.empty:
    ultimo_reg = df_dados.iloc[-1]
    preco_atual = ultimo_reg['close']
    fib_niveis = calcular_retracao_fibonacci(df_dados)
    variacao_real_exchange = obter_variacao_24h_precisa(simbolo_id)

    recomendacao, cor_sinal, analise_justificada = analisar_confluencia_smc_total(df_dados, fib_niveis)

    st.markdown(f"""
    <div style="background-color: {cor_sinal}22; padding: 20px; border-radius: 10px; border: 2px solid {cor_sinal}; margin-bottom: 25px;">
        <h2 style="margin: 0; color: {cor_sinal}; font-size: 24px;">{recomendacao}</h2>
        <p style="margin: 8px 0 0 0; font-size: 16px; color: #ffffff;">{analise_justificada}</p>
    </div>
    """, unsafe_allow_html=True)

    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric(txt["preco_spot"], f"$ {preco_atual:,.4f}")
    m_col2.metric(txt["variacao_24h"], f"{variacao_real_exchange:+.2f}%")
    m_col3.metric(txt["stop_atr"], f"$ {ultimo_reg['ATR_Stop']:,.4f}")

    st.markdown(f"### {txt['fib_niveis_titulo']}")
    fib_df = pd.DataFrame({
        "Nível Fibonacci": txt["fib_nomes"],
