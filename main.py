import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

import math

# ─────────────────────────────────────────────────────────────
# FORMATACAO DE PRECO — notacao compacta para valores micro
# ─────────────────────────────────────────────────────────────
# Logica:
#   Se preco < 0.001 -> contar zeros entre "0." e o 1o digito significativo
#   Exibir: "0.0{N}x{digitos significativos}"
#   Exemplos:
#     0.0000000789 -> 7 zeros -> "0.07x789"
#     0.0000765    -> 4 zeros -> "0.04x765"
#   Se preco >= 0.001 -> formatacao decimal convencional
#
def formatar_preco(valor: float, prefixo: str = "$ ") -> str:
    """
    Formatacao inteligente de precos de criptomoedas.
    Valores micro (< 0.001) usam notacao compacta: 0.0{N_zeros}x{digitos_significativos}
    Exemplos:
      0.0000000789 -> "$ 0.07x789"
      0.0000765    -> "$ 0.04x765"
    Valores normais usam formatacao decimal convencional.
    """
    import math
    from decimal import Decimal
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
        "matriz_detalhada": "📊 Matriz Detalhada de Momentum e Exaustão",
        "compra_forte": "🟢 COMPRA FORTE (SMC + FIBONACCI ALINHADOS)",
        "venda_forte": "🔴 VENDA FORTE (SMC + FIBONACCI ALINHADOS)",
        "neutro": "🟡 NEUTRO (AGUARDAR SMC)",
        "erro_dados": "Dados históricos insuficientes nesta Exchange para calcular a confluência estrutural SMC. Escolha outro Ativo ou reduza o Tempo Gráfico.",
        "fib_nomes": ["0.0% (MÁXIMA)", "23.6%", "38.2% (Fronteira Premium)", "50.0% (Equilíbrio)", "61.8% (Golden Ratio / Desconto)", "78.6%", "100.0% (MÍNIMA)"],
        "fib_posicoes": ["Topo do Ciclo", "Retração Rasa", "Zona de Carga Vendedora", "Preço Justo", "Zona de Compra Institucional", "Retração Profunda", "Fundo do Ciclo"],
        "ctx_desconto": "Ativo posicionado em Zona de Desconto de Fibonacci (Excelente risco/retorno para Institucionais).",
        "ctx_premium": "Ativo posicionado em Zona Premium de Fibonacci (Preço esticado, propício para realização de lucro).",
        "ctx_neutro": "Preço em zona neutra de equilíbrio de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Última Atualização",
        "proximo_refresh": "Próximo refresh em",
        "segundos": "segundos",
        "indicadores_smc": "🧠 Indicadores SMC",
        "bos": "BOS (Break of Structure)",
        "choch": "CHoCH (Change of Character)",
        "fvg": "FVG (Fair Value Gap)",
        "ssl": "SSL Hybrid",
        "macd_hist": "MACD Histograma",
        "cmf": "CMF (Chaikin Money Flow)",
        "wt": "WaveTrend WT1 vs WT2",
        "rsi": "RSI (14)",
        "stoch_rsi_k": "Stoch RSI %K",
        "stoch_rsi_d": "Stoch RSI %D",
        "mfi": "MFI (14)",
        "alta": "ALTA",
        "baixa": "BAIXA",
        "neutro_curto": "NEUTRO",
        "resumo_confluencia": "Resumo de Confluência",
        "pontos_compra": "Pontos de Compra",
        "pontos_venda": "Pontos de Venda",
        "grafico_titulo": "📈 Gráfico de Preço com Indicadores SMC",
        "sem_dados": "Nenhum dado disponível. Verifique a conexão.",
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
        "ctx_neutro": "Price in neutral Fibonacci equilibrium zone (Fair Value Zone).",
        "ultima_atualizacao": "Last Update",
        "proximo_refresh": "Next refresh in",
        "segundos": "seconds",
        "indicadores_smc": "🧠 SMC Indicators",
        "bos": "BOS (Break of Structure)",
        "choch": "CHoCH (Change of Character)",
        "fvg": "FVG (Fair Value Gap)",
        "ssl": "SSL Hybrid",
        "macd_hist": "MACD Histogram",
        "cmf": "CMF (Chaikin Money Flow)",
        "wt": "WaveTrend WT1 vs WT2",
        "rsi": "RSI (14)",
        "stoch_rsi_k": "Stoch RSI %K",
        "stoch_rsi_d": "Stoch RSI %D",
        "mfi": "MFI (14)",
        "alta": "BULLISH",
        "baixa": "BEARISH",
        "neutro_curto": "NEUTRAL",
        "resumo_confluencia": "Confluence Summary",
        "pontos_compra": "Buy Points",
        "pontos_venda": "Sell Points",
        "grafico_titulo": "📈 Price Chart with SMC Indicators",
        "sem_dados": "No data available. Check connection.",
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
        "ctx_neutro": "Precio en zona neutral de equilibrio de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Última Actualización",
        "proximo_refresh": "Próximo refresh en",
        "segundos": "segundos",
        "indicadores_smc": "🧠 Indicadores SMC",
        "bos": "BOS (Ruptura de Estructura)",
        "choch": "CHoCH (Cambio de Carácter)",
        "fvg": "FVG (Gap de Valor Justo)",
        "ssl": "SSL Hybrid",
        "macd_hist": "Histograma MACD",
        "cmf": "CMF (Flujo de Dinero Chaikin)",
        "wt": "WaveTrend WT1 vs WT2",
        "rsi": "RSI (14)",
        "stoch_rsi_k": "Stoch RSI %K",
        "stoch_rsi_d": "Stoch RSI %D",
        "mfi": "MFI (14)",
        "alta": "ALCISTA",
        "baixa": "BAJISTA",
        "neutro_curto": "NEUTRAL",
        "resumo_confluencia": "Resumen de Confluencia",
        "pontos_compra": "Puntos de Compra",
        "pontos_venda": "Puntos de Venta",
        "grafico_titulo": "📈 Gráfico de Precio con Indicadores SMC",
        "sem_dados": "Sin datos disponibles. Verifique la conexión.",
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
        "ctx_neutro": "价格处于斐波那契中性平衡区 (Fair Value Zone).",
        "ultima_atualizacao": "最后更新",
        "proximo_refresh": "下次刷新",
        "segundos": "秒",
        "indicadores_smc": "🧠 SMC 指标",
        "bos": "BOS（结构突破）",
        "choch": "CHoCH（性格转变）",
        "fvg": "FVG（公平价值缺口）",
        "ssl": "SSL 混合",
        "macd_hist": "MACD 柱状图",
        "cmf": "CMF（柴金资金流）",
        "wt": "WaveTrend WT1 vs WT2",
        "rsi": "RSI (14)",
        "stoch_rsi_k": "Stoch RSI %K",
        "stoch_rsi_d": "Stoch RSI %D",
        "mfi": "MFI (14)",
        "alta": "看涨",
        "baixa": "看跌",
        "neutro_curto": "中性",
        "resumo_confluencia": "共振摘要",
        "pontos_compra": "买入分数",
        "pontos_venda": "卖出分数",
        "grafico_titulo": "📈 带SMC指标的价格图表",
        "sem_dados": "无数据。请检查连接。",
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
        "ctx_neutro": "Цена находится в нейтральной зоне равновесия Фибоначчи (Fair Value Zone).",
        "ultima_atualizacao": "Последнее обновление",
        "proximo_refresh": "Следующее обновление через",
        "segundos": "сек",
        "indicadores_smc": "🧠 Индикаторы SMC",
        "bos": "BOS (Пробой структуры)",
        "choch": "CHoCH (Смена характера)",
        "fvg": "FVG (Разрыв справедливой стоимости)",
        "ssl": "SSL Hybrid",
        "macd_hist": "Гистограмма MACD",
        "cmf": "CMF (Индикатор денежного потока Чайкина)",
        "wt": "WaveTrend WT1 vs WT2",
        "rsi": "RSI (14)",
        "stoch_rsi_k": "Stoch RSI %K",
        "stoch_rsi_d": "Stoch RSI %D",
        "mfi": "MFI (14)",
        "alta": "БЫЧИЙ",
        "baixa": "МЕДВЕЖИЙ",
        "neutro_curto": "НЕЙТРАЛЬНО",
        "resumo_confluencia": "Сводка слияния",
        "pontos_compra": "Очки покупки",
        "pontos_venda": "Очки продажи",
        "grafico_titulo": "📈 График цены с индикаторами SMC",
        "sem_dados": "Нет данных. Проверьте соединение.",
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
        "ctx_neutro": "Prix dans la zone d'équilibre neutre de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Dernière mise à jour",
        "proximo_refresh": "Prochain refresh dans",
        "segundos": "secondes",
        "indicadores_smc": "🧠 Indicateurs SMC",
        "bos": "BOS (Rupture de Structure)",
        "choch": "CHoCH (Changement de Caractère)",
        "fvg": "FVG (Écart de Juste Valeur)",
        "ssl": "SSL Hybrid",
        "macd_hist": "Histogramme MACD",
        "cmf": "CMF (Flux Monétaire Chaikin)",
        "wt": "WaveTrend WT1 vs WT2",
        "rsi": "RSI (14)",
        "stoch_rsi_k": "Stoch RSI %K",
        "stoch_rsi_d": "Stoch RSI %D",
        "mfi": "MFI (14)",
        "alta": "HAUSSIER",
        "baixa": "BAISSIER",
        "neutro_curto": "NEUTRE",
        "resumo_confluencia": "Résumé de Confluence",
        "pontos_compra": "Points d'Achat",
        "pontos_venda": "Points de Vente",
        "grafico_titulo": "📈 Graphique de Prix avec Indicateurs SMC",
        "sem_dados": "Aucune donnée disponible. Vérifiez la connexion.",
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

