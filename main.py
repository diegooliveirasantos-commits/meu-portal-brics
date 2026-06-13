import streamlit as st
import ccxt
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import re

st.set_page_config(
    page_title="BRICSVAULT PORTAL",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÕES AUXILIARES DE FORMATAÇÃO (Preço 0.xx e Escalas Financeiras)
# ─────────────────────────────────────────────────────────────────────────────
def fmt_grande(v: float) -> str:
    if v is None: return "—"
    if v >= 1_000_000_000: return f"${v/1_000_000_000:.2f}B"
    if v >= 1_000_000:     return f"${v/1_000_000:.2f}M"
    if v >= 1_000:         return f"${v/1_000:.2f}K"
    return f"${v:.4f}"

def formatar_preco_brics(valor: float) -> str:
    if valor == 0 or valor is None:
        return "$0.00"
    if valor >= 0.0001:
        return f"${valor:,.4f}" if valor < 1 else f"${valor:,.2f}"
    
    string_val = f"{valor:.20f}"
    match = re.match(r"^(0\.0+)([1-9]\d*)", string_val)
    if match:
        zeros = match.group(1)
        significativos = match.group(2)[:4] 
        quantidade_zeros = len(zeros) - 2 
        if quantidade_zeros >= 4:
            return f"$0.{quantidade_zeros}x{significativos}"
    return f"${valor:.8f}"

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR & MECANISMO DE BUSCA ANTI-AMBIGUIDADE
# ─────────────────────────────────────────────────────────────────────────────
st.sidebar.title("🏦 BRICSVAULT PORTAL")
st.sidebar.subheader("Painel de Controle Algorítmico")

@st.cache_resource
def iniciar_exchange():
    return ccxt.gateio({'enableRateLimit': True, 'options': {'defaultType': 'spot'}})

gateio_client = iniciar_exchange()

@st.cache_data(ttl=3600)
def obter_lista_coingecko():
    try:
        url_list = "https://api.coingecko.com/api/v3/coins/list"
        r = requests.get(url_list, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []

ticker_digitado = st.sidebar.text_input(
    "Digite o Ticker ou Nome da Criptomoeda (Ex: BTC, ETH, NEAR):",
    value="BTC"
).strip().lower()

coin_id_selecionado = None
nome_moeda_selecionada = ""
ticker_final_cg = ""

if ticker_digitado:
    todas_moedas = obter_lista_coingecko()
    
    candidatos = [
        c for c in todas_moedas 
        if c.get("symbol", "").lower() == ticker_digitado 
        or c.get("name", "").lower() == ticker_digitado
        or c.get("id", "").lower() == ticker_digitado
    ]
    
    if not candidatos:
        candidatos = [c for c in todas_moedas if ticker_digitado in c.get("symbol", "").lower() or ticker_digitado in c.get("name", "").lower()][:15]

    if len(candidatos) > 1:
        st.sidebar.info("📌 Múltiplos ativos encontrados. Escolha o correto abaixo:")
        opcoes_visuais = {f"{c['name']} ({c['symbol'].upper()}) [ID: {c['id']}]": c for c in candidatos}
        escolha = st.sidebar.selectbox("Selecione o Ativo Desejado:", list(opcoes_visuais.keys()))
        moeda_escolhida = opcoes_visuais[escolha]
        coin_id_selecionado = moeda_escolhida["id"]
        nome_moeda_selecionada = moeda_escolhida["name"]
        ticker_final_cg = moeda_escolhida["symbol"].upper()
    elif len(candidatos) == 1:
        coin_id_selecionado = candidatos[0]["id"]
        nome_moeda_selecionada = candidatos[0]["name"]
        ticker_final_cg = candidatos[0]["symbol"].upper()
    else:
        coin_id_selecionado = ticker_digitado.lower()
        nome_moeda_selecionada = ticker_digitado.upper()
        ticker_final_cg = ticker_digitado.upper()

def verificar_existencia_ticker_spot(symbol_ticker):
    try:
        base = symbol_ticker.strip().upper()
        par_com_barra      = f"{base}/USDT"
        par_com_sublinhado = f"{base}_USDT"
        
        mercados = gateio_client.load_markets()
        for par in [par_com_barra, par_com_sublinhado, base]:
            if par in mercados:
                dados_mercado = mercados[par]
                if dados_mercado.get('spot', False) or dados_mercado.get('type') == 'spot':
                    return True, dados_mercado['id'], base
        return False, par_com_barra, base
    except Exception:
        return False, "", symbol_ticker.upper()

ativo_valido, par_id_api, base_ticker_gate = verificar_existencia_ticker_spot(ticker_final_cg)

if not ativo_valido and ticker_digitado:
    st.sidebar.warning("⚠️ Par correspondente em /USDT não encontrado na Gate.io Spot.")

mapa_timeframes = {
    "1 Minuto": "1m", "5 Minutos": "5m", "15 Minutos": "15m", 
    "1 Hora": "1h", "4 Horas": "4h", "1 Dia": "1d", 
    "1 Semana": "1w", "1 Mês (Longo Prazo)": "1d"  
}
intervalo_escolhido = st.sidebar.selectbox("Escolha o Intervalo de Tempo (Velas):", list(mapa_timeframes.keys()), index=4)
timeframe_api = mapa_timeframes[intervalo_escolhido]

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Engine BRICSVAULT")

clicou_go = st.sidebar.button("Executar Análise (GO) 🚀", use_container_width=True)

nome_exibicao = f"{base_ticker_gate}/USDT" if ativo_valido else "Aguardando ativo válido..."

st.title("🏦 BRICSVAULT PORTAL — Sistema Analítico")
st.caption(f"Monitoramento Estratégico de Alta Performance | Ativo: {nome_exibicao} | Tempo: {intervalo_escolhido}")

# ─────────────────────────────────────────────────────────────────────────────
# BLOCO 1 — MONITOR DE MARKETCAP (CoinGecko)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def buscar_dados_coingecko_por_id(coin_id: str) -> dict | None:
    try:
        if not coin_id: return None
        url_market = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={coin_id}&order=market_cap_desc&per_page=1&page=1&sparkline=false&price_change_percentage=1h,24h,7d"
        r_market = requests.get(url_market, timeout=10)
        if r_market.status_code != 200 or not r_market.json():
            return None
        d = r_market.json()[0]

        url_detail = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&community_data=false&developer_data=false"
        r_detail = requests.get(url_detail, timeout=10)
        market_data = r_detail.json().get("market_data", {}) if r_detail.status_code == 200 else {}

        return {
            "coin_id":           coin_id,
            "nome":              d.get("name", "—"),
            "simbolo":           d.get("symbol", "—").upper(),
            "imagem":            d.get("image", ""),
            "preco_usd":         d.get("current_price", 0),
            "marketcap_usd":     d.get("market_cap", 0),
            "marketcap_rank":    d.get("market_cap_rank", "—"),
            "volume_24h_usd":    d.get("total_volume", 0),
            "variacao_1h":       d.get("price_change_percentage_1h_in_currency", 0) or 0,
            "variacao_24h":      d.get("price_change_percentage_24h", 0) or 0,
            "variacao_7d":       d.get("price_change_percentage_7d_in_currency", 0) or 0,
            "supply_circulante": d.get("circulating_supply", 0),
            "supply_total":      d.get("total_supply", 0) or 0,
            "supply_max":        d.get("max_supply", 0) or 0,
            "fdv":               market_data.get("fully_diluted_valuation", {}).get("usd", 0) or d.get("fully_diluted_valuation", 0) or 0,
        }
    except Exception:
        return None

def badge_var(pct: float) -> str:
    s = "▲" if pct >= 0 else "▼"
    c = "🟢" if pct >= 0 else "🔴"
    return f"{c} {s} {abs(pct):.2f}%"

def renderizar_monitor_marketcap(dados_coingecko: dict | None):
    st.markdown("### 📊 Monitor de Market Cap & Ranking Fundamentalista")
    if dados_coingecko is None:
        st.warning("⚠️ Dados fundamentalistas do ativo indisponíveis via CoinGecko.")
        return

    d = dados_coingecko
    col_img, col_info = st.columns([1, 11])
    with col_img:
        if d["imagem"]: st.image(d["imagem"], width=52)
    with col_info:
        st.markdown(f"### {d['nome']} ({d['simbolo']}) &nbsp;&nbsp; 🏆 **Ranking Oficial: #{d['marketcap_rank']}**")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("💰 Preço USD",  formatar_preco_brics(d['preco_usd']), delta=f"{d['variacao_24h']:+.2f}% (24h)")
    with c2: st.metric("📦 Market Cap", fmt_grande(d['marketcap_usd']))
    with c3: st.metric("🔁 Volume 24h", fmt_grande(d['volume_24h_usd']))
    with c4: st.metric("🏗️ FDV",        fmt_grande(d['fdv']) if d['fdv'] else "—")
    with c5:
        ratio_vm = d['volume_24h_usd'] / d['marketcap_usd'] * 100 if d['marketcap_usd'] > 0 else 0
        st.metric("📈 Vol/MC", f"{ratio_vm:.2f}%")

    cv1, cv2, cv3 = st.columns(3)
    with cv1: st.markdown(f"Variação 1h: {badge_var(d['variacao_1h'])}")
    with cv2: st.markdown(f"Variação 24h: {badge_var(d['variacao_24h'])}")
    with cv3: st.markdown(f"Variação 7d: {badge_var(d['variacao_7d'])}")

# ─────────────────────────────────────────────────────────────────────────────
# BLOCO 2 — MONITOR DE TVL GLOBAL (DefiLlama)
# ─────────────────────────────────────────────────────────────────────────────
DEFILLAMA_BASE = "https://api.llama.fi"
@st.cache_data(ttl=120)
def buscar_lista_protocolos_defillama() -> list[dict]:
    try:
        r = requests.get(f"{DEFILLAMA_BASE}/protocols", timeout=15)
        if r.status_code == 200: return r.json()
    except Exception: pass
    return []

def _renderizar_ranking_chains(lista_protocolos: list[dict]):
    with st.expander("🌍 Top 10 Protocolos DeFi Globais (Contexto On-Chain)", expanded=False):
        top10 = sorted([p for p in lista_protocolos if (p.get("tvl") or 0) > 0], key=lambda x: x.get("tvl", 0), reverse=True)[:10]
        if top10:
            rows = [{"Rank": f"#{i}", "Protocolo": p.get("name", "—"), "Categoria": p.get("category", "—"), "TVL": fmt_grande(p.get("tvl", 0))} for i, p in enumerate(top10, 1)]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# BLOCO 3 — INDICADORES TÉCNICOS & HISTÓRICO CORRIGIDO (Suporte para 1 Mês)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=15)
def carregar_dados_bricsvault(simbolo_id, timeframe):
    try:
        if timeframe == "1d" and intervalo_escolhido == "1 Mês (Longo Prazo)":
            velas = gateio_client.fetch_ohlcv(simbolo_id, timeframe='1d', limit=1000)
        else:
            limite_velas = 500 if timeframe in ['1m', '5m', '15m'] else 300
            velas = gateio_client.fetch_ohlcv(simbolo_id, timeframe=timeframe, limit=limite_velas)
            
        if not velas: return None
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        if timeframe == "1d" and intervalo_escolhido == "1 Mês (Longo Prazo)":
            df.set_index('time', inplace=True)
            df = df.resample('ME').agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})
            df.reset_index(inplace=True)
        
        df['EMA_9']   = ta.ema(df['close'], length=9)
        df['EMA_21']  = ta.ema(df['close'], length=21)
        df['EMA_55']  = ta.ema(df['close'], length=55)
        
        if len(df) >= 200:
            df['EMA_200'] = ta.ema(df['close'], length=200)
        else:
            df['EMA_200'] = df['EMA_55']
            
        df['RSI_14']  = ta.rsi(df['close'], length=14)
        df['ATR_14']  = ta.atr(df['high'], df['low'], df['close'], length=14)
        
        macd_df = ta.macd(df['close'], fast=12, slow=26, signal=9)
        if macd_df is not None and not macd_df.empty:
            df['MACD']        = macd_df.iloc[:, 0]
            df['MACD_SIGNAL'] = macd_df.iloc[:, 1]
            df['MACD_HIST']   = macd_df.iloc[:, 2]
        return df.dropna(subset=['close', 'EMA_9', 'RSI_14'])
    except Exception: return None

