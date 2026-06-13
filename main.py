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
    page_title="BRICSVAULT PORTAL PRO",
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
    """Busca a variação de 24h no CoinGecko usando Cache Estruturado para evitar Rate Limits"""
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

# --- FUNÇÕES DE CÁLCULO MATEMÁTICO NATIVO PRO ---
def calcular_rsi(df, col, periodo=14):
    delta = df[col].diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    ma_ganho = ganho.ewm(span=periodo, adjust=False).mean()
    ma_perda = perda.ewm(span=periodo, adjust=False).mean()
    rs = ma_ganho / ma_perda.replace(0, 0.00001)
    return 100 - (100 / (1 + rs))

def calcular_mfi(df, periodo=14):
    tp = (df['high'] + df['low'] + df['close']) / 3
    rmf = tp * df['volume']
    
    pos_flow = pd.Series(0.0, index=df.index)
    neg_flow = pd.Series(0.0, index=df.index)
    
    for i in range(1, len(df)):
        if tp.iloc[i] > tp.iloc[i-1]:
            pos_flow.iloc[i] = rmf.iloc[i]
        elif tp.iloc[i] < tp.iloc[i-1]:
            neg_flow.iloc[i] = rmf.iloc[i]
            
    pos_mf = pos_flow.rolling(window=periodo).sum()
    neg_mf = neg_flow.rolling(window=periodo).sum()
    
    mfi = 100 - (100 / (1 + (pos_mf / neg_mf.replace(0, 0.00001))))
    return mfi

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
    
    ssl_direction = []
    current_dir = 1
    
    for idx in range(len(df)):
        close = df['close'].iloc[idx]
        h = sma_high.iloc[idx]
        l = sma_low.iloc[idx]
        
        if pd.isna(h) or pd.isna(l):
            ssl_direction.append(current_dir)
            continue
            
        if close > h:
            current_dir = 1
        elif close < l:
            current_dir = -1
        ssl_direction.append(current_dir)
        
    df['ssl_dir'] = ssl_direction
    df['SSL_High'] = sma_high
    df['SSL_Low'] = sma_low
    df['SSL_Baseline'] = df.apply(lambda row: row['SSL_High'] if row['ssl_dir'] == 1 else row['SSL_Low'], axis=1)
    return df

def calcular_atr_stop(df, periodo=14, multiplicador=3.0):
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.ewm(span=periodo, adjust=False).mean()
    
    atr_stop = np.zeros(len(df))
    tendencia = np.zeros(len(df))
    
    for i in range(1, len(df)):
        preco_fechamento = close.iloc[i]
        atr_atual = atr.iloc[i]
        
        if i == 1:
            atr_stop[i] = preco_fechamento - (atr_atual * multiplicador)
            tendencia[i] = 1
            continue
            
        stop_anterior = atr_stop[i-1]
        tendencia_anterior = tendencia[i-1]
        
        if tendencia_anterior == 1:
            if preco_fechamento < stop_anterior:
                tendencia[i] = -1
                atr_stop[i] = preco_fechamento + (atr_atual * multiplicador)
            else:
                tendencia[i] = 1
                atr_stop[i] = max(stop_anterior, preco_fechamento - (atr_atual * multiplicador))
        else:
            if preco_fechamento > stop_anterior:
                tendencia[i] = 1
                atr_stop[i] = preco_fechamento - (atr_atual * multiplicador)
            else:
                tendencia[i] = -1
                atr_stop[i] = min(stop_anterior, preco_fechamento + (atr_atual * multiplicador))
                
    df['ATR_Stop'] = atr_stop
    df['atr_dir'] = tendencia
    return df

def calcular_alpha_trend(df, periodo=14, coeff=1.0):
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.rolling(window=periodo).mean()
    df['MFI'] = calcular_mfi(df, periodo)
    
    up_t = low - coeff * atr
    down_t = high + coeff * atr
    
    alpha_trend = np.zeros(len(df))
    
    for i in range(len(df)):
        if i < periodo:
            alpha_trend[i] = close.iloc[i]
            continue
            
        mfi_atual = df['MFI'].iloc[i]
        
        if mfi_atual >= 50:
            alpha_trend[i] = max(up_t.iloc[i], alpha_trend[i-1])
        else:
            alpha_trend[i] = min(down_t.iloc[i], alpha_trend[i-1])
                
    df['AT_K1'] = alpha_trend
    # Correção de segurança para compatibilidade estrita com Pandas 3.0+
    df['AT_K2'] = df['AT_K1'].shift(2).bfill()
    return df