# ─────────────────────────────────────────────────────────────
# CONEXÃO COM EXCHANGE
# ─────────────────────────────────────────────────────────────

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
        return sorted([s for s in mercados.keys() if s.endswith('/USDT')])
    except Exception:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]

# ─────────────────────────────────────────────────────────────
# FUNÇÕES DE INDICADORES  (todas vetorizadas)
# ─────────────────────────────────────────────────────────────

def calcular_rsi(df, col, periodo=14):
    delta = df[col].diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    ma_ganho = ganho.ewm(span=periodo, adjust=False).mean()
    ma_perda = perda.ewm(span=periodo, adjust=False).mean()
    return 100 - (100 / (1 + (ma_ganho / ma_perda.replace(0, 1e-10))))

def calcular_stoch_rsi(df, periodo=14, k_period=3, d_period=3):
    rsi = df['RSI_14']
    min_rsi = rsi.rolling(window=periodo).min()
    max_rsi = rsi.rolling(window=periodo).max()
    stoch_raw = (rsi - min_rsi) / (max_rsi - min_rsi).replace(0, 1e-10)
    df['StochRSI_K'] = stoch_raw.rolling(window=k_period).mean() * 100
    df['StochRSI_D'] = df['StochRSI_K'].rolling(window=d_period).mean()
    return df