def carregar_livro_ordens_financeiro(simbolo_id):
    try:
        ordens = gateio_client.fetch_order_book(simbolo_id, limit=20)
        bids_proc = [[p, float(p) * float(q)] for p, q in ordens['bids']]
        asks_proc = [[p, float(p) * float(q)] for p, q in ordens['asks']]
        df_bids   = pd.DataFrame(bids_proc, columns=['Preço (Compra)', 'TOTAL (USDT)'])
        df_asks   = pd.DataFrame(asks_proc, columns=['Preço (Venda)',  'TOTAL (USDT)'])
        vol_bids  = df_bids['TOTAL (USDT)'].sum()
        vol_asks  = df_asks['TOTAL (USDT)'].sum()
        ratio     = vol_bids / vol_asks if vol_asks > 0 else 1.0
        pressao   = 'COMPRADORA' if ratio >= 1.15 else ('VENDEDORA' if ratio <= 0.87 else 'NEUTRA')
        return df_bids, df_asks, {'volume_bids_usdt': vol_bids, 'volume_asks_usdt': vol_asks, 'pressao': pressao, 'ratio': ratio}
    except Exception:
        return pd.DataFrame(), pd.DataFrame(), {'pressao': 'NEUTRA', 'ratio': 1.0, 'volume_bids_usdt': 0, 'volume_asks_usdt': 0}

