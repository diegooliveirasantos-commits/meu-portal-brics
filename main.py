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
# DICIONÁRIO DE IDIOMAS (17 línguas)
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
        "filtro_liquidez": "💧 Filtro de Liquidez",
        "liquidez_ok": "✅ Alta Liquidez",
        "liquidez_baixa": "⚠️ Baixa Liquidez",
        "volume_direcional_bull": "📊 Volume Direcional Bullish",
        "volume_direcional_bear": "📊 Volume Direcional Bearish",
        "volume_direcional_neutro": "📊 Volume Direcional Neutro",
        "limiar_dinamico": "Limiar Dinâmico",
        "modulo_mtf": "🔍 Módulo Multi-Timeframe",
        "modulo_estrutura": "🏗️ Módulo de Estrutura SMC",
        "modulo_obv": "📊 Módulo Divergência OBV",
        "modulo_volume": "📈 Módulo Volume Direcional",
        "modulo_fg": "😱 Módulo Fear & Greed",
        "modulo_liquidez": "💧 Módulo Liquidez",
        "intervalos": {
            "1 Minuto": "1m",
            "5 Minutos": "5m",
            "15 Minutos": "15m",
            "30 Minutos": "30m",
            "1 Hora": "1h",
            "4 Horas": "4h",
            "1 Dia": "1d",
            "1 Semana": "1w"
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
        "filtro_liquidez": "💧 Liquidity Filter",
        "liquidez_ok": "✅ High Liquidity",
        "liquidez_baixa": "⚠️ Low Liquidity",
        "volume_direcional_bull": "📊 Bullish Directional Volume",
        "volume_direcional_bear": "📊 Bearish Directional Volume",
        "volume_direcional_neutro": "📊 Neutral Directional Volume",
        "limiar_dinamico": "Dynamic Threshold",
        "modulo_mtf": "🔍 Multi-Timeframe Module",
        "modulo_estrutura": "🏗️ SMC Structure Module",
        "modulo_obv": "📊 OBV Divergence Module",
        "modulo_volume": "📈 Directional Volume Module",
        "modulo_fg": "😱 Fear & Greed Module",
        "modulo_liquidez": "💧 Liquidity Module",
        "intervalos": {
            "1 Minute": "1m",
            "5 Minutes": "5m",
            "15 Minutes": "15m",
            "30 Minutes": "30m",
            "1 Hour": "1h",
            "4 Hours": "4h",
            "1 Day": "1d",
            "1 Week": "1w"
        }
    },
    "中文 (Mandarim)": {
        "titulo": "🏦  BRICSVAULT PORTAL - 聪明钱概念引擎",
        "config_globais": "⚙️  全局设置",
        "selecione_cripto": "选择任意加密货币 (/USDT):",
        "tempo_grafico": "时间周期:",
        "modo_vivo": "启用实时监控",
        "intervalo_refresh": "刷新间隔 (秒):",
        "preco_spot": "实时现货价格",
        "variacao_24h": "24小时涨跌",
        "market_cap": "市值 (USD)",
        "stop_atr": "ATR止损价",
        "compra_forte": "🟢  强力买入",
        "venda_forte": "🔴  强力卖出",
        "neutro": "🟡  中性",
        "spike_alta": "🚀  检测到上行突破",
        "spike_baixa": "💥  检测到下行突破",
        "erro_dados": "历史数据不足。",
        "ctx_desconto": "资产处于斐波那契折扣区。",
        "ctx_premium": "资产处于斐波那契溢价区。",
        "ctx_neutro": "价格处于斐波那契中性区。",
        "ultima_atualizacao": "最后更新",
        "proximo_refresh": "下次刷新",
        "segundos": "秒",
        "pontos_compra": "买入积分",
        "pontos_venda": "卖出积分",
        "sinal_spike": "波动突破",
        "grafico_titulo": "📈  交互式价格图表",
        "buscando_marketcap": "🔍  正在获取市值...",
        "marketcap_nao_disponivel": "不可用",
        "idioma_label": "🌐  语言",
        "idioma_selecao": "选择界面语言:",
        "aviso_aquecimento": "⚠️ 预热K线",
        "backtest_titulo": "📊 高级回测 — 最近100个信号",
        "backtest_compra": "买入",
        "backtest_venda": "卖出",
        "backtest_total": "总信号",
        "backtest_acertos": "命中",
        "backtest_taxa": "命中率",
        "backtest_profit_factor": "盈利因子",
        "backtest_avg_win": "平均盈利",
        "backtest_avg_loss": "平均亏损",
        "backtest_historico": "近期信号历史",
        "backtest_data": "日期",
        "backtest_sinal": "信号",
        "backtest_preco": "入场价",
        "backtest_resultado": "结果",
        "backtest_acerto": "✅ 命中",
        "backtest_erro": "❌ 未命中",
        "backtest_metricas": "绩效指标",
        "poc_label": "POC",
        "vah_label": "VAH",
        "val_label": "VAL",
        "fear_greed_label": "😱 恐惧贪婪指数",
        "medo_extremo": "极度恐惧",
        "medo": "恐惧",
        "neutro_fg": "中性",
        "ganancia": "贪婪",
        "ganancia_extrema": "极度贪婪",
        "estrutura_bos": "🏗️ 结构突破",
        "estrutura_choch": "🔄 特性改变",
        "estrutura_indefinida": "⏳ 结构未定义",
        "divergencia_obv_bull": "📈 OBV看涨背离",
        "divergencia_obv_bear": "📉 OBV看跌背离",
        "divergencia_obv_none": "➖ 无OBV背离",
        "alinhamento_mtf": "🔄 多周期对齐",
        "alinhamento_mtf_sim": "✅ 已对齐",
        "alinhamento_mtf_nao": "❌ 未对齐",
        "filtro_liquidez": "💧 流动性过滤",
        "liquidez_ok": "✅ 高流动性",
        "liquidez_baixa": "⚠️ 低流动性",
        "volume_direcional_bull": "📊 看涨方向量",
        "volume_direcional_bear": "📊 看跌方向量",
        "volume_direcional_neutro": "📊 中性方向量",
        "limiar_dinamico": "动态阈值",
        "modulo_mtf": "🔍 多周期模块",
        "modulo_estrutura": "🏗️ SMC结构模块",
        "modulo_obv": "📊 OBV背离模块",
        "modulo_volume": "📈 方向量模块",
        "modulo_fg": "😱 恐惧贪婪模块",
        "modulo_liquidez": "💧 流动性模块",
        "intervalos": {
            "1 分钟": "1m",
            "5 分钟": "5m",
            "15 分钟": "15m",
            "30 分钟": "30m",
            "1 小时": "1h",
            "4 小时": "4h",
            "1 天": "1d",
            "1 周": "1w"
        }
    },
    "हिन्दी (Hindi)": {
        "titulo": "🏦  BRICSVAULT PORTAL - स्मार्ट मनी कॉन्सेप्ट्स इंजन",
        "config_globais": "⚙️  वैश्विक सेटिंग्स",
        "selecione_cripto": "क्रिप्टोकरेंसी चुनें (/USDT):",
        "tempo_grafico": "समय-सीमा:",
        "modo_vivo": "रीयल-टाइम मॉनिटरिंग",
        "intervalo_refresh": "रीफ्रेश अंतराल (सेकंड):",
        "preco_spot": "स्पॉट मूल्य",
        "variacao_24h": "24 घंटे का बदलाव",
        "market_cap": "मार्केट कैप (USD)",
        "stop_atr": "ATR स्टॉप",
        "compra_forte": "🟢  मजबूत खरीद",
        "venda_forte": "🔴  मजबूत बिक्री",
        "neutro": "🟡  तटस्थ",
        "spike_alta": "🚀  तेजी का स्पाइक",
        "spike_baixa": "💥  मंदी का स्पाइक",
        "erro_dados": "अपर्याप्त डेटा।",
        "ctx_desconto": "फिबोनाची डिस्काउंट ज़ोन।",
        "ctx_premium": "फिबोनाची प्रीमियम ज़ोन।",
        "ctx_neutro": "फिबोनाची तटस्थ क्षेत्र।",
        "ultima_atualizacao": "अंतिम अपडेट",
        "proximo_refresh": "अगला रीफ्रेश",
        "segundos": "सेकंड",
        "pontos_compra": "खरीद अंक",
        "pontos_venda": "बिक्री अंक",
        "sinal_spike": "अस्थिरता स्पाइक",
        "grafico_titulo": "📈  मूल्य चार्ट",
        "buscando_marketcap": "🔍  मार्केट कैप...",
        "marketcap_nao_disponivel": "उपलब्ध नहीं",
        "idioma_label": "🌐  भाषा",
        "idioma_selecao": "भाषा चुनें:",
        "aviso_aquecimento": "⚠️ वार्म-अप कैंडल्स",
        "backtest_titulo": "📊 बैकटेस्टिंग — 100 सिग्नल",
        "backtest_compra": "खरीद",
        "backtest_venda": "बिक्री",
        "backtest_total": "कुल",
        "backtest_acertos": "सफल",
        "backtest_taxa": "सफलता दर",
        "backtest_profit_factor": "लाभ कारक",
        "backtest_avg_win": "औसत लाभ",
        "backtest_avg_loss": "औसत हानि",
        "backtest_historico": "हाल के सिग्नल",
        "backtest_data": "दिनांक",
        "backtest_sinal": "सिग्नल",
        "backtest_preco": "प्रवेश मूल्य",
        "backtest_resultado": "परिणाम",
        "backtest_acerto": "✅ सफल",
        "backtest_erro": "❌ असफल",
        "backtest_metricas": "प्रदर्शन मीट्रिक्स",
        "poc_label": "POC",
        "vah_label": "VAH",
        "val_label": "VAL",
        "fear_greed_label": "😱 फियर एंड ग्रीड",
        "medo_extremo": "अत्यधिक भय",
        "medo": "भय",
        "neutro_fg": "तटस्थ",
        "ganancia": "लालच",
        "ganancia_extrema": "अत्यधिक लालच",
        "estrutura_bos": "🏗️ BOS",
        "estrutura_choch": "🔄 CHoCH",
        "estrutura_indefinida": "⏳ अनिश्चित",
        "divergencia_obv_bull": "📈 OBV बुलिश",
        "divergencia_obv_bear": "📉 OBV बियरिश",
        "divergencia_obv_none": "➖ कोई नहीं",
        "alinhamento_mtf": "🔄 मल्टी-TF",
        "alinhamento_mtf_sim": "✅ संरेखित",
        "alinhamento_mtf_nao": "❌ नहीं",
        "filtro_liquidez": "💧 तरलता",
        "liquidez_ok": "✅ उच्च",
        "liquidez_baixa": "⚠️ कम",
        "volume_direcional_bull": "📊 बुलिश वॉल्यूम",
        "volume_direcional_bear": "📊 बियरिश वॉल्यूम",
        "volume_direcional_neutro": "📊 न्यूट्रल",
        "limiar_dinamico": "गतिशील सीमा",
        "modulo_mtf": "🔍 मल्टी-TF",
        "modulo_estrutura": "🏗️ SMC संरचना",
        "modulo_obv": "📊 OBV डाइवर्जेंस",
        "modulo_volume": "📈 दिशात्मक वॉल्यूम",
        "modulo_fg": "😱 फियर & ग्रीड",
        "modulo_liquidez": "💧 तरलता",
        "intervalos": {
            "1 मिनट": "1m",
            "5 मिनट": "5m",
            "15 मिनट": "15m",
            "30 मिनट": "30m",
            "1 घंटा": "1h",
            "4 घंटे": "4h",
            "1 दिन": "1d",
            "1 सप्ताह": "1w"
        }
    },
    "Español (Espanhol)": {
        "titulo": "🏦  BRICSVAULT PORTAL - Motor SMC",
        "config_globais": "⚙️  Configuración Global",
        "selecione_cripto": "Seleccione Criptomoneda (/USDT):",
        "tempo_grafico": "Marco de Tiempo:",
        "modo_vivo": "Monitoreo en Tiempo Real",
        "intervalo_refresh": "Intervalo (Segundos):",
        "preco_spot": "Precio Spot",
        "variacao_24h": "Variación 24h",
        "market_cap": "Cap. de Mercado (USD)",
        "stop_atr": "Stop ATR",
        "compra_forte": "🟢  COMPRA FUERTE",
        "venda_forte": "🔴  VENTA FUERTE",
        "neutro": "🟡  NEUTRAL",
        "spike_alta": "🚀  SPIKE ALCISTA",
        "spike_baixa": "💥  SPIKE BAJISTA",
        "erro_dados": "Datos insuficientes.",
        "ctx_desconto": "Zona de Descuento Fibonacci.",
        "ctx_premium": "Zona Premium Fibonacci.",
        "ctx_neutro": "Zona neutra Fibonacci.",
        "ultima_atualizacao": "Última Actualización",
        "proximo_refresh": "Próxima en",
        "segundos": "segundos",
        "pontos_compra": "Puntos Compra",
        "pontos_venda": "Puntos Venta",
        "sinal_spike": "Spike Volatilidad",
        "grafico_titulo": "📈  Gráfico Interactivo",
        "buscando_marketcap": "🔍  Market Cap...",
        "marketcap_nao_disponivel": "No disponible",
        "idioma_label": "🌐  Idioma",
        "idioma_selecao": "Seleccione idioma:",
        "aviso_aquecimento": "⚠️ Velas calentamiento",
        "backtest_titulo": "📊 Backtesting — 100 Señales",
        "backtest_compra": "Compra",
        "backtest_venda": "Venta",
        "backtest_total": "Total",
        "backtest_acertos": "Aciertos",
        "backtest_taxa": "Tasa Acierto",
        "backtest_profit_factor": "Factor Beneficio",
        "backtest_avg_win": "Ganancia Media",
        "backtest_avg_loss": "Pérdida Media",
        "backtest_historico": "Historial",
        "backtest_data": "Fecha",
        "backtest_sinal": "Señal",
        "backtest_preco": "Precio Entrada",
        "backtest_resultado": "Resultado",
        "backtest_acerto": "✅ Acierto",
        "backtest_erro": "❌ Error",
        "backtest_metricas": "Métricas",
        "poc_label": "POC",
        "vah_label": "VAH",
        "val_label": "VAL",
        "fear_greed_label": "😱 Miedo y Codicia",
        "medo_extremo": "Miedo Extremo",
        "medo": "Miedo",
        "neutro_fg": "Neutral",
        "ganancia": "Codicia",
        "ganancia_extrema": "Codicia Extrema",
        "estrutura_bos": "🏗️ BOS",
        "estrutura_choch": "🔄 CHoCH",
        "estrutura_indefinida": "⏳ Indefinido",
        "divergencia_obv_bull": "📈 OBV Alcista",
        "divergencia_obv_bear": "📉 OBV Bajista",
        "divergencia_obv_none": "➖ Sin Divergencia",
        "alinhamento_mtf": "🔄 Alineación MTF",
        "alinhamento_mtf_sim": "✅ Alineado",
        "alinhamento_mtf_nao": "❌ No Alineado",
        "filtro_liquidez": "💧 Liquidez",
        "liquidez_ok": "✅ Alta",
        "liquidez_baixa": "⚠️ Baja",
        "volume_direcional_bull": "📊 Vol. Alcista",
        "volume_direcional_bear": "📊 Vol. Bajista",
        "volume_direcional_neutro": "📊 Vol. Neutro",
        "limiar_dinamico": "Umbral Dinámico",
        "modulo_mtf": "🔍 Multi-TF",
        "modulo_estrutura": "🏗️ Estructura SMC",
        "modulo_obv": "📊 Divergencia OBV",
        "modulo_volume": "📈 Vol. Direccional",
        "modulo_fg": "😱 Miedo & Codicia",
        "modulo_liquidez": "💧 Liquidez",
        "intervalos": {
            "1 Minuto": "1m",
            "5 Minutos": "5m",
            "15 Minutos": "15m",
            "30 Minutos": "30m",
            "1 Hora": "1h",
            "4 Horas": "4h",
            "1 Día": "1d",
            "1 Semana": "1w"
        }
    },
    "Français (Francês)": {
        "titulo": "🏦  BRICSVAULT PORTAL - Moteur SMC",
        "config_globais": "⚙️  Configuration Globale",
        "selecione_cripto": "Sélectionnez Crypto (/USDT):",
        "tempo_grafico": "Période:",
        "modo_vivo": "Surveillance Temps Réel",
        "intervalo_refresh": "Intervalle (Secondes):",
        "preco_spot": "Prix Spot",
        "variacao_24h": "Variation 24h",
        "market_cap": "Cap. Boursière (USD)",
        "stop_atr": "Stop ATR",
        "compra_forte": "🟢  ACHAT FORT",
        "venda_forte": "🔴  VENTE FORTE",
        "neutro": "🟡  NEUTRE",
        "spike_alta": "🚀  SPIKE HAUSSIER",
        "spike_baixa": "💥  SPIKE BAISSIER",
        "erro_dados": "Données insuffisantes.",
        "ctx_desconto": "Zone Remise Fibonacci.",
        "ctx_premium": "Zone Premium Fibonacci.",
        "ctx_neutro": "Zone neutre Fibonacci.",
        "ultima_atualizacao": "Dernière MAJ",
        "proximo_refresh": "Prochaine dans",
        "segundos": "secondes",
        "pontos_compra": "Points Achat",
        "pontos_venda": "Points Vente",
        "sinal_spike": "Spike Volatilité",
        "grafico_titulo": "📈  Graphique Interactif",
        "buscando_marketcap": "🔍  Market Cap...",
        "marketcap_nao_disponivel": "Non disponible",
        "idioma_label": "🌐  Langue",
        "idioma_selecao": "Sélectionnez langue:",
        "aviso_aquecimento": "⚠️ Bougies préchauffage",
        "backtest_titulo": "📊 Backtesting — 100 Signaux",
        "backtest_compra": "Achat",
        "backtest_venda": "Vente",
        "backtest_total": "Total",
        "backtest_acertos": "Réussites",
        "backtest_taxa": "Taux Réussite",
        "backtest_profit_factor": "Facteur Profit",
        "backtest_avg_win": "Gain Moyen",
        "backtest_avg_loss": "Perte Moyenne",
        "backtest_historico": "Historique",
        "backtest_data": "Date",
        "backtest_sinal": "Signal",
        "backtest_preco": "Prix Entrée",
        "backtest_resultado": "Résultat",
        "backtest_acerto": "✅ Réussi",
        "backtest_erro": "❌ Échec",
        "backtest_metricas": "Métriques",
        "poc_label": "POC",
        "vah_label": "VAH",
        "val_label": "VAL",
        "fear_greed_label": "😱 Peur et Cupidité",
        "medo_extremo": "Peur Extrême",
        "medo": "Peur",
        "neutro_fg": "Neutre",
        "ganancia": "Cupidité",
        "ganancia_extrema": "Cupidité Extrême",
        "estrutura_bos": "🏗️ BOS",
        "estrutura_choch": "🔄 CHoCH",
        "estrutura_indefinida": "⏳ Indéfini",
        "divergencia_obv_bull": "📈 OBV Haussier",
        "divergencia_obv_bear": "📉 OBV Baissier",
        "divergencia_obv_none": "➖ Aucune",
        "alinhamento_mtf": "🔄 Alignement MTF",
        "alinhamento_mtf_sim": "✅ Aligné",
        "alinhamento_mtf_nao": "❌ Non Aligné",
        "filtro_liquidez": "💧 Liquidité",
        "liquidez_ok": "✅ Haute",
        "liquidez_baixa": "⚠️ Basse",
        "volume_direcional_bull": "📊 Vol. Haussier",
        "volume_direcional_bear": "📊 Vol. Baissier",
        "volume_direcional_neutro": "📊 Vol. Neutre",
        "limiar_dinamico": "Seuil Dynamique",
        "modulo_mtf": "🔍 Multi-TF",
        "modulo_estrutura": "🏗️ Structure SMC",
        "modulo_obv": "📊 Divergence OBV",
        "modulo_volume": "📈 Vol. Directionnel",
        "modulo_fg": "😱 Peur & Cupidité",
        "modulo_liquidez": "💧 Liquidité",
        "intervalos": {
            "1 Minute": "1m",
            "5 Minutes": "5m",
            "15 Minutes": "15m",
            "30 Minutes": "30m",
            "1 Heure": "1h",
            "4 Heures": "4h",
            "1 Jour": "1d",
            "1 Semaine": "1w"
        }
    },
    "Русский (Russo)": {
        "titulo": "🏦  BRICSVAULT PORTAL - Двигатель SMC",
        "config_globais": "⚙️  Настройки",
        "selecione_cripto": "Выберите криптовалюту (/USDT):",
        "tempo_grafico": "Таймфрейм:",
        "modo_vivo": "Реальный Время",
        "intervalo_refresh": "Интервал (Сек):",
        "preco_spot": "Спот Цена",
        "variacao_24h": "Изменение 24ч",
        "market_cap": "Капитализация (USD)",
        "stop_atr": "Стоп ATR",
        "compra_forte": "🟢  СИЛЬНАЯ ПОКУПКА",
        "venda_forte": "🔴  СИЛЬНАЯ ПРОДАЖА",
        "neutro": "🟡  НЕЙТРАЛЬНО",
        "spike_alta": "🚀  ВСПЛЕСК ВВЕРХ",
        "spike_baixa": "💥  ВСПЛЕСК ВНИЗ",
        "erro_dados": "Недостаточно данных.",
        "ctx_desconto": "Зона Скидки Фибоначчи.",
        "ctx_premium": "Премиум Зона Фибоначчи.",
        "ctx_neutro": "Нейтральная зона Фибоначчи.",
        "ultima_atualizacao": "Обновление",
        "proximo_refresh": "Следующее через",
        "segundos": "сек",
        "pontos_compra": "Очки Покупки",
        "pontos_venda": "Очки Продажи",
        "sinal_spike": "Всплеск",
        "grafico_titulo": "📈  График Цены",
        "buscando_marketcap": "🔍  Капитализация...",
        "marketcap_nao_disponivel": "Недоступно",
        "idioma_label": "🌐  Язык",
        "idioma_selecao": "Выберите язык:",
        "aviso_aquecimento": "⚠️ Разогрев свечей",
        "backtest_titulo": "📊 Бэктестинг — 100 Сигналов",
        "backtest_compra": "Покупка",
        "backtest_venda": "Продажа",
        "backtest_total": "Всего",
        "backtest_acertos": "Успешно",
        "backtest_taxa": "% Успеха",
        "backtest_profit_factor": "Фактор Прибыли",
        "backtest_avg_win": "Ср. Прибыль",
        "backtest_avg_loss": "Ср. Убыток",
        "backtest_historico": "История",
        "backtest_data": "Дата",
        "backtest_sinal": "Сигнал",
        "backtest_preco": "Цена Входа",
        "backtest_resultado": "Результат",
        "backtest_acerto": "✅ Успех",
        "backtest_erro": "❌ Неудача",
        "backtest_metricas": "Метрики",
        "poc_label": "POC",
        "vah_label": "VAH",
        "val_label": "VAL",
        "fear_greed_label": "😱 Страх и Жадность",
        "medo_extremo": "Экстрим Страх",
        "medo": "Страх",
        "neutro_fg": "Нейтрально",
        "ganancia": "Жадность",
        "ganancia_extrema": "Экстрим Жадность",
        "estrutura_bos": "🏗️ BOS",
        "estrutura_choch": "🔄 CHoCH",
        "estrutura_indefinida": "⏳ Неопределено",
        "divergencia_obv_bull": "📈 OBV Бычий",
        "divergencia_obv_bear": "📉 OBV Медвежий",
        "divergencia_obv_none": "➖ Нет",
        "alinhamento_mtf": "🔄 Мульти-TF",
        "alinhamento_mtf_sim": "✅ Совпадает",
        "alinhamento_mtf_nao": "❌ Нет",
        "filtro_liquidez": "💧 Ликвидность",
        "liquidez_ok": "✅ Высокая",
        "liquidez_baixa": "⚠️ Низкая",
        "volume_direcional_bull": "📊 Бычий Объем",
        "volume_direcional_bear": "📊 Медвежий Объем",
        "volume_direcional_neutro": "📊 Нейтральный",
        "limiar_dinamico": "Дин. Порог",
        "modulo_mtf": "🔍 Мульти-TF",
        "modulo_estrutura": "🏗️ Структура SMC",
        "modulo_obv": "📊 Дивергенция OBV",
        "modulo_volume": "📈 Напр. Объем",
        "modulo_fg": "😱 Страх и Жадность",
        "modulo_liquidez": "💧 Ликвидность",
        "intervalos": {
            "1 Минута": "1m",
            "5 Минут": "5m",
            "15 Минут": "15m",
            "30 Минут": "30m",
            "1 Час": "1h",
            "4 Часа": "4h",
            "1 День": "1d",
            "1 Неделя": "1w"
        }
    },
    "日本語 (Japonês)": {
        "titulo": "🏦  BRICSVAULT PORTAL - SMCエンジン",
        "config_globais": "⚙️  設定",
        "selecione_cripto": "暗号通貨選択 (/USDT):",
        "tempo_grafico": "時間枠:",
        "modo_vivo": "リアルタイム監視",
        "intervalo_refresh": "更新間隔 (秒):",
        "preco_spot": "スポット価格",
        "variacao_24h": "24時間変動",
        "market_cap": "時価総額 (USD)",
        "stop_atr": "ATRストップ",
        "compra_forte": "🟢  強い買い",
        "venda_forte": "🔴  強い売り",
        "neutro": "🟡  中立",
        "spike_alta": "🚀  上昇スパイク",
        "spike_baixa": "💥  下降スパイク",
        "erro_dados": "データ不足。",
        "ctx_desconto": "フィボナッチディスカウントゾーン。",
        "ctx_premium": "フィボナッチプレミアムゾーン。",
        "ctx_neutro": "フィボナッチ中立ゾーン。",
        "ultima_atualizacao": "最終更新",
        "proximo_refresh": "次回更新まで",
        "segundos": "秒",
        "pontos_compra": "買いポイント",
        "pontos_venda": "売りポイント",
        "sinal_spike": "ボラティリティ",
        "grafico_titulo": "📈  価格チャート",
        "buscando_marketcap": "🔍  時価総額...",
        "marketcap_nao_disponivel": "利用不可",
        "idioma_label": "🌐  言語",
        "idioma_selecao": "言語選択:",
        "aviso_aquecimento": "⚠️ ウォームアップ",
        "backtest_titulo": "📊 バックテスト — 100シグナル",
        "backtest_compra": "買い",
        "backtest_venda": "売り",
        "backtest_total": "合計",
        "backtest_acertos": "成功",
        "backtest_taxa": "成功率",
        "backtest_profit_factor": "利益係数",
        "backtest_avg_win": "平均利益",
        "backtest_avg_loss": "平均損失",
        "backtest_historico": "履歴",
        "backtest_data": "日時",
        "backtest_sinal": "シグナル",
        "backtest_preco": "エントリー",
        "backtest_resultado": "結果",
        "backtest_acerto": "✅ 成功",
        "backtest_erro": "❌ 失敗",
        "backtest_metricas": "パフォーマンス",
        "poc_label": "POC",
        "vah_label": "VAH",
        "val_label": "VAL",
        "fear_greed_label": "😱 恐怖＆強欲",
        "medo_extremo": "極度の恐怖",
        "medo": "恐怖",
        "neutro_fg": "中立",
        "ganancia": "強欲",
        "ganancia_extrema": "極度の強欲",
        "estrutura_bos": "🏗️ BOS",
        "estrutura_choch": "🔄 CHoCH",
        "estrutura_indefinida": "⏳ 未定義",
        "divergencia_obv_bull": "📈 OBV強気",
        "divergencia_obv_bear": "📉 OBV弱気",
        "divergencia_obv_none": "➖ なし",
        "alinhamento_mtf": "🔄 マルチTF",
        "alinhamento_mtf_sim": "✅ 一致",
        "alinhamento_mtf_nao": "❌ 不一致",
        "filtro_liquidez": "💧 流動性",
        "liquidez_ok": "✅ 高い",
        "liquidez_baixa": "⚠️ 低い",
        "volume_direcional_bull": "📊 強気ボリューム",
        "volume_direcional_bear": "📊 弱気ボリューム",
        "volume_direcional_neutro": "📊 中立",
        "limiar_dinamico": "動的閾値",
        "modulo_mtf": "🔍 マルチTF",
        "modulo_estrutura": "🏗️ SMC構造",
        "modulo_obv": "📊 OBV発散",
        "modulo_volume": "📈 方向性出来高",
        "modulo_fg": "😱 恐怖＆強欲",
        "modulo_liquidez": "💧 流動性",
        "intervalos": {
            "1 分": "1m",
            "5 分": "5m",
            "15 分": "15m",
            "30 分": "30m",
            "1 時間": "1h",
            "4 時間": "4h",
            "1 日": "1d",
            "1 週間": "1w"
        }
    },
    "Deutsch (Alemão)": {
        "titulo": "🏦  BRICSVAULT PORTAL - SMC Engine",
        "config_globais": "⚙️  Einstellungen",
        "selecione_cripto": "Krypto wählen (/USDT):",
        "tempo_grafico": "Zeitrahmen:",
        "modo_vivo": "Echtzeit-Überwachung",
        "intervalo_refresh": "Intervall (Sek):",
        "preco_spot": "Spot-Preis",
        "variacao_24h": "24h Änderung",
        "market_cap": "Marktkap. (USD)",
        "stop_atr": "ATR-Stop",
        "compra_forte": "🟢  STARKER KAUF",
        "venda_forte": "🔴  STARKER VERKAUF",
        "neutro": "🟡  NEUTRAL",
        "spike_alta": "🚀  AUFWÄRTSSPIKE",
        "spike_baixa": "💥  ABWÄRTSSPIKE",
        "erro_dados": "Unzureichende Daten.",
        "ctx_desconto": "Fibonacci-Discount-Zone.",
        "ctx_premium": "Fibonacci-Premium-Zone.",
        "ctx_neutro": "Fibonacci-neutrale Zone.",
        "ultima_atualizacao": "Letzte Aktualisierung",
        "proximo_refresh": "Nächste in",
        "segundos": "Sekunden",
        "pontos_compra": "Kaufpunkte",
        "pontos_venda": "Verkaufspunkte",
        "sinal_spike": "Volatilitätsspike",
        "grafico_titulo": "📈  Preis-Chart",
        "buscando_marketcap": "🔍  Marktkap...",
        "marketcap_nao_disponivel": "Nicht verfügbar",
        "idioma_label": "🌐  Sprache",
        "idioma_selecao": "Sprache wählen:",
        "aviso_aquecimento": "⚠️ Aufwärmkerzen",
        "backtest_titulo": "📊 Backtesting — 100 Signale",
        "backtest_compra": "Kauf",
        "backtest_venda": "Verkauf",
        "backtest_total": "Gesamt",
        "backtest_acertos": "Treffer",
        "backtest_taxa": "Trefferquote",
        "backtest_profit_factor": "Profit-Faktor",
        "backtest_avg_win": "Ø Gewinn",
        "backtest_avg_loss": "Ø Verlust",
        "backtest_historico": "Verlauf",
        "backtest_data": "Datum",
        "backtest_sinal": "Signal",
        "backtest_preco": "Einstieg",
        "backtest_resultado": "Ergebnis",
        "backtest_acerto": "✅ Treffer",
        "backtest_erro": "❌ Fehler",
        "backtest_metricas": "Metriken",
        "poc_label": "POC",
        "vah_label": "VAH",
        "val_label": "VAL",
        "fear_greed_label": "😱 Fear & Greed",
        "medo_extremo": "Extreme Angst",
        "medo": "Angst",
        "neutro_fg": "Neutral",
        "ganancia": "Gier",
        "ganancia_extrema": "Extreme Gier",
        "estrutura_bos": "🏗️ BOS",
        "estrutura_choch": "🔄 CHoCH",
        "estrutura_indefinida": "⏳ Undefiniert",
        "divergencia_obv_bull": "📈 OBV Bullish",
        "divergencia_obv_bear": "📉 OBV Bearish",
        "divergencia_obv_none": "➖ Keine",
        "alinhamento_mtf": "🔄 Multi-TF",
        "alinhamento_mtf_sim": "✅ Ausgerichtet",
        "alinhamento_mtf_nao": "❌ Nicht",
        "filtro_liquidez": "💧 Liquidität",
        "liquidez_ok": "✅ Hoch",
        "liquidez_baixa": "⚠️ Niedrig",
        "volume_direcional_bull": "📊 Bullish Vol.",
        "volume_direcional_bear": "📊 Bearish Vol.",
        "volume_direcional_neutro": "📊 Neutral",
        "limiar_dinamico": "Dyn. Schwelle",
        "modulo_mtf": "🔍 Multi-TF",
        "modulo_estrutura": "🏗️ SMC Struktur",
        "modulo_obv": "📊 OBV Divergenz",
        "modulo_volume": "📈 Richtungsvol.",
        "modulo_fg": "😱 Fear & Greed",
        "modulo_liquidez": "💧 Liquidität",
        "intervalos": {
            "1 Minute": "1m",
            "5 Minuten": "5m",
            "15 Minuten": "15m",
            "30 Minuten": "30m",
            "1 Stunde": "1h",
            "4 Stunden": "4h",
            "1 Tag": "1d",
            "1 Woche": "1w"
        }
    },
    "한국어 (Coreano)": {
        "titulo": "🏦  BRICSVAULT PORTAL - SMC 엔진",
        "config_globais": "⚙️  설정",
        "selecione_cripto": "암호화폐 선택 (/USDT):",
        "tempo_grafico": "시간대:",
        "modo_vivo": "실시간 모니터링",
        "intervalo_refresh": "새로고침 (초):",
        "preco_spot": "현물 가격",
        "variacao_24h": "24시간 변동",
        "market_cap": "시가총액 (USD)",
        "stop_atr": "ATR 손절가",
        "compra_forte": "🟢  강력 매수",
        "venda_forte": "🔴  강력 매도",
        "neutro": "🟡  중립",
        "spike_alta": "🚀  상승 스파이크",
        "spike_baixa": "💥  하락 스파이크",
        "erro_dados": "데이터 부족.",
        "ctx_desconto": "피보나치 할인 영역.",
        "ctx_premium": "피보나치 프리미엄 영역.",
        "ctx_neutro": "피보나치 중립 영역.",
        "ultima_atualizacao": "마지막 업데이트",
        "proximo_refresh": "다음 새로고침",
        "segundos": "초",
        "pontos_compra": "매수 점수",
        "pontos_venda": "매도 점수",
        "sinal_spike": "변동성 스파이크",
        "grafico_titulo": "📈  가격 차트",
        "buscando_marketcap": "🔍  시가총액...",
        "marketcap_nao_disponivel": "사용 불가",
        "idioma_label": "🌐  언어",
        "idioma_selecao": "언어 선택:",
        "aviso_aquecimento": "⚠️ 워밍업 캔들",
        "backtest_titulo": "📊 백테스팅 — 100 시그널",
        "backtest_compra": "매수",
        "backtest_venda": "매도",
        "backtest_total": "총계",
        "backtest_acertos": "성공",
        "backtest_taxa": "성공률",
        "backtest_profit_factor": "수익 팩터",
        "backtest_avg_win": "평균 수익",
        "backtest_avg_loss": "평균 손실",
        "backtest_historico": "기록",
        "backtest_data": "날짜",
        "backtest_sinal": "시그널",
        "backtest_preco": "진입가",
        "backtest_resultado": "결과",
        "backtest_acerto": "✅ 성공",
        "backtest_erro": "❌ 실패",
        "backtest_metricas": "성과 지표",
        "poc_label": "POC",
        "vah_label": "VAH",
        "val_label": "VAL",
        "fear_greed_label": "😱 공포·탐욕",
        "medo_extremo": "극도의 공포",
        "medo": "공포",
        "neutro_fg": "중립",
        "ganancia": "탐욕",
        "ganancia_extrema": "극도의 탐욕",
        "estrutura_bos": "🏗️ BOS",
        "estrutura_choch": "🔄 CHoCH",
        "estrutura_indefinida": "⏳ 정의되지 않음",
        "divergencia_obv_bull": "📈 OBV 강세",
        "divergencia_obv_bear": "📉 OBV 약세",
        "divergencia_obv_none": "➖ 없음",
        "alinhamento_mtf": "🔄 멀티TF",
        "alinhamento_mtf_sim": "✅ 정렬됨",
        "alinhamento_mtf_nao": "❌ 정렬 안됨",
        "filtro_liquidez": "💧 유동성",
        "liquidez_ok": "✅ 높음",
        "liquidez_baixa": "⚠️ 낮음",
        "volume_direcional_bull": "📊 강세 거래량",
        "volume_direcional_bear": "📊 약세 거래량",
        "volume_direcional_neutro": "📊 중립",
        "limiar_dinamico": "동적 임계값",
        "modulo_mtf": "🔍 멀티TF",
        "modulo_estrutura": "🏗️ SMC 구조",
        "modulo_obv": "📊 OBV 다이버전스",
        "modulo_volume": "📈 방향성 거래량",
        "modulo_fg": "😱 공포·탐욕",
        "modulo_liquidez": "💧 유동성",
        "intervalos": {
            "1 분": "1m",
            "5 분": "5m",
            "15 분": "15m",
            "30 분": "30m",
            "1 시간": "1h",
            "4 시간": "4h",
            "1 일": "1d",
            "1 주": "1w"
        }
    },
    "العربية (Árabe)": {
        "titulo": "🏦  BRICSVAULT PORTAL - محرك SMC",
        "config_globais": "⚙️  الإعدادات",
        "selecione_cripto": "اختر عملة (/USDT):",
        "tempo_grafico": "الإطار الزمني:",
        "modo_vivo": "مراقبة مباشرة",
        "intervalo_refresh": "فاصل التحديث (ثانية):",
        "preco_spot": "السعر الفوري",
        "variacao_24h": "تغير 24 ساعة",
        "market_cap": "القيمة السوقية (USD)",
        "stop_atr": "وقف ATR",
        "compra_forte": "🟢  شراء قوي",
        "venda_forte": "🔴  بيع قوي",
        "neutro": "🟡  محايد",
        "spike_alta": "🚀  ارتفاع حاد",
        "spike_baixa": "💥  انخفاض حاد",
        "erro_dados": "بيانات غير كافية.",
        "ctx_desconto": "منطقة خصم فيبوناتشي.",
        "ctx_premium": "منطقة فيبوناتشي الممتازة.",
        "ctx_neutro": "منطقة فيبوناتشي المحايدة.",
        "ultima_atualizacao": "آخر تحديث",
        "proximo_refresh": "التالي خلال",
        "segundos": "ثانية",
        "pontos_compra": "نقاط الشراء",
        "pontos_venda": "نقاط البيع",
        "sinal_spike": "ارتفاع التقلب",
        "grafico_titulo": "📈  رسم بياني",
        "buscando_marketcap": "🔍  القيمة السوقية...",
        "marketcap_nao_disponivel": "غير متوفر",
        "idioma_label": "🌐  اللغة",
        "idioma_selecao": "اختر اللغة:",
        "aviso_aquecimento": "⚠️ شموع التسخين",
        "backtest_titulo": "📊 اختبار خلفي — 100 إشارة",
        "backtest_compra": "شراء",
        "backtest_venda": "بيع",
        "backtest_total": "المجموع",
        "backtest_acertos": "ناجحة",
        "backtest_taxa": "نسبة النجاح",
        "backtest_profit_factor": "عامل الربح",
        "backtest_avg_win": "متوسط الربح",
        "backtest_avg_loss": "متوسط الخسارة",
        "backtest_historico": "السجل",
        "backtest_data": "التاريخ",
        "backtest_sinal": "الإشارة",
        "backtest_preco": "سعر الدخول",
        "backtest_resultado": "النتيجة",
        "backtest_acerto": "✅ ناجح",
        "backtest_erro": "❌ فاشل",
        "backtest_metricas": "مقاييس الأداء",
        "poc_label": "POC",
        "vah_label": "VAH",
        "val_label": "VAL",
        "fear_greed_label": "😱 الخوف والطمع",
        "medo_extremo": "خوف شديد",
        "medo": "خوف",
        "neutro_fg": "محايد",
        "ganancia": "طمع",
        "ganancia_extrema": "طمع شديد",
        "estrutura_bos": "🏗️ BOS",
        "estrutura_choch": "🔄 CHoCH",
        "estrutura_indefinida": "⏳ غير محدد",
        "divergencia_obv_bull": "📈 OBV صاعد",
        "divergencia_obv_bear": "📉 OBV هابط",
        "divergencia_obv_none": "➖ لا يوجد",
        "alinhamento_mtf": "🔄 متعدد الأطر",
        "alinhamento_mtf_sim": "✅ متوافق",
        "alinhamento_mtf_nao": "❌ غير متوافق",
        "filtro_liquidez": "💧 السيولة",
        "liquidez_ok": "✅ مرتفعة",
        "liquidez_baixa": "⚠️ منخفضة",
        "volume_direcional_bull": "📊 حجم صاعد",
        "volume_direcional_bear": "📊 حجم هابط",
        "volume_direcional_neutro": "📊 محايد",
        "limiar_dinamico": "عتبة ديناميكية",
        "modulo_mtf": "🔍 متعدد الأطر",
        "modulo_estrutura": "🏗️ هيكل SMC",
        "modulo_obv": "📊 تباعد OBV",
        "modulo_volume": "📈 الحجم الاتجاهي",
        "modulo_fg": "😱 الخوف والطمع",
        "modulo_liquidez": "💧 السيولة",
        "intervalos": {
            "1 دقيقة": "1m",
            "5 دقائق": "5m",
            "15 دقيقة": "15m",
            "30 دقيقة": "30m",
            "1 ساعة": "1h",
            "4 ساعات": "4h",
            "1 يوم": "1d",
            "1 أسبوع": "1w"
        }
    },
    "বাংলা (Bengali)": {
        "titulo": "🏦  BRICSVAULT PORTAL - SMC ইঞ্জিন",
        "config_globais": "⚙️  সেটিংস",
        "selecione_cripto": "ক্রিপ্টো বাছুন (/USDT):",
        "tempo_grafico": "টাইমফ্রেম:",
        "modo_vivo": "লাইভ মনিটরিং",
        "intervalo_refresh": "রিফ্রেশ (সেকেন্ড):",
        "preco_spot": "স্পট মূল্য",
        "variacao_24h": "২৪ঘণ্টা পরিবর্তন",
        "market_cap": "মার্কেট ক্যাপ (USD)",
        "stop_atr": "ATR স্টপ",
        "compra_forte": "🟢  শক্তিশালী ক্রয়",
        "venda_forte": "🔴  শক্তিশালী বিক্রয়",
        "neutro": "🟡  নিরপেক্ষ",
        "spike_alta": "🚀  ঊর্ধ্বমুখী স্পাইক",
        "spike_baixa": "💥  নিম্নমুখী স্পাইক",
        "erro_dados": "অপর্যাপ্ত ডেটা।",
        "ctx_desconto": "ফিবোনাচি ডিসকাউন্ট।",
        "ctx_premium": "ফিবোনাচি প্রিমিয়াম।",
        "ctx_neutro": "ফিবোনাচি নিরপেক্ষ।",
        "ultima_atualizacao": "শেষ আপডেট",
        "proximo_refresh": "পরবর্তী",
        "segundos": "সেকেন্ড",
        "pontos_compra": "ক্রয় পয়েন্ট",
        "pontos_venda": "বিক্রয় পয়েন্ট",
        "sinal_spike": "অস্থিরতা স্পাইক",
        "grafico_titulo": "📈  মূল্য চার্ট",
        "buscando_marketcap": "🔍  মার্কেট ক্যাপ...",
        "marketcap_nao_disponivel": "উপলব্ধ নয়",
        "idioma_label": "🌐  ভাষা",
        "idioma_selecao": "ভাষা বাছুন:",
        "aviso_aquecimento": "⚠️ ওয়ার্ম-আপ",
        "backtest_titulo": "📊 ব্যাকটেস্টিং — ১০০ সিগন্যাল",
        "backtest_compra": "ক্রয়",
        "backtest_venda": "বিক্রয়",
        "backtest_total": "মোট",
        "backtest_acertos": "সফল",
        "backtest_taxa": "সাফল্যের হার",
        "backtest_profit_factor": "লাভ ফ্যাক্টর",
        "backtest_avg_win": "গড় লাভ",
        "backtest_avg_loss": "গড় ক্ষতি",
        "backtest_historico": "ইতিহাস",
        "backtest_data": "তারিখ",
        "backtest_sinal": "সিগন্যাল",
        "backtest_preco": "প্রবেশ মূল্য",
        "backtest_resultado": "ফলাফল",
        "backtest_acerto": "✅ সফল",
        "backtest_erro": "❌ ব্যর্থ",
        "backtest_metricas": "কর্মক্ষমতা",
        "poc_label": "POC",
        "vah_label": "VAH",
        "val_label": "VAL",
        "fear_greed_label": "😱 ভয় ও লোভ",
        "medo_extremo": "চরম ভয়",
        "medo": "ভয়",
        "neutro_fg": "নিরপেক্ষ",
        "ganancia": "লোভ",
        "ganancia_extrema": "চরম লোভ",
        "estrutura_bos": "🏗️ BOS",
        "estrutura_choch": "🔄 CHoCH",
        "estrutura_indefinida": "⏳ অনির্ধারিত",
        "divergencia_obv_bull": "📈 OBV বুলিশ",
        "divergencia_obv_bear": "📉 OBV বিয়ারিশ",
        "divergencia_obv_none": "➖ নেই",
        "alinhamento_mtf": "🔄 মাল্টি-TF",
        "alinhamento_mtf_sim": "✅ সংযুক্ত",
        "alinhamento_mtf_nao": "❌ নয়",
        "filtro_liquidez": "💧 তরলতা",
        "liquidez_ok": "✅ উচ্চ",
        "liquidez_baixa": "⚠️ নিম্ন",
        "volume_direcional_bull": "📊 বুলিশ ভলিউম",
        "volume_direcional_bear": "📊 বিয়ারিশ ভলিউম",
        "volume_direcional_neutro": "📊 নিরপেক্ষ",
        "limiar_dinamico": "গতিশীল সীমা",
        "modulo_mtf": "🔍 মাল্টি-TF",
        "modulo_estrutura": "🏗️ SMC কাঠামো",
        "modulo_obv": "📊 OBV ডাইভারজেন্স",
        "modulo_volume": "📈 দিকনির্দেশক ভলিউম",
        "modulo_fg": "😱 ভয় ও লোভ",
        "modulo_liquidez": "💧 তরলতা",
        "intervalos": {
            "১ মিনিট": "1m",
            "৫ মিনিট": "5m",
            "১৫ মিনিট": "15m",
            "৩০ মিনিট": "30m",
            "১ ঘন্টা": "1h",
            "৪ ঘন্টা": "4h",
            "১ দিন": "1d",
            "১ সপ্তাহ": "1w"
        }
    },
    "Türkçe (Turco)": {
        "titulo": "🏦  BRICSVAULT PORTAL - SMC Motoru",
        "config_globais": "⚙️  Ayarlar",
        "selecione_cripto": "Kripto Seç (/USDT):",
        "tempo_grafico": "Zaman Dilimi:",
        "modo_vivo": "Canlı İzleme",
        "intervalo_refresh": "Yenileme (Saniye):",
        "preco_spot": "Spot Fiyat",
        "variacao_24h": "24s Değişim",
        "market_cap": "Piyasa Değeri (USD)",
        "stop_atr": "ATR Stop",
        "compra_forte": "🟢  GÜÇLÜ AL",
        "venda_forte": "🔴  GÜÇLÜ SAT",
        "neutro": "🟡  NÖTR",
        "spike_alta": "🚀  YÜKSELİŞ",
        "spike_baixa": "💥  DÜŞÜŞ",
        "erro_dados": "Yetersiz veri.",
        "ctx_desconto": "Fibonacci İndirim Bölgesi.",
        "ctx_premium": "Fibonacci Premium Bölgesi.",
        "ctx_neutro": "Fibonacci Nötr Bölge.",
        "ultima_atualizacao": "Son Güncelleme",
        "proximo_refresh": "Sonraki",
        "segundos": "saniye",
        "pontos_compra": "Alış Puanı",
        "pontos_venda": "Satış Puanı",
        "sinal_spike": "Volatilite",
        "grafico_titulo": "📈  Fiyat Grafiği",
        "buscando_marketcap": "🔍  Piyasa Değeri...",
        "marketcap_nao_disponivel": "Mevcut değil",
        "idioma_label": "🌐  Dil",
        "idioma_selecao": "Dil seçin:",
        "aviso_aquecimento": "⚠️ Isınma mumları",
        "backtest_titulo": "📊 Geriye Dönük Test — 100 Sinyal",
        "backtest_compra": "Alış",
        "backtest_venda": "Satış",
        "backtest_total": "Toplam",
        "backtest_acertos": "Başarılı",
        "backtest_taxa": "Başarı Oranı",
        "backtest_profit_factor": "Kâr Faktörü",
        "backtest_avg_win": "Ort. Kâr",
        "backtest_avg_loss": "Ort. Zarar",
        "backtest_historico": "Geçmiş",
        "backtest_data": "Tarih",
        "backtest_sinal": "Sinyal",
        "backtest_preco": "Giriş",
        "backtest_resultado": "Sonuç",
        "backtest_acerto": "✅ Başarılı",
        "backtest_erro": "❌ Başarısız",
        "backtest_metricas": "Metrikler",
        "poc_label": "POC",
        "vah_label": "VAH",
        "val_label": "VAL",
        "fear_greed_label": "😱 Korku & Açgözlülük",
        "medo_extremo": "Aşırı Korku",
        "medo": "Korku",
        "neutro_fg": "Nötr",
        "ganancia": "Açgözlülük",
        "ganancia_extrema": "Aşırı Açgözlülük",
        "estrutura_bos": "🏗️ BOS",
        "estrutura_choch": "🔄 CHoCH",
        "estrutura_indefinida": "⏳ Belirsiz",
        "divergencia_obv_bull": "📈 OBV Yükseliş",
        "divergencia_obv_bear": "📉 OBV Düşüş",
        "divergencia_obv_none": "➖ Yok",
        "alinhamento_mtf": "🔄 Çoklu TF",
        "alinhamento_mtf_sim": "✅ Uyumlu",
        "alinhamento_mtf_nao": "❌ Uyumsuz",
        "filtro_liquidez": "💧 Likidite",
        "liquidez_ok": "✅ Yüksek",
        "liquidez_baixa": "⚠️ Düşük",
        "volume_direcional_bull": "📊 Yükseliş Hacmi",
        "volume_direcional_bear": "📊 Düşüş Hacmi",
        "volume_direcional_neutro": "📊 Nötr",
        "limiar_dinamico": "Dinamik Eşik",
        "modulo_mtf": "🔍 Çoklu TF",
        "modulo_estrutura": "🏗️ SMC Yapı",
        "modulo_obv": "📊 OBV Uyumsuzluk",
        "modulo_volume": "📈 Yönlü Hacim",
        "modulo_fg": "😱 Korku & Açgözlülük",
        "modulo_liquidez": "💧 Likidite",
        "intervalos": {
            "1 Dakika": "1m",
            "5 Dakika": "5m",
            "15 Dakika": "15m",
            "30 Dakika": "30m",
            "1 Saat": "1h",
            "4 Saat": "4h",
            "1 Gün": "1d",
            "1 Hafta": "1w"
        }
    },
    "Tiếng Việt (Vietnamita)": {
        "titulo": "🏦  BRICSVAULT PORTAL - Động Cơ SMC",
        "config_globais": "⚙️  Cài Đặt",
        "selecione_cripto": "Chọn Crypto (/USDT):",
        "tempo_grafico": "Khung Thời Gian:",
        "modo_vivo": "Giám Sát Live",
        "intervalo_refresh": "Làm Mới (Giây):",
        "preco_spot": "Giá Spot",
        "variacao_24h": "Biến Động 24h",
        "market_cap": "Vốn Hóa (USD)",
        "stop_atr": "Cắt Lỗ ATR",
        "compra_forte": "🟢  MUA MẠNH",
        "venda_forte": "🔴  BÁN MẠNH",
        "neutro": "🟡  TRUNG LẬP",
        "spike_alta": "🚀  TĂNG ĐỘT BIẾN",
        "spike_baixa": "💥  GIẢM ĐỘT BIẾN",
        "erro_dados": "Dữ liệu không đủ.",
        "ctx_desconto": "Vùng Chiết Khấu Fibonacci.",
        "ctx_premium": "Vùng Premium Fibonacci.",
        "ctx_neutro": "Vùng Trung Lập Fibonacci.",
        "ultima_atualizacao": "Cập Nhật Lần Cuối",
        "proximo_refresh": "Làm mới sau",
        "segundos": "giây",
        "pontos_compra": "Điểm Mua",
        "pontos_venda": "Điểm Bán",
        "sinal_spike": "Đột Biến",
        "grafico_titulo": "📈  Biểu Đồ Giá",
        "buscando_marketcap": "🔍  Vốn Hóa...",
        "marketcap_nao_disponivel": "Không có",
        "idioma_label": "🌐  Ngôn Ngữ",
        "idioma_selecao": "Chọn ngôn ngữ:",
        "aviso_aquecimento": "⚠️ Nến khởi động",
        "backtest_titulo": "📊 Backtesting — 100 Tín Hiệu",
        "backtest_compra": "Mua",
        "backtest_venda": "Bán",
        "backtest_total": "Tổng",
        "backtest_acertos": "Thành Công",
        "backtest_taxa": "Tỷ Lệ",
        "backtest_profit_factor": "Hệ Số Lợi Nhuận",
        "backtest_avg_win": "Lãi TB",
        "backtest_avg_loss": "Lỗ TB",
        "backtest_historico": "Lịch Sử",
        "backtest_data": "Ngày",
        "backtest_sinal": "Tín Hiệu",
        "backtest_preco": "Giá Vào",
        "backtest_resultado": "Kết Quả",
        "backtest_acerto": "✅ Thành Công",
        "backtest_erro": "❌ Thất Bại",
        "backtest_metricas": "Chỉ Số",
        "poc_label": "POC",
        "vah_label": "VAH",
        "val_label": "VAL",
        "fear_greed_label": "😱 Sợ Hãi & Tham Lam",
        "medo_extremo": "Sợ Cực Độ",
        "medo": "Sợ Hãi",
        "neutro_fg": "Trung Lập",
        "ganancia": "Tham Lam",
        "ganancia_extrema": "Tham Cực Độ",
        "estrutura_bos": "🏗️ BOS",
        "estrutura_choch": "🔄 CHoCH",
        "estrutura_indefinida": "⏳ Không XĐ",
        "divergencia_obv_bull": "📈 OBV Tăng",
        "divergencia_obv_bear": "📉 OBV Giảm",
        "divergencia_obv_none": "➖ Không",
        "alinhamento_mtf": "🔄 Đa TF",
        "alinhamento_mtf_sim": "✅ Căn Chỉnh",
        "alinhamento_mtf_nao": "❌ Không",
        "filtro_liquidez": "💧 Thanh Khoản",
        "liquidez_ok": "✅ Cao",
        "liquidez_baixa": "⚠️ Thấp",
        "volume_direcional_bull": "📊 KL Tăng",
        "volume_direcional_bear": "📊 KL Giảm",
        "volume_direcional_neutro": "📊 Trung Lập",
        "limiar_dinamico": "Ngưỡng Động",
        "modulo_mtf": "🔍 Đa TF",
        "modulo_estrutura": "🏗️ Cấu Trúc SMC",
        "modulo_obv": "📊 Phân Kỳ OBV",
        "modulo_volume": "📈 KL Hướng",
        "modulo_fg": "😱 Sợ & Tham",
        "modulo_liquidez": "💧 Thanh Khoản",
        "intervalos": {
            "1 Phút": "1m",
            "5 Phút": "5m",
            "15 Phút": "15m",
            "30 Phút": "30m",
            "1 Giờ": "1h",
            "4 Giờ": "4h",
            "1 Ngày": "1d",
            "1 Tuần": "1w"
        }
    },
    "Italiano (Italiano)": {
        "titulo": "🏦  BRICSVAULT PORTAL - Motore SMC",
        "config_globais": "⚙️  Impostazioni",
        "selecione_cripto": "Seleziona Crypto (/USDT):",
        "tempo_grafico": "Timeframe:",
        "modo_vivo": "Monitoraggio Live",
        "intervalo_refresh": "Intervallo (Secondi):",
        "preco_spot": "Prezzo Spot",
        "variacao_24h": "Variazione 24h",
        "market_cap": "Cap. Mercato (USD)",
        "stop_atr": "Stop ATR",
        "compra_forte": "🟢  ACQUISTO FORTE",
        "venda_forte": "🔴  VENDITA FORTE",
        "neutro": "🟡  NEUTRO",
        "spike_alta": "🚀  SPIKE RIALZISTA",
        "spike_baixa": "💥  SPIKE RIBASSISTA",
        "erro_dados": "Dati insufficienti.",
        "ctx_desconto": "Zona Sconto Fibonacci.",
        "ctx_premium": "Zona Premium Fibonacci.",
        "ctx_neutro": "Zona Neutra Fibonacci.",
        "ultima_atualizacao": "Ultimo Aggiornamento",
        "proximo_refresh": "Prossimo tra",
        "segundos": "secondi",
        "pontos_compra": "Punti Acquisto",
        "pontos_venda": "Punti Vendita",
        "sinal_spike": "Spike Volatilità",
        "grafico_titulo": "📈  Grafico Prezzi",
        "buscando_marketcap": "🔍  Market Cap...",
        "marketcap_nao_disponivel": "Non disponibile",
        "idioma_label": "🌐  Lingua",
        "idioma_selecao": "Seleziona lingua:",
        "aviso_aquecimento": "⚠️ Candele riscaldamento",
        "backtest_titulo": "📊 Backtesting — 100 Segnali",
        "backtest_compra": "Acquisto",
        "backtest_venda": "Vendita",
        "backtest_total": "Totale",
        "backtest_acertos": "Successi",
        "backtest_taxa": "Tasso Successo",
        "backtest_profit_factor": "Fattore Profitto",
        "backtest_avg_win": "Guadagno Medio",
        "backtest_avg_loss": "Perdita Media",
        "backtest_historico": "Cronologia",
        "backtest_data": "Data",
        "backtest_sinal": "Segnale",
        "backtest_preco": "Prezzo Entrata",
        "backtest_resultado": "Risultato",
        "backtest_acerto": "✅ Successo",
        "backtest_erro": "❌ Fallito",
        "backtest_metricas": "Metriche",
        "poc_label": "POC",
        "vah_label": "VAH",
        "val_label": "VAL",
        "fear_greed_label": "😱 Paura & Avidità",
        "medo_extremo": "Paura Estrema",
        "medo": "Paura",
        "neutro_fg": "Neutro",
        "ganancia": "Avidità",
        "ganancia_extrema": "Avidità Estrema",
        "estrutura_bos": "🏗️ BOS",
        "estrutura_choch": "🔄 CHoCH",
        "estrutura_indefinida": "⏳ Indefinito",
        "divergencia_obv_bull": "📈 OBV Rialzista",
        "divergencia_obv_bear": "📉 OBV Ribassista",
        "divergencia_obv_none": "➖ Nessuna",
        "alinhamento_mtf": "🔄 Multi-TF",
        "alinhamento_mtf_sim": "✅ Allineato",
        "alinhamento_mtf_nao": "❌ Non Allineato",
        "filtro_liquidez": "💧 Liquidità",
        "liquidez_ok": "✅ Alta",
        "liquidez_baixa": "⚠️ Bassa",
        "volume_direcional_bull": "📊 Vol. Rialzista",
        "volume_direcional_bear": "📊 Vol. Ribassista",
        "volume_direcional_neutro": "📊 Neutro",
        "limiar_dinamico": "Soglia Dinamica",
        "modulo_mtf": "🔍 Multi-TF",
        "modulo_estrutura": "🏗️ Struttura SMC",
        "modulo_obv": "📊 Divergenza OBV",
        "modulo_volume": "📈 Vol. Direzionale",
        "modulo_fg": "😱 Paura & Avidità",
        "modulo_liquidez": "💧 Liquidità",
        "intervalos": {
            "1 Minuto": "1m",
            "5 Minuti": "5m",
            "15 Minuti": "15m",
            "30 Minuti": "30m",
            "1 Ora": "1h",
            "4 Ore": "4h",
            "1 Giorno": "1d",
            "1 Settimana": "1w"
        }
    },
    "ไทย (Tailandês)": {
        "titulo": "🏦  BRICSVAULT PORTAL - เครื่องมือ SMC",
        "config_globais": "⚙️  การตั้งค่า",
        "selecione_cripto": "เลือกคริปโต (/USDT):",
        "tempo_grafico": "กรอบเวลา:",
        "modo_vivo": "ติดตามเรียลไทม์",
        "intervalo_refresh": "รีเฟรช (วินาที):",
        "preco_spot": "ราคาสปอต",
        "variacao_24h": "เปลี่ยน 24ชม.",
        "market_cap": "มูลค่าตลาด (USD)",
        "stop_atr": "หยุด ATR",
        "compra_forte": "🟢  ซื้อแข็งแกร่ง",
        "venda_forte": "🔴  ขายแข็งแกร่ง",
        "neutro": "🟡  เป็นกลาง",
        "spike_alta": "🚀  พุ่งขึ้น",
        "spike_baixa": "💥  ดิ่งลง",
        "erro_dados": "ข้อมูลไม่เพียงพอ",
        "ctx_desconto": "เขตส่วนลดฟิโบ",
        "ctx_premium": "เขตพรีเมียมฟิโบ",
        "ctx_neutro": "เขตเป็นกลางฟิโบ",
        "ultima_atualizacao": "อัปเดตล่าสุด",
        "proximo_refresh": "ถัดไปใน",
        "segundos": "วินาที",
        "pontos_compra": "คะแนนซื้อ",
        "pontos_venda": "คะแนนขาย",
        "sinal_spike": "ความผันผวน",
        "grafico_titulo": "📈  กราฟราคา",
        "buscando_marketcap": "🔍  มูลค่าตลาด...",
        "marketcap_nao_disponivel": "ไม่พร้อมใช้งาน",
        "idioma_label": "🌐  ภาษา",
        "idioma_selecao": "เลือกภาษา:",
        "aviso_aquecimento": "⚠️ แท่งเทียนอุ่น",
        "backtest_titulo": "📊 ทดสอบย้อนหลัง — 100 สัญญาณ",
        "backtest_compra": "ซื้อ",
        "backtest_venda": "ขาย",
        "backtest_total": "รวม",
        "backtest_acertos": "สำเร็จ",
        "backtest_taxa": "อัตราสำเร็จ",
        "backtest_profit_factor": "ปัจจัยกำไร",
        "backtest_avg_win": "กำไรเฉลี่ย",
        "backtest_avg_loss": "ขาดทุนเฉลี่ย",
        "backtest_historico": "ประวัติ",
        "backtest_data": "วันที่",
        "backtest_sinal": "สัญญาณ",
        "backtest_preco": "ราคาเข้า",
        "backtest_resultado": "ผลลัพธ์",
        "backtest_acerto": "✅ สำเร็จ",
        "backtest_erro": "❌ ล้มเหลว",
        "backtest_metricas": "ตัวชี้วัด",
        "poc_label": "POC",
        "vah_label": "VAH",
        "val_label": "VAL",
        "fear_greed_label": "😱 กลัวและโลภ",
        "medo_extremo": "กลัวสุดขีด",
        "medo": "กลัว",
        "neutro_fg": "เป็นกลาง",
        "ganancia": "โลภ",
        "ganancia_extrema": "โลภสุดขีด",
        "estrutura_bos": "🏗️ BOS",
        "estrutura_choch": "🔄 CHoCH",
        "estrutura_indefinida": "⏳ ไม่ระบุ",
        "divergencia_obv_bull": "📈 OBV ขาขึ้น",
        "divergencia_obv_bear": "📉 OBV ขาลง",
        "divergencia_obv_none": "➖ ไม่มี",
        "alinhamento_mtf": "🔄 หลาย TF",
        "alinhamento_mtf_sim": "✅ สอดคล้อง",
        "alinhamento_mtf_nao": "❌ ไม่สอดคล้อง",
        "filtro_liquidez": "💧 สภาพคล่อง",
        "liquidez_ok": "✅ สูง",
        "liquidez_baixa": "⚠️ ต่ำ",
        "volume_direcional_bull": "📊 วอลุ่มขาขึ้น",
        "volume_direcional_bear": "📊 วอลุ่มขาลง",
        "volume_direcional_neutro": "📊 เป็นกลาง",
        "limiar_dinamico": "เกณฑ์พลวัต",
        "modulo_mtf": "🔍 หลาย TF",
        "modulo_estrutura": "🏗️ โครงสร้าง SMC",
        "modulo_obv": "📊 การเบี่ยงเบน OBV",
        "modulo_volume": "📈 วอลุ่มทิศทาง",
        "modulo_fg": "😱 กลัวและโลภ",
        "modulo_liquidez": "💧 สภาพคล่อง",
        "intervalos": {
            "1 นาที": "1m",
            "5 นาที": "5m",
            "15 นาที": "15m",
            "30 นาที": "30m",
            "1 ชั่วโมง": "1h",
            "4 ชั่วโมง": "4h",
            "1 วัน": "1d",
            "1 สัปดาห์": "1w"
        }
    },
    "Bahasa Indonesia (Indonésio)": {
        "titulo": "🏦  BRICSVAULT PORTAL - Mesin SMC",
        "config_globais": "⚙️  Pengaturan",
        "selecione_cripto": "Pilih Kripto (/USDT):",
        "tempo_grafico": "Jangka Waktu:",
        "modo_vivo": "Pantauan Langsung",
        "intervalo_refresh": "Interval (Detik):",
        "preco_spot": "Harga Spot",
        "variacao_24h": "Perubahan 24j",
        "market_cap": "Kap. Pasar (USD)",
        "stop_atr": "Stop ATR",
        "compra_forte": "🟢  BELI KUAT",
        "venda_forte": "🔴  JUAL KUAT",
        "neutro": "🟡  NETRAL",
        "spike_alta": "🚀  LONJAKAN NAIK",
        "spike_baixa": "💥  LONJAKAN TURUN",
        "erro_dados": "Data tidak cukup.",
        "ctx_desconto": "Zona Diskon Fibonacci.",
        "ctx_premium": "Zona Premium Fibonacci.",
        "ctx_neutro": "Zona Netral Fibonacci.",
        "ultima_atualizacao": "Update Terakhir",
        "proximo_refresh": "Berikutnya",
        "segundos": "detik",
        "pontos_compra": "Poin Beli",
        "pontos_venda": "Poin Jual",
        "sinal_spike": "Lonjakan",
        "grafico_titulo": "📈  Grafik Harga",
        "buscando_marketcap": "🔍  Kap. Pasar...",
        "marketcap_nao_disponivel": "Tak tersedia",
        "idioma_label": "🌐  Bahasa",
        "idioma_selecao": "Pilih bahasa:",
        "aviso_aquecimento": "⚠️ Lilin pemanasan",
        "backtest_titulo": "📊 Backtesting — 100 Sinyal",
        "backtest_compra": "Beli",
        "backtest_venda": "Jual",
        "backtest_total": "Total",
        "backtest_acertos": "Berhasil",
        "backtest_taxa": "Tingkat Sukses",
        "backtest_profit_factor": "Faktor Laba",
        "backtest_avg_win": "Laba Rata2",
        "backtest_avg_loss": "Rugi Rata2",
        "backtest_historico": "Riwayat",
        "backtest_data": "Tanggal",
        "backtest_sinal": "Sinyal",
        "backtest_preco": "Harga Masuk",
        "backtest_resultado": "Hasil",
        "backtest_acerto": "✅ Berhasil",
        "backtest_erro": "❌ Gagal",
        "backtest_metricas": "Metrik",
        "poc_label": "POC",
        "vah_label": "VAH",
        "val_label": "VAL",
        "fear_greed_label": "😱 Takut & Serakah",
        "medo_extremo": "Takut Ekstrem",
        "medo": "Takut",
        "neutro_fg": "Netral",
        "ganancia": "Serakah",
        "ganancia_extrema": "Serakah Ekstrem",
        "estrutura_bos": "🏗️ BOS",
        "estrutura_choch": "🔄 CHoCH",
        "estrutura_indefinida": "⏳ Tak Pasti",
        "divergencia_obv_bull": "📈 OBV Bullish",
        "divergencia_obv_bear": "📉 OBV Bearish",
        "divergencia_obv_none": "➖ Tidak Ada",
        "alinhamento_mtf": "🔄 Multi-TF",
        "alinhamento_mtf_sim": "✅ Selaras",
        "alinhamento_mtf_nao": "❌ Tidak",
        "filtro_liquidez": "💧 Likuiditas",
        "liquidez_ok": "✅ Tinggi",
        "liquidez_baixa": "⚠️ Rendah",
        "volume_direcional_bull": "📊 Vol. Bullish",
        "volume_direcional_bear": "📊 Vol. Bearish",
        "volume_direcional_neutro": "📊 Netral",
        "limiar_dinamico": "Ambang Dinamis",
        "modulo_mtf": "🔍 Multi-TF",
        "modulo_estrutura": "🏗️ Struktur SMC",
        "modulo_obv": "📊 Divergensi OBV",
        "modulo_volume": "📈 Vol. Arah",
        "modulo_fg": "😱 Takut & Serakah",
        "modulo_liquidez": "💧 Likuiditas",
        "intervalos": {
            "1 Menit": "1m",
            "5 Menit": "5m",
            "15 Menit": "15m",
            "30 Menit": "30m",
            "1 Jam": "1h",
            "4 Jam": "4h",
            "1 Hari": "1d",
            "1 Minggu": "1w"
        }
    }
}

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
# MÓDULO 1: ANÁLISE MULTI-TIMEFRAME (MTF)
def carregar_dados_mtf(simbolo_id, timeframe):
    """Carrega dados para um timeframe específico para MTF."""
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
    """
    Confirma se timeframe atual está alinhado com timeframes superiores.
    Retorna: (alinhado_bool, peso_mtf, detalhes_dict)
    """
    mapa_tf_superior = {
        '1m': ['15m', '1h'],
        '5m': ['30m', '4h'],
        '15m': ['1h', '4h'],
        '30m': ['1h', '4h'],
        '1h': ['4h', '1d'],
        '4h': ['1d', '1w'],
        '1d': ['1w', '1w'],
        '1w': ['1w', '1w']
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

        if u['ssl_dir'] == 1:
            score_tf += 1
        else:
            score_tf -= 1

        if u['MACD_HIST'] > 0:
            score_tf += 1
        else:
            score_tf -= 1

        if not np.isnan(u.get('OBV_Aceleracao', 0)):
            if u['OBV_Aceleracao'] > 0:
                score_tf += 1
            else:
                score_tf -= 1

        detalhes[tf] = 'bullish' if score_tf >= 2 else ('bearish' if score_tf <= -2 else 'neutral')
        if score_tf >= 1:
            alinhamentos += 1
        elif score_tf <= -1:
            alinhamentos -= 1

    peso_mtf = alinhamentos * 1.25
    return alinhamentos >= 1, peso_mtf, detalhes


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO 2: ANÁLISE DE ESTRUTURA SMC (BOS/CHoCH)
def detectar_estrutura_smc(df):
    """
    Detecta Break of Structure (BOS) e Change of Character (CHoCH).
    Usa swing highs/lows para identificar quebras de estrutura.
    """
    if len(df) < 50:
        return 'INDEFINIDO', 0.0

    df_recente = df.iloc[-60:]
    high = df_recente['high'].values
    low = df_recente['low'].values
    close = df_recente['close'].values

    # Encontrar swing highs e lows (pivôs de 5 velas)
    swing_highs = []
    swing_lows = []
    for i in range(2, len(df_recente) - 2):
        if high[i] > high[i-1] and high[i] > high[i-2] and high[i] > high[i+1] and high[i] > high[i+2]:
            swing_highs.append((i, high[i]))
        if low[i] < low[i-1] and low[i] < low[i-2] and low[i] < low[i+1] and low[i] < low[i+2]:
            swing_lows.append((i, low[i]))

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return 'INDEFINIDO', 0.0

    # Analisar últimos 2 swing highs e 2 swing lows
    ultimos_highs = swing_highs[-2:]
    ultimos_lows = swing_lows[-2:]

    preco_atual = close[-1]

    # BOS Bullish: preço rompe último swing high
    if len(ultimos_highs) >= 2:
        ultimo_sh = ultimos_highs[-1][1]
        penultimo_sh = ultimos_highs[-2][1]
        if preco_atual > ultimo_sh and ultimo_sh > penultimo_sh:
            return 'BOS', 3.5

    # BOS Bearish: preço rompe último swing low
    if len(ultimos_lows) >= 2:
        ultimo_sl = ultimos_lows[-1][1]
        penultimo_sl = ultimos_lows[-2][1]
        if preco_atual < ultimo_sl and ultimo_sl < penultimo_sl:
            return 'BOS', -3.5

    # CHoCH Bullish: preço faz fundo mais alto e rompe estrutura anterior
    if len(ultimos_lows) >= 2 and len(ultimos_highs) >= 1:
        if ultimos_lows[-1][1] > ultimos_lows[-2][1]:
            if preco_atual > ultimos_highs[-1][1]:
                return 'CHoCH', 3.0

    # CHoCH Bearish: preço faz topo mais baixo e rompe estrutura anterior
    if len(ultimos_highs) >= 2 and len(ultimos_lows) >= 1:
        if ultimos_highs[-1][1] < ultimos_highs[-2][1]:
            if preco_atual < ultimos_lows[-1][1]:
                return 'CHoCH', -3.0

    # Verificar tendência pela direção dos pivôs
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
    """
    Detecta divergência entre OBV e Preço.
    Bullish: Preço faz fundo menor, OBV faz fundo maior.
    Bearish: Preço faz topo maior, OBV faz topo menor.
    """
    if len(df) < periodo:
        return 'NONE', 0.0

    df_window = df.iloc[-periodo:]
    preco = df_window['close'].values
    obv = df_window['OBV'].values

    # Encontrar máximos e mínimos na janela (simplificado)
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

    # Divergência Bearish: preço faz topo maior, OBV faz topo menor
    if preco_max_2 > preco_max_1 and obv_max_2 < obv_max_1:
        return 'BEARISH', -3.0

    # Divergência Bullish: preço faz fundo menor, OBV faz fundo maior
    if preco_min_2 < preco_min_1 and obv_min_2 > obv_min_1:
        return 'BULLISH', 3.0

    return 'NONE', 0.0


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO 4: VOLUME DIRECIONAL
def calcular_volume_direcional(df, periodo=15):
    """
    Compara volume em candles de alta vs baixa.
    Retorna: ratio (>1 = bullish, <1 = bearish), peso
    """
    velas_alta = df['close'] > df['open']
    velas_baixa = df['close'] < df['open']

    vol_alta = df.loc[velas_alta, 'volume'].tail(periodo).mean()
    vol_baixa = df.loc[velas_baixa, 'volume'].tail(periodo).mean()

    if pd.isna(vol_alta):
        vol_alta = 0
    if pd.isna(vol_baixa):
        vol_baixa = 0

    if vol_baixa > 0:
        ratio = vol_alta / vol_baixa
    else:
        ratio = 2.0 if vol_alta > 0 else 1.0

    if ratio > 1.5:
        return 'BULLISH', 2.0
    elif ratio < 0.67:
        return 'BEARISH', -2.0
    elif ratio > 1.2:
        return 'LEAN_BULLISH', 1.0
    elif ratio < 0.83:
        return 'LEAN_BEARISH', -1.0
    else:
        return 'NEUTRO', 0.0


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO 5: FILTRO DE LIQUIDEZ
def filtro_liquidez(timestamp):
    """
    Evita sinais em horários de baixa liquidez.
    UTC: Sobreposição Londres-NY = 13-17h (melhor liquidez)
    """
    hora_utc = timestamp.hour

    # Horários de alta liquidez (sobreposição sessões)
    if 8 <= hora_utc <= 21:
        return True, "Alta liquidez - Sessões Principais"
    # Média liquidez
    elif hora_utc in [6, 7, 22, 23]:
        return True, "Liquidez moderada"
    # Baixa liquidez (sessão asiática profunda)
    else:
        return False, "Baixa liquidez - Sessão Asiática"


# ─────────────────────────────────────────────────────────────────────────────
# MÓDULO 6: INTEGRAÇÃO FEAR & GREED
def integrar_fear_greed(fg_valor):
    """
    Filtro contrário: comprar no medo, vender na ganância.
    """
    if fg_valor is None:
        return 0.0, 0.0

    if fg_valor <= 25:
        return 2.0, -3.0
    elif fg_valor <= 40:
        return 1.0, -1.5
    elif fg_valor >= 75:
        return -3.0, 2.0
    elif fg_valor >= 60:
        return -1.5, 1.0
    else:
        return 0.0, 0.0


# ─────────────────────────────────────────────────────────────────────────────
# CÁLCULO DO LIMIAR DINÂMICO
def calcular_limiar_dinamico(df):
    """Limiar ajustado pela volatilidade do ativo."""
    atr_series = calcular_atr(df)
    if atr_series.empty or pd.isna(atr_series.iloc[-1]):
        return 9.0

    atr_percentual = (atr_series.iloc[-1] / df['close'].iloc[-1]) * 100

    if atr_percentual > 8:
        return 11.0
    elif atr_percentual > 5:
        return 10.0
    elif atr_percentual > 3:
        return 9.0
    elif atr_percentual > 1.5:
        return 8.0
    else:
        return 7.0


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
            simbolo_id,
            timeframe=timeframe_selecionado,
            limit=VELAS_TOTAL
        )
        if not velas or len(velas) < PERIODO_AQUECIMENTO + 50:
            return None
        df = pd.DataFrame(
            velas,
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
        )
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
# ANÁLISE DE CONFLUÊNCIA SMC AVANÇADA (OTIMIZADA PARA 80%+)
def analisar_confluencia(df_completo, simbolo_id, timeframe, fg_valor, txt):
    df_analise = df_completo.iloc[PERIODO_AQUECIMENTO:].copy()

    if df_analise.empty:
        return txt["neutro"], "#ffcc00", txt["ctx_neutro"], 0.0, 0.0, None, None, None, None, {}

    u = df_analise.iloc[-1]
    preco_atual = u['close']
    timestamp_atual = u['time']

    # Fibonacci
    fib_niveis = calcular_retracao_fibonacci(df_analise)

    # Volume Profile
    poc, vah, val = calcular_volume_profile(df_analise)

    # Limiar dinâmico
    limiar_dinamico = calcular_limiar_dinamico(df_completo)

    # Módulos Avançados
    alinhado_mtf, peso_mtf, detalhes_mtf = analisar_alinhamento_mtf(simbolo_id, timeframe)
    estrutura_smc, peso_estrutura = detectar_estrutura_smc(df_analise)
    divergencia_obv, peso_divergencia = detectar_divergencia_obv(df_analise)
    volume_dir, peso_volume = calcular_volume_direcional(df_analise)
    liquidez_ok, liquidez_msg = filtro_liquidez(timestamp_atual)
    peso_fg_compra, peso_fg_venda = integrar_fear_greed(fg_valor)

    # Pontuação base (indicadores originais com pesos ajustados)
    pontos_alta = 0.0
    pontos_baixa = 0.0

    # RSI com peso maior em extremos
    rsi_val = u['RSI_14']
    if not math.isnan(rsi_val):
        if rsi_val < 30:
            pontos_alta += 3.0
        elif rsi_val < 40:
            pontos_alta += 2.0
        elif rsi_val > 70:
            pontos_baixa += 3.0
        elif rsi_val > 60:
            pontos_baixa += 2.0

    # MACD
    macd_hist = u['MACD_HIST']
    if not math.isnan(macd_hist):
        if macd_hist > 0:
            pontos_alta += 2.5
        else:
            pontos_baixa += 2.5

    # OBV Aceleração
    obv_acel = u.get('OBV_Aceleracao', 0)
    if not (np.isnan(obv_acel) or np.isinf(obv_acel)):
        if obv_acel > 0:
            pontos_alta += 1.0
        else:
            pontos_baixa += 1.0

    # MFI
    mfi_val = u['MFI']
    if not math.isnan(mfi_val):
        if mfi_val < 30:
            pontos_alta += 1.5
        elif mfi_val > 70:
            pontos_baixa += 1.5

    # SSL
    if u['ssl_dir'] == 1:
        pontos_alta += 1.0
    else:
        pontos_baixa += 1.0

    # ATR
    if u['atr_dir'] == 1:
        pontos_alta += 1.0
    else:
        pontos_baixa += 1.0

    # PPO
    ppo_val = u['PPO']
    ppo_sig = u['PPO_Signal']
    if not (math.isnan(ppo_val) or math.isnan(ppo_sig)):
        if ppo_val > ppo_sig:
            pontos_alta += 1.5
        else:
            pontos_baixa += 1.5

    # Volume Profile
    if poc is not None and vah is not None and val is not None:
        if preco_atual <= val:
            pontos_alta += 2.0
        elif preco_atual >= vah:
            pontos_baixa += 2.0

    # Fibonacci
    if preco_atual >= fib_niveis['fib_382']:
        pontos_baixa += 2.0
        contexto_fib = txt["ctx_premium"]
    elif preco_atual <= fib_niveis['fib_618']:
        pontos_alta += 2.0
        contexto_fib = txt["ctx_desconto"]
    else:
        contexto_fib = txt["ctx_neutro"]

    # === INTEGRAÇÃO DOS MÓDULOS AVANÇADOS ===

    # Estrutura SMC (peso 3.5)
    if peso_estrutura > 0:
        pontos_alta += abs(peso_estrutura)
    elif peso_estrutura < 0:
        pontos_baixa += abs(peso_estrutura)

    # Divergência OBV (peso 3.0)
    if peso_divergencia > 0:
        pontos_alta += abs(peso_divergencia)
    elif peso_divergencia < 0:
        pontos_baixa += abs(peso_divergencia)

    # Volume Direcional (peso 2.0)
    if peso_volume > 0:
        pontos_alta += abs(peso_volume)
    elif peso_volume < 0:
        pontos_baixa += abs(peso_volume)

    # Alinhamento MTF (peso 2.5)
    if peso_mtf > 0:
        pontos_alta += abs(peso_mtf)
    elif peso_mtf < 0:
        pontos_baixa += abs(peso_mtf)

    # Fear & Greed
    pontos_alta += peso_fg_compra
    pontos_baixa += peso_fg_venda

    # Filtro de Liquidez: reduz sinais em baixa liquidez
    if not liquidez_ok:
        pontos_alta *= 0.6
        pontos_baixa *= 0.6

    # Spike
    spike = detectar_spike_volatilidade(df_analise)

    # Detalhes dos módulos para exibição
    modulos_info = {
        'mtf_alinhado': alinhado_mtf,
        'mtf_peso': peso_mtf,
        'mtf_detalhes': detalhes_mtf,
        'estrutura': estrutura_smc,
        'estrutura_peso': peso_estrutura,
        'divergencia_obv': divergencia_obv,
        'divergencia_peso': peso_divergencia,
        'volume_direcional': volume_dir,
        'volume_peso': peso_volume,
        'liquidez_ok': liquidez_ok,
        'liquidez_msg': liquidez_msg,
        'fg_peso_compra': peso_fg_compra,
        'fg_peso_venda': peso_fg_venda,
        'limiar_dinamico': limiar_dinamico
    }

    # Decisão final com limiar dinâmico
    if pontos_alta >= limiar_dinamico and pontos_alta > pontos_baixa:
        return (
            txt["compra_forte"], "#00cc66",
            f"{contexto_fib} | {estrutura_smc} | Alinhamento MTF: {'✅' if alinhado_mtf else '⚠️'}",
            pontos_alta, pontos_baixa, spike, poc, vah, val, modulos_info
        )
    elif pontos_baixa >= limiar_dinamico and pontos_baixa > pontos_alta:
        return (
            txt["venda_forte"], "#ff3333",
            f"{contexto_fib} | {estrutura_smc} | Alinhamento MTF: {'✅' if alinhado_mtf else '⚠️'}",
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

        # Classificação simplificada
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
            # Definir TP e SL
            tp_pct = 1.5
            sl_pct = 0.75

            if tipo_sinal == "COMPRA":
                tp_preco = preco_entrada * (1 + tp_pct / 100)
                sl_preco = preco_entrada * (1 - sl_pct / 100)
            else:
                tp_preco = preco_entrada * (1 - tp_pct / 100)
                sl_preco = preco_entrada * (1 + sl_pct / 100)

            # Verificar candles futuros (até 20 velas)
            acerto = False
            pnl_pct = 0
            idx_fim = min(i + 20, len(df_analise))

            for j in range(i + 1, idx_fim):
                high_j = df_analise.iloc[j]['high']
                low_j = df_analise.iloc[j]['low']
                close_j = df_analise.iloc[j]['close']

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
                # Fim da janela: usar último close
                ultimo_close = df_analise.iloc[idx_fim - 1]['close']
                pnl_pct = ((ultimo_close - preco_entrada) / preco_entrada) * 100
                if tipo_sinal == "VENDA":
                    pnl_pct = -pnl_pct
                acerto = pnl_pct > 0

            if acerto:
                if tipo_sinal == "COMPRA":
                    acertos_compra += 1
                else:
                    acertos_venda += 1
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
        open=df_grafico['open'],
        high=df_grafico['high'],
        low=df_grafico['low'],
        close=df_grafico['close'],
        name=simbolo_id,
        increasing_line_color='#10b981',
        decreasing_line_color='#ef4444',
        increasing_fillcolor='#10b981',
        decreasing_fillcolor='#ef4444'
    ))

    fig.add_trace(go.Scatter(
        x=df_grafico['time'],
        y=df_grafico['SSL_Baseline'],
        mode='lines',
        name='SMC Baseline (SSL)',
        line=dict(color='#00aaff', width=2)
    ))

    fig.add_trace(go.Scatter(
        x=df_grafico['time'],
        y=df_grafico['ATR_Stop'],
        mode='lines',
        name='ATR Trailing Stop',
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
        paper_bgcolor='#0b0f19',
        plot_bgcolor='#0b0f19',
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

    recomendacao, cor_sinal, analise, pontos_alta, pontos_baixa, spike, poc, vah, val, modulos_info = analisar_confluencia(
        df_dados, simbolo_id, timeframe, fg_valor, txt
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

    # Segunda linha de métricas
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
        if modulos_info:
            liq_ok = modulos_info.get('liquidez_ok', True)
            st.metric(txt["filtro_liquidez"], txt["liquidez_ok"] if liq_ok else txt["liquidez_baixa"])
        else:
            st.metric(txt["filtro_liquidez"], "—")

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

    # Indicadores técnicos
    atr_stop_val = ultimo_reg['ATR_Stop']
    st.markdown(
        f"**{txt['stop_atr']}:** {formatar_preco(atr_stop_val)}"
        f"  |  RSI: **{ultimo_reg['RSI_14']:.1f}**"
        f"  |  MFI: **{ultimo_reg['MFI']:.1f}**"
        f"  |  MACD Hist: **{ultimo_reg['MACD_HIST']:.6f}**"
    )

    # Gráfico
    st.markdown(f"### {txt['grafico_titulo']}")
    renderizar_grafico_plotly(df_dados, simbolo_id, poc, vah, val, txt)

    if poc is not None:
        st.caption(
            f"📊 **Volume Profile:** POC = {formatar_preco(poc)} | "
            f"VAH = {formatar_preco(vah)} | VAL = {formatar_preco(val)} | "
            f"Preço: {'🟡 Equilíbrio' if val <= preco_atual <= vah else ('🔴 Distribuição' if preco_atual > vah else '🟢 Acumulação')}"
        )

    # Backtesting
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

        # Métricas avançadas
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

    # Status
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