def calcular_macd(df, col):
    ema_rapida = df[col].ewm(span=12, adjust=False).mean()
    ema_lenta  = df[col].ewm(span=26, adjust=False).mean()
    macd       = ema_rapida - ema_lenta
    sinal      = macd.ewm(span=9, adjust=False).mean()
    return macd, sinal, macd - sinal

def calcular_chaikin_money_flow(df, periodo=20):
    rng = (df['high'] - df['low']).replace(0, 1e-10)
    mfm = ((df['close'] - df['low']) - (df['high'] - df['close'])) / rng
    mfv = mfm * df['volume']
    vol_sum = df['volume'].rolling(window=periodo).sum().replace(0, 1e-10)
    df['CMF'] = mfv.rolling(window=periodo).sum() / vol_sum
    return df

def calcular_wavetrend_oscillator(df, n1=10, n2=21):
    ap  = (df['high'] + df['low'] + df['close']) / 3
    esa = ap.ewm(span=n1, adjust=False).mean()
    d   = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
    ci  = (ap - esa) / (0.015 * d.replace(0, 1e-10))
    df['WT1'] = ci.ewm(span=n2, adjust=False).mean()
    df['WT2'] = df['WT1'].rolling(window=4).mean().bfill()
    return df

def calcular_mfi(df, periodo=14):
    tp  = (df['high'] + df['low'] + df['close']) / 3
    rmf = tp * df['volume']
    tp_shift = tp.shift(1)
    pos_flow = rmf.where(tp > tp_shift, 0.0)
    neg_flow = rmf.where(tp < tp_shift, 0.0)
    pos_sum  = pos_flow.rolling(window=periodo).sum()
    neg_sum  = neg_flow.rolling(window=periodo).sum().replace(0, 1e-10)
    return 100 - (100 / (1 + pos_sum / neg_sum))

