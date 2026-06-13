import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import time

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="BRICSVAULT PORTAL ULTRA",
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

# --- FONTE DE DADOS EM PERCENTUAIS COM CACHE DE SEGURANÇA ANTIBAN ---
def obter_variacao_coingecko_segura(simbolo_id):
    agora = time.time()
    chave_cache_tempo = f"tempo_{simbolo_id}"
    chave_cache_valor = f"valor_{simbolo_id}"
    
    if chave_cache_tempo in st.session_state and (agora - st.session_state[chave_cache_tempo] < 300):
        return st.session_state[chave_cache_valor], "Variação 24h (CoinGecko - Cached)"
        
    try:
        moeda = simbolo_id.split('/')[0].lower()
        mapeamento = {"btc": "bitcoin", "eth": "ethereum", "sol": "solana", "xrp": "ripple", "bnb": "binancecoin"}
        coin_id = mapeamento.get(moeda, moeda)
        
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
        resposta = requests.get(url, timeout=3).json()
        
        if coin_id in resposta and 'usd_24h_change' in resposta[coin_id]:
            valor = resposta[coin_id]['usd_24h_change']
            st.session_state[chave_cache_tempo] = agora
            st.session_state[chave_cache_valor] = valor
            return valor, "Variação 24h (CoinGecko Live)"
    except Exception:
        pass
        
    if chave_cache_valor in st.session_state:
        return st.session_state[chave_cache_valor], "Variação 24h (CoinGecko - Fallback Cache)"
    return None, "Variação Histórica (Exchange)"

# --- FUNÇÕES DE CÁLCULO MATEMÁTICO AVANÇADO (TODOS OS INDICADORES) ---
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

def calcular_macd(df, col):
    ema_rapida = df[col].ewm(span=12, adjust=False).mean()
    ema_lenta = df[col].ewm(span=26, adjust=False).mean()
    macd = ema_rapida - ema_lenta
    sinal = macd.ewm(span=9, adjust=False).mean()
    hist = macd - sinal
    return macd, sinal, hist

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

def calcular_chaikin_money_flow(df, periodo=20):
    """Mede o fluxo real de entrada de capital institucional (Volume Ponderado)"""
    mfv = (((df['close'] - df['low']) - (df['high'] - df['close'])) / (df['high'] - df['low']).replace(0, 0.00001)) * df['volume']
    df['CMF'] = mfv.rolling(window=periodo).sum() / df['volume'].rolling(window=periodo).sum().replace(0, 0.00001)
    return df

def calcular_wavetrend_oscillator(df, n1=10, n2=21):
    """Mapeia pontos milimétricos de exaustão e cruzamento de gatilho"""
    ap = (df['high'] + df['low'] + df['close']) / 3
    esa = ap.ewm(span=n1, adjust=False).mean()
    d = (ap - esa).abs().ewm(span=n1, adjust=False).mean()
    ci = (ap - esa) / (0.015 * d).replace(0, 0.00001)
    df['WT1'] = ci.ewm(span=n2, adjust=False).mean()
    df['WT2'] = df['WT1'].rolling(window=4).mean().bfill()
    return df

# --- MOTOR DE INTELIGÊNCIA CONFLUENTE BRICS (DECISÃO ABSOLUTA) ---
def analisar_confluencia_brics_total(df):
    u = df.iloc[-1]
    
    # 1. Filtros de Tendência Macro (Peso Máximo)
    f_alpha = 1 if u['AT_K1'] > u['AT_K2'] else -1
    f_ssl = 1 if u['ssl_dir'] == 1 else -1
    f_atr = 1 if u['atr_dir'] == 1 else -1
    
    # 2. Filtros de Momentum e Exaustão
    f_rsi = 1 if u['RSI_14'] < 50 else -1
    f_stoch = 1 if u['StochRSI_K'] > u['StochRSI_D'] and u['StochRSI_K'] < 80 else (-1 if u['StochRSI_K'] > 80 else 0)
    f_macd = 1 if u['MACD_HIST'] > 0 else -1
    
    # 3. Filtros de Fluxo de Volume e Dinheiro
    f_cmf = 1 if u['CMF'] > 0 else -1
    f_wt = 1 if u['WT1'] > u['WT2'] else -1
    
    # Sistema de Pontuação Ponderada
    score_total = (f_alpha * 2.5) + (f_ssl * 2.0) + (f_atr * 2.0) + (f_rsi * 1.0) + (f_stoch * 1.0) + (f_macd * 1.0) + (f_cmf * 1.5) + (f_wt * 1.5)
    
    # Tomada de Decisão baseada no Comitê Completo de Indicadores
    if score_total >= 5.0:
        return "🟢 COMPRA FORTE", "#00cc66", f"Pontuação de Confluência: {score_total:+.1f}. Estrutura validada por AlphaTrend/SSL, com forte fluxo comprador detectado via Chaikin Money Flow."
    elif score_total <= -5.0:
        return "🔴 VENDA FORTE", "#ff3333", f"Pontuação de Confluência: {score_total:+.1f}. Alinhamento de baixa macro confirmado. Fluxo de saída institucional e cruzamento de baixa no WaveTrend."
    else:
        return "🟡 NEUTRO (AGUARDAR)", "#ffcc00", f"Pontuação de Confluência: {score_total:+.1f}. Mercado fragmentado ou em consolidação. Aguarde o alinhamento de volume e tendência."

