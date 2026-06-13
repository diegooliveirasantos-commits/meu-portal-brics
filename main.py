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

# Inicialização segura do cliente Gate.io via CCXT
@st.cache_resource
def inicializar_exchange():
    return ccxt.gate({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })

gateio_client = inicializar_exchange()

# Carregamento dinâmico de TODOS os pares USDT disponíveis na exchange
@st.cache_data(ttl=3600)
def obter_todos_pares_usdt():
    try:
        mercados = gateio_client.load_markets()
        pares_usdt = [simbolo for simbolo in mercados.keys() if simbolo.endswith('/USDT')]
        return sorted(pares_usdt)
    except Exception:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]

# --- MATRIZ DE INDICADORES MATEMÁTICOS TRADICIONAIS E FLUXO ---
def calcular_rsi(df, col, periodo=14):
    delta = df[col].diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    ma_ganho = ganho.ewm(span=periodo, adjust=False).mean()
    ma_perda = perda.ewm(span=periodo, adjust=False).mean()
    rs = ma_ganho / ma_perda.replace(0, 0.00001)
    return 100 - (100 / (1 + rs))

def calcular_stoch_rsi(df, periodo=14, k_period=3, d_period=3):
    rsi = df['RSI_14']
    min_rsi = rsi.rolling(window=periodo).min()
    max_rsi = rsi.rolling(window=periodo).max()
    stoch_rsi = (rsi - min_rsi) / (max_rsi - min_rsi).replace(0, 0.00001)
    df['StochRSI_K'] = stoch_rsi.rolling(window=k_period).mean() * 100
    df['StochRSI_D'] = df['StochRSI_K'].rolling(window=d_period).mean()
    return df

def calcular_macd(df, col):
    ema_rapida = df[col].ewm(span=12, adjust=False).mean()
    ema_lenta = df[col].ewm(span=26, adjust=False).mean()
    macd = ema_rapida - ema_lenta
    sinal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - sinal
    return macd, sinal, hist