def calcular_ssl_hybrid(df, periodo=20):
    sma_high = df['high'].rolling(window=periodo).mean()
    sma_low  = df['low'].rolling(window=periodo).mean()
    close_arr  = df['close'].values
    sma_h_arr  = sma_high.values
    sma_l_arr  = sma_low.values
    ssl_dir    = np.ones(len(df), dtype=int)
    current    = 1
    for i in range(len(df)):
        if np.isnan(sma_h_arr[i]) or np.isnan(sma_l_arr[i]):
            ssl_dir[i] = current
            continue
        if   close_arr[i] > sma_h_arr[i]: current = 1
        elif close_arr[i] < sma_l_arr[i]: current = -1
        ssl_dir[i] = current
    df['ssl_dir']      = ssl_dir
    df['SSL_Baseline'] = np.where(df['ssl_dir'] == 1, sma_high, sma_low)
    return df

def calcular_atr_stop(df, periodo=14, multiplicador=3.0):
    high, low, close = df['high'], df['low'], df['close']
    tr  = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low  - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    atr = tr.ewm(span=periodo, adjust=False).mean()
    atr_stop  = np.zeros(len(df))
    tendencia = np.zeros(len(df), dtype=int)
    close_arr = close.values
    atr_arr   = atr.values
    for i in range(1, len(df)):
        if i == 1:
            atr_stop[i]  = close_arr[i] - (atr_arr[i] * multiplicador)
            tendencia[i] = 1
            continue
        if tendencia[i-1] == 1:
            if close_arr[i] < atr_stop[i-1]:
                tendencia[i] = -1
                atr_stop[i]  = close_arr[i] + (atr_arr[i] * multiplicador)
            else:
                tendencia[i] = 1
                atr_stop[i]  = max(atr_stop[i-1], close_arr[i] - (atr_arr[i] * multiplicador))
        else:
            if close_arr[i] > atr_stop[i-1]:
                tendencia[i] = 1
                atr_stop[i]  = close_arr[i] - (atr_arr[i] * multiplicador)
            else:
                tendencia[i] = -1
                atr_stop[i]  = min(atr_stop[i-1], close_arr[i] + (atr_arr[i] * multiplicador))
    df['ATR_Stop'] = atr_stop
    df['atr_dir']  = tendencia
    return df

def calcular_alpha_trend(df, periodo=14, coeff=1.0):
    high, low, close = df['high'], df['low'], df['close']
    tr  = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low  - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    atr    = tr.rolling(window=periodo).mean()
    up_t   = low  - coeff * atr
    down_t = high + coeff * atr
    mfi    = df['MFI'].values
    alpha_trend = np.zeros(len(df))
    for i in range(len(df)):
        if i < periodo:
            alpha_trend[i] = close.iloc[i]
            continue
        if mfi[i] >= 50:
            alpha_trend[i] = max(up_t.iloc[i], alpha_trend[i-1])
        else:
            alpha_trend[i] = min(down_t.iloc[i], alpha_trend[i-1])
    df['AT_K1'] = alpha_trend
    return df

def mapear_estrutura_smc(df):
    fechamentos = df['close'].values
    maximas     = df['high'].values
    minimas     = df['low'].values
    bos_detectado   = 0
    choch_detectado = 0
    fvg_pendente    = 0
    for i in range(len(df) - 3, len(df) - 1):
        if minimas[i+1] > maximas[i-1]:
            fvg_pendente = 1
        elif maximas[i+1] < minimas[i-1]:
            fvg_pendente = -1
    topo_local  = np.max(fechamentos[-15:-2])
    fundo_local = np.min(fechamentos[-15:-2])
    if   fechamentos[-1] > topo_local:  bos_detectado  = 1
    elif fechamentos[-1] < fundo_local: bos_detectado  = -1
    if   fechamentos[-1] > topo_local  and fechamentos[-2] <= topo_local:  choch_detectado = 1
    elif fechamentos[-1] < fundo_local and fechamentos[-2] >= fundo_local: choch_detectado = -1
    df['SMC_BOS']   = bos_detectado
    df['SMC_CHOCH'] = choch_detectado
    df['SMC_FVG']   = fvg_pendente
    return df

