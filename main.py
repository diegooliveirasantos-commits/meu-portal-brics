import streamlit as st
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
from datetime import datetime

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
PERIODO_SWING_DEFAULT = 50   # Período para detectar o swing

# ─────────────────────────────────────────────────────────────────────────────
# DICIONÁRIO DE IDIOMAS (15 línguas) – incluídos os novos textos
# (Mesmo dicionário da versão anterior, com os campos adicionados)
# Para não repetir o código gigante, mantive exatamente o mesmo DICIONARIO_LINGUAS
# da resposta anterior. Se preferir, posso reenviá-lo completo.
# ─────────────────────────────────────────────────────────────────────────────

# (Aqui vai o DICIONARIO_LINGUAS completo – igual ao da resposta anterior)
# Para economizar espaço, estou supondo que você já o tem.
# Se precisar, me peça que eu reenvio o dicionário completo.

# ─────────────────────────────────────────────────────────────────────────────
# FORMATAÇÃO (funções formatar_preco, formatar_market_cap – iguais)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# GERENCIADOR DE EXCHANGES (igual)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÕES DE MERCADO (obter_todos_pares_usdt, obter_dados_24h, etc – iguais)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# INDICADORES TÉCNICOS (RSI, MACD, MFI, SSL, ATR, PPO – iguais)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# DETECTOR DE SWING (ATUALIZADO)
def detectar_swing(df, periodo=PERIODO_SWING_DEFAULT):
    """Retorna o topo (high) e o fundo (low) do período especificado."""
    if len(df) < periodo:
        periodo = len(df)
    df_swing = df.iloc[-periodo:].copy()
    swing_high = df_swing['high'].max()
    swing_low = df_swing['low'].min()
    return swing_high, swing_low

# ─────────────────────────────────────────────────────────────────────────────
# GERADOR DE SINAL FIBONACCI (NOVA LÓGICA)
def gerar_sinal_fibonacci(df, direcao, multiplicadores):
    """
    Gera entrada (preço atual), stop loss (topo/fundo do swing) e alvos.
    direcao: 'LONG' ou 'SHORT'
    multiplicadores: lista de floats (ex: [0.236, 0.5, 0.786, ...])
    """
    swing_high, swing_low = detectar_swing(df)
    preco_atual = df['close'].iloc[-1]

    if direcao == "LONG":
        stop = swing_low
        risco = preco_atual - stop
        alvos = [preco_atual + mult * risco for mult in multiplicadores]
    else:  # SHORT
        stop = swing_high
        risco = stop - preco_atual
        alvos = [preco_atual - mult * risco for mult in multiplicadores]

    # Filtra apenas alvos com lucro positivo (ou seja, acima do preço para LONG, abaixo para SHORT)
    if direcao == "LONG":
        alvos_validos = [a for a in alvos if a > preco_atual]
    else:
        alvos_validos = [a for a in alvos if a < preco_atual]

    # Pega os primeiros 8 alvos (ou menos)
    alvos_finais = alvos_validos[:8]
    mult_utilizados = multiplicadores[:len(alvos_finais)]

    return {
        "direcao": direcao,
        "swing_high": swing_high,
        "swing_low": swing_low,
        "entrada": preco_atual,
        "stop": stop,
        "risco": risco,
        "alvos": alvos_finais,
        "multiplicadores": mult_utilizados
    }

# ─────────────────────────────────────────────────────────────────────────────
# ANÁLISE DE CONFLUÊNCIA SMC (retorna direção) – igual à anterior
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# CARREGAMENTO DE DADOS (igual)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO (igual)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR – com novos controles
idiomas_disponiveis = list(DICIONARIO_LINGUAS.keys())

st.sidebar.markdown(f"### {DICIONARIO_LINGUAS['Português (BR)']['idioma_label']}")
idioma_selecionado = st.sidebar.selectbox(
    DICIONARIO_LINGUAS['Português (BR)']['idioma_selecao'],
    options=idiomas_disponiveis,
    index=0
)
txt = DICIONARIO_LINGUAS[idioma_selecionado]
st.title(txt["titulo"])
st.sidebar.header(txt["config_globais"])

lista_criptos = obter_todos_pares_usdt()
if not lista_criptos:
    lista_criptos = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]

simbolo_id = st.sidebar.selectbox(
    txt["selecione_cripto"],
    lista_criptos,
    index=lista_criptos.index("SOL/USDT") if "SOL/USDT" in lista_criptos else 0
)

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

# ⭐ NOVOS CONTROLES PARA OS MULTIPLICADORES
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

