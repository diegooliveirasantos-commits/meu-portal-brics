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
# CONSTANTES DE AQUECIMENTO
VELAS_TOTAL = 500
PERIODO_AQUECIMENTO = 100

# ─────────────────────────────────────────────────────────────────────────────
# DICIONÁRIO DE IDIOMAS – 15 línguas (com "Preço Atual")
DICIONARIO_LINGUAS = {
    "Português (BR)": {
        "titulo": "🏦  BRICSVAULT PORTAL - Motor de Smart Money Concepts (SMC)",
        "config_globais": "⚙️  Configurações Globais",
        "selecione_cripto": "Selecione Qualquer Criptomoeda (/USDT):",
        "tempo_grafico": "Tempo Gráfico:",
        "modo_vivo": "Ativar Monitoramento em Tempo Real",
        "intervalo_refresh": "Intervalo de Atualização (Segundos):",
        "preco_spot": "Preço Atual",
        "variacao_24h": "Variação 24h",
        "volume_24h": "Volume 24h (USDT)",
        "market_cap": "Market Cap (USD)",
        "stop_atr": "Preço Stop ATR",
        "compra_forte": "🟢  COMPRA FORTE (SMC + FIBONACCI ALINHADOS)",
        "venda_forte": "🔴  VENDA FORTE (SMC + FIBONACCI ALINHADOS)",
        "neutro": "🟡  NEUTRO (AGUARDAR SMC)",
        "erro_dados": "Dados históricos insuficientes. Tente outro ativo ou reduza o Tempo Gráfico.",
        "ctx_desconto": "Ativo em Zona de Desconto de Fibonacci (Excelente risco/retorno para Institucionais).",
        "ctx_premium": "Ativo em Zona Premium de Fibonacci (Preço esticado, propício para realização de lucro).",
        "ctx_neutro": "Preço em zona neutra de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Última Atualização",
        "proximo_refresh": "Próximo refresh em",
        "segundos": "segundos",
        "pontos_compra": "Pontos de Compra",
        "pontos_venda": "Pontos de Venda",
        "grafico_titulo": "📈  Gráfico de Preço Interativo",
        "buscando_marketcap": "🔍  Buscando Market Cap...",
        "marketcap_nao_disponivel": "Não disponível",
        "idioma_label": "🌐  Idioma / Language",
        "idioma_selecao": "Selecione o idioma da interface:",
        "aviso_aquecimento": "⚠️ Velas de aquecimento usadas no cálculo",
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
        "preco_spot": "Current Price",
        "variacao_24h": "24h Variation",
        "volume_24h": "24h Volume (USDT)",
        "market_cap": "Market Cap (USD)",
        "stop_atr": "ATR Stop Price",
        "compra_forte": "🟢  STRONG BUY (SMC + FIBONACCI ALIGNED)",
        "venda_forte": "🔴  STRONG SELL (SMC + FIBONACCI ALIGNED)",
        "neutro": "🟡  NEUTRAL (AWAIT SMC)",
        "erro_dados": "Insufficient historical data. Try another asset or reduce the Timeframe.",
        "ctx_desconto": "Asset in Fibonacci Discount Zone (Excellent risk/reward for Institutionals).",
        "ctx_premium": "Asset in Fibonacci Premium Zone (Price stretched, suitable for profit-taking).",
        "ctx_neutro": "Price in neutral Fibonacci zone (Fair Value Zone).",
        "ultima_atualizacao": "Last Update",
        "proximo_refresh": "Next refresh in",
        "segundos": "seconds",
        "pontos_compra": "Buy Points",
        "pontos_venda": "Sell Points",
        "grafico_titulo": "📈  Interactive Price Chart",
        "buscando_marketcap": "🔍  Fetching Market Cap...",
        "marketcap_nao_disponivel": "Not available",
        "idioma_label": "🌐  Language / Idioma",
        "idioma_selecao": "Select Interface Language:",
        "aviso_aquecimento": "⚠️ Warm-up candles used in calculation",
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
    "Español": {
        "titulo": "🏦  BRICSVAULT PORTAL - Motor de Smart Money Concepts (SMC)",
        "config_globais": "⚙️  Configuraciones Globales",
        "selecione_cripto": "Seleccione cualquier criptomoneda (/USDT):",
        "tempo_grafico": "Marco temporal:",
        "modo_vivo": "Activar monitoreo en tiempo real",
        "intervalo_refresh": "Intervalo de actualización (segundos):",
        "preco_spot": "Precio Actual",
        "variacao_24h": "Variación 24h",
        "volume_24h": "Volumen 24h (USDT)",
        "market_cap": "Capitalización (USD)",
        "stop_atr": "Precio Stop ATR",
        "compra_forte": "🟢  COMPRA FUERTE (SMC + FIBONACCI ALINEADOS)",
        "venda_forte": "🔴  VENTA FUERTE (SMC + FIBONACCI ALINEADOS)",
        "neutro": "🟡  NEUTRO (ESPERAR SMC)",
        "erro_dados": "Datos históricos insuficientes. Pruebe con otro activo o reduzca el marco temporal.",
        "ctx_desconto": "Activo en Zona de Descuento de Fibonacci (Excelente riesgo/retorno para Institucionales).",
        "ctx_premium": "Activo en Zona Premium de Fibonacci (Precio estirado, propicio para toma de ganancias).",
        "ctx_neutro": "Precio en zona neutral de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Última actualización",
        "proximo_refresh": "Próxima actualización en",
        "segundos": "segundos",
        "pontos_compra": "Puntos de Compra",
        "pontos_venda": "Puntos de Venta",
        "grafico_titulo": "📈  Gráfico de Precio Interactivo",
        "buscando_marketcap": "🔍  Buscando Capitalización...",
        "marketcap_nao_disponivel": "No disponible",
        "idioma_label": "🌐  Idioma / Language",
        "idioma_selecao": "Seleccione el idioma de la interfaz:",
        "aviso_aquecimento": "⚠️ Velas de calentamiento usadas en el cálculo",
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
    "Français": {
        "titulo": "🏦  BRICSVAULT PORTAL - Moteur Smart Money Concepts (SMC)",
        "config_globais": "⚙️  Paramètres globaux",
        "selecione_cripto": "Sélectionnez une cryptomonnaie (/USDT):",
        "tempo_grafico": "Période:",
        "modo_vivo": "Activer la surveillance en temps réel",
        "intervalo_refresh": "Intervalle de rafraîchissement (secondes):",
        "preco_spot": "Prix Actuel",
        "variacao_24h": "Variation 24h",
        "volume_24h": "Volume 24h (USDT)",
        "market_cap": "Capitalisation (USD)",
        "stop_atr": "Prix Stop ATR",
        "compra_forte": "🟢  ACHAT FORT (SMC + FIBONACCI ALIGNÉS)",
        "venda_forte": "🔴  VENTE FORTE (SMC + FIBONACCI ALIGNÉS)",
        "neutro": "🟡  NEUTRE (ATTENDRE SMC)",
        "erro_dados": "Données historiques insuffisantes. Essayez un autre actif ou réduisez la période.",
        "ctx_desconto": "Actif en zone de discount de Fibonacci (Excellent risque/rendement pour les institutionnels).",
        "ctx_premium": "Actif en zone premium de Fibonacci (Prix étiré, propice à la prise de bénéfices).",
        "ctx_neutro": "Prix en zone neutre de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Dernière mise à jour",
        "proximo_refresh": "Prochain rafraîchissement dans",
        "segundos": "secondes",
        "pontos_compra": "Points d'achat",
        "pontos_venda": "Points de vente",
        "grafico_titulo": "📈  Graphique de prix interactif",
        "buscando_marketcap": "🔍  Recherche de la capitalisation...",
        "marketcap_nao_disponivel": "Indisponible",
        "idioma_label": "🌐  Langue / Language",
        "idioma_selecao": "Sélectionnez la langue de l'interface:",
        "aviso_aquecimento": "⚠️ Bougies de chauffe utilisées dans le calcul",
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
    "Deutsch": {
        "titulo": "🏦  BRICSVAULT PORTAL - Smart Money Concepts (SMC) Motor",
        "config_globais": "⚙️  Globale Einstellungen",
        "selecione_cripto": "Wählen Sie eine Kryptowährung (/USDT):",
        "tempo_grafico": "Zeitrahmen:",
        "modo_vivo": "Echtzeit-Überwachung aktivieren",
        "intervalo_refresh": "Aktualisierungsintervall (Sekunden):",
        "preco_spot": "Aktueller Preis",
        "variacao_24h": "24h-Veränderung",
        "volume_24h": "24h-Volumen (USDT)",
        "market_cap": "Marktkapitalisierung (USD)",
        "stop_atr": "ATR-Stop-Preis",
        "compra_forte": "🟢  STARKER KAUF (SMC + FIBONACCI AUSGERICHTET)",
        "venda_forte": "🔴  STARKER VERKAUF (SMC + FIBONACCI AUSGERICHTET)",
        "neutro": "🟡  NEUTRAL (SMC ABWARTEN)",
        "erro_dados": "Unzureichende historische Daten. Versuchen Sie es mit einem anderen Vermögenswert oder reduzieren Sie den Zeitrahmen.",
        "ctx_desconto": "Vermögenswert in Fibonacci-Discount-Zone (Ausgezeichnetes Risiko/Rendite für Institutionelle).",
        "ctx_premium": "Vermögenswert in Fibonacci-Premium-Zone (Preis gedehnt, gewinnmitnahme geeignet).",
        "ctx_neutro": "Preis in neutraler Fibonacci-Zone (Fair Value Zone).",
        "ultima_atualizacao": "Letzte Aktualisierung",
        "proximo_refresh": "Nächste Aktualisierung in",
        "segundos": "Sekunden",
        "pontos_compra": "Kaufpunkte",
        "pontos_venda": "Verkaufspunkte",
        "grafico_titulo": "📈  Interaktives Kursdiagramm",
        "buscando_marketcap": "🔍  Marktkapitalisierung wird abgerufen...",
        "marketcap_nao_disponivel": "Nicht verfügbar",
        "idioma_label": "🌐  Sprache / Language",
        "idioma_selecao": "Wählen Sie die Oberflächensprache:",
        "aviso_aquecimento": "⚠️ Aufwärm-Kerzen im Rechengang verwendet",
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
    "Italiano": {
        "titulo": "🏦  BRICSVAULT PORTAL - Motore Smart Money Concepts (SMC)",
        "config_globais": "⚙️  Impostazioni globali",
        "selecione_cripto": "Seleziona una criptovaluta (/USDT):",
        "tempo_grafico": "Timeframe:",
        "modo_vivo": "Attiva monitoraggio in tempo reale",
        "intervalo_refresh": "Intervallo di aggiornamento (secondi):",
        "preco_spot": "Prezzo Corrente",
        "variacao_24h": "Variazione 24h",
        "volume_24h": "Volume 24h (USDT)",
        "market_cap": "Capitalizzazione (USD)",
        "stop_atr": "Prezzo Stop ATR",
        "compra_forte": "🟢  ACQUISTO FORTE (SMC + FIBONACCI ALLINEATI)",
        "venda_forte": "🔴  VENDITA FORTE (SMC + FIBONACCI ALLINEATI)",
        "neutro": "🟡  NEUTRO (ATTENDERE SMC)",
        "erro_dados": "Dati storici insufficienti. Prova un altro asset o riduci il timeframe.",
        "ctx_desconto": "Asset in Zona di Sconto di Fibonacci (Ottimo rischio/rendimento per Istituzionali).",
        "ctx_premium": "Asset in Zona Premium di Fibonacci (Prezzo allungato, adatto per presa di profitto).",
        "ctx_neutro": "Prezzo in zona neutrale di Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Ultimo aggiornamento",
        "proximo_refresh": "Prossimo aggiornamento tra",
        "segundos": "secondi",
        "pontos_compra": "Punti di Acquisto",
        "pontos_venda": "Punti di Vendita",
        "grafico_titulo": "📈  Grafico Prezzo Interattivo",
        "buscando_marketcap": "🔍  Ricerca Capitalizzazione...",
        "marketcap_nao_disponivel": "Non disponibile",
        "idioma_label": "🌐  Lingua / Language",
        "idioma_selecao": "Seleziona la lingua dell'interfaccia:",
        "aviso_aquecimento": "⚠️ Candele di riscaldamento utilizzate nel calcolo",
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
    "Русский": {
        "titulo": "🏦  BRICSVAULT PORTAL - Двигатель Smart Money Concepts (SMC)",
        "config_globais": "⚙️  Глобальные настройки",
        "selecione_cripto": "Выберите криптовалюту (/USDT):",
        "tempo_grafico": "Таймфрейм:",
        "modo_vivo": "Включить мониторинг в реальном времени",
        "intervalo_refresh": "Интервал обновления (секунды):",
        "preco_spot": "Текущая цена",
        "variacao_24h": "Изменение за 24ч",
        "volume_24h": "Объем за 24ч (USDT)",
        "market_cap": "Рыночная капитализация (USD)",
        "stop_atr": "Цена стоп-лосса ATR",
        "compra_forte": "🟢  СИЛЬНАЯ ПОКУПКА (SMC + ФИБОНАЧЧИ СОГЛАСОВАНЫ)",
        "venda_forte": "🔴  СИЛЬНАЯ ПРОДАЖА (SMC + ФИБОНАЧЧИ СОГЛАСОВАНЫ)",
        "neutro": "🟡  НЕЙТРАЛЬНО (ОЖИДАТЬ SMC)",
        "erro_dados": "Недостаточно исторических данных. Попробуйте другой актив или уменьшите таймфрейм.",
        "ctx_desconto": "Актив в зоне скидки Фибоначчи (Отличное соотношение риск/доходность для институционалов).",
        "ctx_premium": "Актив в премиальной зоне Фибоначчи (Цена растянута, подходит для фиксации прибыли).",
        "ctx_neutro": "Цена в нейтральной зоне Фибоначчи (Fair Value Zone).",
        "ultima_atualizacao": "Последнее обновление",
        "proximo_refresh": "Следующее обновление через",
        "segundos": "секунд",
        "pontos_compra": "Очки покупки",
        "pontos_venda": "Очки продажи",
        "grafico_titulo": "📈  Интерактивный график цены",
        "buscando_marketcap": "🔍  Получение рыночной капитализации...",
        "marketcap_nao_disponivel": "Недоступно",
        "idioma_label": "🌐  Язык / Language",
        "idioma_selecao": "Выберите язык интерфейса:",
        "aviso_aquecimento": "⚠️ Используются свечи разогрева в расчетах",
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
    "日本語": {
        "titulo": "🏦  BRICSVAULT PORTAL - スマートマネーコンセプト（SMC）エンジン",
        "config_globais": "⚙️  グローバル設定",
        "selecione_cripto": "暗号通貨を選択（/USDT）:",
        "tempo_grafico": "タイムフレーム:",
        "modo_vivo": "リアルタイム監視を有効にする",
        "intervalo_refresh": "更新間隔（秒）:",
        "preco_spot": "現在価格",
        "variacao_24h": "24時間変動",
        "volume_24h": "24時間出来高（USDT）",
        "market_cap": "時価総額（USD）",
        "stop_atr": "ATRストップ価格",
        "compra_forte": "🟢  強い買い（SMC＋フィボナッチ整合）",
        "venda_forte": "🔴  強い売り（SMC＋フィボナッチ整合）",
        "neutro": "🟡  中立（SMC待機）",
        "erro_dados": "履歴データが不十分です。別の資産を選ぶか、タイムフレームを小さくしてください。",
        "ctx_desconto": "フィボナッチ割引ゾーンにある資産（機関投資家向けの優れたリスク/リターン）。",
        "ctx_premium": "フィボナッチプレミアムゾーンにある資産（価格が伸びており、利益確定に適している）。",
        "ctx_neutro": "フィボナッチ中立ゾーンの価格（フェアバリューゾーン）。",
        "ultima_atualizacao": "最終更新",
        "proximo_refresh": "次の更新まで",
        "segundos": "秒",
        "pontos_compra": "買いポイント",
        "pontos_venda": "売りポイント",
        "grafico_titulo": "📈  インタラクティブ価格チャート",
        "buscando_marketcap": "🔍  時価総額を取得中...",
        "marketcap_nao_disponivel": "利用不可",
        "idioma_label": "🌐  言語 / Language",
        "idioma_selecao": "インターフェース言語を選択:",
        "aviso_aquecimento": "⚠️ 計算にウォームアップローソクを使用",
        "intervalos": {
            "1分": "1m",
            "5分": "5m",
            "15分": "15m",
            "30分": "30m",
            "1時間": "1h",
            "4時間": "4h",
            "1日": "1d",
            "1週間": "1w"
        }
    },
    "中文 (简体)": {
        "titulo": "🏦  BRICSVAULT PORTAL - 智能资金概念（SMC）引擎",
        "config_globais": "⚙️  全局设置",
        "selecione_cripto": "选择加密货币（/USDT）：",
        "tempo_grafico": "时间周期：",
        "modo_vivo": "启用实时监控",
        "intervalo_refresh": "刷新间隔（秒）：",
        "preco_spot": "当前价格",
        "variacao_24h": "24小时变化",
        "volume_24h": "24小时成交量（USDT）",
        "market_cap": "市值（美元）",
        "stop_atr": "ATR止损价",
        "compra_forte": "🟢  强烈买入（SMC + 斐波那契一致）",
        "venda_forte": "🔴  强烈卖出（SMC + 斐波那契一致）",
        "neutro": "🟡  中性（等待SMC）",
        "erro_dados": "历史数据不足。请选择其他资产或缩短时间周期。",
        "ctx_desconto": "资产处于斐波那契折价区（机构级卓越风险/回报）。",
        "ctx_premium": "资产处于斐波那契溢价区（价格拉伸，适合获利了结）。",
        "ctx_neutro": "价格处于斐波那契中性区（公允价值区）。",
        "ultima_atualizacao": "最后更新",
        "proximo_refresh": "下次刷新于",
        "segundos": "秒",
        "pontos_compra": "买入点",
        "pontos_venda": "卖出点",
        "grafico_titulo": "📈  交互式价格图表",
        "buscando_marketcap": "🔍  正在获取市值...",
        "marketcap_nao_disponivel": "不可用",
        "idioma_label": "🌐  语言 / Language",
        "idioma_selecao": "选择界面语言：",
        "aviso_aquecimento": "⚠️ 计算中使用预热K线",
        "intervalos": {
            "1分钟": "1m",
            "5分钟": "5m",
            "15分钟": "15m",
            "30分钟": "30m",
            "1小时": "1h",
            "4小时": "4h",
            "1天": "1d",
            "1周": "1w"
        }
    },
    "हिन्दी": {
        "titulo": "🏦  BRICSVAULT PORTAL - स्मार्ट मनी कॉन्सेप्ट्स (SMC) इंजन",
        "config_globais": "⚙️  वैश्विक सेटिंग्स",
        "selecione_cripto": "कोई भी क्रिप्टोकरेंसी चुनें (/USDT):",
        "tempo_grafico": "टाइमफ्रेम:",
        "modo_vivo": "रीयल-टाइम मॉनिटरिंग सक्षम करें",
        "intervalo_refresh": "रिफ्रेश अंतराल (सेकंड):",
        "preco_spot": "वर्तमान मूल्य",
        "variacao_24h": "24 घंटे का बदलाव",
        "volume_24h": "24 घंटे का वॉल्यूम (USDT)",
        "market_cap": "बाजार पूंजीकरण (USD)",
        "stop_atr": "ATR स्टॉप मूल्य",
        "compra_forte": "🟢  मजबूत खरीद (SMC + फिबोनाची संरेखित)",
        "venda_forte": "🔴  मजबूत बिक्री (SMC + फिबोनाची संरेखित)",
        "neutro": "🟡  तटस्थ (SMC की प्रतीक्षा करें)",
        "erro_dados": "अपर्याप्त ऐतिहासिक डेटा। कोई अन्य संपत्ति चुनें या टाइमफ्रेम कम करें।",
        "ctx_desconto": "संपत्ति फिबोनाची डिस्काउंट ज़ोन में (संस्थागतों के लिए उत्कृष्ट जोखिम/रिटर्न)।",
        "ctx_premium": "संपत्ति फिबोनाची प्रीमियम ज़ोन में (मूल्य खिंचा हुआ, लाभ-बुकिंग के लिए उपयुक्त)।",
        "ctx_neutro": "फिबोनाची तटस्थ क्षेत्र में मूल्य (Fair Value Zone)।",
        "ultima_atualizacao": "अंतिम अद्यतन",
        "proximo_refresh": "अगला रिफ्रेश",
        "segundos": "सेकंड",
        "pontos_compra": "खरीद अंक",
        "pontos_venda": "बिक्री अंक",
        "grafico_titulo": "📈  इंटरैक्टिव मूल्य चार्ट",
        "buscando_marketcap": "🔍  बाजार पूंजीकरण प्राप्त किया जा रहा है...",
        "marketcap_nao_disponivel": "उपलब्ध नहीं",
        "idioma_label": "🌐  भाषा / Language",
        "idioma_selecao": "इंटरफ़ेस भाषा चुनें:",
        "aviso_aquecimento": "⚠️ गणना में वार्म-अप मोमबत्तियों का उपयोग किया गया",
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
    "বাংলা": {
        "titulo": "🏦  BRICSVAULT PORTAL - স্মার্ট মানি কনসেপ্টস (SMC) ইঞ্জিন",
        "config_globais": "⚙️  গ্লোবাল সেটিংস",
        "selecione_cripto": "যেকোনো ক্রিপ্টোকারেন্সি নির্বাচন করুন (/USDT):",
        "tempo_grafico": "টাইমফ্রেম:",
        "modo_vivo": "রিয়েল-টাইম মনিটরিং সক্রিয় করুন",
        "intervalo_refresh": "রিফ্রেশ বিরতি (সেকেন্ড):",
        "preco_spot": "বর্তমান মূল্য",
        "variacao_24h": "২৪ ঘণ্টার পরিবর্তন",
        "volume_24h": "২৪ ঘণ্টার ভলিউম (USDT)",
        "market_cap": "বাজার মূলধন (USD)",
        "stop_atr": "ATR স্টপ মূল্য",
        "compra_forte": "🟢  শক্তিশালী ক্রয় (SMC + ফিবোনাচি সারিবদ্ধ)",
        "venda_forte": "🔴  শক্তিশালী বিক্রয় (SMC + ফিবোনাচি সারিবদ্ধ)",
        "neutro": "🟡  নিরপেক্ষ (SMC এর জন্য অপেক্ষা করুন)",
        "erro_dados": "অপর্যাপ্ত ঐতিহাসিক ডেটা। অন্য সম্পদ নির্বাচন করুন বা টাইমফ্রেম কমিয়ে দিন।",
        "ctx_desconto": "সম্পদ ফিবোনাচি ডিসকাউন্ট জোনে (প্রাতিষ্ঠানিকদের জন্য চমৎকার ঝুঁকি/রিটার্ন)।",
        "ctx_premium": "সম্পদ ফিবোনাচি প্রিমিয়াম জোনে (মূল্য প্রসারিত, মুনাফা গ্রহণের জন্য উপযুক্ত)।",
        "ctx_neutro": "ফিবোনাচি নিরপেক্ষ অঞ্চলে মূল্য (Fair Value Zone)।",
        "ultima_atualizacao": "শেষ আপডেট",
        "proximo_refresh": "পরবর্তী রিফ্রেশ",
        "segundos": "সেকেন্ড",
        "pontos_compra": "ক্রয় পয়েন্ট",
        "pontos_venda": "বিক্রয় পয়েন্ট",
        "grafico_titulo": "📈  ইন্টারেক্টিভ মূল্য চার্ট",
        "buscando_marketcap": "🔍  বাজার মূলধন সংগ্রহ করা হচ্ছে...",
        "marketcap_nao_disponivel": "উপলব্ধ নয়",
        "idioma_label": "🌐  ভাষা / Language",
        "idioma_selecao": "ইন্টারফেস ভাষা নির্বাচন করুন:",
        "aviso_aquecimento": "⚠️ গণনায় ওয়ার্ম-আপ মোমবাতি ব্যবহার করা হয়েছে",
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
    "العربية": {
        "titulo": "🏦  BRICSVAULT PORTAL - محرك مفاهيم الأموال الذكية (SMC)",
        "config_globais": "⚙️  الإعدادات العامة",
        "selecione_cripto": "اختر أي عملة مشفرة (/USDT):",
        "tempo_grafico": "الإطار الزمني:",
        "modo_vivo": "تفعيل المراقبة في الوقت الفعلي",
        "intervalo_refresh": "فترة التحديث (ثواني):",
        "preco_spot": "السعر الحالي",
        "variacao_24h": "تغير 24 ساعة",
        "volume_24h": "حجم التداول 24 ساعة (USDT)",
        "market_cap": "القيمة السوقية (USD)",
        "stop_atr": "سعر وقف ATR",
        "compra_forte": "🟢  شراء قوي (SMC + فيبوناتشي متوافقة)",
        "venda_forte": "🔴  بيع قوي (SMC + فيبوناتشي متوافقة)",
        "neutro": "🟡  محايد (انتظار SMC)",
        "erro_dados": "بيانات تاريخية غير كافية. اختر أصلًا آخر أو قلل الإطار الزمني.",
        "ctx_desconto": "الأصل في منطقة خصم فيبوناتشي (مخاطرة/عائد ممتاز للمؤسسات).",
        "ctx_premium": "الأصل في منطقة فيبوناتشي الممتازة (السعر ممتد، مناسب لجني الأرباح).",
        "ctx_neutro": "السعر في منطقة فيبوناتشي المحايدة (منطقة القيمة العادلة).",
        "ultima_atualizacao": "آخر تحديث",
        "proximo_refresh": "التحديث التالي في",
        "segundos": "ثواني",
        "pontos_compra": "نقاط الشراء",
        "pontos_venda": "نقاط البيع",
        "grafico_titulo": "📈  مخطط الأسعار التفاعلي",
        "buscando_marketcap": "🔍  جاري الحصول على القيمة السوقية...",
        "marketcap_nao_disponivel": "غير متاح",
        "idioma_label": "🌐  اللغة / Language",
        "idioma_selecao": "اختر لغة الواجهة:",
        "aviso_aquecimento": "⚠️ تم استخدام شموع الإحماء في الحساب",
        "intervalos": {
            "دقيقة واحدة": "1m",
            "5 دقائق": "5m",
            "15 دقيقة": "15m",
            "30 دقيقة": "30m",
            "ساعة واحدة": "1h",
            "4 ساعات": "4h",
            "يوم واحد": "1d",
            "أسبوع واحد": "1w"
        }
    },
    "한국어": {
        "titulo": "🏦  BRICSVAULT PORTAL - 스마트 머니 컨셉(SMC) 엔진",
        "config_globais": "⚙️  글로벌 설정",
        "selecione_cripto": "암호화폐 선택 (/USDT):",
        "tempo_grafico": "시간 프레임:",
        "modo_vivo": "실시간 모니터링 활성화",
        "intervalo_refresh": "새로 고침 간격(초):",
        "preco_spot": "현재 가격",
        "variacao_24h": "24시간 변동",
        "volume_24h": "24시간 거래량 (USDT)",
        "market_cap": "시가총액 (USD)",
        "stop_atr": "ATR 스탑 가격",
        "compra_forte": "🟢  강한 매수 (SMC + 피보나치 정렬)",
        "venda_forte": "🔴  강한 매도 (SMC + 피보나치 정렬)",
        "neutro": "🟡  중립 (SMC 대기)",
        "erro_dados": "과거 데이터가 부족합니다. 다른 자산을 선택하거나 시간 프레임을 줄이세요.",
        "ctx_desconto": "자산이 피보나치 할인 영역에 있습니다 (기관용 우수한 위험/수익률).",
        "ctx_premium": "자산이 피보나치 프리미엄 영역에 있습니다 (가격이 늘어나 있어 이익 실현에 적합).",
        "ctx_neutro": "피보나치 중립 영역의 가격 (공정 가치 영역).",
        "ultima_atualizacao": "마지막 업데이트",
        "proximo_refresh": "다음 새로 고침까지",
        "segundos": "초",
        "pontos_compra": "매수 포인트",
        "pontos_venda": "매도 포인트",
        "grafico_titulo": "📈  대화형 가격 차트",
        "buscando_marketcap": "🔍  시가총액 가져오는 중...",
        "marketcap_nao_disponivel": "사용 불가",
        "idioma_label": "🌐  언어 / Language",
        "idioma_selecao": "인터페이스 언어 선택:",
        "aviso_aquecimento": "⚠️ 계산에 워밍업 캔들 사용됨",
        "intervalos": {
            "1분": "1m",
            "5분": "5m",
            "15분": "15m",
            "30분": "30m",
            "1시간": "1h",
            "4시간": "4h",
            "1일": "1d",
            "1주": "1w"
        }
    },
    "Tiếng Việt": {
        "titulo": "🏦  BRICSVAULT PORTAL - Động cơ Khái niệm Tiền thông minh (SMC)",
        "config_globais": "⚙️  Cài đặt toàn cầu",
        "selecione_cripto": "Chọn bất kỳ tiền mã hóa nào (/USDT):",
        "tempo_grafico": "Khung thời gian:",
        "modo_vivo": "Bật giám sát thời gian thực",
        "intervalo_refresh": "Khoảng thời gian làm mới (giây):",
        "preco_spot": "Giá hiện tại",
        "variacao_24h": "Biến động 24h",
        "volume_24h": "Khối lượng 24h (USDT)",
        "market_cap": "Vốn hóa thị trường (USD)",
        "stop_atr": "Giá dừng ATR",
        "compra_forte": "🟢  MUA MẠNH (SMC + FIBONACCI CĂN CHỈNH)",
        "venda_forte": "🔴  BÁN MẠNH (SMC + FIBONACCI CĂN CHỈNH)",
        "neutro": "🟡  TRUNG LẬP (CHỜ SMC)",
        "erro_dados": "Dữ liệu lịch sử không đủ. Chọn tài sản khác hoặc giảm khung thời gian.",
        "ctx_desconto": "Tài sản nằm trong vùng chiết khấu Fibonacci (Tỷ lệ rủi ro/lợi nhuận tuyệt vời cho tổ chức).",
        "ctx_premium": "Tài sản nằm trong vùng cao cấp Fibonacci (Giá kéo dài, phù hợp để chốt lời).",
        "ctx_neutro": "Giá nằm trong vùng trung tính Fibonacci (Vùng giá trị hợp lý).",
        "ultima_atualizacao": "Cập nhật cuối cùng",
        "proximo_refresh": "Làm mới tiếp theo trong",
        "segundos": "giây",
        "pontos_compra": "Điểm mua",
        "pontos_venda": "Điểm bán",
        "grafico_titulo": "📈  Biểu đồ giá tương tác",
        "buscando_marketcap": "🔍  Đang tìm vốn hóa thị trường...",
        "marketcap_nao_disponivel": "Không có sẵn",
        "idioma_label": "🌐  Ngôn ngữ / Language",
        "idioma_selecao": "Chọn ngôn ngữ giao diện:",
        "aviso_aquecimento": "⚠️ Nến làm nóng được sử dụng trong tính toán",
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
    "Türkçe": {
        "titulo": "🏦  BRICSVAULT PORTAL - Akıllı Para Kavramları (SMC) Motoru",
        "config_globais": "⚙️  Genel Ayarlar",
        "selecione_cripto": "Herhangi bir Kripto Para Birimi Seçin (/USDT):",
        "tempo_grafico": "Zaman Dilimi:",
        "modo_vivo": "Gerçek Zamanlı İzlemeyi Etkinleştir",
        "intervalo_refresh": "Yenileme Aralığı (Saniye):",
        "preco_spot": "Güncel Fiyat",
        "variacao_24h": "24 Saatlik Değişim",
        "volume_24h": "24 Saatlik Hacim (USDT)",
        "market_cap": "Piyasa Değeri (USD)",
        "stop_atr": "ATR Durdurma Fiyatı",
        "compra_forte": "🟢  GÜÇLÜ ALIM (SMC + FIBONACCI UYUMLU)",
        "venda_forte": "🔴  GÜÇLÜ SATIM (SMC + FIBONACCI UYUMLU)",
        "neutro": "🟡  NÖTR (SMC BEKLE)",
        "erro_dados": "Yetersiz geçmiş veri. Başka bir varlık seçin veya Zaman Dilimini azaltın.",
        "ctx_desconto": "Varlık Fibonacci İskonto Bölgesinde (Kurumlar için mükemmel risk/getiri).",
        "ctx_premium": "Varlık Fibonacci Prim Bölgesinde (Fiyat gerilmiş, kar alma için uygun).",
        "ctx_neutro": "Fiyat Fibonacci nötr bölgesinde (Fair Value Zone).",
        "ultima_atualizacao": "Son Güncelleme",
        "proximo_refresh": "Sonraki yenileme",
        "segundos": "saniye",
        "pontos_compra": "Alım Noktaları",
        "pontos_venda": "Satım Noktaları",
        "grafico_titulo": "📈  Etkileşimli Fiyat Grafiği",
        "buscando_marketcap": "🔍  Piyasa Değeri alınıyor...",
        "marketcap_nao_disponivel": "Mevcut değil",
        "idioma_label": "🌐  Dil / Language",
        "idioma_selecao": "Arayüz dilini seçin:",
        "aviso_aquecimento": "⚠️ Hesaplamada ısınma mumları kullanıldı",
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
# GERENCIADOR DE EXCHANGES (fallback interno)
class ExchangeManager:
    """Gerencia múltiplas exchanges com fallback e cache, sem exposição ao usuário."""
    
    EXCHANGES = {
        "Gate.io": {
            "class": ccxt.gate,
            "config": {"enableRateLimit": True, "options": {"defaultType": "spot"}},
            "separator": "/",
            "has_volume_usd": False
        },
        "Kraken": {
            "class": ccxt.kraken,
            "config": {"enableRateLimit": True},
            "separator": "/",
            "has_volume_usd": False
        },
        "MEXC": {
            "class": ccxt.mexc,
            "config": {"enableRateLimit": True},
            "separator": "",
            "has_volume_usd": True
        },
        "KuCoin": {
            "class": ccxt.kucoin,
            "config": {"enableRateLimit": True},
            "separator": "-",
            "has_volume_usd": True
        }
    }
    
    PRIORITY = ["Gate.io", "Kraken", "MEXC", "KuCoin"]
    
    def __init__(self):
        self.clients = {}
        self._init_clients()
    
    def _init_clients(self):
        for name, config in self.EXCHANGES.items():
            try:
                self.clients[name] = config["class"](config["config"])
            except Exception:
                pass
    
    def get_client(self, exchange_name):
        return self.clients.get(exchange_name)
    
    def get_separator(self, exchange_name):
        return self.EXCHANGES.get(exchange_name, {}).get("separator", "/")
    
    def get_symbol_format(self, exchange_name, symbol):
        if exchange_name == "MEXC":
            return symbol.replace("/", "")
        elif exchange_name == "KuCoin":
            return symbol.replace("/", "-")
        else:
            return symbol


# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÕES DE MERCADO COM FALLBACK

def obter_todos_pares_usdt():
    manager = ExchangeManager()
    client = manager.get_client("Gate.io")
    if not client:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]
    try:
        markets = client.load_markets()
        pairs = [s for s in markets.keys() if s.endswith('/USDT')]
        return sorted(pairs)
    except Exception:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]


def obter_dados_24h(simbolo):
    manager = ExchangeManager()
    for exchange_name in manager.PRIORITY:
        try:
            client = manager.get_client(exchange_name)
            if not client:
                continue
            symbol = manager.get_symbol_format(exchange_name, simbolo)
            ticker = client.fetch_ticker(symbol)
            if ticker:
                result = {
                    "last": ticker.get("last"),
                    "change": ticker.get("percentage"),
                    "volume": ticker.get("quoteVolume") or ticker.get("baseVolume"),
                    "high": ticker.get("high"),
                    "low": ticker.get("low"),
                    "bid": ticker.get("bid"),
                    "ask": ticker.get("ask")
                }
                if not result["volume"] and manager.EXCHANGES[exchange_name].get("has_volume_usd"):
                    result["volume"] = obter_volume_usd_direto(exchange_name, simbolo)
                if result["last"] is not None:
                    return result
        except Exception:
            continue
    return None


def obter_dados_24h_direto(exchange_name, simbolo):
    try:
        if exchange_name == "Gate.io":
            pair = simbolo.replace("/", "_")
            url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={pair}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    d = data[0]
                    return {
                        "last": float(d.get("last", 0)),
                        "change": float(d.get("change_percentage", 0)),
                        "volume": float(d.get("quote_volume", 0)),
                        "high": float(d.get("high_24h", 0)),
                        "low": float(d.get("low_24h", 0)),
                        "bid": float(d.get("highest_bid", 0)),
                        "ask": float(d.get("lowest_ask", 0))
                    }
        elif exchange_name == "MEXC":
            pair = simbolo.replace("/", "")
            url = f"https://api.mexc.com/api/v3/ticker/24hr?symbol={pair}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                d = resp.json()
                return {
                    "last": float(d.get("lastPrice", 0)),
                    "change": float(d.get("priceChangePercent", 0)),
                    "volume": float(d.get("quoteVolume", 0)) or float(d.get("volume", 0)),
                    "high": float(d.get("highPrice", 0)),
                    "low": float(d.get("lowPrice", 0)),
                    "bid": float(d.get("bidPrice", 0)),
                    "ask": float(d.get("askPrice", 0))
                }
        elif exchange_name == "KuCoin":
            pair = simbolo.replace("/", "-")
            url = f"https://api.kucoin.com/api/v1/market/stats?symbol={pair}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "200000":
                    d = data.get("data", {})
                    return {
                        "last": float(d.get("last", 0)),
                        "change": float(d.get("changeRate", 0)) * 100,
                        "volume": float(d.get("volValue", 0)),
                        "high": float(d.get("high", 0)),
                        "low": float(d.get("low", 0)),
                        "bid": float(d.get("buy", 0)),
                        "ask": float(d.get("sell", 0))
                    }
    except Exception:
        pass
    return None


def obter_volume_usd_direto(exchange_name, simbolo):
    try:
        if exchange_name == "MEXC":
            pair = simbolo.replace("/", "")
            url = f"https://api.mexc.com/api/v3/ticker/24hr?symbol={pair}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return float(resp.json().get("quoteVolume", 0))
        elif exchange_name == "KuCoin":
            pair = simbolo.replace("/", "-")
            url = f"https://api.kucoin.com/api/v1/market/stats?symbol={pair}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "200000":
                    return float(data.get("data", {}).get("volValue", 0))
    except:
        pass
    return None


# ─────────────────────────────────────────────────────────────────────────────
# NOME EXTENSO DA CRIPTO
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
# MARKET CAP (CoinGecko + CoinCap)

@st.cache_data(ttl=3600)
def obter_id_coingecko(simbolo):
    try:
        url = "https://api.coingecko.com/api/v3/search"
        params = {"query": simbolo}
        headers = {"Accept": "application/json"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        coins = data.get("coins", [])
        simbolo_upper = simbolo.upper()
        for coin in coins:
            if coin.get("symbol", "").upper() == simbolo_upper:
                return coin.get("id")
        if coins:
            return coins[0].get("id")
        return None
    except Exception:
        return None


@st.cache_data(ttl=600)
def obter_market_cap_coingecko(simbolo):
    coin_id = obter_id_coingecko(simbolo)
    if not coin_id:
        return None
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "ids": coin_id,
            "order": "market_cap_desc",
            "per_page": 1,
            "page": 1,
            "sparkline": "false"
        }
        headers = {"Accept": "application/json"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        if resp.status_code == 200:
            dados = resp.json()
            if dados and len(dados) > 0:
                mc = dados[0].get("market_cap")
                if mc and float(mc) > 1_000_000:
                    return float(mc)
        return None
    except Exception:
        return None


@st.cache_data(ttl=600)
def obter_market_cap_coincap(simbolo):
    try:
        asset_id = simbolo.lower()
        url = f"https://api.coincap.io/v2/assets/{asset_id}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            mc = data.get("data", {}).get("marketCapUsd")
            if mc:
                mc_float = float(mc)
                if mc_float > 1_000_000:
                    return mc_float
        url_list = "https://api.coincap.io/v2/assets"
        params = {"limit": 2000}
        resp = requests.get(url_list, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("data", []):
                if item.get("symbol", "").upper() == simbolo.upper():
                    mc = item.get("marketCapUsd")
                    if mc:
                        mc_float = float(mc)
                        if mc_float > 1_000_000:
                            return mc_float
        return None
    except Exception:
        return None


def obter_market_cap_robusto(simbolo_id):
    simbolo = simbolo_id.split('/')[0]
    mc = obter_market_cap_coingecko(simbolo)
    if mc is not None:
        return mc
    mc = obter_market_cap_coincap(simbolo)
    if mc is not None:
        return mc
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
# CARREGAMENTO DE DADOS COM FALLBACK

def carregar_dados(simbolo_id, timeframe_selecionado):
    manager = ExchangeManager()
    for exchange_name in manager.PRIORITY:
        try:
            client = manager.get_client(exchange_name)
            if not client:
                continue
            symbol = manager.get_symbol_format(exchange_name, simbolo_id)
            velas = client.fetch_ohlcv(
                symbol,
                timeframe=timeframe_selecionado,
                limit=VELAS_TOTAL
            )
            if velas and len(velas) >= PERIODO_AQUECIMENTO + 50:
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

                df['SSL_Baseline'] = df['SSL_Baseline'].ffill()
                df['ATR_Stop'] = df['ATR_Stop'].replace(0, np.nan).ffill()

                return df.dropna(subset=['close']).reset_index(drop=True)
        except Exception:
            continue
    return None


# ─────────────────────────────────────────────────────────────────────────────
# ANÁLISE DE CONFLUÊNCIA SMC
def analisar_confluencia(df_completo, txt):
    df_analise = df_completo.iloc[PERIODO_AQUECIMENTO:].copy()

    if df_analise.empty:
        return txt["neutro"], "#ffcc00", txt["ctx_neutro"], 0.0, 0.0

    u = df_analise.iloc[-1]
    preco_atual = u['close']
    fib_niveis = calcular_retracao_fibonacci(df_analise)

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

    if preco_atual >= fib_niveis['fib_382']:
        pontos_baixa += 2.0
        contexto_fib = txt["ctx_premium"]
    elif preco_atual <= fib_niveis['fib_618']:
        pontos_alta += 2.0
        contexto_fib = txt["ctx_desconto"]
    else:
        contexto_fib = txt["ctx_neutro"]

    if pontos_alta >= 8.5:
        return (
            txt["compra_forte"], "#00cc66",
            f"{contexto_fib} SMC + PPO Order Flow Bullish.",
            pontos_alta, pontos_baixa
        )
    elif pontos_baixa >= 8.5:
        return (
            txt["venda_forte"], "#ff3333",
            f"{contexto_fib} SMC + PPO Order Flow Bearish.",
            pontos_alta, pontos_baixa
        )
    else:
        return txt["neutro"], "#ffcc00", contexto_fib, pontos_alta, pontos_baixa


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO
def renderizar_grafico_plotly(df_completo, simbolo_id):
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

    dados_24h = obter_dados_24h(simbolo_id)
    variacao_24h = dados_24h.get("change") if dados_24h else 0.0
    volume_24h = dados_24h.get("volume") if dados_24h else None

    market_cap = obter_market_cap_robusto(simbolo_id)

    recomendacao, cor_sinal, analise, pontos_alta, pontos_baixa = analisar_confluencia(
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

    nome_extenso = obter_nome_extenso_cripto(simbolo_id)
    label_preco = f"{nome_extenso} | {txt['preco_spot']}"

    # Volume agora usa a mesma formatação do Market Cap
    volume_formatado = formatar_market_cap(volume_24h) if volume_24h is not None else "—"

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric(label_preco, formatar_preco(preco_atual))
    m2.metric(txt["variacao_24h"], f"{variacao_24h:+.2f}%" if variacao_24h is not None else "—")
    m3.metric(txt["volume_24h"], volume_formatado)

    if market_cap is not None:
        m4.metric(txt["market_cap"], formatar_market_cap(market_cap))
    else:
        m4.metric(txt["market_cap"], txt["marketcap_nao_disponivel"])

    m5.metric(txt["pontos_compra"], f"{pontos_alta:.1f}")
    m6.metric(txt["pontos_venda"], f"{pontos_baixa:.1f}")

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


painel_principal(simbolo_id, timeframe, txt, modo_vivo, intervalo_refresh)