def calcular_retracao_fibonacci(df):
    maxima = df['high'].max()
    minima = df['low'].min()
    diff   = maxima - minima
    return {
        'fib_0':   maxima,
        'fib_236': maxima - 0.236 * diff,
        'fib_382': maxima - 0.382 * diff,
        'fib_500': maxima - 0.500 * diff,
        'fib_618': maxima - 0.618 * diff,
        'fib_786': maxima - 0.786 * diff,
        'fib_100': minima
    }

# ─────────────────────────────────────────────────────────────
# CARREGAMENTO DE DADOS
# ─────────────────────────────────────────────────────────────

def carregar_dados_bricsvault_smc(simbolo_id, timeframe_selecionado):
    try:
        velas = gateio_client.fetch_ohlcv(simbolo_id, timeframe=timeframe_selecionado, limit=200)
        if not velas:
            return None
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['RSI_14'] = calcular_rsi(df, 'close', 14)
        df = calcular_stoch_rsi(df)
        macd, sinal, hist = calcular_macd(df, 'close')
        df['MACD'], df['MACD_SIGNAL'], df['MACD_HIST'] = macd, sinal, hist
        df['MFI'] = calcular_mfi(df)
        df = calcular_ssl_hybrid(df)
        df = calcular_atr_stop(df)
        df = calcular_alpha_trend(df)
        df = calcular_chaikin_money_flow(df)
        df = calcular_wavetrend_oscillator(df)
        df = mapear_estrutura_smc(df)
        return df.dropna(subset=['close', 'SSL_Baseline'])
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

def obter_variacao_24h_precisa(simbolo_id):
    try:
        dados_24h = gateio_client.fetch_ohlcv(simbolo_id, timeframe='1d', limit=2)
        if dados_24h and len(dados_24h) >= 2:
            close_hoje  = dados_24h[-1][4]
            close_ontem = dados_24h[-2][4]
            return ((close_hoje - close_ontem) / close_ontem) * 100
    except Exception:
        pass
    return 0.0

# ─────────────────────────────────────────────────────────────
# CONFLUÊNCIA SMC
# ─────────────────────────────────────────────────────────────

def analisar_confluencia_smc_total(df, fib_niveis):
    u = df.iloc[-1]
    preco_atual  = u['close']
    pontos_alta  = 0.0
    pontos_baixa = 0.0
    if u['SMC_CHOCH'] == 1  or u['SMC_BOS'] == 1:  pontos_alta  += 3
    if u['SMC_CHOCH'] == -1 or u['SMC_BOS'] == -1: pontos_baixa += 3
    if u['SMC_FVG'] == 1:  pontos_alta  += 1
    if u['SMC_FVG'] == -1: pontos_baixa += 1
    if preco_atual <= fib_niveis['fib_618']:
        pontos_alta  += 2.0
        contexto_fib  = txt["ctx_desconto"]
    elif preco_atual >= fib_niveis['fib_382']:
        pontos_baixa += 2.0
        contexto_fib  = txt["ctx_premium"]
    else:
        contexto_fib  = txt["ctx_neutro"]
    if u['CMF'] > 0:        pontos_alta  += 1.5
    else:                   pontos_baixa += 1.5
    if u['WT1'] > u['WT2']: pontos_alta  += 1
    else:                   pontos_baixa += 1
    if u['MACD_HIST'] > 0:  pontos_alta  += 1
    else:                   pontos_baixa += 1
    if pontos_alta >= 7.5:
        return txt["compra_forte"], "#00cc66", f"{contexto_fib} SMC Order Flow Bullish Structure.", pontos_alta, pontos_baixa
    elif pontos_baixa >= 7.5:
        return txt["venda_forte"], "#ff3333", f"{contexto_fib} SMC Order Flow Bearish Structure.", pontos_alta, pontos_baixa
    else:
        return txt["neutro"], "#ffcc00", contexto_fib, pontos_alta, pontos_baixa

