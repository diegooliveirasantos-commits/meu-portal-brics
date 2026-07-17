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
# DICIONÁRIO DE IDIOMAS (mantido integralmente, igual à versão anterior)
# ... (insira aqui todo o dicionário _TRADUCOES e a função de fallback)
# Para não alongar, mantenha o mesmo bloco de idiomas do código anterior.
# ─────────────────────────────────────────────────────────────────────────────

# (O restante das funções auxiliares, ExchangeManager, market data, book,
#  Wyckoff, indicadores e carregamento de dados permanecem idênticos à versão
#  que já incluía as médias móveis e volume. Para evitar repetição, assuma que
#  todo o código anterior até a função `analisar_confluencia` está presente.)

# ─────────────────────────────────────────────────────────────────────────────
# ANÁLISE DE CONFLUÊNCIA (com os novos indicadores) - já implementada antes
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# PLANO DE TRADE (funções escolher_stop, construir_alvos, lucro_percentual)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# RENDERIZAÇÃO DO GRÁFICO (MODIFICADA: agora aceita stop_loss opcional)
def renderizar_grafico_plotly(df_completo, simbolo_id, wyk, book, stop_loss=None):
    df_grafico = df_completo.iloc[PERIODO_AQUECIMENTO:].copy()
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df_grafico['time'], open=df_grafico['open'], high=df_grafico['high'],
        low=df_grafico['low'], close=df_grafico['close'], name=simbolo_id,
        increasing_line_color='#10b981', decreasing_line_color='#ef4444',
        increasing_fillcolor='#10b981', decreasing_fillcolor='#ef4444'
    ))
    fig.add_trace(go.Scatter(
        x=df_grafico['time'], y=df_grafico['SSL_Baseline'], mode='lines',
        name='SMC Baseline (SSL)', line=dict(color='#00aaff', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=df_grafico['time'], y=df_grafico['ATR_Stop'], mode='lines',
        name='ATR Trailing Stop', line=dict(color='#ffaa00', width=1, dash='dash')
    ))
    if wyk and wyk.get("range_valido"):
        fig.add_hline(y=wyk["suporte"], line=dict(color="#22c55e", width=1, dash="dot"),
                      annotation_text="TR Suporte", annotation_position="bottom left",
                      annotation_font_color="#22c55e")
        fig.add_hline(y=wyk["resistencia"], line=dict(color="#f43f5e", width=1, dash="dot"),
                      annotation_text="TR Resistência", annotation_position="top left",
                      annotation_font_color="#f43f5e")
    if book:
        maior_compra = book["muralhas_compra"][0]["preco"] if book["muralhas_compra"] else None
        maior_venda = book["muralhas_venda"][0]["preco"] if book["muralhas_venda"] else None
        if maior_compra:
            fig.add_hline(y=maior_compra, line=dict(color="#22c55e", width=2),
                          annotation_text="Muralha bid", annotation_position="bottom right",
                          annotation_font_color="#22c55e")
        if maior_venda:
            fig.add_hline(y=maior_venda, line=dict(color="#f43f5e", width=2),
                          annotation_text="Muralha ask", annotation_position="top right",
                          annotation_font_color="#f43f5e")

    # ----- NOVO: exibir stop loss se fornecido -----
    if stop_loss is not None and not math.isnan(stop_loss):
        fig.add_hline(y=stop_loss, line=dict(color="#f43f5e", width=2, dash="dash"),
                      annotation_text="Stop Loss", annotation_position="top right",
                      annotation_font_color="#f43f5e")

    fig.update_layout(
        paper_bgcolor='#0b0f19', plot_bgcolor='#0b0f19', font=dict(color='#e2e8f0'),
        xaxis=dict(gridcolor='#1e293b', showgrid=True, rangeslider=dict(visible=False)),
        yaxis=dict(gridcolor='#1e293b', showgrid=True),
        legend=dict(bgcolor='#1e293b', bordercolor='#475569', borderwidth=1),
        margin=dict(l=10, r=10, t=30, b=10), height=520
    )
    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# RENDERIZAÇÃO DOS DEMAIS COMPONENTES (book, wyckoff, card de trade)
# (mantidos exatamente como antes)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# PAINEL PRINCIPAL (MODIFICADO: calcula stop e passa para o gráfico)
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

    # ----- CALCULAR STOP E ALVOS (se houver direção) -----
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
    # Passamos o stop (ou None) para o gráfico
    renderizar_grafico_plotly(df_dados, simbolo_id, wyk, book, stop_loss=stop)

    hora = pd.Timestamp.now().strftime("%H:%M:%S")
    prefixo = "🟢" if modo_vivo else "⏸"
    extra = f" | {txt['proximo_refresh']} {intervalo_refresh} {txt['segundos']}" if modo_vivo else ""
    st.info(
        f"{prefixo} {txt['ultima_atualizacao']}: {hora}{extra} | "
        f"{txt['aviso_aquecimento']}: {PERIODO_AQUECIMENTO} | "
        f"Velas analisadas: {len(df_analise)}"
    )

painel_principal(simbolo_id, timeframe, txt, modo_vivo, intervalo_refresh)