def rastrear_grandes_negocios(simbolo_id):
    try:
        historico = gateio_client.fetch_trades(simbolo_id, limit=60)
        if not historico: return pd.DataFrame(), {'pressao_whales': 'NEUTRA', 'ratio_whales': 1.0, 'vol_compra_usdt': 0, 'vol_venda_usdt': 0}
        df_trades = pd.DataFrame(historico, columns=['timestamp', 'side', 'price', 'amount', 'cost'])
        df_trades['Horário']      = pd.to_datetime(df_trades['timestamp'], unit='ms').dt.strftime('%H:%M:%S')
        df_trades['Total (USDT)'] = pd.to_numeric(df_trades['cost'], errors='coerce').fillna(0)
        
        threshold = df_trades['Total (USDT)'].quantile(0.75)
        df_w = df_trades[df_trades['Total (USDT)'] >= threshold].copy()
        vc        = df_w.loc[df_w['side'] == 'buy',  'Total (USDT)'].sum()
        vv        = df_w.loc[df_w['side'] == 'sell', 'Total (USDT)'].sum()
        rw        = vc / vv if vv > 0 else 1.0
        pw        = 'COMPRADORA' if rw >= 1.20 else ('VENDEDORA' if rw <= 0.83 else 'NEUTRA')
        df_ex = df_trades.rename(columns={'side': 'Operação', 'price': 'Preço', 'amount': 'Volume'})[['Horário', 'Operação', 'Preço', 'Volume', 'Total (USDT)']].sort_values(by='Total (USDT)', ascending=False)
        return df_ex, {'pressao_whales': pw, 'vol_compra_usdt': vc, 'vol_venda_usdt': vv, 'ratio_whales': rw}
    except Exception:
        return pd.DataFrame(), {'pressao_whales': 'NEUTRA', 'ratio_whales': 1.0, 'vol_compra_usdt': 0, 'vol_venda_usdt': 0}

