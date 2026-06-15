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
# DICIONÁRIO DE IDIOMAS (17 línguas: PT, EN + 15 mais faladas no mundo)
# Ordem: Mandarim, Hindi, Espanhol, Árabe, Bengali, Francês, Russo, 
#         Japonês, Alemão, Coreano, Turco, Vietnamita, Italiano, Tailandês, Indonésio
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
        "erro_dados": "Dados históricos insuficientes nesta Exchange. Escolha outro ativo ou reduza o Tempo Gráfico.",
        "ctx_desconto": "Ativo em Zona de Desconto de Fibonacci (Excelente risco/retorno para Institucionais).",
        "ctx_premium": "Ativo em Zona Premium de Fibonacci (Preço esticado, propício para realização de lucro).",
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
        "backtest_titulo": "📊 Backtesting — Últimos 100 Sinais",
        "backtest_compra": "Compra",
        "backtest_venda": "Venda",
        "backtest_total": "Total Sinais",
        "backtest_acertos": "Acertos",
        "backtest_taxa": "Taxa de Acerto",
        "backtest_historico": "Histórico de Sinais Recentes",
        "backtest_data": "Data/Hora",
        "backtest_sinal": "Sinal",
        "backtest_preco": "Preço Entrada",
        "backtest_resultado": "Resultado",
        "backtest_acerto": "✅ Acerto",
        "backtest_erro": "❌ Erro",
        "poc_label": "POC (Point of Control)",
        "vah_label": "VAH (Value Area High)",
        "val_label": "VAL (Value Area Low)",
        "fear_greed_label": "😱 Fear & Greed Index",
        "medo_extremo": "Medo Extremo",
        "medo": "Medo",
        "neutro_fg": "Neutro",
        "ganancia": "Ganância",
        "ganancia_extrema": "Ganância Extrema",
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
        "erro_dados": "Insufficient historical data on this Exchange. Choose another asset or reduce the Timeframe.",
        "ctx_desconto": "Asset in Fibonacci Discount Zone (Excellent risk/reward for Institutionals).",
        "ctx_premium": "Asset in Fibonacci Premium Zone (Price stretched, suitable for profit-taking).",
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
        "backtest_titulo": "📊 Backtesting — Last 100 Signals",
        "backtest_compra": "Buy",
        "backtest_venda": "Sell",
        "backtest_total": "Total Signals",
        "backtest_acertos": "Hits",
        "backtest_taxa": "Hit Rate",
        "backtest_historico": "Recent Signal History",
        "backtest_data": "Date/Time",
        "backtest_sinal": "Signal",
        "backtest_preco": "Entry Price",
        "backtest_resultado": "Result",
        "backtest_acerto": "✅ Hit",
        "backtest_erro": "❌ Miss",
        "poc_label": "POC (Point of Control)",
        "vah_label": "VAH (Value Area High)",
        "val_label": "VAL (Value Area Low)",
        "fear_greed_label": "😱 Fear & Greed Index",
        "medo_extremo": "Extreme Fear",
        "medo": "Fear",
        "neutro_fg": "Neutral",
        "ganancia": "Greed",
        "ganancia_extrema": "Extreme Greed",
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
        "titulo": "🏦  BRICSVAULT PORTAL - 聪明钱概念引擎 (SMC)",
        "config_globais": "⚙️  全局设置",
        "selecione_cripto": "选择任意加密货币 (/USDT):",
        "tempo_grafico": "时间周期:",
        "modo_vivo": "启用实时监控",
        "intervalo_refresh": "刷新间隔 (秒):",
        "preco_spot": "实时现货价格",
        "variacao_24h": "24小时涨跌 (交易所)",
        "market_cap": "市值 (USD)",
        "stop_atr": "ATR止损价",
        "compra_forte": "🟢  强力买入 (SMC + 斐波那契对齐)",
        "venda_forte": "🔴  强力卖出 (SMC + 斐波那契对齐)",
        "neutro": "🟡  中性 (等待SMC信号)",
        "spike_alta": "🚀  检测到上行突破 (成交量 + OBV + 波幅)",
        "spike_baixa": "💥  检测到下行突破 (成交量 + OBV + 波幅)",
        "erro_dados": "此交易所历史数据不足。请选择其他资产或缩短时间周期。",
        "ctx_desconto": "资产处于斐波那契折扣区 (机构级风险收益比极佳)。",
        "ctx_premium": "资产处于斐波那契溢价区 (价格拉伸，适合获利了结)。",
        "ctx_neutro": "价格处于斐波那契中性区 (公允价值区间)。",
        "ultima_atualizacao": "最后更新",
        "proximo_refresh": "下次刷新",
        "segundos": "秒",
        "pontos_compra": "买入积分",
        "pontos_venda": "卖出积分",
        "sinal_spike": "波动突破",
        "grafico_titulo": "📈  交互式价格图表",
        "buscando_marketcap": "🔍  正在获取市值...",
        "marketcap_nao_disponivel": "不可用",
        "idioma_label": "🌐  语言 / Language",
        "idioma_selecao": "选择界面语言:",
        "aviso_aquecimento": "⚠️ 计算中使用的预热K线",
        "backtest_titulo": "📊 回测 — 最近100个信号",
        "backtest_compra": "买入",
        "backtest_venda": "卖出",
        "backtest_total": "总信号",
        "backtest_acertos": "命中",
        "backtest_taxa": "命中率",
        "backtest_historico": "近期信号历史",
        "backtest_data": "日期/时间",
        "backtest_sinal": "信号",
        "backtest_preco": "入场价",
        "backtest_resultado": "结果",
        "backtest_acerto": "✅ 命中",
        "backtest_erro": "❌ 未命中",
        "poc_label": "POC (控制点)",
        "vah_label": "VAH (价值区域上限)",
        "val_label": "VAL (价值区域下限)",
        "fear_greed_label": "😱 恐惧贪婪指数",
        "medo_extremo": "极度恐惧",
        "medo": "恐惧",
        "neutro_fg": "中性",
        "ganancia": "贪婪",
        "ganancia_extrema": "极度贪婪",
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
        "titulo": "🏦  BRICSVAULT PORTAL - स्मार्ट मनी कॉन्सेप्ट्स (SMC) इंजन",
        "config_globais": "⚙️  वैश्विक सेटिंग्स",
        "selecione_cripto": "कोई भी क्रिप्टोकरेंसी चुनें (/USDT):",
        "tempo_grafico": "समय-सीमा:",
        "modo_vivo": "रीयल-टाइम मॉनिटरिंग सक्षम करें",
        "intervalo_refresh": "रीफ्रेश अंतराल (सेकंड):",
        "preco_spot": "वास्तविक स्पॉट मूल्य",
        "variacao_24h": "24 घंटे का बदलाव (एक्सचेंज)",
        "market_cap": "मार्केट कैप (USD)",
        "stop_atr": "ATR स्टॉप मूल्य",
        "compra_forte": "🟢  मजबूत खरीद (SMC + फिबोनाची संरेखित)",
        "venda_forte": "🔴  मजबूत बिक्री (SMC + फिबोनाची संरेखित)",
        "neutro": "🟡  तटस्थ (SMC की प्रतीक्षा करें)",
        "spike_alta": "🚀  तेजी का स्पाइक पहचाना गया (वॉल्यूम + OBV + रेंज)",
        "spike_baixa": "💥  मंदी का स्पाइक पहचाना गया (वॉल्यूम + OBV + रेंज)",
        "erro_dados": "इस एक्सचेंज पर अपर्याप्त ऐतिहासिक डेटा। कोई अन्य संपत्ति चुनें या समय-सीमा कम करें।",
        "ctx_desconto": "संपत्ति फिबोनाची डिस्काउंट ज़ोन में (संस्थागत निवेशकों के लिए उत्कृष्ट जोखिम/लाभ)।",
        "ctx_premium": "संपत्ति फिबोनाची प्रीमियम ज़ोन में (मूल्य खिंचा हुआ, लाभ लेने के लिए उपयुक्त)।",
        "ctx_neutro": "मूल्य फिबोनाची तटस्थ क्षेत्र में (उचित मूल्य क्षेत्र)।",
        "ultima_atualizacao": "अंतिम अपडेट",
        "proximo_refresh": "अगला रीफ्रेश",
        "segundos": "सेकंड",
        "pontos_compra": "खरीद अंक",
        "pontos_venda": "बिक्री अंक",
        "sinal_spike": "अस्थिरता स्पाइक",
        "grafico_titulo": "📈  इंटरैक्टिव मूल्य चार्ट",
        "buscando_marketcap": "🔍  मार्केट कैप प्राप्त कर रहे हैं...",
        "marketcap_nao_disponivel": "उपलब्ध नहीं",
        "idioma_label": "🌐  भाषा / Language",
        "idioma_selecao": "इंटरफ़ेस भाषा चुनें:",
        "aviso_aquecimento": "⚠️ गणना में उपयोग की गई वार्म-अप कैंडल्स",
        "backtest_titulo": "📊 बैकटेस्टिंग — पिछले 100 सिग्नल",
        "backtest_compra": "खरीद",
        "backtest_venda": "बिक्री",
        "backtest_total": "कुल सिग्नल",
        "backtest_acertos": "सफल",
        "backtest_taxa": "सफलता दर",
        "backtest_historico": "हाल के सिग्नल इतिहास",
        "backtest_data": "दिनांक/समय",
        "backtest_sinal": "सिग्नल",
        "backtest_preco": "प्रवेश मूल्य",
        "backtest_resultado": "परिणाम",
        "backtest_acerto": "✅ सफल",
        "backtest_erro": "❌ असफल",
        "poc_label": "POC (नियंत्रण बिंदु)",
        "vah_label": "VAH (मूल्य क्षेत्र उच्च)",
        "val_label": "VAL (मूल्य क्षेत्र निम्न)",
        "fear_greed_label": "😱 फियर एंड ग्रीड इंडेक्स",
        "medo_extremo": "अत्यधिक भय",
        "medo": "भय",
        "neutro_fg": "तटस्थ",
        "ganancia": "लालच",
        "ganancia_extrema": "अत्यधिक लालच",
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
        "titulo": "🏦  BRICSVAULT PORTAL - Motor de Smart Money Concepts (SMC)",
        "config_globais": "⚙️  Configuración Global",
        "selecione_cripto": "Seleccione Cualquier Criptomoneda (/USDT):",
        "tempo_grafico": "Marco de Tiempo:",
        "modo_vivo": "Activar Monitoreo en Tiempo Real",
        "intervalo_refresh": "Intervalo de Actualización (Segundos):",
        "preco_spot": "Precio Spot Real",
        "variacao_24h": "Variación 24h (Exchange)",
        "market_cap": "Capitalización de Mercado (USD)",
        "stop_atr": "Precio Stop ATR",
        "compra_forte": "🟢  COMPRA FUERTE (SMC + FIBONACCI ALINEADOS)",
        "venda_forte": "🔴  VENTA FUERTE (SMC + FIBONACCI ALINEADOS)",
        "neutro": "🟡  NEUTRAL (ESPERAR SMC)",
        "spike_alta": "🚀  SPIKE ALCISTA DETECTADO (Volumen + OBV + Rango)",
        "spike_baixa": "💥  SPIKE BAJISTA DETECTADO (Volumen + OBV + Rango)",
        "erro_dados": "Datos históricos insuficientes en este Exchange. Elija otro activo o reduzca el Marco de Tiempo.",
        "ctx_desconto": "Activo en Zona de Descuento Fibonacci (Excelente riesgo/beneficio para Institucionales).",
        "ctx_premium": "Activo en Zona Premium Fibonacci (Precio estirado, propicio para toma de ganancias).",
        "ctx_neutro": "Precio en zona neutral Fibonacci (Zona de Valor Justo).",
        "ultima_atualizacao": "Última Actualización",
        "proximo_refresh": "Próxima actualización en",
        "segundos": "segundos",
        "pontos_compra": "Puntos de Compra",
        "pontos_venda": "Puntos de Venta",
        "sinal_spike": "Spike de Volatilidad",
        "grafico_titulo": "📈  Gráfico de Precio Interactivo",
        "buscando_marketcap": "🔍  Obteniendo Market Cap...",
        "marketcap_nao_disponivel": "No disponible",
        "idioma_label": "🌐  Idioma / Language",
        "idioma_selecao": "Seleccione el idioma de la interfaz:",
        "aviso_aquecimento": "⚠️ Velas de calentamiento usadas en el cálculo",
        "backtest_titulo": "📊 Backtesting — Últimos 100 Señales",
        "backtest_compra": "Compra",
        "backtest_venda": "Venta",
        "backtest_total": "Total Señales",
        "backtest_acertos": "Aciertos",
        "backtest_taxa": "Tasa de Acierto",
        "backtest_historico": "Historial de Señales Recientes",
        "backtest_data": "Fecha/Hora",
        "backtest_sinal": "Señal",
        "backtest_preco": "Precio Entrada",
        "backtest_resultado": "Resultado",
        "backtest_acerto": "✅ Acierto",
        "backtest_erro": "❌ Error",
        "poc_label": "POC (Punto de Control)",
        "vah_label": "VAH (Área de Valor Alto)",
        "val_label": "VAL (Área de Valor Bajo)",
        "fear_greed_label": "😱 Índice de Miedo y Codicia",
        "medo_extremo": "Miedo Extremo",
        "medo": "Miedo",
        "neutro_fg": "Neutral",
        "ganancia": "Codicia",
        "ganancia_extrema": "Codicia Extrema",
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
    "العربية (Árabe)": {
        "titulo": "🏦  BRICSVAULT PORTAL - محرك مفاهيم المال الذكي (SMC)",
        "config_globais": "⚙️  الإعدادات العامة",
        "selecione_cripto": "اختر أي عملة مشفرة (/USDT):",
        "tempo_grafico": "الإطار الزمني:",
        "modo_vivo": "تفعيل المراقبة المباشرة",
        "intervalo_refresh": "فاصل التحديث (ثواني):",
        "preco_spot": "السعر الفوري الحقيقي",
        "variacao_24h": "التغير خلال 24 ساعة (المنصة)",
        "market_cap": "القيمة السوقية (USD)",
        "stop_atr": "سعر وقف ATR",
        "compra_forte": "🟢  شراء قوي (SMC + فيبوناتشي متوافق)",
        "venda_forte": "🔴  بيع قوي (SMC + فيبوناتشي متوافق)",
        "neutro": "🟡  محايد (انتظار SMC)",
        "spike_alta": "🚀  تم اكتشاف ارتفاع حاد (حجم + OBV + نطاق)",
        "spike_baixa": "💥  تم اكتشاف انخفاض حاد (حجم + OBV + نطاق)",
        "erro_dados": "بيانات تاريخية غير كافية في هذه المنصة. اختر أصلاً آخر أو قلل الإطار الزمني.",
        "ctx_desconto": "الأصل في منطقة خصم فيبوناتشي (مخاطرة/عائد ممتاز للمؤسسات).",
        "ctx_premium": "الأصل في منطقة فيبوناتشي الممتازة (السعر متمدد، مناسب لجني الأرباح).",
        "ctx_neutro": "السعر في منطقة فيبوناتشي المحايدة (منطقة القيمة العادلة).",
        "ultima_atualizacao": "آخر تحديث",
        "proximo_refresh": "التحديث التالي خلال",
        "segundos": "ثانية",
        "pontos_compra": "نقاط الشراء",
        "pontos_venda": "نقاط البيع",
        "sinal_spike": "ارتفاع التقلب",
        "grafico_titulo": "📈  رسم بياني تفاعلي للسعر",
        "buscando_marketcap": "🔍  جاري جلب القيمة السوقية...",
        "marketcap_nao_disponivel": "غير متوفر",
        "idioma_label": "🌐  اللغة / Language",
        "idioma_selecao": "اختر لغة الواجهة:",
        "aviso_aquecimento": "⚠️ شموع التسخين المستخدمة في الحساب",
        "backtest_titulo": "📊 الاختبار الخلفي — آخر 100 إشارة",
        "backtest_compra": "شراء",
        "backtest_venda": "بيع",
        "backtest_total": "إجمالي الإشارات",
        "backtest_acertos": "ناجحة",
        "backtest_taxa": "نسبة النجاح",
        "backtest_historico": "سجل الإشارات الحديثة",
        "backtest_data": "التاريخ/الوقت",
        "backtest_sinal": "الإشارة",
        "backtest_preco": "سعر الدخول",
        "backtest_resultado": "النتيجة",
        "backtest_acerto": "✅ ناجح",
        "backtest_erro": "❌ فاشل",
        "poc_label": "POC (نقطة التحكم)",
        "vah_label": "VAH (منطقة القيمة العليا)",
        "val_label": "VAL (منطقة القيمة الدنيا)",
        "fear_greed_label": "😱 مؤشر الخوف والطمع",
        "medo_extremo": "خوف شديد",
        "medo": "خوف",
        "neutro_fg": "محايد",
        "ganancia": "طمع",
        "ganancia_extrema": "طمع شديد",
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
        "titulo": "🏦  BRICSVAULT PORTAL - স্মার্ট মানি কনসেপ্টস (SMC) ইঞ্জিন",
        "config_globais": "⚙️  গ্লোবাল সেটিংস",
        "selecione_cripto": "যেকোনো ক্রিপ্টোকারেন্সি নির্বাচন করুন (/USDT):",
        "tempo_grafico": "টাইমফ্রেম:",
        "modo_vivo": "রিয়েল-টাইম মনিটরিং সক্রিয় করুন",
        "intervalo_refresh": "রিফ্রেশ ইন্টারভাল (সেকেন্ড):",
        "preco_spot": "প্রকৃত স্পট মূল্য",
        "variacao_24h": "২৪ ঘন্টার পরিবর্তন (এক্সচেঞ্জ)",
        "market_cap": "মার্কেট ক্যাপ (USD)",
        "stop_atr": "ATR স্টপ মূল্য",
        "compra_forte": "🟢  শক্তিশালী ক্রয় (SMC + ফিবোনাচি সমন্বিত)",
        "venda_forte": "🔴  শক্তিশালী বিক্রয় (SMC + ফিবোনাচি সমন্বিত)",
        "neutro": "🟡  নিরপেক্ষ (SMC-এর জন্য অপেক্ষা)",
        "spike_alta": "🚀  ঊর্ধ্বমুখী স্পাইক সনাক্ত (ভলিউম + OBV + রেঞ্জ)",
        "spike_baixa": "💥  নিম্নমুখী স্পাইক সনাক্ত (ভলিউম + OBV + রেঞ্জ)",
        "erro_dados": "এই এক্সচেঞ্জে অপর্যাপ্ত ঐতিহাসিক ডেটা। অন্য সম্পদ নির্বাচন করুন বা টাইমফ্রেম কমান।",
        "ctx_desconto": "সম্পদ ফিবোনাচি ডিসকাউন্ট জোনে (প্রাতিষ্ঠানিক বিনিয়োগকারীদের জন্য চমৎকার ঝুঁকি/রিটার্ন)।",
        "ctx_premium": "সম্পদ ফিবোনাচি প্রিমিয়াম জোনে (মূল্য প্রসারিত, মুনাফা তোলার জন্য উপযুক্ত)।",
        "ctx_neutro": "মূল্য ফিবোনাচি নিরপেক্ষ অঞ্চলে (ন্যায্য মূল্য অঞ্চল)।",
        "ultima_atualizacao": "সর্বশেষ আপডেট",
        "proximo_refresh": "পরবর্তী রিফ্রেশ",
        "segundos": "সেকেন্ড",
        "pontos_compra": "ক্রয় পয়েন্ট",
        "pontos_venda": "বিক্রয় পয়েন্ট",
        "sinal_spike": "অস্থিরতা স্পাইক",
        "grafico_titulo": "📈  ইন্টারেক্টিভ মূল্য চার্ট",
        "buscando_marketcap": "🔍  মার্কেট ক্যাপ আনা হচ্ছে...",
        "marketcap_nao_disponivel": "উপলব্ধ নয়",
        "idioma_label": "🌐  ভাষা / Language",
        "idioma_selecao": "ইন্টারফেস ভাষা নির্বাচন করুন:",
        "aviso_aquecimento": "⚠️ গণনায় ব্যবহৃত ওয়ার্ম-আপ ক্যান্ডেল",
        "backtest_titulo": "📊 ব্যাকটেস্টিং — শেষ ১০০টি সিগন্যাল",
        "backtest_compra": "ক্রয়",
        "backtest_venda": "বিক্রয়",
        "backtest_total": "মোট সিগন্যাল",
        "backtest_acertos": "সফল",
        "backtest_taxa": "সাফল্যের হার",
        "backtest_historico": "সাম্প্রতিক সিগন্যাল ইতিহাস",
        "backtest_data": "তারিখ/সময়",
        "backtest_sinal": "সিগন্যাল",
        "backtest_preco": "প্রবেশ মূল্য",
        "backtest_resultado": "ফলাফল",
        "backtest_acerto": "✅ সফল",
        "backtest_erro": "❌ ব্যর্থ",
        "poc_label": "POC (নিয়ন্ত্রণ বিন্দু)",
        "vah_label": "VAH (মূল্য এলাকা উচ্চ)",
        "val_label": "VAL (মূল্য এলাকা নিম্ন)",
        "fear_greed_label": "😱 ভয় ও লোভ সূচক",
        "medo_extremo": "চরম ভয়",
        "medo": "ভয়",
        "neutro_fg": "নিরপেক্ষ",
        "ganancia": "লোভ",
        "ganancia_extrema": "চরম লোভ",
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
    "Français (Francês)": {
        "titulo": "🏦  BRICSVAULT PORTAL - Moteur Smart Money Concepts (SMC)",
        "config_globais": "⚙️  Configuration Globale",
        "selecione_cripto": "Sélectionnez une Cryptomonnaie (/USDT):",
        "tempo_grafico": "Période:",
        "modo_vivo": "Activer la Surveillance en Temps Réel",
        "intervalo_refresh": "Intervalle d'Actualisation (Secondes):",
        "preco_spot": "Prix Spot Réel",
        "variacao_24h": "Variation 24h (Exchange)",
        "market_cap": "Capitalisation Boursière (USD)",
        "stop_atr": "Prix Stop ATR",
        "compra_forte": "🟢  ACHAT FORT (SMC + FIBONACCI ALIGNÉS)",
        "venda_forte": "🔴  VENTE FORTE (SMC + FIBONACCI ALIGNÉS)",
        "neutro": "🟡  NEUTRE (ATTENDRE SMC)",
        "spike_alta": "🚀  SPIKE HAUSSIER DÉTECTÉ (Volume + OBV + Range)",
        "spike_baixa": "💥  SPIKE BAISSIER DÉTECTÉ (Volume + OBV + Range)",
        "erro_dados": "Données historiques insuffisantes sur cet Exchange. Choisissez un autre actif ou réduisez la Période.",
        "ctx_desconto": "Actif en Zone de Remise Fibonacci (Excellent risque/rendement pour les Institutionnels).",
        "ctx_premium": "Actif en Zone Premium Fibonacci (Prix étiré, propice aux prises de bénéfices).",
        "ctx_neutro": "Prix en zone neutre Fibonacci (Zone de Juste Valeur).",
        "ultima_atualizacao": "Dernière Mise à Jour",
        "proximo_refresh": "Prochaine actualisation dans",
        "segundos": "secondes",
        "pontos_compra": "Points d'Achat",
        "pontos_venda": "Points de Vente",
        "sinal_spike": "Spike de Volatilité",
        "grafico_titulo": "📈  Graphique de Prix Interactif",
        "buscando_marketcap": "🔍  Récupération Market Cap...",
        "marketcap_nao_disponivel": "Non disponible",
        "idioma_label": "🌐  Langue / Language",
        "idioma_selecao": "Sélectionnez la langue de l'interface:",
        "aviso_aquecimento": "⚠️ Bougies de préchauffage utilisées dans le calcul",
        "backtest_titulo": "📊 Backtesting — 100 Derniers Signaux",
        "backtest_compra": "Achat",
        "backtest_venda": "Vente",
        "backtest_total": "Total Signaux",
        "backtest_acertos": "Réussites",
        "backtest_taxa": "Taux de Réussite",
        "backtest_historico": "Historique des Signaux Récents",
        "backtest_data": "Date/Heure",
        "backtest_sinal": "Signal",
        "backtest_preco": "Prix d'Entrée",
        "backtest_resultado": "Résultat",
        "backtest_acerto": "✅ Réussi",
        "backtest_erro": "❌ Échec",
        "poc_label": "POC (Point de Contrôle)",
        "vah_label": "VAH (Zone de Valeur Haute)",
        "val_label": "VAL (Zone de Valeur Basse)",
        "fear_greed_label": "😱 Indice de Peur et Cupidité",
        "medo_extremo": "Peur Extrême",
        "medo": "Peur",
        "neutro_fg": "Neutre",
        "ganancia": "Cupidité",
        "ganancia_extrema": "Cupidité Extrême",
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
        "titulo": "🏦  BRICSVAULT PORTAL - Двигатель Smart Money Concepts (SMC)",
        "config_globais": "⚙️  Глобальные Настройки",
        "selecione_cripto": "Выберите Криптовалюту (/USDT):",
        "tempo_grafico": "Таймфрейм:",
        "modo_vivo": "Включить Мониторинг в Реальном Времени",
        "intervalo_refresh": "Интервал Обновления (Секунд):",
        "preco_spot": "Реальная Спотовая Цена",
        "variacao_24h": "Изменение за 24ч (Биржа)",
        "market_cap": "Рыночная Капитализация (USD)",
        "stop_atr": "Цена Стоп ATR",
        "compra_forte": "🟢  СИЛЬНАЯ ПОКУПКА (SMC + ФИБОНАЧЧИ СОВПАДАЮТ)",
        "venda_forte": "🔴  СИЛЬНАЯ ПРОДАЖА (SMC + ФИБОНАЧЧИ СОВПАДАЮТ)",
        "neutro": "🟡  НЕЙТРАЛЬНО (ОЖИДАНИЕ SMC)",
        "spike_alta": "🚀  ОБНАРУЖЕН ВСПЛЕСК ВВЕРХ (Объем + OBV + Диапазон)",
        "spike_baixa": "💥  ОБНАРУЖЕН ВСПЛЕСК ВНИЗ (Объем + OBV + Диапазон)",
        "erro_dados": "Недостаточно исторических данных на этой бирже. Выберите другой актив или уменьшите таймфрейм.",
        "ctx_desconto": "Актив в Зоне Скидки Фибоначчи (Отличное соотношение риск/доход для институционалов).",
        "ctx_premium": "Актив в Премиум Зоне Фибоначчи (Цена растянута, подходит для фиксации прибыли).",
        "ctx_neutro": "Цена в нейтральной зоне Фибоначчи (Зона Справедливой Стоимости).",
        "ultima_atualizacao": "Последнее Обновление",
        "proximo_refresh": "Следующее обновление через",
        "segundos": "секунд",
        "pontos_compra": "Очки Покупки",
        "pontos_venda": "Очки Продажи",
        "sinal_spike": "Всплеск Волатильности",
        "grafico_titulo": "📈  Интерактивный График Цены",
        "buscando_marketcap": "🔍  Получение Market Cap...",
        "marketcap_nao_disponivel": "Недоступно",
        "idioma_label": "🌐  Язык / Language",
        "idioma_selecao": "Выберите язык интерфейса:",
        "aviso_aquecimento": "⚠️ Разогревочные свечи использованы в расчете",
        "backtest_titulo": "📊 Бэктестинг — Последние 100 Сигналов",
        "backtest_compra": "Покупка",
        "backtest_venda": "Продажа",
        "backtest_total": "Всего Сигналов",
        "backtest_acertos": "Успешных",
        "backtest_taxa": "Процент Успеха",
        "backtest_historico": "История Недавних Сигналов",
        "backtest_data": "Дата/Время",
        "backtest_sinal": "Сигнал",
        "backtest_preco": "Цена Входа",
        "backtest_resultado": "Результат",
        "backtest_acerto": "✅ Успех",
        "backtest_erro": "❌ Неудача",
        "poc_label": "POC (Точка Контроля)",
        "vah_label": "VAH (Верхняя Граница Области Стоимости)",
        "val_label": "VAL (Нижняя Граница Области Стоимости)",
        "fear_greed_label": "😱 Индекс Страха и Жадности",
        "medo_extremo": "Экстремальный Страх",
        "medo": "Страх",
        "neutro_fg": "Нейтрально",
        "ganancia": "Жадность",
        "ganancia_extrema": "Экстремальная Жадность",
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
        "titulo": "🏦  BRICSVAULT PORTAL - スマートマネーコンセプト (SMC) エンジン",
        "config_globais": "⚙️  グローバル設定",
        "selecione_cripto": "任意の暗号通貨を選択 (/USDT):",
        "tempo_grafico": "時間枠:",
        "modo_vivo": "リアルタイム監視を有効化",
        "intervalo_refresh": "更新間隔 (秒):",
        "preco_spot": "リアルスポット価格",
        "variacao_24h": "24時間変動 (取引所)",
        "market_cap": "時価総額 (USD)",
        "stop_atr": "ATRストップ価格",
        "compra_forte": "🟢  強い買い (SMC + フィボナッチ一致)",
        "venda_forte": "🔴  強い売り (SMC + フィボナッチ一致)",
        "neutro": "🟡  中立 (SMC待ち)",
        "spike_alta": "🚀  上昇スパイク検出 (出来高 + OBV + レンジ)",
        "spike_baixa": "💥  下降スパイク検出 (出来高 + OBV + レンジ)",
        "erro_dados": "この取引所の履歴データが不十分です。別の資産を選択するか、時間枠を短くしてください。",
        "ctx_desconto": "資産はフィボナッチディスカウントゾーン (機関投資家向けに優れたリスク/リターン)。",
        "ctx_premium": "資産はフィボナッチプレミアムゾーン (価格が伸びており、利確に適しています)。",
        "ctx_neutro": "価格はフィボナッチ中立ゾーン (公正価値ゾーン)。",
        "ultima_atualizacao": "最終更新",
        "proximo_refresh": "次の更新まで",
        "segundos": "秒",
        "pontos_compra": "買いポイント",
        "pontos_venda": "売りポイント",
        "sinal_spike": "ボラティリティスパイク",
        "grafico_titulo": "📈  インタラクティブ価格チャート",
        "buscando_marketcap": "🔍  時価総額取得中...",
        "marketcap_nao_disponivel": "利用不可",
        "idioma_label": "🌐  言語 / Language",
        "idioma_selecao": "インターフェース言語を選択:",
        "aviso_aquecimento": "⚠️ 計算に使用されたウォームアップローソク",
        "backtest_titulo": "📊 バックテスト — 直近100シグナル",
        "backtest_compra": "買い",
        "backtest_venda": "売り",
        "backtest_total": "総シグナル数",
        "backtest_acertos": "成功",
        "backtest_taxa": "成功率",
        "backtest_historico": "最近のシグナル履歴",
        "backtest_data": "日時",
        "backtest_sinal": "シグナル",
        "backtest_preco": "エントリー価格",
        "backtest_resultado": "結果",
        "backtest_acerto": "✅ 成功",
        "backtest_erro": "❌ 失敗",
        "poc_label": "POC (コントロールポイント)",
        "vah_label": "VAH (バリューエリア上限)",
        "val_label": "VAL (バリューエリア下限)",
        "fear_greed_label": "😱 恐怖＆強欲指数",
        "medo_extremo": "極度の恐怖",
        "medo": "恐怖",
        "neutro_fg": "中立",
        "ganancia": "強欲",
        "ganancia_extrema": "極度の強欲",
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
        "titulo": "🏦  BRICSVAULT PORTAL - Smart Money Concepts (SMC) Engine",
        "config_globais": "⚙️  Globale Einstellungen",
        "selecione_cripto": "Kryptowährung auswählen (/USDT):",
        "tempo_grafico": "Zeitrahmen:",
        "modo_vivo": "Echtzeit-Überwachung aktivieren",
        "intervalo_refresh": "Aktualisierungsintervall (Sekunden):",
        "preco_spot": "Echter Spot-Preis",
        "variacao_24h": "24h-Änderung (Börse)",
        "market_cap": "Marktkapitalisierung (USD)",
        "stop_atr": "ATR-Stop-Preis",
        "compra_forte": "🟢  STARKER KAUF (SMC + FIBONACCI AUSGERICHTET)",
        "venda_forte": "🔴  STARKER VERKAUF (SMC + FIBONACCI AUSGERICHTET)",
        "neutro": "🟡  NEUTRAL (AUF SMC WARTEN)",
        "spike_alta": "🚀  AUFWÄRTSSPIKE ERKANNT (Volumen + OBV + Range)",
        "spike_baixa": "💥  ABWÄRTSSPIKE ERKANNT (Volumen + OBV + Range)",
        "erro_dados": "Unzureichende historische Daten an dieser Börse. Anderen Vermögenswert wählen oder Zeitrahmen reduzieren.",
        "ctx_desconto": "Vermögenswert in Fibonacci-Discount-Zone (Ausgezeichnetes Risiko/Rendite für Institutionelle).",
        "ctx_premium": "Vermögenswert in Fibonacci-Premium-Zone (Preis überdehnt, geeignet für Gewinnmitnahmen).",
        "ctx_neutro": "Preis in neutraler Fibonacci-Zone (Fair-Value-Zone).",
        "ultima_atualizacao": "Letzte Aktualisierung",
        "proximo_refresh": "Nächste Aktualisierung in",
        "segundos": "Sekunden",
        "pontos_compra": "Kaufpunkte",
        "pontos_venda": "Verkaufspunkte",
        "sinal_spike": "Volatilitätsspike",
        "grafico_titulo": "📈  Interaktiver Preis-Chart",
        "buscando_marketcap": "🔍  Marktkapitalisierung wird abgerufen...",
        "marketcap_nao_disponivel": "Nicht verfügbar",
        "idioma_label": "🌐  Sprache / Language",
        "idioma_selecao": "Wählen Sie die Oberflächensprache:",
        "aviso_aquecimento": "⚠️ Aufwärmkerzen in Berechnung verwendet",
        "backtest_titulo": "📊 Backtesting — Letzte 100 Signale",
        "backtest_compra": "Kauf",
        "backtest_venda": "Verkauf",
        "backtest_total": "Gesamtsignale",
        "backtest_acertos": "Treffer",
        "backtest_taxa": "Trefferquote",
        "backtest_historico": "Verlauf Aktueller Signale",
        "backtest_data": "Datum/Zeit",
        "backtest_sinal": "Signal",
        "backtest_preco": "Einstiegspreis",
        "backtest_resultado": "Ergebnis",
        "backtest_acerto": "✅ Treffer",
        "backtest_erro": "❌ Fehler",
        "poc_label": "POC (Kontrollpunkt)",
        "vah_label": "VAH (Value Area High)",
        "val_label": "VAL (Value Area Low)",
        "fear_greed_label": "😱 Fear & Greed Index",
        "medo_extremo": "Extreme Angst",
        "medo": "Angst",
        "neutro_fg": "Neutral",
        "ganancia": "Gier",
        "ganancia_extrema": "Extreme Gier",
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
        "titulo": "🏦  BRICSVAULT PORTAL - 스마트머니 컨셉 (SMC) 엔진",
        "config_globais": "⚙️  글로벌 설정",
        "selecione_cripto": "암호화폐 선택 (/USDT):",
        "tempo_grafico": "시간대:",
        "modo_vivo": "실시간 모니터링 활성화",
        "intervalo_refresh": "새로고침 간격 (초):",
        "preco_spot": "실시간 현물 가격",
        "variacao_24h": "24시간 변동 (거래소)",
        "market_cap": "시가총액 (USD)",
        "stop_atr": "ATR 손절가",
        "compra_forte": "🟢  강력 매수 (SMC + 피보나치 정렬)",
        "venda_forte": "🔴  강력 매도 (SMC + 피보나치 정렬)",
        "neutro": "🟡  중립 (SMC 대기)",
        "spike_alta": "🚀  상승 스파이크 감지 (거래량 + OBV + 범위)",
        "spike_baixa": "💥  하락 스파이크 감지 (거래량 + OBV + 범위)",
        "erro_dados": "이 거래소의 과거 데이터가 부족합니다. 다른 자산을 선택하거나 시간대를 줄이세요.",
        "ctx_desconto": "자산이 피보나치 할인 영역에 있음 (기관 투자자에게 탁월한 위험/수익).",
        "ctx_premium": "자산이 피보나치 프리미엄 영역에 있음 (가격이 과도하게 상승, 수익 실현에 적합).",
        "ctx_neutro": "가격이 피보나치 중립 영역에 있음 (공정가치 영역).",
        "ultima_atualizacao": "마지막 업데이트",
        "proximo_refresh": "다음 새로고침까지",
        "segundos": "초",
        "pontos_compra": "매수 점수",
        "pontos_venda": "매도 점수",
        "sinal_spike": "변동성 스파이크",
        "grafico_titulo": "📈  대화형 가격 차트",
        "buscando_marketcap": "🔍  시가총액 가져오는 중...",
        "marketcap_nao_disponivel": "사용 불가",
        "idioma_label": "🌐  언어 / Language",
        "idioma_selecao": "인터페이스 언어 선택:",
        "aviso_aquecimento": "⚠️ 계산에 사용된 워밍업 캔들",
        "backtest_titulo": "📊 백테스팅 — 최근 100개 시그널",
        "backtest_compra": "매수",
        "backtest_venda": "매도",
        "backtest_total": "총 시그널",
        "backtest_acertos": "성공",
        "backtest_taxa": "성공률",
        "backtest_historico": "최근 시그널 기록",
        "backtest_data": "날짜/시간",
        "backtest_sinal": "시그널",
        "backtest_preco": "진입 가격",
        "backtest_resultado": "결과",
        "backtest_acerto": "✅ 성공",
        "backtest_erro": "❌ 실패",
        "poc_label": "POC (통제점)",
        "vah_label": "VAH (가치영역 상단)",
        "val_label": "VAL (가치영역 하단)",
        "fear_greed_label": "😱 공포·탐욕 지수",
        "medo_extremo": "극도의 공포",
        "medo": "공포",
        "neutro_fg": "중립",
        "ganancia": "탐욕",
        "ganancia_extrema": "극도의 탐욕",
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
    "Türkçe (Turco)": {
        "titulo": "🏦  BRICSVAULT PORTAL - Akıllı Para Konseptleri (SMC) Motoru",
        "config_globais": "⚙️  Küresel Ayarlar",
        "selecione_cripto": "Herhangi Bir Kripto Para Seçin (/USDT):",
        "tempo_grafico": "Zaman Dilimi:",
        "modo_vivo": "Gerçek Zamanlı İzlemeyi Etkinleştir",
        "intervalo_refresh": "Yenileme Aralığı (Saniye):",
        "preco_spot": "Gerçek Spot Fiyat",
        "variacao_24h": "24s Değişim (Borsa)",
        "market_cap": "Piyasa Değeri (USD)",
        "stop_atr": "ATR Stop Fiyatı",
        "compra_forte": "🟢  GÜÇLÜ AL (SMC + FIBONACCI UYUMLU)",
        "venda_forte": "🔴  GÜÇLÜ SAT (SMC + FIBONACCI UYUMLU)",
        "neutro": "🟡  NÖTR (SMC BEKLE)",
        "spike_alta": "🚀  YÜKSELİŞ SİNYALİ TESPİT EDİLDİ (Hacim + OBV + Aralık)",
        "spike_baixa": "💥  DÜŞÜŞ SİNYALİ TESPİT EDİLDİ (Hacim + OBV + Aralık)",
        "erro_dados": "Bu borsada yetersiz geçmiş veri. Başka bir varlık seçin veya zaman dilimini azaltın.",
        "ctx_desconto": "Varlık Fibonacci İndirim Bölgesinde (Kurumsallar için mükemmel risk/getiri).",
        "ctx_premium": "Varlık Fibonacci Premium Bölgesinde (Fiyat gergin, kâr alımına uygun).",
        "ctx_neutro": "Fiyat Fibonacci nötr bölgede (Gerçek Değer Bölgesi).",
        "ultima_atualizacao": "Son Güncelleme",
        "proximo_refresh": "Sonraki yenileme",
        "segundos": "saniye",
        "pontos_compra": "Alış Puanları",
        "pontos_venda": "Satış Puanları",
        "sinal_spike": "Volatilite Sinyali",
        "grafico_titulo": "📈  İnteraktif Fiyat Grafiği",
        "buscando_marketcap": "🔍  Piyasa Değeri Alınıyor...",
        "marketcap_nao_disponivel": "Mevcut değil",
        "idioma_label": "🌐  Dil / Language",
        "idioma_selecao": "Arayüz dilini seçin:",
        "aviso_aquecimento": "⚠️ Hesaplamada kullanılan ısınma mumları",
        "backtest_titulo": "📊 Geriye Dönük Test — Son 100 Sinyal",
        "backtest_compra": "Alış",
        "backtest_venda": "Satış",
        "backtest_total": "Toplam Sinyal",
        "backtest_acertos": "Başarılı",
        "backtest_taxa": "Başarı Oranı",
        "backtest_historico": "Son Sinyal Geçmişi",
        "backtest_data": "Tarih/Saat",
        "backtest_sinal": "Sinyal",
        "backtest_preco": "Giriş Fiyatı",
        "backtest_resultado": "Sonuç",
        "backtest_acerto": "✅ Başarılı",
        "backtest_erro": "❌ Başarısız",
        "poc_label": "POC (Kontrol Noktası)",
        "vah_label": "VAH (Değer Alanı Üst)",
        "val_label": "VAL (Değer Alanı Alt)",
        "fear_greed_label": "😱 Korku ve Açgözlülük Endeksi",
        "medo_extremo": "Aşırı Korku",
        "medo": "Korku",
        "neutro_fg": "Nötr",
        "ganancia": "Açgözlülük",
        "ganancia_extrema": "Aşırı Açgözlülük",
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
        "titulo": "🏦  BRICSVAULT PORTAL - Động Cơ Smart Money Concepts (SMC)",
        "config_globais": "⚙️  Cài Đặt Toàn Cầu",
        "selecione_cripto": "Chọn Bất Kỳ Tiền Điện Tử Nào (/USDT):",
        "tempo_grafico": "Khung Thời Gian:",
        "modo_vivo": "Bật Giám Sát Thời Gian Thực",
        "intervalo_refresh": "Khoảng Thời Gian Làm Mới (Giây):",
        "preco_spot": "Giá Spot Thực",
        "variacao_24h": "Biến Động 24h (Sàn)",
        "market_cap": "Vốn Hóa Thị Trường (USD)",
        "stop_atr": "Giá Cắt Lỗ ATR",
        "compra_forte": "🟢  MUA MẠNH (SMC + FIBONACCI CĂN CHỈNH)",
        "venda_forte": "🔴  BÁN MẠNH (SMC + FIBONACCI CĂN CHỈNH)",
        "neutro": "🟡  TRUNG LẬP (CHỜ SMC)",
        "spike_alta": "🚀  PHÁT HIỆN TĂNG ĐỘT BIẾN (Khối Lượng + OBV + Biên Độ)",
        "spike_baixa": "💥  PHÁT HIỆN GIẢM ĐỘT BIẾN (Khối Lượng + OBV + Biên Độ)",
        "erro_dados": "Dữ liệu lịch sử không đủ trên Sàn này. Chọn tài sản khác hoặc giảm Khung Thời Gian.",
        "ctx_desconto": "Tài sản trong Vùng Chiết Khấu Fibonacci (Rủi ro/lợi nhuận tuyệt vời cho Tổ chức).",
        "ctx_premium": "Tài sản trong Vùng Premium Fibonacci (Giá kéo dài, thích hợp để chốt lời).",
        "ctx_neutro": "Giá trong vùng Fibonacci trung lập (Vùng Giá Trị Hợp Lý).",
        "ultima_atualizacao": "Cập Nhật Lần Cuối",
        "proximo_refresh": "Lần làm mới tiếp theo trong",
        "segundos": "giây",
        "pontos_compra": "Điểm Mua",
        "pontos_venda": "Điểm Bán",
        "sinal_spike": "Đột Biến Biến Động",
        "grafico_titulo": "📈  Biểu Đồ Giá Tương Tác",
        "buscando_marketcap": "🔍  Đang Lấy Vốn Hóa Thị Trường...",
        "marketcap_nao_disponivel": "Không có sẵn",
        "idioma_label": "🌐  Ngôn Ngữ / Language",
        "idioma_selecao": "Chọn ngôn ngữ giao diện:",
        "aviso_aquecimento": "⚠️ Nến khởi động được sử dụng trong tính toán",
        "backtest_titulo": "📊 Kiểm Tra Lịch Sử — 100 Tín Hiệu Cuối",
        "backtest_compra": "Mua",
        "backtest_venda": "Bán",
        "backtest_total": "Tổng Tín Hiệu",
        "backtest_acertos": "Thành Công",
        "backtest_taxa": "Tỷ Lệ Thành Công",
        "backtest_historico": "Lịch Sử Tín Hiệu Gần Đây",
        "backtest_data": "Ngày/Giờ",
        "backtest_sinal": "Tín Hiệu",
        "backtest_preco": "Giá Vào",
        "backtest_resultado": "Kết Quả",
        "backtest_acerto": "✅ Thành Công",
        "backtest_erro": "❌ Thất Bại",
        "poc_label": "POC (Điểm Kiểm Soát)",
        "vah_label": "VAH (Vùng Giá Trị Cao)",
        "val_label": "VAL (Vùng Giá Trị Thấp)",
        "fear_greed_label": "😱 Chỉ Số Sợ Hãi & Tham Lam",
        "medo_extremo": "Sợ Hãi Cực Độ",
        "medo": "Sợ Hãi",
        "neutro_fg": "Trung Lập",
        "ganancia": "Tham Lam",
        "ganancia_extrema": "Tham Lam Cực Độ",
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
        "titulo": "🏦  BRICSVAULT PORTAL - Motore Smart Money Concepts (SMC)",
        "config_globais": "⚙️  Impostazioni Globali",
        "selecione_cripto": "Seleziona Qualsiasi Criptovaluta (/USDT):",
        "tempo_grafico": "Timeframe:",
        "modo_vivo": "Attiva Monitoraggio in Tempo Reale",
        "intervalo_refresh": "Intervallo di Aggiornamento (Secondi):",
        "preco_spot": "Prezzo Spot Reale",
        "variacao_24h": "Variazione 24h (Exchange)",
        "market_cap": "Capitalizzazione di Mercato (USD)",
        "stop_atr": "Prezzo Stop ATR",
        "compra_forte": "🟢  ACQUISTO FORTE (SMC + FIBONACCI ALLINEATI)",
        "venda_forte": "🔴  VENDITA FORTE (SMC + FIBONACCI ALLINEATI)",
        "neutro": "🟡  NEUTRO (ATTENDERE SMC)",
        "spike_alta": "🚀  SPIKE RIALZISTA RILEVATO (Volume + OBV + Range)",
        "spike_baixa": "💥  SPIKE RIBASSISTA RILEVATO (Volume + OBV + Range)",
        "erro_dados": "Dati storici insufficienti su questo Exchange. Scegli un altro asset o riduci il Timeframe.",
        "ctx_desconto": "Asset in Zona di Sconto Fibonacci (Eccellente rischio/rendimento per Istituzionali).",
        "ctx_premium": "Asset in Zona Premium Fibonacci (Prezzo stirato, adatto per prendere profitto).",
        "ctx_neutro": "Prezzo in zona Fibonacci neutra (Fair Value Zone).",
        "ultima_atualizacao": "Ultimo Aggiornamento",
        "proximo_refresh": "Prossimo aggiornamento tra",
        "segundos": "secondi",
        "pontos_compra": "Punti Acquisto",
        "pontos_venda": "Punti Vendita",
        "sinal_spike": "Spike di Volatilità",
        "grafico_titulo": "📈  Grafico Prezzi Interattivo",
        "buscando_marketcap": "🔍  Recupero Market Cap...",
        "marketcap_nao_disponivel": "Non disponibile",
        "idioma_label": "🌐  Lingua / Language",
        "idioma_selecao": "Seleziona la lingua dell'interfaccia:",
        "aviso_aquecimento": "⚠️ Candele di riscaldamento usate nel calcolo",
        "backtest_titulo": "📊 Backtesting — Ultimi 100 Segnali",
        "backtest_compra": "Acquisto",
        "backtest_venda": "Vendita",
        "backtest_total": "Totale Segnali",
        "backtest_acertos": "Successi",
        "backtest_taxa": "Tasso di Successo",
        "backtest_historico": "Cronologia Segnali Recenti",
        "backtest_data": "Data/Ora",
        "backtest_sinal": "Segnale",
        "backtest_preco": "Prezzo Entrata",
        "backtest_resultado": "Risultato",
        "backtest_acerto": "✅ Successo",
        "backtest_erro": "❌ Fallimento",
        "poc_label": "POC (Punto di Controllo)",
        "vah_label": "VAH (Area di Valore Alto)",
        "val_label": "VAL (Area di Valore Basso)",
        "fear_greed_label": "😱 Indice Paura e Avidità",
        "medo_extremo": "Paura Estrema",
        "medo": "Paura",
        "neutro_fg": "Neutro",
        "ganancia": "Avidità",
        "ganancia_extrema": "Avidità Estrema",
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
        "titulo": "🏦  BRICSVAULT PORTAL - เครื่องมือ Smart Money Concepts (SMC)",
        "config_globais": "⚙️  การตั้งค่าสากล",
        "selecione_cripto": "เลือกคริปโตใดๆ (/USDT):",
        "tempo_grafico": "กรอบเวลา:",
        "modo_vivo": "เปิดการติดตามแบบเรียลไทม์",
        "intervalo_refresh": "ช่วงรีเฟรช (วินาที):",
        "preco_spot": "ราคาสปอตจริง",
        "variacao_24h": "เปลี่ยนแปลง 24ชม. (Exchange)",
        "market_cap": "มูลค่าตลาด (USD)",
        "stop_atr": "ราคาหยุด ATR",
        "compra_forte": "🟢  ซื้อแข็งแกร่ง (SMC + ฟิโบนัชชีตรงกัน)",
        "venda_forte": "🔴  ขายแข็งแกร่ง (SMC + ฟิโบนัชชีตรงกัน)",
        "neutro": "🟡  เป็นกลาง (รอ SMC)",
        "spike_alta": "🚀  ตรวจพบสัญญาณพุ่งขึ้น (วอลุ่ม + OBV + ช่วง)",
        "spike_baixa": "💥  ตรวจพบสัญญาณดิ่งลง (วอลุ่ม + OBV + ช่วง)",
        "erro_dados": "ข้อมูลย้อนหลังไม่เพียงพอใน Exchange นี้ เลือกสินทรัพย์อื่นหรือลดกรอบเวลา",
        "ctx_desconto": "สินทรัพย์ในเขตส่วนลดฟิโบนัชชี (ความเสี่ยง/ผลตอบแทนดีเยี่ยมสำหรับสถาบัน)",
        "ctx_premium": "สินทรัพย์ในเขตพรีเมียมฟิโบนัชชี (ราคายืด เหมาะสำหรับทำกำไร)",
        "ctx_neutro": "ราคาในเขตฟิโบนัชชีเป็นกลาง (เขตมูลค่ายุติธรรม)",
        "ultima_atualizacao": "อัปเดตล่าสุด",
        "proximo_refresh": "รีเฟรชครั้งถัดไปใน",
        "segundos": "วินาที",
        "pontos_compra": "คะแนนซื้อ",
        "pontos_venda": "คะแนนขาย",
        "sinal_spike": "ความผันผวนพุ่ง",
        "grafico_titulo": "📈  กราฟราคาแบบโต้ตอบ",
        "buscando_marketcap": "🔍  กำลังดึงมูลค่าตลาด...",
        "marketcap_nao_disponivel": "ไม่พร้อมใช้งาน",
        "idioma_label": "🌐  ภาษา / Language",
        "idioma_selecao": "เลือกภาษาอินเทอร์เฟซ:",
        "aviso_aquecimento": "⚠️ แท่งเทียนอุ่นเครื่องที่ใช้ในการคำนวณ",
        "backtest_titulo": "📊 การทดสอบย้อนหลัง — 100 สัญญาณล่าสุด",
        "backtest_compra": "ซื้อ",
        "backtest_venda": "ขาย",
        "backtest_total": "รวมสัญญาณ",
        "backtest_acertos": "สำเร็จ",
        "backtest_taxa": "อัตราสำเร็จ",
        "backtest_historico": "ประวัติสัญญาณล่าสุด",
        "backtest_data": "วันที่/เวลา",
        "backtest_sinal": "สัญญาณ",
        "backtest_preco": "ราคาเข้า",
        "backtest_resultado": "ผลลัพธ์",
        "backtest_acerto": "✅ สำเร็จ",
        "backtest_erro": "❌ ล้มเหลว",
        "poc_label": "POC (จุดควบคุม)",
        "vah_label": "VAH (พื้นที่มูลค่าสูง)",
        "val_label": "VAL (พื้นที่มูลค่าต่ำ)",
        "fear_greed_label": "😱 ดัชนีความกลัวและความโลภ",
        "medo_extremo": "กลัวสุดขีด",
        "medo": "กลัว",
        "neutro_fg": "เป็นกลาง",
        "ganancia": "โลภ",
        "ganancia_extrema": "โลภสุดขีด",
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
        "titulo": "🏦  BRICSVAULT PORTAL - Mesin Smart Money Concepts (SMC)",
        "config_globais": "⚙️  Pengaturan Global",
        "selecione_cripto": "Pilih Mata Uang Kripto (/USDT):",
        "tempo_grafico": "Jangka Waktu:",
        "modo_vivo": "Aktifkan Pemantauan Real-Time",
        "intervalo_refresh": "Interval Penyegaran (Detik):",
        "preco_spot": "Harga Spot Real",
        "variacao_24h": "Perubahan 24j (Exchange)",
        "market_cap": "Kapitalisasi Pasar (USD)",
        "stop_atr": "Harga Stop ATR",
        "compra_forte": "🟢  BELI KUAT (SMC + FIBONACCI SELARAS)",
        "venda_forte": "🔴  JUAL KUAT (SMC + FIBONACCI SELARAS)",
        "neutro": "🟡  NETRAL (TUNGGU SMC)",
        "spike_alta": "🚀  SPIKE NAIK TERDETEKSI (Volume + OBV + Rentang)",
        "spike_baixa": "💥  SPIKE TURUN TERDETEKSI (Volume + OBV + Rentang)",
        "erro_dados": "Data historis tidak mencukupi di Exchange ini. Pilih aset lain atau kurangi Jangka Waktu.",
        "ctx_desconto": "Aset di Zona Diskon Fibonacci (Risiko/imbal hasil sangat baik untuk Institusional).",
        "ctx_premium": "Aset di Zona Premium Fibonacci (Harga melar, cocok untuk mengambil untung).",
        "ctx_neutro": "Harga di zona Fibonacci netral (Zona Nilai Wajar).",
        "ultima_atualizacao": "Pembaruan Terakhir",
        "proximo_refresh": "Penyegaran berikutnya dalam",
        "segundos": "detik",
        "pontos_compra": "Poin Beli",
        "pontos_venda": "Poin Jual",
        "sinal_spike": "Lonjakan Volatilitas",
        "grafico_titulo": "📈  Grafik Harga Interaktif",
        "buscando_marketcap": "🔍  Mengambil Kapitalisasi Pasar...",
        "marketcap_nao_disponivel": "Tidak tersedia",
        "idioma_label": "🌐  Bahasa / Language",
        "idioma_selecao": "Pilih bahasa antarmuka:",
        "aviso_aquecimento": "⚠️ Lilin pemanasan digunakan dalam perhitungan",
        "backtest_titulo": "📊 Backtesting — 100 Sinyal Terakhir",
        "backtest_compra": "Beli",
        "backtest_venda": "Jual",
        "backtest_total": "Total Sinyal",
        "backtest_acertos": "Berhasil",
        "backtest_taxa": "Tingkat Keberhasilan",
        "backtest_historico": "Riwayat Sinyal Terbaru",
        "backtest_data": "Tanggal/Waktu",
        "backtest_sinal": "Sinyal",
        "backtest_preco": "Harga Masuk",
        "backtest_resultado": "Hasil",
        "backtest_acerto": "✅ Berhasil",
        "backtest_erro": "❌ Gagal",
        "poc_label": "POC (Titik Kendali)",
        "vah_label": "VAH (Area Nilai Atas)",
        "val_label": "VAL (Area Nilai Bawah)",
        "fear_greed_label": "😱 Indeks Takut & Serakah",
        "medo_extremo": "Takut Ekstrem",
        "medo": "Takut",
        "neutro_fg": "Netral",
        "ganancia": "Serakah",
        "ganancia_extrema": "Serakah Ekstrem",
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
# FEAR & GREED INDEX (alternative.me — API gratuita, sem chave)
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
# MARKET CAP — CoinGecko (endpoint /coins/markets com busca por símbolo)
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
        elif response.status_code == 429:
            return None

        coin_id_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
            "BNB": "binancecoin", "XRP": "ripple", "ADA": "cardano",
            "DOGE": "dogecoin", "TRX": "tron", "DOT": "polkadot",
            "MATIC": "matic-network", "POL": "matic-network", "LTC": "litecoin",
            "AVAX": "avalanche-2", "LINK": "chainlink", "UNI": "uniswap",
            "ATOM": "cosmos", "XLM": "stellar", "ETC": "ethereum-classic",
            "FIL": "filecoin", "NEAR": "near", "APT": "aptos",
            "ARB": "arbitrum", "OP": "optimism", "SUI": "sui",
            "INJ": "injective-protocol", "SEI": "sei-network",
            "TON": "the-open-network", "PEPE": "pepe", "SHIB": "shiba-inu",
            "WIF": "dogwifcoin", "BONK": "bonk", "FET": "fetch-ai",
            "RENDER": "render-token", "TAO": "bittensor",
            "JUP": "jupiter-exchange-solana", "W": "wormhole",
            "PYTH": "pyth-network", "STRK": "starknet",
            "MANTA": "manta-network", "LIT": "litentry",
            "HBAR": "hedera-hashgraph", "VET": "vechain",
            "ALGO": "algorand", "SAND": "the-sandbox",
            "MANA": "decentraland", "AXS": "axie-infinity",
            "CRV": "curve-dao-token", "AAVE": "aave",
            "MKR": "maker", "SNX": "synthetix-network-token",
            "GRT": "the-graph", "LDO": "lido-dao",
            "IMX": "immutable-x", "RUNE": "thorchain",
            "FLOKI": "floki", "CFX": "conflux-token",
            "KAVA": "kava", "ZIL": "zilliqa",
            "BLUR": "blur", "MAGIC": "magic",
        }
        coin_id = coin_id_map.get(simbolo.upper())
        if coin_id:
            params2 = {
                "vs_currency": "usd",
                "ids": coin_id,
                "order": "market_cap_desc",
                "per_page": 1,
                "page": 1,
                "sparkline": "false"
            }
            resp2 = requests.get(url, params=params2, headers=headers, timeout=10)
            if resp2.status_code == 200:
                dados2 = resp2.json()
                if dados2 and len(dados2) > 0:
                    mc2 = dados2[0].get("market_cap")
                    if mc2 and float(mc2) > 1_000_000:
                        return float(mc2)
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
    if spike_range:
        score += 1
    if spike_volume:
        score += 1
    if spike_obv and not (np.isnan(obv_acel) or np.isinf(obv_acel)):
        score += 1

    if score >= 2:
        if direcao > 0:
            return "ALTA"
        else:
            return "BAIXA"

    return None


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
# CARREGAMENTO DE DADOS
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
# ANÁLISE DE CONFLUÊNCIA SMC
def analisar_confluencia(df_completo, txt):
    df_analise = df_completo.iloc[PERIODO_AQUECIMENTO:].copy()

    if df_analise.empty:
        return txt["neutro"], "#ffcc00", txt["ctx_neutro"], 0.0, 0.0, None, None, None, None

    u = df_analise.iloc[-1]
    preco_atual = u['close']

    fib_niveis = calcular_retracao_fibonacci(df_analise)
    poc, vah, val = calcular_volume_profile(df_analise)

    pontos_alta = 0.0
    pontos_baixa = 0.0

    rsi_val = u['RSI_14']
    if not math.isnan(rsi_val):
        if rsi_val < 40:
            pontos_alta += 2
        elif rsi_val > 60:
            pontos_baixa += 2

    macd_hist = u['MACD_HIST']
    if not math.isnan(macd_hist):
        if macd_hist > 0:
            pontos_alta += 2
        else:
            pontos_baixa += 2

    obv_acel = u.get('OBV_Aceleracao', 0)
    if not (np.isnan(obv_acel) or np.isinf(obv_acel)):
        if obv_acel > 0:
            pontos_alta += 1.5
        else:
            pontos_baixa += 1.5

    vol_ratio = u.get('Volume_Ratio', 1)
    if vol_ratio > 2.0:
        if macd_hist > 0:
            pontos_alta += 1
        else:
            pontos_baixa += 1

    mfi_val = u['MFI']
    if not math.isnan(mfi_val):
        if mfi_val > 50:
            pontos_alta += 1
        else:
            pontos_baixa += 1

    if u['ssl_dir'] == 1:
        pontos_alta += 1
    else:
        pontos_baixa += 1

    if u['atr_dir'] == 1:
        pontos_alta += 1
    else:
        pontos_baixa += 1

    ppo_val = u['PPO']
    ppo_sig = u['PPO_Signal']
    if not (math.isnan(ppo_val) or math.isnan(ppo_sig)):
        if ppo_val > ppo_sig:
            pontos_alta += 1.5
        else:
            pontos_baixa += 1.5

    if poc is not None and vah is not None and val is not None:
        if preco_atual <= val:
            pontos_alta += 1.5
        elif preco_atual >= vah:
            pontos_baixa += 1.5

    if preco_atual >= fib_niveis['fib_382']:
        pontos_baixa += 2.0
        contexto_fib = txt["ctx_premium"]
    elif preco_atual <= fib_niveis['fib_618']:
        pontos_alta += 2.0
        contexto_fib = txt["ctx_desconto"]
    else:
        contexto_fib = txt["ctx_neutro"]

    spike = detectar_spike_volatilidade(df_analise)

    if pontos_alta >= 8.5:
        return (
            txt["compra_forte"], "#00cc66",
            f"{contexto_fib} SMC + PPO Order Flow Bullish.",
            pontos_alta, pontos_baixa, spike, poc, vah, val
        )
    elif pontos_baixa >= 8.5:
        return (
            txt["venda_forte"], "#ff3333",
            f"{contexto_fib} SMC + PPO Order Flow Bearish.",
            pontos_alta, pontos_baixa, spike, poc, vah, val
        )
    else:
        return txt["neutro"], "#ffcc00", contexto_fib, pontos_alta, pontos_baixa, spike, poc, vah, val


# ─────────────────────────────────────────────────────────────────────────────
# BACKTESTING SIMPLES
def executar_backtesting(df_completo, txt):
    df_analise = df_completo.iloc[PERIODO_AQUECIMENTO:].copy()
    if len(df_analise) < 150:
        return None, None, None, None, []

    sinais_compra = 0
    sinais_venda = 0
    acertos_compra = 0
    acertos_venda = 0
    historico = []

    inicio = max(0, len(df_analise) - 105)
    for i in range(inicio, len(df_analise) - 5):
        janela = df_analise.iloc[:i+1]
        if len(janela) < PERIODO_AQUECIMENTO:
            continue

        u = janela.iloc[-1]
        preco_entrada = u['close']

        rsi_val = u['RSI_14']
        macd_hist = u['MACD_HIST']
        ssl_dir = u.get('ssl_dir', 0)
        atr_dir = u.get('atr_dir', 0)

        score_alta = 0
        score_baixa = 0
        if not math.isnan(rsi_val):
            if rsi_val < 40: score_alta += 2
            elif rsi_val > 60: score_baixa += 2
        if not math.isnan(macd_hist):
            if macd_hist > 0: score_alta += 2
            else: score_baixa += 2
        if ssl_dir == 1: score_alta += 1
        else: score_baixa += 1
        if atr_dir == 1: score_alta += 1
        else: score_baixa += 1

        tipo_sinal = None
        if score_alta >= 4:
            tipo_sinal = "COMPRA"
            sinais_compra += 1
        elif score_baixa >= 4:
            tipo_sinal = "VENDA"
            sinais_venda += 1

        if tipo_sinal:
            preco_futuro = df_analise.iloc[i + 5]['close']
            variacao = ((preco_futuro - preco_entrada) / preco_entrada) * 100

            acerto = False
            if tipo_sinal == "COMPRA" and variacao > 0.5:
                acerto = True
                acertos_compra += 1
            elif tipo_sinal == "VENDA" and variacao < -0.5:
                acerto = True
                acertos_venda += 1

            historico.append({
                'data': df_analise.iloc[i]['time'],
                'sinal': tipo_sinal,
                'preco_entrada': preco_entrada,
                'variacao': variacao,
                'acerto': acerto
            })

    total_sinais = sinais_compra + sinais_venda
    total_acertos = acertos_compra + acertos_venda
    taxa_acerto = (total_acertos / total_sinais * 100) if total_sinais > 0 else 0

    return sinais_compra, sinais_venda, total_acertos, taxa_acerto, historico


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
        fig.add_hline(
            y=poc,
            line_dash="dash",
            line_color="#ffdd57",
            annotation_text=f"{txt.get('poc_label', 'POC')}: {formatar_preco(poc)}",
            annotation_position="bottom right",
            annotation_font=dict(color="#ffdd57", size=10)
        )
    if vah is not None:
        fig.add_hline(
            y=vah,
            line_dash="dot",
            line_color="#ff6b6b",
            annotation_text=f"{txt.get('vah_label', 'VAH')}: {formatar_preco(vah)}",
            annotation_position="bottom right",
            annotation_font=dict(color="#ff6b6b", size=10)
        )
    if val is not None:
        fig.add_hline(
            y=val,
            line_dash="dot",
            line_color="#51cf66",
            annotation_text=f"{txt.get('val_label', 'VAL')}: {formatar_preco(val)}",
            annotation_position="bottom right",
            annotation_font=dict(color="#51cf66", size=10)
        )

    fig.update_layout(
        paper_bgcolor='#0b0f19',
        plot_bgcolor='#0b0f19',
        font=dict(color='#e2e8f0'),
        xaxis=dict(
            gridcolor='#1e293b',
            showgrid=True,
            rangeslider=dict(visible=False)
        ),
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
    index=lista_criptos.index("SOL/USDT") if "SOL/USDT" in lista_criptos else 0
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

    recomendacao, cor_sinal, analise, pontos_alta, pontos_baixa, spike, poc, vah, val = analisar_confluencia(
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

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if fg_valor is not None:
            fg_emoji = ""
            if fg_valor <= 25:
                fg_emoji = "😱"
            elif fg_valor <= 45:
                fg_emoji = "😟"
            elif fg_valor <= 55:
                fg_emoji = "😐"
            elif fg_valor <= 75:
                fg_emoji = "😀"
            else:
                fg_emoji = "🤩"
            st.metric(
                txt["fear_greed_label"],
                f"{fg_emoji} {fg_valor}/100",
                delta=fg_classificacao,
                delta_color="off"
            )
        else:
            st.metric(txt["fear_greed_label"], "—")

    with col2:
        st.metric("POC (Volume Profile)", formatar_preco(poc) if poc else "—")

    with col3:
        obv_val = ultimo_reg.get('OBV', 0)
        obv_acel = ultimo_reg.get('OBV_Aceleracao', 0)
        if not (np.isnan(obv_acel) or np.isinf(obv_acel)):
            st.metric("OBV Aceleração", f"{obv_acel:,.0f}")
        else:
            st.metric("OBV Aceleração", "—")

    with col4:
        vol_ratio = ultimo_reg.get('Volume_Ratio', 1)
        if not np.isnan(vol_ratio):
            st.metric("Volume Ratio", f"{vol_ratio:.2f}x")
        else:
            st.metric("Volume Ratio", "—")

    atr_stop_val = ultimo_reg['ATR_Stop']
    st.markdown(
        f"**{txt['stop_atr']}:** {formatar_preco(atr_stop_val)}"
        f"  |  RSI: **{ultimo_reg['RSI_14']:.1f}**"
        f"  |  MFI: **{ultimo_reg['MFI']:.1f}**"
        f"  |  MACD Hist: **{ultimo_reg['MACD_HIST']:.6f}**"
    )

    st.markdown(f"### {txt['grafico_titulo']}")
    renderizar_grafico_plotly(df_dados, simbolo_id, poc, vah, val, txt)

    if poc is not None:
        st.caption(
            f"📊 **Volume Profile:** POC = {formatar_preco(poc)} | "
            f"VAH = {formatar_preco(vah)} | "
            f"VAL = {formatar_preco(val)} | "
            f"Preço atual: {'🟡 Equilíbrio (perto do POC)' if val <= preco_atual <= vah else ('🔴 Distribuição (acima do VAH)' if preco_atual > vah else '🟢 Acumulação (abaixo do VAL)')}"
        )

    st.markdown("---")
    st.markdown(f"### {txt['backtest_titulo']}")

    sinais_compra, sinais_venda, total_acertos, taxa_acerto, historico = executar_backtesting(df_dados, txt)

    if sinais_compra is not None and sinais_venda is not None:
        bt1, bt2, bt3, bt4, bt5 = st.columns(5)
        bt1.metric(txt["backtest_compra"], sinais_compra)
        bt2.metric(txt["backtest_venda"], sinais_venda)
        bt3.metric(txt["backtest_total"], sinais_compra + sinais_venda)
        bt4.metric(txt["backtest_acertos"], total_acertos)
        bt5.metric(txt["backtest_taxa"], f"{taxa_acerto:.1f}%")

        if historico:
            st.markdown(f"**{txt['backtest_historico']}**")
            hist_df = pd.DataFrame(historico[-10:][::-1])
            hist_df['Resultado'] = hist_df['acerto'].apply(
                lambda x: txt["backtest_acerto"] if x else txt["backtest_erro"]
            )
            hist_df['Preço'] = hist_df['preco_entrada'].apply(lambda x: formatar_preco(x))
            hist_df['Var %'] = hist_df['variacao'].apply(lambda x: f"{x:+.2f}%")
            hist_df_display = hist_df[['data', 'sinal', 'Preço', 'Var %', 'Resultado']].copy()
            hist_df_display.columns = [
                txt["backtest_data"], txt["backtest_sinal"],
                txt["backtest_preco"], 'Var %', txt["backtest_resultado"]
            ]
            st.dataframe(hist_df_display, use_container_width=True, hide_index=True)
    else:
        st.info("Backtesting requer mais dados históricos. Aguarde mais candles.")

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