# ─────────────────────────────────────────────────────────────
# GRÁFICO PRINCIPAL
# ─────────────────────────────────────────────────────────────

def construir_grafico(df, fib_niveis, simbolo_id):
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        row_heights=[0.50, 0.17, 0.17, 0.16],
        vertical_spacing=0.03,
        subplot_titles=(
            f"{simbolo_id} — Candlestick + ATR Stop + SSL Hybrid",
            "MACD",
            "RSI / Stoch RSI",
            "CMF / WaveTrend"
        )
    )
    fig.add_trace(go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name="OHLC", increasing_line_color='#00cc66',
        decreasing_line_color='#ff3333'
    ), row=1, col=1)
    atr_colors = df['atr_dir'].apply(lambda d: '#00cc66' if d == 1 else '#ff3333')
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['ATR_Stop'], mode='markers',
        marker=dict(color=atr_colors, size=3), name="ATR Stop"
    ), row=1, col=1)
    ssl_colors = df['ssl_dir'].apply(lambda d: '#00aaff' if d == 1 else '#ff6600')
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['SSL_Baseline'], mode='lines',
        line=dict(width=1.5), marker=dict(color=ssl_colors), name="SSL Hybrid"
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['AT_K1'], mode='lines',
        line=dict(color='#aa44ff', width=1, dash='dot'), name="Alpha Trend"
    ), row=1, col=1)
    fib_cores = {
        'fib_0':   ('#ff4444', '0.0%'),  'fib_236': ('#ffaa00', '23.6%'),
        'fib_382': ('#ffdd00', '38.2%'), 'fib_500': ('#aaaaaa', '50.0%'),
        'fib_618': ('#00cc66', '61.8%'), 'fib_786': ('#00aaff', '78.6%'),
        'fib_100': ('#4444ff', '100%')
    }
    for chave, (cor, label) in fib_cores.items():
        fig.add_hline(
            y=fib_niveis[chave], line_dash="dot", line_color=cor,
            line_width=1, annotation_text=label,
            annotation_position="right", row=1, col=1
        )
    hist_colors = df['MACD_HIST'].apply(lambda v: '#00cc66' if v >= 0 else '#ff3333')
    fig.add_trace(go.Bar(x=df['time'], y=df['MACD_HIST'], marker_color=hist_colors, name="MACD Hist"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['MACD'], line=dict(color='#00aaff', width=1), name="MACD"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['MACD_SIGNAL'], line=dict(color='#ff6600', width=1), name="Signal"), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['RSI_14'], line=dict(color='#ffdd00', width=1.5), name="RSI 14"), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['StochRSI_K'], line=dict(color='#00cc66', width=1), name="Stoch K"), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['StochRSI_D'], line=dict(color='#ff4444', width=1), name="Stoch D"), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red",   line_width=0.8, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", line_width=0.8, row=3, col=1)
    cmf_colors = df['CMF'].apply(lambda v: '#00cc66' if v >= 0 else '#ff3333')
    fig.add_trace(go.Bar(x=df['time'], y=df['CMF'], marker_color=cmf_colors, name="CMF"), row=4, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['WT1'], line=dict(color='#00aaff', width=1), name="WT1"), row=4, col=1)
    fig.add_trace(go.Scatter(x=df['time'], y=df['WT2'], line=dict(color='#ffaa00', width=1), name="WT2"), row=4, col=1)
    fig.update_layout(
        height=800, paper_bgcolor='#0e1117', plot_bgcolor='#0e1117',
        font=dict(color='#ffffff', size=11), xaxis_rangeslider_visible=False,
        legend=dict(orientation='h', y=1.02, bgcolor='rgba(0,0,0,0)'),
        margin=dict(l=60, r=80, t=40, b=20)
    )
    fig.update_xaxes(gridcolor='#222', showgrid=True)
    fig.update_yaxes(gridcolor='#222', showgrid=True)
    return fig

# ─────────────────────────────────────────────────────────────
# MATRIZ DE INDICADORES
# ─────────────────────────────────────────────────────────────

