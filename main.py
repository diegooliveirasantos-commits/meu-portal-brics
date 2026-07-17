import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import requests
import math
from decimal import Decimal
import plotly.graph_objects as go

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
IDIOMA_PADRAO = "Português (BR)"
TTL_MERCADOS_SEGUNDOS = 3600
TTL_DADOS_LIVE_SEGUNDOS = 15
TTL_BOOK_SEGUNDOS = 12
EXCHANGE_TIMEOUT_MS = 10000

LIMITE_BOOK = 100
FAIXA_BOOK = 0.015
PASSO_AGRUPAMENTO = 0.0005

JANELA_BASE_WYCKOFF = 60
JANELA_EVENTO_WYCKOFF = 15

LIMIAR_SINAL_LIQUIDO = 32.0

# ─────────────────────────────────────────────────────────────────────────────
# DICIONÁRIO DE IDIOMAS (mesmo da versão anterior, omitido para economia)
# ... (insira aqui o dicionário completo _TEXTOS_BASE_PT_BR e _TRADUCOES)
# ─────────────────────────────────────────────────────────────────────────────

# (Aqui vão todas as funções auxiliares: formatar_preco, formatar_usdt_compacto,
#  valor_com_memoria, ExchangeManager, obter_todos_pares_usdt, obter_dados_24h,
#  resolver_volume_usdt, obter_id_coingecko, obter_dados_coingecko,
#  obter_id_coinpaprika, obter_dados_coinpaprika, resolver_market_cap,
#  obter_book_agregado, detectar_muralha_bloqueante, detectar_wyckoff,
#  calcular_rsi, calcular_rsi_estocastico, calcular_macd, calcular_mfi,
#  calcular_ssl_hybrid, calcular_atr_stop, calcular_ppo, calcular_retracao_fibonacci,
#  carregar_dados (com médias móveis e volume médio), analisar_confluencia (com os novos pesos),
#  escolher_stop, construir_alvos, lucro_percentual,
#  renderizar_card_plano, _chips, renderizar_book, renderizar_wyckoff,
#  renderizar_grafico_plotly (com suporte a stop_loss) )

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR ────────────────────────────────────────────────────────────────────

# Preparar lista de idiomas
idiomas_disponiveis = list(DICIONARIO_LINGUAS.keys())
indice_idioma_padrao = idiomas_disponiveis.index(IDIOMA_PADRAO) if IDIOMA_PADRAO in idiomas_disponiveis else 0

st.sidebar.markdown(f"### {DICIONARIO_LINGUAS[IDIOMA_PADRAO]['idioma_label']}")
idioma_selecionado = st.sidebar.selectbox(
    DICIONARIO_LINGUAS[IDIOMA_PADRAO]['idioma_selecao'],
    options=idiomas_disponiveis,
    index=indice_idioma_padrao
)
txt = DICIONARIO_LINGUAS[idioma_selecionado]
st.title(txt["titulo"])
st.sidebar.header(txt["config_globais"])

# Seleção de par
lista_criptos = obter_todos_pares_usdt()
simbolo_id = st.sidebar.selectbox(
    txt["selecione_cripto"],
    lista_criptos,
    index=lista_criptos.index("SOL/USDT") if "SOL/USDT" in lista_criptos else 0
)

# Timeframe
intervalos = txt["intervalos"]
valores_intervalos = list(intervalos.values())
indice_padrao_timeframe = valores_intervalos.index("4h") if "4h" in valores_intervalos else 0
intervalo_escolhido = st.sidebar.selectbox(
    txt["tempo_grafico"],
    list(intervalos.keys()),
    index=indice_padrao_timeframe
)
timeframe = intervalos[intervalo_escolhido]

st.sidebar.markdown("---")
modo_vivo = st.sidebar.toggle(txt["modo_vivo"], value=False)
intervalo_refresh = st.sidebar.slider(
    txt["intervalo_refresh"], min_value=20, max_value=120, value=30
)