def calcular_chaikin_money_flow(df, periodo=20):
    mfv = (((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low']).replace(0, 0.00001)) * df['volume']
    df['CMF'] = mfv.rolling(window=periodo).sum() / df['volume'].rolling(window=periodo).sum().replace(0, 0.00001)
    return df

def calcular_wavetrend_oscillator(df, n1=10, n2=21):
    ap = (df['high'] + df['low'] + df['close']) / 3
    esa = ap.ewm(span=n1, adjust=False).mean()
    d = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
    ci = (ap - esa) / (0.015 * d).replace(0, 0.00001)
    df['WT1'] = ci.ewm(span=n2, adjust=False).mean()
    df['WT2'] = df['WT1'].rolling(window=4).mean().bfill()
    return df

def calcular_mfi(df, periodo=14):
    tp = (df['high'] + df['low'] + df['close']) / 3
    rmf = tp * df['volume']
    pos_flow = pd.Series(0.0, index=df.index)
    neg_flow = pd.Series(0.0, index=df.index)
    for i in range(1, len(df)):
        if tp.iloc[i] > tp.iloc[i-1]: pos_flow.iloc[i] = rmf.iloc[i]
        elif tp.iloc[i] < tp.iloc[i-1]: neg_flow.iloc[i] = rmf.iloc[i]
    pos_mf = pos_flow.rolling(window=periodo).sum()
    neg_mf = neg_flow.rolling(window=periodo).sum()
    return 100 - (100 / (1 + (pos_mf / neg_mf.replace(0, 0.00001))))

def calcular_ssl_hybrid(df, periodo=20):
    sma_high = df['high'].rolling(window=periodo).mean()
    sma_low = df['low'].rolling(window=periodo).mean()
    ssl_direction, current_dir = [], 1
    for idx in range(len(df)):
        close = df['close'].iloc[idx]
        h, l = sma_high.iloc[idx], sma_low.iloc[idx]
        if pd.isna(h) or pd.isna(l):
            ssl_direction.append(current_dir); continue
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
        if i == 1:
            atr_stop[i] = close.iloc[i] - (atr.iloc[i] * multiplicador); tendencia[i] = 1; continue
        if tendencia[i-1] == 1:
            if close.iloc[i] < atr_stop[i-1]:
                tendencia[i] = -1; atr_stop[i] = close.iloc[i] + (atr.iloc[i] * multiplicador)
            else:
                tendencia[i] = 1; atr_stop[i] = max(atr_stop[i-1], close.iloc[i] - (atr.iloc[i] * multiplicador))
        else:
            if close.iloc[i] > atr_stop[i-1]:
                tendencia[i] = 1; atr_stop[i] = close.iloc[i] - (atr.iloc[i] * multiplicador)
            else:
                tendencia[i] = -1; atr_stop[i] = min(atr_stop[i-1], close.iloc[i] + (atr.iloc[i] * multiplicador))
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
    df['AT_K2'] = df['AT_K1'].shift(2).bfill()
    return df

# --- ALGORITMO GEOMÉTRICO SMC REAL ---
def mapear_estrutura_smc(df):
    fechamentos = df['close'].values
    maximas = df['high'].values
    minimas = df['low'].values
    
    bos_detectado = 0  
    choch_detectado = 0 
    fvg_pendente = 0   
    
    for i in range(len(df) - 3, len(df) - 1):
        if minimas[i+1] > maximas[i-1]:
            fvg_pendente = 1
        elif maximas[i+1] < minimas[i-1]:
            fvg_pendente = -1

    ultimos_fechamentos = fechamentos[-15:]
    topo_local = np.max(ultimos_fechamentos[:-2])
    fundo_local = np.min(ultimos_fechamentos[:-2])
    
    preco_atual = fechamentos[-1]
    preco_anterior = fechamentos[-2]
    
    if preco_atual > topo_local:
        bos_detectado = 1
    elif preco_atual < fundo_local:
        bos_detectado = -1
        
    if preco_atual > topo_local and preco_anterior <= topo_local:
        choch_detectado = 1
    elif preco_atual < fundo_local and preco_anterior >= fundo_local:
        choch_detectado = -1
        
    df['SMC_BOS'] = bos_detectado
    df['SMC_CHOCH'] = choch_detectado
    df['SMC_FVG'] = fvg_pendente
    return df

# --- MOTOR DE DECISÃO INTEGRADA (SMC + FIBONACCI + OSCILADORES) ---
def analisar_confluencia_smc_total(df, fib_niveis):
    u = df.iloc[-1]
    preco_atual = u['close']
    bos = u['SMC_BOS']
    choch = u['SMC_CHOCH']
    fvg = u['SMC_FVG']
    
    cmf_positivo = u['CMF'] > 0
    wt_alta = u['WT1'] > u['WT2']
    rsi_normal = u['RSI_14']
    macd_hist_positivo = u['MACD_HIST'] > 0
    stoch_k = u['StochRSI_K']
    stoch_d = u['StochRSI_D']
    
    pontos_alta = 0
    pontos_baixa = 0
    
    # 🌟 PESOS DA ESTRUTURA INSTITUCIONAL SMC
    if choch == 1 or bos == 1: pontos_alta += 3
    if choch == -1 or bos == -1: pontos_baixa += 3
    if fvg == 1: pontos_alta += 1
    if fvg == -1: pontos_baixa += 1
    
    # 🌟 FILTRO CONCEITUAL DE RETRAÇÃO DE FIBONACCI (ZONAS DE DESCONTO INSTITUCIONAL)
    # Se o preço está abaixo do nível de 61.8%, está em zona barata (Desconto) otimizando a compra.
    # Se o preço está acima do nível de 38.2%, está em zona cara (Premium) otimizando a venda.
    if preco_atual <= fib_niveis['fib_618']:
        pontos_alta += 2.0
        contexto_fib = "Ativo posicionado em Zona de Desconto de Fibonacci (Excelente risco/retorno para Institucionais)."
    elif preco_atual >= fib_niveis['fib_382']:
        pontos_baixa += 2.0
        contexto_fib = "Ativo posicionado em Zona Premium de Fibonacci (Preço esticado, propício para realização)."
    else:
        contexto_fib = "Preço em faixa neutra de equilíbrio de Fibonacci (Fair Value Zone)."

    # OUTROS INDICADORES
    if cmf_positivo: pontos_alta += 1.5
    else: pontos_baixa += 1.5
    if wt_alta: pontos_alta += 1
    else: pontos_baixa += 1
    if macd_hist_positivo: pontos_alta += 1
    else: pontos_baixa += 1
    if rsi_normal < 45 and stoch_k > stoch_d: pontos_alta += 1
    if rsi_normal > 55 and stoch_k < stoch_d: pontos_baixa += 1

    if pontos_alta >= 7.5:
        justificativa = f"Rastreador SMC confirma Quebra Estrutural (BOS/CHoCH). {contexto_fib} Alinhado com entrada de fluxo institucional (CMF)."
        return "🟢 COMPRA FORTE (SMC + FIBONACCI ALINHADOS)", "#00cc66", justificativa
    elif pontos_baixa >= 7.5:
        justificativa = f"Rastreador SMC aponta Distribuição. {contexto_fib} Presença de Bearish FVG ativo e fluxo de capital em declínio."
        return "🔴 VENDA FORTE (SMC + FIBONACCI ALINHADOS)", "#ff3333", justificativa
    else:
        justificativa = f"Estrutura travada em faixa de liquidez (Alta: {pontos_alta} / Baixa: {pontos_baixa}). {contexto_fib}"
        return "🟡 NEUTRO (AGUARDAR SMC)", "#ffcc00", justificativa

# --- CARREGAMENTO INTEGRADO DE DADOS ---
def carregar_dados_bricsvault_smc(simbolo_id, timeframe_selecionado):
    try:
        limite = 350
        timeframe_fetch = timeframe_selecionado
        agrupar_meses = None
        
        if timeframe_selecionado == "3M": timeframe_fetch = "1M"; agrupar_meses = 3
        elif timeframe_selecionado == "6M": timeframe_fetch = "1M"; agrupar_meses = 6
        elif timeframe_selecionado == "1Y": timeframe_fetch = "1M"; agrupar_meses = 12

        velas = gateio_client.fetch_ohlcv(simbolo_id, timeframe=timeframe_fetch, limit=limite)
        if not velas: return None
            
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        if agrupar_meses:
            df.set_index('time', inplace=True)
            df = df.resample(f'{agrupar_meses}ME').agg({
                'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'
            }).dropna().reset_index()
        
        if len(df) < 30: return None
            
        # Cálculos matemáticos puros
        df['RSI_14'] = calcular_rsi(df, 'close', 14)
        df = calcular_stoch_rsi(df)
        macd, sinal, hist = calcular_macd(df, 'close')
        df['MACD'] = macd
        df['MACD_SIGNAL'] = sinal
        df['MACD_HIST'] = hist
        df = calcular_ssl_hybrid(df, periodo=20)
        df = calcular_atr_stop(df, periodo=14, multiplicador=3.0)
        df = calcular_alpha_trend(df, periodo=14, coeff=1.0)
        df = calcular_chaikin_money_flow(df)
        df = calcular_wavetrend_oscillator(df)
        df = mapear_estrutura_smc(df)

        return df.dropna(subset=['close', 'SSL_Baseline', 'AT_K1'])
    except Exception as e:
        st.error(f"Erro técnico na extração dos dados: {e}")
        return None

# --- ENGINE MATEMÁTICO DE RETRAÇÃO DE FIBONACCI ---
def calcular_retracao_fibonacci(df):
    """Calcula matematicamente os níveis de Fibonacci com base no ciclo macro visível"""
    maxima_absoluta = df['high'].max()
    minima_absoluta = df['low'].min()
    diff = maxima_absoluta - minima_absoluta
    
    # Mapeamento padrão de níveis de retração de topo a fundo
    niveis = {
        'fib_0': maxima_absoluta,
        'fib_236': maxima_absoluta - (0.236 * diff),
        'fib_382': maxima_absoluta - (0.382 * diff),
        'fib_500': maxima_absoluta - (0.500 * diff),
        'fib_618': maxima_absoluta - (0.618 * diff),
        'fib_786': maxima_absoluta - (0.786 * diff),
        'fib_100': minima_absoluta
    }
    return niveis

# --- EXTRAÇÃO MATEMÁTICA PURA E INFALÍVEL DE 24 HORAS ---
def obter_variacao_24h_precisa(simbolo_id):
    try:
        dados_24h = gateio_client.fetch_ohlcv(simbolo_id, timeframe='1d', limit=2)
        if dados_24h and len(dados_24h) >= 2:
            preco_abertura_dia = dados_24h[-1][1] 
            preco_atual = dados_24h[-1][4]       
            if preco_abertura_dia > 0:
                variacao_real = ((preco_atual - preco_abertura_dia) / preco_abertura_dia) * 100
                return variacao_real
    except Exception:
        pass
    return None

# --- PORTAL INTERFACE ---
st.title("🏦 BRICSVAULT PORTAL - Smart Money Concepts (SMC) Engine")

st.sidebar.header("⚙️ Configurações Globais")
lista_criptos = obter_todos_pares_usdt()
simbolo_id = st.sidebar.selectbox("Selecione Qualquer Criptomoeda (/USDT):", lista_criptos, index=lista_criptos.index("SOL/USDT") if "SOL/USDT" in lista_criptos else 0)

intervalos = {
    "1 Minuto": "1m", "5 Minutos": "5m", "1 Hora": "1h", "4 Horas": "4h",
    "8 Horas": "8h", "12 Horas": "12h", "1 Dia": "1d", "1 Semana": "1w",
    "1 Mês": "1M", "3 Meses": "3M", "6 Meses": "6M", "1 Ano": "1Y"
}
intervalo_escolhido = st.sidebar.selectbox("Tempo Gráfico:", list(intervalos.keys()))
timeframe = intervalos[intervalo_escolhido]

st.sidebar.markdown("---")
modo_vivo = st.sidebar.toggle("Ativar Monitoramento em Tempo Real", value=True)
intervalo_refresh = st.sidebar.slider("Intervalo de Atualização (Segundos):", min_value=5, max_value=30, value=10)

if "execucao_inicializada" not in st.session_state:
    st.session_state["execucao_inicializada"] = True

if st.session_state["execucao_inicializada"]:
    df_dados = carregar_dados_bricsvault_smc(simbolo_id, timeframe)
        
    if df_dados is not None and not df_dados.empty:
        ultimo_reg = df_dados.iloc[-1]
        preco_atual = ultimo_reg['close']
        
        # Ativação do cálculo de Fibonacci
        fib_niveis = calcular_retracao_fibonacci(df_dados)
        
        # Variação real direta de 24h
        variacao_real_exchange = obter_variacao_24h_precisa(simbolo_id)
        if variacao_real_exchange is None:
            variacao_real_exchange = ((preco_atual - df_dados.iloc[0]['close']) / df_dados.iloc[0]['close']) * 100

        # Análise integrada incluindo a Retração de Fibonacci
        recomendacao, cor_sinal, analise_justificada = analisar_confluencia_smc_total(df_dados, fib_niveis)

        # 🚨 SEÇÃO 1: PAINEL DE TOMADA DE DECISÃO INSTITUCIONAL 🚨
        st.markdown(f"""
        <div style="background-color: {cor_sinal}22; padding: 20px; border-radius: 10px; border: 2px solid {cor_sinal}; margin-bottom: 25px;">
            <h2 style="margin: 0; color: {cor_sinal}; font-size: 26px;">DIRETRIZ DE FLUXO SMC: {recomendacao}</h2>
            <p style="margin: 8px 0 0 0; font-size: 16px; color: #ffffff;"><b>Diagnóstico Estrutural de Mercado:</b> {analise_justificada}</p>
        </div>
        """, unsafe_allow_html=True)

        # SEÇÃO 2: CARDS DE MÉTRICAS REAIS
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Preço Spot Real", f"$ {preco_atual:,.4f}")
        m_col2.metric("Variação 24 Horas (Exchange)", f"{variacao_real_exchange:+.2f}%")
        m_col3.metric("Preço Stop ATR", f"$ {ultimo_reg['ATR_Stop']:,.4f}")

        # SEÇÃO 3: TABELA DE MATRIZ FIBONACCI
        st.markdown("### 📐 Níveis Críticos de Retração de Fibonacci (Ciclo Atual)")
        fib_df = pd.DataFrame({
            "Nível Fibonacci": ["0.0% (MÁXIMA)", "23.6%", "38.2% (Fronteira Premium)", "50.0% (Equilíbrio)", "61.8% (Golden Ratio / Desconto)", "78.6%", "100.0% (MÍNIMA)"],
            "Preço do Alvo": [f"$ {fib_niveis['fib_0']:,.4f}", f"$ {fib_niveis['fib_236']:,.4f}", f"$ {fib_niveis['fib_382']:,.4f}", f"$ {fib_niveis['fib_500']:,.4f}", f"$ {fib_niveis['fib_618']:,.4f}", f"$ {fib_niveis['fib_786']:,.4f}", f"$ {fib_niveis['fib_100']:,.4f}"],
            "Posição Temporal": ["Topo do Ciclo", "Retração Rasa", "Zona Carga Vendedora", "Preço Justo", "Zona Institucional Compra", "Retração Profunda", "Fundo do Ciclo"]
        })
        st.table(fib_df)

        # SEÇÃO 4: MULTI-SUBPLOTS GRÁFICOS AVANÇADOS com Fibonacci em Linha Tracejada Amarela
        fig = make_subplots(
            rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06, 
            subplot_titles=(f'Candlesticks + Fibonacci & Indicadores - {simbolo_id}', 'RSI & Stochastic RSI', 'Fluxo de Dinheiro Permanente (Chaikin Money Flow)'),
            row_width=[0.2, 0.2, 0.6]
        )

        fig.add_trace(go.Candlestick(x=df_dados['time'], open=df_dados['open'], high=df_dados['high'], low=df_dados['low'], close=df_dados['close'], name="Preço"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['SSL_Baseline'], line=dict(color='#00ffff', width=1.5), name="SSL Baseline"), row=1, col=1)
        cor_atr = '#17becf' if ultimo_reg['atr_dir'] == 1 else '#d62728'
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['ATR_Stop'], line=dict(color=cor_atr, width=2, dash='dot'), name="Stop ATR"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['AT_K1'], line=dict(color='#00ffcc', width=2), name="AlphaTrend K1"), row=1, col=1)

        # Plotagem Visual das Linhas Otimizadas de Fibonacci
        cores_fib = {'fib_0': '#aaaaaa', 'fib_236': '#ff4d4d', 'fib_382': '#ff9900', 'fib_500': '#ffffff', 'fib_618': '#00ffcc', 'fib_786': '#00ff55', 'fib_100': '#aaaaaa'}
        for chave, nome_linha in [('fib_0', 'Fib 0%'), ('fib_236', 'Fib 23.6%'), ('fib_382', 'Fib 38.2%'), ('fib_500', 'Fib 50.0%'), ('fib_618', 'Fib 61.8%'), ('fib_786', 'Fib 78.6%'), ('fib_100', 'Fib 100%')]:
            fig.add_trace(go.Scatter(
                x=[df_dados['time'].iloc[0], df_dados['time'].iloc[-1]], 
                y=[fib_niveis[chave], fib_niveis[chave]], 
                mode="lines", 
                line=dict(color=cores_fib[chave], width=1, dash='dash'), 
                name=nome_linha
            ), row=1, col=1)

        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['RSI_14'], line=dict(color='purple', width=2), name="RSI 14"), row=2, col=1)
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['StochRSI_K'], line=dict(color='#ffaa00', width=1, dash='dash'), name="Stoch K"), row=2, col=1)
        fig.add_hline(y=80, line_dash="dot", line_color="red", row=2, col=1)
        fig.add_hline(y=20, line_dash="dot", line_color="green", row=2, col=1)

        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['CMF'], line=dict(color='#00ff55', width=1.5), name="CMF (Fluxo Net)"), row=3, col=1)
        fig.add_hline(y=0, line_dash="solid", line_color="white", row=3, col=1)

        fig.update_layout(height=850, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=40, r=40, t=40, b=40))
        st.plotly_chart(fig, width='stretch')

        # --- SEÇÃO 5: LEGENDAS DINÂMICAS EXCLUSIVAS ---
        st.markdown("---")
        st.markdown("### 📘 Legendas e Notas Conceituais de Mercado")
        
        st.info("""
        **🏦 PREÇO SPOT REAL** Refere-se ao preço de liquidação imediata do ativo no mercado à vista (Spot) no exato milissegundo da última consulta. É o valor de troca corrente do par contra o dólar tether (USDT), livre de projeções de derivativos, ágios ou taxas futuras.
        """)

        if modo_vivo:
            time.sleep(intervalo_refresh)
            st.rerun()
    else:
        st.error("Dados históricos insuficientes nesta Exchange para calcular a confluência estrutural SMC. Escolha outro Ativo ou reduza o Tempo Gráfico.")