def renderizar_matriz(df, txt):
    u = df.iloc[-1]
    st.markdown(f"### {txt['matriz_detalhada']}")

    def badge(condicao_alta, label_alta, label_baixa, valor_str=""):
        if condicao_alta:
            cor, sinal = "#00cc66", txt["alta"]
        else:
            cor, sinal = "#ff3333", txt["baixa"]
        label = label_alta if condicao_alta else label_baixa
        return f"""<span style='background:{cor}22;border:1px solid {cor};border-radius:6px;
            padding:3px 10px;color:{cor};font-size:13px;font-weight:600;'>{sinal}</span>
            &nbsp;<span style='color:#ccc;font-size:12px;'>{label} {valor_str}</span>"""

    def neutro_badge(label):
        return f"""<span style='background:#ffcc0022;border:1px solid #ffcc00;border-radius:6px;
            padding:3px 10px;color:#ffcc00;font-size:13px;font-weight:600;'>{txt['neutro_curto']}</span>
            &nbsp;<span style='color:#ccc;font-size:12px;'>{label}</span>"""

    indicadores = []
    bos = int(u['SMC_BOS'])
    if bos != 0:
        indicadores.append(badge(bos == 1, txt["bos"], txt["bos"]))
    else:
        indicadores.append(neutro_badge(txt["bos"]))
    choch = int(u['SMC_CHOCH'])
    if choch != 0:
        indicadores.append(badge(choch == 1, txt["choch"], txt["choch"]))
    else:
        indicadores.append(neutro_badge(txt["choch"]))
    fvg = int(u['SMC_FVG'])
    if fvg != 0:
        indicadores.append(badge(fvg == 1, txt["fvg"], txt["fvg"]))
    else:
        indicadores.append(neutro_badge(txt["fvg"]))
    indicadores.append(badge(u['ssl_dir'] == 1, txt["ssl"], txt["ssl"]))
    indicadores.append(badge(u['MACD_HIST'] > 0, txt["macd_hist"], txt["macd_hist"], f"({u['MACD_HIST']:+.4f})"))
    indicadores.append(badge(u['CMF'] > 0, txt["cmf"], txt["cmf"], f"({u['CMF']:+.4f})"))
    indicadores.append(badge(u['WT1'] > u['WT2'], txt["wt"], txt["wt"], f"(WT1={u['WT1']:.1f} / WT2={u['WT2']:.1f})"))
    rsi_val = u['RSI_14']
    if rsi_val >= 70:
        indicadores.append(badge(False, txt["rsi"], txt["rsi"], f"({rsi_val:.1f} — Sobrecomprado)"))
    elif rsi_val <= 30:
        indicadores.append(badge(True, txt["rsi"], txt["rsi"], f"({rsi_val:.1f} — Sobrevendido)"))
    else:
        indicadores.append(neutro_badge(f"{txt['rsi']} ({rsi_val:.1f})"))
    indicadores.append(badge(u['StochRSI_K'] > u['StochRSI_D'], txt["stoch_rsi_k"], txt["stoch_rsi_k"], f"(K={u['StochRSI_K']:.1f} / D={u['StochRSI_D']:.1f})"))
    mfi_val = u['MFI']
    indicadores.append(badge(mfi_val >= 50, txt["mfi"], txt["mfi"], f"({mfi_val:.1f})"))
    cols = st.columns(2)
    for i, ind in enumerate(indicadores):
        with cols[i % 2]:
            st.markdown(ind, unsafe_allow_html=True)
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# TABELA FIBONACCI
# ─────────────────────────────────────────────────────────────