# ─────────────────────────────────────────────────────────────────────────────
# CONFIRMAÇÃO SEVERA DE INDICADORES ANTES DE EXIBIR O SINAL
# ─────────────────────────────────────────────────────────────────────────────
def avaliar_sinal_completo(df, metricas_ordens, metricas_whales):
    if df is None or df.empty or not metricas_ordens or not metricas_whales or 'RSI_14' not in df.columns:
        return 'AGUARDANDO INTEGRALIDADE E CONFLUÊNCIA DOS INDICADORES', 0, 0, {}

    atual    = df.iloc[-1]
    preco    = atual['close']
    atr      = atual['ATR_14']
    
    alinhamento_bull = (atual['EMA_9'] > atual['EMA_21'] and atual['EMA_21'] > atual['EMA_55'] and atual['EMA_55'] > atual['EMA_200'])
    rsi_ok  = 30 < atual['RSI_14'] < 65
    macd_ok = atual.get('MACD', 0) > atual.get('MACD_SIGNAL', 0)
    reversao_bear = (atual['EMA_9'] < atual['EMA_21'] or atual['close'] < atual['EMA_55'] or atual['close'] < atual['EMA_200'])
    
    po = metricas_ordens.get('pressao', 'NEUTRA')
    pw = metricas_whales.get('pressao_whales', 'NEUTRA')

    condicoes_tec = alinhamento_bull and rsi_ok and macd_ok
    conf_fluxo    = (po == 'COMPRADORA') or (pw == 'COMPRADORA')
    bloq_fluxo    = (po == 'VENDEDORA') and (pw == 'VENDEDORA')

    sl = preco - (1.5 * atr)
    tp = preco + (3.0 * atr)
    
    detalhes = {
        'alinhamento_emas': alinhamento_bull, 'rsi_ok': rsi_ok, 'macd_ok': macd_ok,
        'pressao_ordens': po, 'pressao_whales': pw, 'bloqueio_fluxo': bloq_fluxo
    }
    
    if reversao_bear or bloq_fluxo: 
        return 'VENDA IMEDIATAMENTE', sl, tp, detalhes
    elif condicoes_tec and conf_fluxo and po != 'VENDEDORA' and pw != 'VENDEDORA': 
        return 'COMPRE AGORA', sl, tp, detalhes
    else: 
        return 'SEM COMPRAS A FAZER', 0, 0, detalhes