# ─────────────────────────────────────────────────────────────────────────────
# PAINEL PRINCIPAL
@st.fragment(run_every=intervalo_refresh if modo_vivo else None)
def painel_principal(simbolo_id, timeframe, txt, modo_vivo, intervalo_refresh,
                     multiplicadores, periodo_swing):
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

    # Dados de 24h
    dados_24h = obter_dados_24h(simbolo_id)
    variacao_24h = dados_24h.get("change") if dados_24h else 0.0
    volume_24h = dados_24h.get("volume") if dados_24h else None
    market_cap = obter_market_cap_robusto(simbolo_id)

    # Análise SMC (retorna direção)
    recomendacao, cor_sinal, analise, pontos_alta, pontos_baixa, direcao = analisar_confluencia(
        df_dados, txt
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

    # ⭐ GERAR SINAL FIBONACCI COM OS MULTIPLICADORES E PERÍODO DO SWING
    # Atualiza o detector de swing com o período escolhido
    # (a função detectar_swing usa a variável global, mas passamos como argumento)
    def detectar_swing_local(df, periodo=periodo_swing):
        if len(df) < periodo:
            periodo = len(df)
        df_swing = df.iloc[-periodo:].copy()
        return df_swing['high'].max(), df_swing['low'].min()

    # Sobrescrevemos a função localmente para usar o período selecionado
    # Para simplificar, redefinimos a função gerar_sinal_fibonacci com o período
    def gerar_sinal_fibonacci_local(df, direcao, mults):
        swing_high, swing_low = detectar_swing_local(df)
        preco = df['close'].iloc[-1]
        if direcao == "LONG":
            stop = swing_low
            risco = preco - stop
            alvos = [preco + m * risco for m in mults]
        else:
            stop = swing_high
            risco = stop - preco
            alvos = [preco - m * risco for m in mults]
        if direcao == "LONG":
            alvos_validos = [a for a in alvos if a > preco]
        else:
            alvos_validos = [a for a in alvos if a < preco]
        alvos_finais = alvos_validos[:8]
        mult_utilizados = mults[:len(alvos_finais)]
        return {
            "direcao": direcao,
            "swing_high": swing_high,
            "swing_low": swing_low,
            "entrada": preco,
            "stop": stop,
            "risco": risco,
            "alvos": alvos_finais,
            "multiplicadores": mult_utilizados
        }

    sinal_fib = gerar_sinal_fibonacci_local(df_dados, direcao, multiplicadores)

    # Exibe o card de alvos
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
        cols1 = st.columns(4)
        for i in range(min(4, len(alvos))):
            label = txt["alvo_prefix"].format(n=i+1)
            preco_alvo = alvos[i]
            if sinal_fib['direcao'] == "LONG":
                pct = ((preco_alvo - sinal_fib['entrada']) / sinal_fib['entrada']) * 100
            else:
                pct = ((sinal_fib['entrada'] - preco_alvo) / sinal_fib['entrada']) * 100
            cols1[i].metric(label, formatar_preco(preco_alvo), delta=f"{pct:+.2f}%")
        if len(alvos) > 4:
            cols2 = st.columns(4)
            for i in range(4, min(8, len(alvos))):
                label = txt["alvo_prefix"].format(n=i+1)
                preco_alvo = alvos[i]
                if sinal_fib['direcao'] == "LONG":
                    pct = ((preco_alvo - sinal_fib['entrada']) / sinal_fib['entrada']) * 100
                else:
                    pct = ((sinal_fib['entrada'] - preco_alvo) / sinal_fib['entrada']) * 100
                cols2[i-4].metric(label, formatar_preco(preco_alvo), delta=f"{pct:+.2f}%")
    else:
        st.info(txt["sem_alvos"])

    st.divider()

    # Métricas principais
    nome_extenso = obter_nome_extenso_cripto(simbolo_id)
    label_preco = f"{nome_extenso} | {txt['preco_spot']}"
    volume_formatado = formatar_market_cap(volume_24h)
    market_cap_formatado = formatar_market_cap(market_cap)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(label_preco, formatar_preco(preco_atual))
    m2.metric(txt["variacao_24h"], f"{variacao_24h:+.2f}%" if variacao_24h is not None else "—")
    m3.metric(txt["volume_24h"], volume_formatado)
    m4.metric(txt["market_cap"], market_cap_formatado)

    atr_stop_val = ultimo_reg['ATR_Stop']
    st.markdown(
        f"**{txt['stop_atr']}:** {formatar_preco(atr_stop_val)}"
        f"  |  RSI: **{ultimo_reg['RSI_14']:.1f}**"
        f"  |  MFI: **{ultimo_reg['MFI']:.1f}**"
    )

    st.markdown(f"### {txt['grafico_titulo']}")
    renderizar_grafico_plotly(df_dados, simbolo_id)

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


painel_principal(simbolo_id, timeframe, txt, modo_vivo, intervalo_refresh,
                 multiplicadores, periodo_swing)