# ─────────────────────────────────────────────────────────────────────────────
# PAINEL PRINCIPAL (definido APÓS a sidebar, para ter acesso a modo_vivo e intervalo_refresh)
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

    ultimo = df_analise.iloc[-1]
    preco_atual = float(ultimo['close'])
    atr_atual = float(ultimo['ATR']) if not math.isnan(ultimo['ATR']) else preco_atual * 0.01
    simbolo_base = simbolo_id.split('/')[0]

    book = obter_book_agregado(simbolo_id)
    wyk = detectar_wyckoff(df_analise.reset_index(drop=True))
    dados_24h = obter_dados_24h(simbolo_id)
    variacao_24h = dados_24h.get("change") if dados_24h else None
    dados_gecko = obter_dados_coingecko(simbolo_base)
    dados_paprika = None
    if not dados_gecko or not dados_gecko.get("market_cap"):
        dados_paprika = obter_dados_coinpaprika(simbolo_base)

    volume_bruto = resolver_volume_usdt(dados_24h, preco_atual, dados_gecko)
    volume_usdt, volume_da_memoria = valor_com_memoria(f"vol::{simbolo_id}", volume_bruto)
    mc_bruto = resolver_market_cap(simbolo_base, preco_atual, dados_gecko, dados_paprika)
    market_cap, mc_da_memoria = valor_com_memoria(f"mc::{simbolo_id}", mc_bruto)

    res = analisar_confluencia(df_dados, txt, book, wyk)

    st.markdown(
        f"""
        <div style="background:{res['cor']}22;padding:20px;border-radius:10px;
            border:2px solid {res['cor']};margin-bottom:20px;">
            <h2 style="margin:0;color:{res['cor']};">{res['recomendacao']}</h2>
            <p style="margin:8px 0 0 0;color:#ddd;">{res['contexto']}
            | <b>{txt['escore_liquido']}: {res['liquido']:+.1f} / 100</b></p>
        </div>
        """,
        unsafe_allow_html=True
    )
    if res["bloqueado"]:
        st.warning(txt["alerta_muralha"])

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric(f"{simbolo_base} | {txt['preco_spot']}", formatar_preco(preco_atual))
    m2.metric(txt["variacao_24h"], f"{variacao_24h:+.2f}%" if variacao_24h is not None else "---")
    m3.metric(
        txt["volume_24h"],
        formatar_usdt_compacto(volume_usdt),
        delta=txt["valor_memorizado"] if volume_da_memoria else None,
        delta_color="off"
    )
    m4.metric(
        txt["market_cap"],
        formatar_usdt_compacto(market_cap) if market_cap else txt["marketcap_nao_disponivel"],
        delta=txt["valor_memorizado"] if mc_da_memoria else None,
        delta_color="off"
    )
    m5.metric(txt["pontos_compra"], f"{res['alta']:.1f}")
    m6.metric(txt["pontos_venda"], f"{res['baixa']:.1f}")

    stoch_k = float(ultimo['STOCH_K']) if not math.isnan(ultimo['STOCH_K']) else None
    partes = [f"**{txt['stop_atr']}:** {formatar_preco(ultimo['ATR_Stop'])}"]
    if not math.isnan(ultimo['RSI_14']):
        partes.append(f"RSI: **{ultimo['RSI_14']:.1f}**")
    if stoch_k is not None:
        partes.append(f"RSI Stoch %K: **{stoch_k:.1f}**")
    if not math.isnan(ultimo['MFI']):
        partes.append(f"MFI: **{ultimo['MFI']:.1f}**")
    if not math.isnan(ultimo['MACD_HIST']):
        partes.append(f"MACD Hist: **{ultimo['MACD_HIST']:+.4f}**")
    partes.append(f"SSL: **{'ALTA' if ultimo['ssl_dir'] == 1 else 'BAIXA'}**")
    st.markdown(" | ".join(partes))

    st.markdown(f"### {txt['wyckoff_titulo']}")
    renderizar_wyckoff(txt, wyk)
    st.markdown(f"### {txt['book_titulo']}")
    renderizar_book(txt, book)

    # Plano de trade e stop
    stop = None
    alvos = []
    base_stop = ""
    if res["direcao"] in ("long", "short"):
        stop, base_stop = escolher_stop(res["direcao"], preco_atual, atr_atual,
                                        ultimo['ATR_Stop'], wyk, book)
        alvos = construir_alvos(res["direcao"], preco_atual, atr_atual, wyk, book)
        if alvos:
            st.markdown(f"### {txt['plano_trade']}")
            renderizar_card_plano(txt, simbolo_id, res["direcao"], preco_atual,
                                  stop, alvos, base_stop, preco_atual)

    st.markdown(f"### {txt['grafico_titulo']}")
    renderizar_grafico_plotly(df_dados, simbolo_id, wyk, book, stop_loss=stop)

    hora = pd.Timestamp.now().strftime("%H:%M:%S")
    prefixo = "🟢" if modo_vivo else "⏸"
    extra = f" | {txt['proximo_refresh']} {intervalo_refresh} {txt['segundos']}" if modo_vivo else ""
    st.info(
        f"{prefixo} {txt['ultima_atualizacao']}: {hora}{extra} | "
        f"{txt['aviso_aquecimento']}: {PERIODO_AQUECIMENTO} | "
        f"Velas analisadas: {len(df_analise)}"
    )

# ─────────────────────────────────────────────────────────────────────────────
# EXECUÇÃO
painel_principal(simbolo_id, timeframe, txt, modo_vivo, intervalo_refresh)