# --- CARREGAMENTO INTEGRADO DE DADOS ---
def carregar_dados_bricsvault_completos(simbolo_id, timeframe_selecionado):
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
            
        # Execução sequencial matemática da esteira de indicadores
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

        return df.dropna(subset=['close', 'SSL_Baseline', 'AT_K1'])
    except Exception as e:
        st.error(f"Erro técnico na extração dos dados: {e}")
        return None

# --- PORTAL INTERFACE ---
st.title("🏦 BRICSVAULT PORTAL - Sistema de Confluência Suprema")

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
    df_dados = carregar_dados_bricsvault_completos(simbolo_id, timeframe)
        
    if df_dados is not None and not df_dados.empty:
        ultimo_reg = df_dados.iloc[-1]
        preco_atual = ultimo_reg['close']
        
        variacao_cg, fonte_rotulo = obter_variacao_coingecko_segura(simbolo_id)
        if variacao_cg is None:
            variacao_cg = ((preco_atual - df_dados.iloc[0]['close']) / df_dados.iloc[0]['close']) * 100

        # Análise Ponderada de TODOS os indicadores unificados
        recomendacao, cor_sinal, analise_justificada = analisar_confluencia_brics_total(df_dados)

        # 🚨 SEÇÃO 1: PAINEL DE TOMADA DE DECISÃO SUPREMA 🚨
        st.markdown(f"""
        <div style="background-color: {cor_sinal}22; padding: 20px; border-radius: 10px; border: 2px solid {cor_sinal}; margin-bottom: 25px;">
            <h2 style="margin: 0; color: {cor_sinal}; font-size: 26px;">AÇÃO RECOMENDADA: {recomendacao}</h2>
            <p style="margin: 8px 0 0 0; font-size: 16px; color: #ffffff;"><b>Análise de Consenso Técnico:</b> {analise_justificada}</p>
        </div>
        """, unsafe_allow_html=True)

        # SEÇÃO 2: CARDS DE MÉTRICAS RÁPIDAS
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Preço Spot Real", f"$ {preco_atual:,.4f}")
        m_col2.metric(fonte_rotulo, f"{variacao_cg:+.2f}%")
        m_col3.metric("Fluxo de Capital (CMF)", f"{ultimo_reg['CMF']:+.4f}")

        # SEÇÃO 3: PAINEL COMPACTO DE TABELAS (RSI + STOCH RSI + MACD)
        st.markdown("### 📊 Matriz de Osciladores e Momentum")
        t_col1, t_col2 = st.columns(2)
        
        with t_col1:
            st.markdown("**Métricas Tradicionais (RSI & MACD)**")
            df_tabela_1 = pd.DataFrame({
                "Indicador": ["RSI (14)", "MACD Linha", "Histograma MACD"],
                "Valor Atual": [f"{ultimo_reg['RSI_14']:.2f}", f"{ultimo_reg['MACD']:.4f}", f"{ultimo_reg['MACD_HIST']:.4f}"],
                "Condição": ["Zona Neutra" if 30<=ultimo_reg['RSI_14']<=70 else ("Sobrecomprado" if ultimo_reg['RSI_14']>70 else "Sobrevendido"),
                             "Tendência de Alta" if ultimo_reg['MACD']>0 else "Tendência de Baixa",
                             "Pressão Compradora" if ultimo_reg['MACD_HIST']>0 else "Pressão Vendedora"]
            })
            st.table(df_tabela_1)
            
        with t_col2:
            st.markdown("**Métricas Derivadas (Stochastic RSI & WaveTrend)**")
            df_tabela_2 = pd.DataFrame({
                "Indicador": ["StochRSI K", "StochRSI D", "WaveTrend WT1"],
                "Valor Atual": [f"{ultimo_reg['StochRSI_K']:.2f}", f"{ultimo_reg['StochRSI_D']:.2f}", f"{ultimo_reg['WT1']:.2f}"],
                "Sinal Técnico": ["Cruzamento Altista" if ultimo_reg['StochRSI_K']>ultimo_reg['StochRSI_D'] else "Cruzamento Baixista",
                                  "Momento de Expansão" if ultimo_reg['StochRSI_D']<80 else "Exaustão Compradora",
                                  "Gatilho Comprador" if ultimo_reg['WT1']>ultimo_reg['WT2'] else "Gatilho Vendedor"]
            })
            st.table(df_tabela_2)

        # SEÇÃO 4: MULTI-SUBPLOTS GRÁFICOS AVANÇADOS
        fig = make_subplots(
            rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06, 
            subplot_titles=(f'Candlesticks + Tendências Combinadas (AlphaTrend/SSL/Stop ATR) - {simbolo_id}', 'Momentum (RSI & Stochastic RSI)', 'Fluxo de Volume (Chaikin Money Flow)'),
            row_width=[0.2, 0.2, 0.6]
        )

        # Gráfico Principal
        fig.add_trace(go.Candlestick(x=df_dados['time'], open=df_dados['open'], high=df_dados['high'], low=df_dados['low'], close=df_dados['close'], name="Preço"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['SSL_Baseline'], line=dict(color='#00ffff', width=1.5), name="SSL Baseline"), row=1, col=1)
        cor_atr = '#17becf' if ultimo_reg['atr_dir'] == 1 else '#d62728'
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['ATR_Stop'], line=dict(color=cor_atr, width=2, dash='dot'), name="Stop ATR"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['AT_K1'], line=dict(color='#00ffcc', width=2), name="AlphaTrend K1"), row=1, col=1)

        # Gráfico de Osciladores
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['RSI_14'], line=dict(color='purple', width=2), name="RSI 14"), row=2, col=1)
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['StochRSI_K'], line=dict(color='#ffaa00', width=1, dash='dash'), name="Stoch K"), row=2, col=1)
        fig.add_hline(y=80, line_dash="dot", line_color="red", row=2, col=1)
        fig.add_hline(y=20, line_dash="dot", line_color="green", row=2, col=1)

        # Gráfico de Volume Ponderado (CMF)
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['CMF'], line=dict(color='#00ff55', width=1.5), name="CMF Flow"), row=3, col=1)
        fig.add_hline(y=0, line_dash="solid", line_color="white", row=3, col=1)

        fig.update_layout(height=800, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=40, r=40, t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)

        # --- SEÇÃO 5: LEGENDAS DINÂMICAS PROTEGIDAS NO RODAPÉ ---
        st.markdown("---")
        st.markdown("### 📘 Legendas e Notas Conceituais de Mercado")
        
        # Detecção de integridade do Volume Histórico
        volume_disponivel = bool(df_dados['volume'].sum() > 0)
        
        if volume_disponivel:
            col_leg1, col_leg2 = st.columns(2)
            with col_leg1:
                st.info("""
                **🏦 PREÇO SPOT REAL** Refere-se ao preço de liquidação imediata do ativo no mercado à vista (Spot) no exato milissegundo da última consulta. É o valor de troca corrente do par contra o dólar tether (USDT), livre de projeções de derivativos, ágios ou taxas futuras.
                """)
            with col_leg2:
                st.info("""
                **📊 VOLUME HISTÓRICO** Representa o somatório total de unidades da criptomoeda que foram efetivamente negociadas (compradas e vendidas) ao longo do período temporal selecionado. É a métrica definitiva para validar a liquidez e a relevância institucional por trás de um movimento de preço.
                """)
        else:
            # Caso a moeda não possua ou não permita extração de volume, exibe apenas o Spot
            st.info("""
            **🏦 PREÇO SPOT REAL** Refere-se ao preço de liquidação imediata do ativo no mercado à vista (Spot) no exato milissegundo da última consulta. É o valor de troca corrente do par contra o dólar tether (USDT), livre de projeções de derivativos, ágios ou taxas futuras.
            """)

        if modo_vivo:
            time.sleep(intervalo_refresh)
            st.rerun()
    else:
        st.error("Dados históricos insuficientes nesta Exchange para calcular a confluência completa. Escolha outro Ativo ou reduza o Tempo Gráfico.")