# --- SISTEMA DE SINALIZAÇÃO CONFLUENTE BRICS ---
def calcular_sinal_BRICS(df):
    ultimo = df.iloc[-1]
    rsi = ultimo['RSI_14']
    ssl_dir = ultimo['ssl_dir']
    atr_dir = ultimo['atr_dir']
    k1 = ultimo['AT_K1']
    k2 = ultimo['AT_K2']
    
    ponto_compra = 0
    ponto_venda = 0
    
    if ssl_dir == 1: ponto_compra += 1
    else: ponto_venda += 1
        
    if atr_dir == 1: ponto_compra += 1
    else: ponto_venda += 1
        
    if k1 > k2: ponto_compra += 1
    else: ponto_venda += 1
    
    if rsi < 45: ponto_compra += 1
    elif rsi > 55: ponto_venda += 1
    
    if ponto_compra >= 3:
        return "🟢 COMPRA FORTE", "#00cc66", "Confluência Ativa: Alinhamento Positivo entre SSL Hybrid, Stop ATR e AlphaTrend."
    elif ponto_venda >= 3:
        return "🔴 VENDA FORTE", "#ff3333", "Aviso de Baixa: Rompimento estrutural sincronizado no canal AlphaTrend e Stop ATR."
    else:
        return "🟡 NEUTRO", "#ffcc00", "Indicadores Divergentes: AlphaTrend e SSL Hybrid sem consenso direcional estável."

# --- CARREGAMENTO E SINCRO DE DADOS GRÁFICOS ---
def carregar_dados_bricsvault(simbolo_id, timeframe_selecionado):
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
            
        df['RSI_14'] = calcular_rsi(df, 'close', 14)
        macd, sinal, hist = calcular_macd(df, 'close')
        df['MACD_HIST'] = hist
        
        df = calcular_ssl_hybrid(df, periodo=20)
        df = calcular_atr_stop(df, periodo=14, multiplicador=3.0)
        df = calcular_alpha_trend(df, periodo=14, coeff=1.0)

        return df.dropna(subset=['close', 'SSL_Baseline', 'AT_K1'])
    except Exception as e:
        st.error(f"Erro na extração de dados: {e}")
        return None