def renderizar_fibonacci(df, fib_niveis, txt):
    st.markdown(f"### {txt['fib_niveis_titulo']}")
    preco_atual = df.iloc[-1]['close']
    chaves = ['fib_0', 'fib_236', 'fib_382', 'fib_500', 'fib_618', 'fib_786', 'fib_100']
    fib_df = pd.DataFrame({
        "Nível Fibonacci":    txt["fib_nomes"],
        "Posição de Mercado": txt["fib_posicoes"],
        "Preço (USDT)":       [formatar_preco(fib_niveis[k]) for k in chaves],
        "Δ Preço Atual":      [f"{((fib_niveis[k] - preco_atual) / preco_atual * 100):+.2f}%" for k in chaves],
    })
    distancias = [abs(fib_niveis[k] - preco_atual) for k in chaves]
    idx_mais_proximo = int(np.argmin(distancias))
    def highlight_row(row):
        if row.name == idx_mais_proximo:
            return ['background-color: #ffffff18; font-weight: bold'] * len(row)
        return [''] * len(row)
    st.dataframe(fib_df.style.apply(highlight_row, axis=1), use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────
# INTERFACE PRINCIPAL
# ─────────────────────────────────────────────────────────────

st.title(txt["titulo"])

st.sidebar.header(txt["config_globais"])
lista_criptos = obter_todos_pares_usdt()
simbolo_id    = st.sidebar.selectbox(
    txt["selecione_cripto"],
    lista_criptos,
    index=lista_criptos.index("SOL/USDT") if "SOL/USDT" in lista_criptos else 0
)

# Todos os timeframes reais suportados pela Gate.io (fonte: ccxt gate().timeframes)
# 10s | 1m | 5m | 15m | 30m | 1h | 2h | 4h | 8h | 1d | 7d
# Nota: 12h e 1M (mensal) NÃO são suportados pela Gate.io e foram omitidos intencionalmente.
intervalos = {
    "10s": "10s",
    "1m":  "1m",
    "5m":  "5m",
    "15m": "15m",
    "30m": "30m",
    "1h":  "1h",
    "2h":  "2h",
    "4h":  "4h",
    "8h":  "8h",
    "1d":  "1d",
    "7d":  "7d",
}
timeframe  = st.sidebar.selectbox(txt["tempo_grafico"], list(intervalos.keys()), index=5)
st.sidebar.caption("⚠️ Gate.io não suporta 12h nem 1M (mensal). Todos os intervalos listados são os oficialmente disponíveis na exchange.")

st.sidebar.markdown("---")
modo_vivo         = st.sidebar.toggle(txt["modo_vivo"], value=True)
intervalo_refresh = st.sidebar.slider(txt["intervalo_refresh"], min_value=5, max_value=60, value=15)

status_placeholder = st.empty()

df_dados = carregar_dados_bricsvault_smc(simbolo_id, timeframe)

if df_dados is None or df_dados.empty:
    st.warning(txt["erro_dados"])
else:
    ultimo_reg   = df_dados.iloc[-1]
    preco_atual  = ultimo_reg['close']
    fib_niveis   = calcular_retracao_fibonacci(df_dados)
    variacao_24h = obter_variacao_24h_precisa(simbolo_id)

    recomendacao, cor_sinal, analise_justificada, pontos_alta, pontos_baixa = \
        analisar_confluencia_smc_total(df_dados, fib_niveis)

    st.markdown(f"""
    <div style="background:{cor_sinal}22;padding:20px;border-radius:10px;
                border:2px solid {cor_sinal};margin-bottom:20px;">
        <h2 style="margin:0;color:{cor_sinal};font-size:24px;">{recomendacao}</h2>
        <p style="margin:8px 0 0 0;font-size:15px;color:#ddd;">{analise_justificada}</p>
    </div>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(txt["preco_spot"],    formatar_preco(preco_atual))
    m2.metric(txt["variacao_24h"],  f"{variacao_24h:+.2f}%")
    m3.metric(txt["stop_atr"],      formatar_preco(ultimo_reg['ATR_Stop']))
    m4.metric(txt["pontos_compra"], f"{pontos_alta:.1f}")
    m5.metric(txt["pontos_venda"],  f"{pontos_baixa:.1f}")

    st.markdown("---")
    st.markdown(f"### {txt['grafico_titulo']}")
    fig = construir_grafico(df_dados, fib_niveis, simbolo_id)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    col_fib, col_mat = st.columns([1, 1])
    with col_fib:
        renderizar_fibonacci(df_dados, fib_niveis, txt)
    with col_mat:
        renderizar_matriz(df_dados, txt)

    st.markdown("---")
    hora_atual = pd.Timestamp.now().strftime("%H:%M:%S")
    if modo_vivo:
        status_placeholder.info(
            f"🟢 {txt['ultima_atualizacao']}: {hora_atual}  |  "
            f"{txt['proximo_refresh']} {intervalo_refresh} {txt['segundos']}"
        )
        time.sleep(intervalo_refresh)
        st.rerun()
    else:
        status_placeholder.info(f"⏸ {txt['ultima_atualizacao']}: {hora_atual}")