# ─────────────────────────────────────────────────────────────────────────────
# EXECUÇÃO DO BLOCO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
if ativo_valido and clicou_go:
    with st.spinner("Consolidando confluências de blocos..."):
        d_cg = buscar_dados_coingecko_por_id(coin_id_selecionado)
        lista_ll = buscar_lista_protocolos_defillama()
        df_portal = carregar_dados_bricsvault(par_id_api, timeframe_api)
        df_bids, df_asks, metricas_ordens = carregar_livro_ordens_financeiro(par_id_api)
        df_baleias, metricas_whales = rastrear_grandes_negocios(par_id_api)

    if df_portal is not None and not df_portal.empty:
        renderizar_monitor_marketcap(d_cg)
        _renderizar_ranking_chains(lista_ll)
        st.markdown("---")

        status_sinal, sl_proj, tp_proj, detalhes = avaliar_sinal_completo(df_portal, metricas_ordens, metricas_whales)

        st.markdown("### 🔔 Direcionamento Estratégico de Ação")
        if status_sinal == 'COMPRE AGORA':
            st.success(f"🟢 **AÇÃO RECOMENDADA: COMPRE AGORA!** | Todos os indicadores validados. Alvo: {formatar_preco_brics(tp_proj)} | Stop Loss: {formatar_preco_brics(sl_proj)}")
        elif status_sinal == 'VENDA IMEDIATAMENTE':
            st.error(f"🔴 **AÇÃO RECOMENDADA: VENDA IMEDIATAMENTE!** | Rompimento ou cruzamento de baixa disparado em fluxo.")
        else:
            st.info(f"⚪ **AÇÃO RECOMENDADA: SEM COMPRAS A FAZER.** | Fora das zonas ideais de confluência.")
        
        st.markdown("---")

        preco_atual = df_portal.iloc[-1]['close']
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Preço de Fechamento", formatar_preco_brics(preco_atual))
        with c2: st.metric("RSI 14", f"{df_portal.iloc[-1]['RSI_14']:.2f}")
        with c3: st.metric("EMA 9", formatar_preco_brics(df_portal.iloc[-1]['EMA_9']))
        with c4: st.metric("EMA 200", formatar_preco_brics(df_portal.iloc[-1]['EMA_200']))

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.75, 0.25])
        fig.add_trace(go.Candlestick(x=df_portal['time'], open=df_portal['open'], high=df_portal['high'], low=df_portal['low'], close=df_portal['close'], name="Velas"), row=1, col=1)
        
        for col, cor, lbl in [('EMA_9', '#2196f3', 'EMA 9'), ('EMA_21', '#ff9800', 'EMA 21'), ('EMA_55', '#e91e63', 'EMA 55'), ('EMA_200', '#ffd700', 'EMA 200')]:
            fig.add_trace(go.Scatter(x=df_portal['time'], y=df_portal[col], name=lbl, line=dict(color=cor, width=1.5)), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df_portal['time'], y=df_portal['RSI_14'], name='RSI 14', line=dict(color='#9c27b0')), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=600, margin=dict(l=15, r=15, t=10, b=10), paper_bgcolor="#131722", plot_bgcolor="#131722", xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 📊 Monitor de Fluxo e Volume em Tempo Real (Live Streaming Depths)")
        
        @st.fragment(run_every=2)
        def render_fluxo_dinamico_realtime():
            db, da, met = carregar_livro_ordens_financeiro(par_id_api)
            d_whales, _ = rastrear_grandes_negocios(par_id_api)
            
            c_livro, c_whales = st.columns(2)
            with c_livro:
                st.markdown(f"⏳ **LIVRO DE ORDENS** (Pressão: `{met['pressao']}` | Ratio: `{met['ratio']:.2f}x`)")
                col_compra, col_venda = st.columns(2)
                with col_compra:
                    st.caption("Ordens Limite de Compra")
                    if db is not None and not db.empty:
                        db_p = db.copy()
                        db_p['Preço (Compra)'] = db_p['Preço (Compra)'].apply(formatar_preco_brics)
                        st.dataframe(db_p.head(10), use_container_width=True, hide_index=True)
                with col_venda:
                    st.caption("Ordens Limite de Venda")
                    if da is not None and not da.empty:
                        da_p = da.copy()
                        da_p['Preço (Venda)'] = da_p['Preço (Venda)'].apply(formatar_preco_brics)
                        st.dataframe(da_p.head(10), use_container_width=True, hide_index=True)
            with c_whales:
                st.markdown("🐋 **RASTREADOR DE GRANDES NEGOCIAÇÕES (WHALES)**")
                if d_whales is not None and not d_whales.empty:
                    dw_p = d_whales.copy()
                    dw_p['Preço'] = dw_p['Preço'].apply(formatar_preco_brics)
                    st.dataframe(dw_p.head(10), use_container_width=True, hide_index=True)
                else:
                    st.info("Aguardando novas execuções de blocos na exchange...")

        render_fluxo_dinamico_realtime()

elif not clicou_go and ativo_valido:
    st.info("💡 Ativo selecionado na barra lateral. Pressione o botão **'Executar Análise (GO) 🚀'** para consolidar os indicadores.")
else:
    st.warning("Insira um ativo válido do mercado SPOT pareado em USDT para carregar o portal.")