# --- PORTAL INTERFACE ---
st.title("🏦 BRICSVAULT PORTAL - Inteligência Avançada Certificada")

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
    df_dados = carregar_dados_bricsvault(simbolo_id, timeframe)
        
    if df_dados is not None and not df_dados.empty:
        ultimo_reg = df_dados.iloc[-1]
        preco_atual = ultimo_reg['close']
        
        variacao_cg, fonte_rotulo = obter_variacao_coingecko_segura(simbolo_id)
        if variacao_cg is None:
            variacao_cg = ((preco_atual - df_dados.iloc[0]['close']) / df_dados.iloc[0]['close']) * 100

        recomendacao, cor_sinal, justificativa = calcular_sinal_BRICS(df_dados)

        # 🚨 SEÇÃO 1: PAINEL DE CONFLUÊNCIA DE SINAIS 🚨
        st.markdown(f"""
        <div style="background-color: {cor_sinal}22; padding: 20px; border-radius: 10px; border: 2px solid {cor_sinal}; margin-bottom: 25px;">
            <h2 style="margin: 0; color: {cor_sinal}; font-size: 26px;">SINAL EMITIDO: {recomendacao}</h2>
            <p style="margin: 8px 0 0 0; font-size: 16px; color: #ffffff;"><b>Filtro Confluente Multi-Indicadores:</b> {justificativa}</p>
        </div>
        """, unsafe_allow_html=True)

        # SEÇÃO 2: CARD DE MÉTRICAS CORRIGIDO E SEGURO
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Preço Spot Real", f"$ {preco_atual:,.4f}")
        m_col2.metric(fonte_rotulo, f"{variacao_cg:+.2f}%")
        m_col3.metric("Preço Stop ATR", f"$ {ultimo_reg['ATR_Stop']:,.4f}")

        # SEÇÃO 3: TABELA DINÂMICA DO MOMENTUM RSI 14
        st.markdown("### 📊 Tabela de Zonas de Momentum e Exaustão (RSI 14)")
        rsi_atual = ultimo_reg['RSI_14']
        estado_rsi = "🔴 SOBRECOMPRADO (Exaustão Alta)" if rsi_atual > 70 else ("🟢 SOBREVENDIDO (Exaustão Baixa)" if rsi_atual < 30 else "🟡 ZONA NEUTRA (Continuidade)")
        
        tabela_rsi_dados = pd.DataFrame({
            "Métrica": ["RSI Atual", "Estado de Momento", "Zona de Alerta Compra", "Zona de Alerta Venda"],
            "Valor / Limiar": [f"{rsi_atual:.2f}", estado_rsi, "Abaixo de 30 ou 45 (Confluente)", "Acima de 70 ou 55 (Confluente)"]
        })
        st.table(tabela_rsi_dados)

        # SEÇÃO 4: GRÁFICO AVANÇADO SUBPLOTS (COM SSL, STOP ATR E ALPHATREND)
        fig = make_subplots(
            rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06, 
            subplot_titles=(f'Candlesticks + SSL Hybrid + Stop ATR + AlphaTrend - {simbolo_id}', 'Índice de Força Relativa (RSI)', 'Histograma MACD'),
            row_width=[0.2, 0.2, 0.6]
        )

        fig.add_trace(go.Candlestick(
            x=df_dados['time'], open=df_dados['open'], high=df_dados['high'], low=df_dados['low'], close=df_dados['close'], name="Preço"
        ), row=1, col=1)
        
        # Linhas do SSL Hybrid
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['SSL_Baseline'], line=dict(color='#00ffff', width=1.5), name="SSL Baseline"), row=1, col=1)
        
        # Linha do Stop ATR
        cor_atr = '#17becf' if ultimo_reg['atr_dir'] == 1 else '#d62728'
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['ATR_Stop'], line=dict(color=cor_atr, width=2, dash='dot'), name="Stop ATR"), row=1, col=1)
        
        # Linhas do Indicador AlphaTrend
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['AT_K1'], line=dict(color='#00ffcc', width=2), name="AlphaTrend (K1)"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['AT_K2'], line=dict(color='#ff0055', width=1.5), name="AlphaTrend Line (K2)"), row=1, col=1)

        # Subplots Auxiliares
        fig.add_trace(go.Scatter(x=df_dados['time'], y=df_dados['RSI_14'], line=dict(color='purple', width=2), name="RSI"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        fig.add_trace(go.Bar(x=df_dados['time'], y=df_dados['MACD_HIST'], name="Hist MACD", marker_color='cyan'), row=3, col=1)

        fig.update_layout(height=750, template="plotly_dark", xaxis_rangeslider_visible=False, margin=dict(l=40, r=40, t=40, b=40))
        st.plotly_chart(fig, use_container_width=True)

        # --- SEÇÃO 5: LEGENDAS E GLOSSÁRIO EDUCACIONAL NO RODAPÉ ---
        st.markdown("---")
        st.markdown("### 📘 Legendas e Notas Conceituais de Mercado")
        col_leg1, col_leg2 = st.columns(2)
        
        with col_leg1:
            st.info("""
            **🏦 PREÇO SPOT REAL**
            Refere-se ao preço de liquidação imediata do ativo no mercado à vista (Spot) no exato milissegundo da última consulta. É o valor de troca corrente do par contra o dólar tether (USDT), livre de prejuções de derivativos, ágios ou taxas futuras.
            """)
            
        with col_leg2:
            st.info("""
            **📊 VOLUME HISTÓRICO**
            Representa o somatório total de unidades da criptomoeda que foram efetivamente negociadas (compradas e vendidas) ao longo do período temporal selecionado. É a métrica definitiva para validar a liquidez e a relevância institucional por trás de um movimento de preço.
            """)

        if modo_vivo:
            time.sleep(intervalo_refresh)
            st.rerun()
    else:
        st.error("Dados históricos insuficientes nesta Exchange para calcular os novos modelos confluentes (AlphaTrend exige mais histórico). Mude o Ativo ou reduza o Tempo Gráfico.")
