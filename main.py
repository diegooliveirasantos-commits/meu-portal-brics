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
PERIODO_AQUECIMENTO = 100          # será sobrescrito pelo slider, mas mantido como fallback
PERIODO_SWING_DEFAULT = 50

# ─────────────────────────────────────────────────────────────────────────────
# DICIONÁRIO DE IDIOMAS – 15 LÍNGUAS (COMPLETO) – MANTIDO INTEGRALMENTE
DICIONARIO_LINGUAS = {
    "Português (BR)": {
        "titulo": "🏦  BRICSVAULT PORTAL - Motor SMC + Fibonacci",
        "config_globais": "⚙️  Configurações Globais",
        "selecione_cripto": "Selecione Qualquer Criptomoeda (/USDT):",
        "tempo_grafico": "Tempo Gráfico:",
        "modo_vivo": "Ativar Monitoramento em Tempo Real",
        "intervalo_refresh": "Intervalo de Atualização (Segundos):",
        "preco_spot": "Preço Atual",
        "variacao_24h": "Variação 24h",
        "volume_24h": "Volume 24h (USDT)",
        "market_cap": "Market Cap (USD)",
        "stop_atr": "Stop ATR",
        "compra_forte": "🟢  COMPRA FORTE (SMC + FIBONACCI)",
        "venda_forte": "🔴  VENDA FORTE (SMC + FIBONACCI)",
        "neutro": "🟡  NEUTRO (AGUARDAR SMC)",
        "erro_dados": "Dados históricos insuficientes. Tente outro ativo ou reduza o Tempo Gráfico.",
        "ctx_desconto": "Zona de Desconto de Fibonacci (Excelente risco/retorno).",
        "ctx_premium": "Zona Premium de Fibonacci (Preço esticado, propício para realização).",
        "ctx_neutro": "Zona neutra de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Última Atualização",
        "proximo_refresh": "Próximo refresh em",
        "segundos": "segundos",
        "grafico_titulo": "📈  Gráfico de Preço Interativo",
        "buscando_marketcap": "🔍  Buscando Market Cap...",
        "marketcap_nao_disponivel": "Não disponível",
        "idioma_label": "🌐  Idioma / Language",
        "idioma_selecao": "Selecione o idioma da interface:",
        "aviso_aquecimento": "⚠️ Velas de aquecimento usadas no cálculo",
        "alvo_swing_title": "🎯 Projeção de Alvos (Fibonacci / Smart Money)",
        "direcao_operacao": "Direção",
        "entrada_projetada": "Entrada Projetada",
        "stop_projetado": "Stop Loss Projetado",
        "swing_alto": "Topo do Swing (High)",
        "swing_baixo": "Fundo do Swing (Low)",
        "range_label": "Oscilação (Range)",
        "alvo_prefix": "ALVO {n}",
        "sem_alvos": "Nenhum alvo projetado para este movimento.",
        "contexto_smc": "Contexto SMC",
        "trend_ascendente": "Tendência de Alta 🟢",
        "trend_descendente": "Tendência de Baixa 🔴",
        "trend_neutra": "Tendência Neutra 🟡",
        "intervalos": {
            "1 Minuto": "1m", "5 Minutos": "5m", "15 Minutos": "15m",
            "30 Minutos": "30m", "1 Hora": "1h", "4 Horas": "4h",
            "1 Dia": "1d", "1 Semana": "1w"
        }
    },
    "English (EN)": {
        "titulo": "🏦  BRICSVAULT PORTAL - SMC + Fibonacci Engine",
        "config_globais": "⚙️  Global Settings",
        "selecione_cripto": "Select Any Cryptocurrency (/USDT):",
        "tempo_grafico": "Timeframe:",
        "modo_vivo": "Enable Real-Time Monitoring",
        "intervalo_refresh": "Refresh Interval (Seconds):",
        "preco_spot": "Current Price",
        "variacao_24h": "24h Variation",
        "volume_24h": "24h Volume (USDT)",
        "market_cap": "Market Cap (USD)",
        "stop_atr": "ATR Stop",
        "compra_forte": "🟢  STRONG BUY (SMC + FIBONACCI)",
        "venda_forte": "🔴  STRONG SELL (SMC + FIBONACCI)",
        "neutro": "🟡  NEUTRAL (AWAIT SMC)",
        "erro_dados": "Insufficient historical data. Try another asset or reduce the Timeframe.",
        "ctx_desconto": "Fibonacci Discount Zone (Excellent risk/reward).",
        "ctx_premium": "Fibonacci Premium Zone (Price stretched, suitable for profit-taking).",
        "ctx_neutro": "Neutral Fibonacci zone (Fair Value Zone).",
        "ultima_atualizacao": "Last Update",
        "proximo_refresh": "Next refresh in",
        "segundos": "seconds",
        "grafico_titulo": "📈  Interactive Price Chart",
        "buscando_marketcap": "🔍  Fetching Market Cap...",
        "marketcap_nao_disponivel": "Not available",
        "idioma_label": "🌐  Language / Idioma",
        "idioma_selecao": "Select Interface Language:",
        "aviso_aquecimento": "⚠️ Warm-up candles used in calculation",
        "alvo_swing_title": "🎯 Target Projection (Fibonacci / Smart Money)",
        "direcao_operacao": "Direction",
        "entrada_projetada": "Projected Entry",
        "stop_projetado": "Projected Stop Loss",
        "swing_alto": "Swing High",
        "swing_baixo": "Swing Low",
        "range_label": "Range",
        "alvo_prefix": "TARGET {n}",
        "sem_alvos": "No targets projected for this move.",
        "contexto_smc": "SMC Context",
        "trend_ascendente": "Uptrend 🟢",
        "trend_descendente": "Downtrend 🔴",
        "trend_neutra": "Neutral Trend 🟡",
        "intervalos": {
            "1 Minute": "1m", "5 Minutes": "5m", "15 Minutes": "15m",
            "30 Minutes": "30m", "1 Hour": "1h", "4 Hours": "4h",
            "1 Day": "1d", "1 Week": "1w"
        }
    },
    "Español": {
        "titulo": "🏦  BRICSVAULT PORTAL - Motor SMC + Fibonacci",
        "config_globais": "⚙️  Configuraciones Globales",
        "selecione_cripto": "Seleccione cualquier criptomoneda (/USDT):",
        "tempo_grafico": "Marco temporal:",
        "modo_vivo": "Activar monitoreo en tiempo real",
        "intervalo_refresh": "Intervalo de actualización (segundos):",
        "preco_spot": "Precio Actual",
        "variacao_24h": "Variación 24h",
        "volume_24h": "Volumen 24h (USDT)",
        "market_cap": "Capitalización (USD)",
        "stop_atr": "Stop ATR",
        "compra_forte": "🟢  COMPRA FUERTE (SMC + FIBONACCI)",
        "venda_forte": "🔴  VENTA FUERTE (SMC + FIBONACCI)",
        "neutro": "🟡  NEUTRO (ESPERAR SMC)",
        "erro_dados": "Datos históricos insuficientes. Pruebe con otro activo o reduzca el marco temporal.",
        "ctx_desconto": "Zona de Descuento de Fibonacci (Excelente riesgo/retorno).",
        "ctx_premium": "Zona Premium de Fibonacci (Precio estirado, propicio para toma de ganancias).",
        "ctx_neutro": "Zona neutral de Fibonacci (Fair Value Zone).",
        "ultima_atualizacion": "Última actualización",
        "proximo_refresh": "Próxima actualización en",
        "segundos": "segundos",
        "grafico_titulo": "📈  Gráfico de Precio Interactivo",
        "buscando_marketcap": "🔍  Buscando Capitalización...",
        "marketcap_nao_disponivel": "No disponible",
        "idioma_label": "🌐  Idioma / Language",
        "idioma_selecao": "Seleccione el idioma de la interfaz:",
        "aviso_aquecimento": "⚠️ Velas de calentamiento usadas en el cálculo",
        "alvo_swing_title": "🎯 Proyección de Objetivos (Fibonacci / Smart Money)",
        "direcao_operacao": "Dirección",
        "entrada_projetada": "Entrada Proyectada",
        "stop_projetado": "Stop Loss Proyectado",
        "swing_alto": "Máximo del Swing",
        "swing_baixo": "Mínimo del Swing",
        "range_label": "Rango",
        "alvo_prefix": "OBJETIVO {n}",
        "sem_alvos": "No hay objetivos proyectados para este movimiento.",
        "contexto_smc": "Contexto SMC",
        "trend_ascendente": "Tendencia Alcista 🟢",
        "trend_descendente": "Tendencia Bajista 🔴",
        "trend_neutra": "Tendencia Neutral 🟡",
        "intervalos": {
            "1 Minuto": "1m", "5 Minutos": "5m", "15 Minutos": "15m",
            "30 Minutos": "30m", "1 Hora": "1h", "4 Horas": "4h",
            "1 Día": "1d", "1 Semana": "1w"
        }
    },
    "Français": {
        "titulo": "🏦  BRICSVAULT PORTAL - Moteur SMC + Fibonacci",
        "config_globais": "⚙️  Paramètres globaux",
        "selecione_cripto": "Sélectionnez une cryptomonnaie (/USDT):",
        "tempo_grafico": "Période:",
        "modo_vivo": "Activer la surveillance en temps réel",
        "intervalo_refresh": "Intervalle de rafraîchissement (secondes):",
        "preco_spot": "Prix Actuel",
        "variacao_24h": "Variation 24h",
        "volume_24h": "Volume 24h (USDT)",
        "market_cap": "Capitalisation (USD)",
        "stop_atr": "Stop ATR",
        "compra_forte": "🟢  ACHAT FORT (SMC + FIBONACCI)",
        "venda_forte": "🔴  VENTE FORTE (SMC + FIBONACCI)",
        "neutro": "🟡  NEUTRE (ATTENDRE SMC)",
        "erro_dados": "Données historiques insuffisantes. Essayez un autre actif ou réduisez la période.",
        "ctx_desconto": "Zone de discount de Fibonacci (Excellent risque/rendement).",
        "ctx_premium": "Zone premium de Fibonacci (Prix étiré, propice à la prise de bénéfices).",
        "ctx_neutro": "Zone neutre de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Dernière mise à jour",
        "proximo_refresh": "Prochain rafraîchissement dans",
        "segundos": "secondes",
        "grafico_titulo": "📈  Graphique de prix interactif",
        "buscando_marketcap": "🔍  Recherche de la capitalisation...",
        "marketcap_nao_disponivel": "Indisponible",
        "idioma_label": "🌐  Langue / Language",
        "idioma_selecao": "Sélectionnez la langue de l'interface:",
        "aviso_aquecimento": "⚠️ Bougies de chauffe utilisées dans le calcul",
        "alvo_swing_title": "🎯 Projection d'Objectifs (Fibonacci / Smart Money)",
        "direcao_operacao": "Direction",
        "entrada_projetada": "Entrée Projetée",
        "stop_projetado": "Stop Loss Projeté",
        "swing_alto": "Haut du Swing",
        "swing_baixo": "Bas du Swing",
        "range_label": "Plage",
        "alvo_prefix": "OBJECTIF {n}",
        "sem_alvos": "Aucun objectif projeté pour ce mouvement.",
        "contexto_smc": "Contexte SMC",
        "trend_ascendente": "Tendance Haussière 🟢",
        "trend_descendente": "Tendance Baissière 🔴",
        "trend_neutra": "Tendance Neutre 🟡",
        "intervalos": {
            "1 Minute": "1m", "5 Minutes": "5m", "15 Minutes": "15m",
            "30 Minutes": "30m", "1 Heure": "1h", "4 Heures": "4h",
            "1 Jour": "1d", "1 Semaine": "1w"
        }
    },
    "Deutsch": {
        "titulo": "🏦  BRICSVAULT PORTAL - SMC + Fibonacci Motor",
        "config_globais": "⚙️  Globale Einstellungen",
        "selecione_cripto": "Wählen Sie eine Kryptowährung (/USDT):",
        "tempo_grafico": "Zeitrahmen:",
        "modo_vivo": "Echtzeit-Überwachung aktivieren",
        "intervalo_refresh": "Aktualisierungsintervall (Sekunden):",
        "preco_spot": "Aktueller Preis",
        "variacao_24h": "24h-Veränderung",
        "volume_24h": "24h-Volumen (USDT)",
        "market_cap": "Marktkapitalisierung (USD)",
        "stop_atr": "ATR-Stop",
        "compra_forte": "🟢  STARKER KAUF (SMC + FIBONACCI)",
        "venda_forte": "🔴  STARKER VERKAUF (SMC + FIBONACCI)",
        "neutro": "🟡  NEUTRAL (SMC ABWARTEN)",
        "erro_dados": "Unzureichende historische Daten. Versuchen Sie es mit einem anderen Vermögenswert oder reduzieren Sie den Zeitrahmen.",
        "ctx_desconto": "Fibonacci-Discount-Zone (Ausgezeichnetes Risiko/Rendite).",
        "ctx_premium": "Fibonacci-Premium-Zone (Preis gedehnt, gewinnmitnahme geeignet).",
        "ctx_neutro": "Neutrale Fibonacci-Zone (Fair Value Zone).",
        "ultima_atualizacao": "Letzte Aktualisierung",
        "proximo_refresh": "Nächste Aktualisierung in",
        "segundos": "Sekunden",
        "grafico_titulo": "📈  Interaktives Kursdiagramm",
        "buscando_marketcap": "🔍  Marktkapitalisierung wird abgerufen...",
        "marketcap_nao_disponivel": "Nicht verfügbar",
        "idioma_label": "🌐  Sprache / Language",
        "idioma_selecao": "Wählen Sie die Oberflächensprache:",
        "aviso_aquecimento": "⚠️ Aufwärm-Kerzen im Rechengang verwendet",
        "alvo_swing_title": "🎯 Zielprojektion (Fibonacci / Smart Money)",
        "direcao_operacao": "Richtung",
        "entrada_projetada": "Projizierter Einstieg",
        "stop_projetado": "Projizierter Stop Loss",
        "swing_alto": "Swing-Hoch",
        "swing_baixo": "Swing-Tief",
        "range_label": "Bereich",
        "alvo_prefix": "ZIEL {n}",
        "sem_alvos": "Für diese Bewegung wurden keine Ziele projiziert.",
        "contexto_smc": "SMC-Kontext",
        "trend_ascendente": "Aufwärtstrend 🟢",
        "trend_descendente": "Abwärtstrend 🔴",
        "trend_neutra": "Neutraler Trend 🟡",
        "intervalos": {
            "1 Minute": "1m", "5 Minuten": "5m", "15 Minuten": "15m",
            "30 Minuten": "30m", "1 Stunde": "1h", "4 Stunden": "4h",
            "1 Tag": "1d", "1 Woche": "1w"
        }
    },
    "Italiano": {
        "titulo": "🏦  BRICSVAULT PORTAL - Motore SMC + Fibonacci",
        "config_globais": "⚙️  Impostazioni globali",
        "selecione_cripto": "Seleziona una criptovaluta (/USDT):",
        "tempo_grafico": "Timeframe:",
        "modo_vivo": "Attiva monitoraggio in tempo reale",
        "intervalo_refresh": "Intervallo di aggiornamento (secondi):",
        "preco_spot": "Prezzo Corrente",
        "variacao_24h": "Variazione 24h",
        "volume_24h": "Volume 24h (USDT)",
        "market_cap": "Capitalizzazione (USD)",
        "stop_atr": "Stop ATR",
        "compra_forte": "🟢  ACQUISTO FORTE (SMC + FIBONACCI)",
        "venda_forte": "🔴  VENDITA FORTE (SMC + FIBONACCI)",
        "neutro": "🟡  NEUTRO (ATTENDERE SMC)",
        "erro_dados": "Dati storici insufficienti. Prova un altro asset o riduci il timeframe.",
        "ctx_desconto": "Zona di Sconto di Fibonacci (Ottimo rischio/rendimento).",
        "ctx_premium": "Zona Premium di Fibonacci (Prezzo allungato, adatto per presa di profitto).",
        "ctx_neutro": "Zona neutrale di Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Ultimo aggiornamento",
        "proximo_refresh": "Prossimo aggiornamento tra",
        "segundos": "secondi",
        "grafico_titulo": "📈  Grafico Prezzo Interattivo",
        "buscando_marketcap": "🔍  Ricerca Capitalizzazione...",
        "marketcap_nao_disponivel": "Non disponibile",
        "idioma_label": "🌐  Lingua / Language",
        "idioma_selecao": "Seleziona la lingua dell'interfaccia:",
        "aviso_aquecimento": "⚠️ Candele di riscaldamento utilizzate nel calcolo",
        "alvo_swing_title": "🎯 Proiezione Obiettivi (Fibonacci / Smart Money)",
        "direcao_operacao": "Direzione",
        "entrada_projetada": "Ingresso Proiettato",
        "stop_projetado": "Stop Loss Proiettato",
        "swing_alto": "Massimo dello Swing",
        "swing_baixo": "Minimo dello Swing",
        "range_label": "Intervallo",
        "alvo_prefix": "OBIETTIVO {n}",
        "sem_alvos": "Nessun obiettivo proiettato per questo movimento.",
        "contexto_smc": "Contesto SMC",
        "trend_ascendente": "Tendenza Rialzista 🟢",
        "trend_descendente": "Tendenza Ribassista 🔴",
        "trend_neutra": "Tendenza Neutra 🟡",
        "intervalos": {
            "1 Minuto": "1m", "5 Minuti": "5m", "15 Minuti": "15m",
            "30 Minuti": "30m", "1 Ora": "1h", "4 Ore": "4h",
            "1 Giorno": "1d", "1 Settimana": "1w"
        }
    },
    "Русский": {
        "titulo": "🏦  BRICSVAULT PORTAL - Двигатель SMC + Fibonacci",
        "config_globais": "⚙️  Глобальные настройки",
        "selecione_cripto": "Выберите криптовалюту (/USDT):",
        "tempo_grafico": "Таймфрейм:",
        "modo_vivo": "Включить мониторинг в реальном времени",
        "intervalo_refresh": "Интервал обновления (секунды):",
        "preco_spot": "Текущая цена",
        "variacao_24h": "Изменение за 24ч",
        "volume_24h": "Объем за 24ч (USDT)",
        "market_cap": "Рыночная капитализация (USD)",
        "stop_atr": "Стоп-лосс ATR",
        "compra_forte": "🟢  СИЛЬНАЯ ПОКУПКА (SMC + ФИБОНАЧЧИ)",
        "venda_forte": "🔴  СИЛЬНАЯ ПРОДАЖА (SMC + ФИБОНАЧЧИ)",
        "neutro": "🟡  НЕЙТРАЛЬНО (ОЖИДАТЬ SMC)",
        "erro_dados": "Недостаточно исторических данных. Попробуйте другой актив или уменьшите таймфрейм.",
        "ctx_desconto": "Зона скидки Фибоначчи (Отличное соотношение риск/доходность).",
        "ctx_premium": "Премиальная зона Фибоначчи (Цена растянута, подходит для фиксации прибыли).",
        "ctx_neutro": "Нейтральная зона Фибоначчи (Fair Value Zone).",
        "ultima_atualizacao": "Последнее обновление",
        "proximo_refresh": "Следующее обновление через",
        "segundos": "секунд",
        "grafico_titulo": "📈  Интерактивный график цены",
        "buscando_marketcap": "🔍  Получение рыночной капитализации...",
        "marketcap_nao_disponivel": "Недоступно",
        "idioma_label": "🌐  Язык / Language",
        "idioma_selecao": "Выберите язык интерфейса:",
        "aviso_aquecimento": "⚠️ Используются свечи разогрева в расчетах",
        "alvo_swing_title": "🎯 Проекция целей (Fibonacci / Smart Money)",
        "direcao_operacao": "Направление",
        "entrada_projetada": "Прогнозируемый вход",
        "stop_projetado": "Прогнозируемый стоп-лосс",
        "swing_alto": "Максимум свинга",
        "swing_baixo": "Минимум свинга",
        "range_label": "Диапазон",
        "alvo_prefix": "ЦЕЛЬ {n}",
        "sem_alvos": "Для этого движения цели не спроецированы.",
        "contexto_smc": "Контекст SMC",
        "trend_ascendente": "Восходящий тренд 🟢",
        "trend_descendente": "Нисходящий тренд 🔴",
        "trend_neutra": "Нейтральный тренд 🟡",
        "intervalos": {
            "1 Минута": "1m", "5 Минут": "5m", "15 Минут": "15m",
            "30 Минут": "30m", "1 Час": "1h", "4 Часа": "4h",
            "1 День": "1d", "1 Неделя": "1w"
        }
    },
    "日本語": {
        "titulo": "🏦  BRICSVAULT PORTAL - SMC + フィボナッチエンジン",
        "config_globais": "⚙️  グローバル設定",
        "selecione_cripto": "暗号通貨を選択（/USDT）:",
        "tempo_grafico": "タイムフレーム:",
        "modo_vivo": "リアルタイム監視を有効にする",
        "intervalo_refresh": "更新間隔（秒）:",
        "preco_spot": "現在価格",
        "variacao_24h": "24時間変動",
        "volume_24h": "24時間出来高（USDT）",
        "market_cap": "時価総額（USD）",
        "stop_atr": "ATRストップ",
        "compra_forte": "🟢  強い買い（SMC＋フィボナッチ）",
        "venda_forte": "🔴  強い売り（SMC＋フィボナッチ）",
        "neutro": "🟡  中立（SMC待機）",
        "erro_dados": "履歴データが不十分です。別の資産を選ぶか、タイムフレームを小さくしてください。",
        "ctx_desconto": "フィボナッチ割引ゾーン（優れたリスク/リターン）。",
        "ctx_premium": "フィボナッチプレミアムゾーン（価格が伸びており、利益確定に適している）。",
        "ctx_neutro": "フィボナッチ中立ゾーン（フェアバリューゾーン）。",
        "ultima_atualizacao": "最終更新",
        "proximo_refresh": "次の更新まで",
        "segundos": "秒",
        "grafico_titulo": "📈  インタラクティブ価格チャート",
        "buscando_marketcap": "🔍  時価総額を取得中...",
        "marketcap_nao_disponivel": "利用不可",
        "idioma_label": "🌐  言語 / Language",
        "idioma_selecao": "インターフェース言語を選択:",
        "aviso_aquecimento": "⚠️ 計算にウォームアップローソクを使用",
        "alvo_swing_title": "🎯 ターゲット投影（フィボナッチ / スマートマネー）",
        "direcao_operacao": "方向",
        "entrada_projetada": "投影エントリー",
        "stop_projetado": "投影ストップロス",
        "swing_alto": "スイング高値",
        "swing_baixo": "スイング安値",
        "range_label": "レンジ",
        "alvo_prefix": "ターゲット {n}",
        "sem_alvos": "この動きに対するターゲットはありません。",
        "contexto_smc": "SMCコンテキスト",
        "trend_ascendente": "上昇トレンド 🟢",
        "trend_descendente": "下降トレンド 🔴",
        "trend_neutra": "中立トレンド 🟡",
        "intervalos": {
            "1分": "1m", "5分": "5m", "15分": "15m",
            "30分": "30m", "1時間": "1h", "4時間": "4h",
            "1日": "1d", "1週間": "1w"
        }
    },
    "中文 (简体)": {
        "titulo": "🏦  BRICSVAULT PORTAL - SMC + 斐波那契引擎",
        "config_globais": "⚙️  全局设置",
        "selecione_cripto": "选择加密货币（/USDT）：",
        "tempo_grafico": "时间周期：",
        "modo_vivo": "启用实时监控",
        "intervalo_refresh": "刷新间隔（秒）：",
        "preco_spot": "当前价格",
        "variacao_24h": "24小时变化",
        "volume_24h": "24小时成交量（USDT）",
        "market_cap": "市值（美元）",
        "stop_atr": "ATR止损",
        "compra_forte": "🟢  强烈买入（SMC + 斐波那契）",
        "venda_forte": "🔴  强烈卖出（SMC + 斐波那契）",
        "neutro": "🟡  中性（等待SMC）",
        "erro_dados": "历史数据不足。请选择其他资产或缩短时间周期。",
        "ctx_desconto": "斐波那契折价区（卓越风险/回报）。",
        "ctx_premium": "斐波那契溢价区（价格拉伸，适合获利了结）。",
        "ctx_neutro": "斐波那契中性区（公允价值区）。",
        "ultima_atualizacao": "最后更新",
        "proximo_refresh": "下次刷新于",
        "segundos": "秒",
        "grafico_titulo": "📈  交互式价格图表",
        "buscando_marketcap": "🔍  正在获取市值...",
        "marketcap_nao_disponivel": "不可用",
        "idioma_label": "🌐  语言 / Language",
        "idioma_selecao": "选择界面语言：",
        "aviso_aquecimento": "⚠️ 计算中使用预热K线",
        "alvo_swing_title": "🎯 目标投影（斐波那契 / 智能资金）",
        "direcao_operacao": "方向",
        "entrada_projetada": "投影进场",
        "stop_projetado": "投影止损",
        "swing_alto": "摆动高点",
        "swing_baixo": "摆动低点",
        "range_label": "范围",
        "alvo_prefix": "目标 {n}",
        "sem_alvos": "此运动未投影目标。",
        "contexto_smc": "SMC 背景",
        "trend_ascendente": "上升趋势 🟢",
        "trend_descendente": "下降趋势 🔴",
        "trend_neutra": "中性趋势 🟡",
        "intervalos": {
            "1分钟": "1m", "5分钟": "5m", "15分钟": "15m",
            "30分钟": "30m", "1小时": "1h", "4小时": "4h",
            "1天": "1d", "1周": "1w"
        }
    },
    "हिन्दी": {
        "titulo": "🏦  BRICSVAULT PORTAL - SMC + फिबोनाची इंजन",
        "config_globais": "⚙️  वैश्विक सेटिंग्स",
        "selecione_cripto": "कोई भी क्रिप्टोकरेंसी चुनें (/USDT):",
        "tempo_grafico": "टाइमफ्रेम:",
        "modo_vivo": "रीयल-टाइम मॉनिटरिंग सक्षम करें",
        "intervalo_refresh": "रिफ्रेश अंतराल (सेकंड):",
        "preco_spot": "वर्तमान मूल्य",
        "variacao_24h": "24 घंटे का बदलाव",
        "volume_24h": "24 घंटे का वॉल्यूम (USDT)",
        "market_cap": "बाजार पूंजीकरण (USD)",
        "stop_atr": "ATR स्टॉप",
        "compra_forte": "🟢  मजबूत खरीद (SMC + फिबोनाची)",
        "venda_forte": "🔴  मजबूत बिक्री (SMC + फिबोनाची)",
        "neutro": "🟡  तटस्थ (SMC की प्रतीक्षा करें)",
        "erro_dados": "अपर्याप्त ऐतिहासिक डेटा। कोई अन्य संपत्ति चुनें या टाइमफ्रेम कम करें।",
        "ctx_desconto": "फिबोनाची डिस्काउंट ज़ोन (उत्कृष्ट जोखिम/रिटर्न)।",
        "ctx_premium": "फिबोनाची प्रीमियम ज़ोन (मूल्य खिंचा हुआ, लाभ-बुकिंग के लिए उपयुक्त)।",
        "ctx_neutro": "फिबोनाची तटस्थ क्षेत्र (Fair Value Zone)।",
        "ultima_atualizacao": "अंतिम अद्यतन",
        "proximo_refresh": "अगला रिफ्रेश",
        "segundos": "सेकंड",
        "grafico_titulo": "📈  इंटरैक्टिव मूल्य चार्ट",
        "buscando_marketcap": "🔍  बाजार पूंजीकरण प्राप्त किया जा रहा है...",
        "marketcap_nao_disponivel": "उपलब्ध नहीं",
        "idioma_label": "🌐  भाषा / Language",
        "idioma_selecao": "इंटरफ़ेस भाषा चुनें:",
        "aviso_aquecimento": "⚠️ गणना में वार्म-अप मोमबत्तियों का उपयोग किया गया",
        "alvo_swing_title": "🎯 लक्ष्य प्रक्षेपण (फिबोनाची / स्मार्ट मनी)",
        "direcao_operacao": "दिशा",
        "entrada_projetada": "अनुमानित प्रवेश",
        "stop_projetado": "अनुमानित स्टॉप लॉस",
        "swing_alto": "स्विंग उच्च",
        "swing_baixo": "स्विंग निम्न",
        "range_label": "सीमा",
        "alvo_prefix": "लक्ष्य {n}",
        "sem_alvos": "इस आंदोलन के लिए कोई लक्ष्य नहीं।",
        "contexto_smc": "SMC संदर्भ",
        "trend_ascendente": "उपरि प्रवृत्ति 🟢",
        "trend_descendente": "अधोमुखी प्रवृत्ति 🔴",
        "trend_neutra": "तटस्थ प्रवृत्ति 🟡",
        "intervalos": {
            "1 मिनट": "1m", "5 मिनट": "5m", "15 मिनट": "15m",
            "30 मिनट": "30m", "1 घंटा": "1h", "4 घंटे": "4h",
            "1 दिन": "1d", "1 सप्ताह": "1w"
        }
    },
    "বাংলা": {
        "titulo": "🏦  BRICSVAULT PORTAL - SMC + ফিবোনাচি ইঞ্জিন",
        "config_globais": "⚙️  গ্লোবাল সেটিংস",
        "selecione_cripto": "যেকোনো ক্রিপ্টোকারেন্সি নির্বাচন করুন (/USDT):",
        "tempo_grafico": "টাইমফ্রেম:",
        "modo_vivo": "রিয়েল-টাইম মনিটরিং সক্রিয় করুন",
        "intervalo_refresh": "রিফ্রেশ বিরতি (সেকেন্ড):",
        "preco_spot": "বর্তমান মূল্য",
        "variacao_24h": "২৪ ঘণ্টার পরিবর্তন",
        "volume_24h": "২৪ ঘণ্টার ভলিউম (USDT)",
        "market_cap": "বাজার মূলধন (USD)",
        "stop_atr": "ATR স্টপ",
        "compra_forte": "🟢  শক্তিশালী ক্রয় (SMC + ফিবোনাচি)",
        "venda_forte": "🔴  শক্তিশালী বিক্রয় (SMC + ফিবোনাচি)",
        "neutro": "🟡  নিরপেক্ষ (SMC এর জন্য অপেক্ষা করুন)",
        "erro_dados": "অপর্যাপ্ত ঐতিহাসিক ডেটা। অন্য সম্পদ নির্বাচন করুন বা টাইমফ্রেম কমিয়ে দিন।",
        "ctx_desconto": "ফিবোনাচি ডিসকাউন্ট জোন (চমৎকার ঝুঁকি/রিটার্ন)।",
        "ctx_premium": "ফিবোনাচি প্রিমিয়াম জোন (মূল্য প্রসারিত, মুনাফা গ্রহণের জন্য উপযুক্ত)।",
        "ctx_neutro": "ফিবোনাচি নিরপেক্ষ অঞ্চল (Fair Value Zone)।",
        "ultima_atualizacao": "শেষ আপডেট",
        "proximo_refresh": "পরবর্তী রিফ্রেশ",
        "segundos": "সেকেন্ড",
        "grafico_titulo": "📈  ইন্টারেক্টিভ মূল্য চার্ট",
        "buscando_marketcap": "🔍  বাজার মূলধন সংগ্রহ করা হচ্ছে...",
        "marketcap_nao_disponivel": "উপলব্ধ নয়",
        "idioma_label": "🌐  ভাষা / Language",
        "idioma_selecao": "ইন্টারফেস ভাষা নির্বাচন করুন:",
        "aviso_aquecimento": "⚠️ গণনায় ওয়ার্ম-আপ মোমবাতি ব্যবহার করা হয়েছে",
        "alvo_swing_title": "🎯 লক্ষ্য প্রক্ষেপণ (ফিবোনাচি / স্মার্ট মানি)",
        "direcao_operacao": "দিকনির্দেশ",
        "entrada_projetada": "অনুমানিত প্রবেশ",
        "stop_projetado": "অনুমানিত স্টপ লস",
        "swing_alto": "সুইং উচ্চ",
        "swing_baixo": "সুইং নিম্ন",
        "range_label": "পরিসীমা",
        "alvo_prefix": "লক্ষ্য {n}",
        "sem_alvos": "এই আন্দোলনের জন্য কোন লক্ষ্য নেই।",
        "contexto_smc": "SMC প্রসঙ্গ",
        "trend_ascendente": "উর্ধ্বগামী প্রবণতা 🟢",
        "trend_descendente": "নিম্নগামী প্রবণতা 🔴",
        "trend_neutra": "নিরপেক্ষ প্রবণতা 🟡",
        "intervalos": {
            "১ মিনিট": "1m", "৫ মিনিট": "5m", "১৫ মিনিট": "15m",
            "৩০ মিনিট": "30m", "১ ঘন্টা": "1h", "৪ ঘন্টা": "4h",
            "১ দিন": "1d", "১ সপ্তাহ": "1w"
        }
    },
    "العربية": {
        "titulo": "🏦  BRICSVAULT PORTAL - محرك SMC + فيبوناتشي",
        "config_globais": "⚙️  الإعدادات العامة",
        "selecione_cripto": "اختر أي عملة مشفرة (/USDT):",
        "tempo_grafico": "الإطار الزمني:",
        "modo_vivo": "تفعيل المراقبة في الوقت الفعلي",
        "intervalo_refresh": "فترة التحديث (ثواني):",
        "preco_spot": "السعر الحالي",
        "variacao_24h": "تغير 24 ساعة",
        "volume_24h": "حجم التداول 24 ساعة (USDT)",
        "market_cap": "القيمة السوقية (USD)",
        "stop_atr": "وقف ATR",
        "compra_forte": "🟢  شراء قوي (SMC + فيبوناتشي)",
        "venda_forte": "🔴  بيع قوي (SMC + فيبوناتشي)",
        "neutro": "🟡  محايد (انتظار SMC)",
        "erro_dados": "بيانات تاريخية غير كافية. اختر أصلًا آخر أو قلل الإطار الزمني.",
        "ctx_desconto": "منطقة خصم فيبوناتشي (مخاطرة/عائد ممتاز).",
        "ctx_premium": "منطقة فيبوناتشي الممتازة (السعر ممتد، مناسب لجني الأرباح).",
        "ctx_neutro": "منطقة فيبوناتشي المحايدة (منطقة القيمة العادلة).",
        "ultima_atualizacao": "آخر تحديث",
        "proximo_refresh": "التحديث التالي في",
        "segundos": "ثواني",
        "grafico_titulo": "📈  مخطط الأسعار التفاعلي",
        "buscando_marketcap": "🔍  جاري الحصول على القيمة السوقية...",
        "marketcap_nao_disponivel": "غير متاح",
        "idioma_label": "🌐  اللغة / Language",
        "idioma_selecao": "اختر لغة الواجهة:",
        "aviso_aquecimento": "⚠️ تم استخدام شموع الإحماء في الحساب",
        "alvo_swing_title": "🎯 إسقاط الأهداف (فيبوناتشي / الأموال الذكية)",
        "direcao_operacao": "اتجاه",
        "entrada_projetada": "الدخول المتوقع",
        "stop_projetado": "وقف الخسارة المتوقع",
        "swing_alto": "قمة التذبذب",
        "swing_baixo": "قاع التذبذب",
        "range_label": "النطاق",
        "alvo_prefix": "الهدف {n}",
        "sem_alvos": "لا توجد أهداف متوقعة لهذه الحركة.",
        "contexto_smc": "سياق SMC",
        "trend_ascendente": "اتجاه صاعد 🟢",
        "trend_descendente": "اتجاه هابط 🔴",
        "trend_neutra": "اتجاه محايد 🟡",
        "intervalos": {
            "دقيقة واحدة": "1m", "5 دقائق": "5m", "15 دقيقة": "15m",
            "30 دقيقة": "30m", "ساعة واحدة": "1h", "4 ساعات": "4h",
            "يوم واحد": "1d", "أسبوع واحد": "1w"
        }
    },
    "한국어": {
        "titulo": "🏦  BRICSVAULT PORTAL - SMC + 피보나치 엔진",
        "config_globais": "⚙️  글로벌 설정",
        "selecione_cripto": "암호화폐 선택 (/USDT):",
        "tempo_grafico": "시간 프레임:",
        "modo_vivo": "실시간 모니터링 활성화",
        "intervalo_refresh": "새로 고침 간격(초):",
        "preco_spot": "현재 가격",
        "variacao_24h": "24시간 변동",
        "volume_24h": "24시간 거래량 (USDT)",
        "market_cap": "시가총액 (USD)",
        "stop_atr": "ATR 스탑",
        "compra_forte": "🟢  강한 매수 (SMC + 피보나치)",
        "venda_forte": "🔴  강한 매도 (SMC + 피보나치)",
        "neutro": "🟡  중립 (SMC 대기)",
        "erro_dados": "과거 데이터가 부족합니다. 다른 자산을 선택하거나 시간 프레임을 줄이세요.",
        "ctx_desconto": "피보나치 할인 영역 (우수한 위험/수익률).",
        "ctx_premium": "피보나치 프리미엄 영역 (가격이 늘어나 있어 이익 실현에 적합).",
        "ctx_neutro": "피보나치 중립 영역 (공정 가치 영역).",
        "ultima_atualizacao": "마지막 업데이트",
        "proximo_refresh": "다음 새로 고침까지",
        "segundos": "초",
        "grafico_titulo": "📈  대화형 가격 차트",
        "buscando_marketcap": "🔍  시가총액 가져오는 중...",
        "marketcap_nao_disponivel": "사용 불가",
        "idioma_label": "🌐  언어 / Language",
        "idioma_selecao": "인터페이스 언어 선택:",
        "aviso_aquecimento": "⚠️ 계산에 워밍업 캔들 사용됨",
        "alvo_swing_title": "🎯 목표 투영 (피보나치 / 스마트 머니)",
        "direcao_operacao": "방향",
        "entrada_projetada": "예상 진입",
        "stop_projetado": "예상 스탑로스",
        "swing_alto": "스윙 고점",
        "swing_baixo": "스윙 저점",
        "range_label": "범위",
        "alvo_prefix": "목표 {n}",
        "sem_alvos": "이 움직임에 대한 목표가 없습니다.",
        "contexto_smc": "SMC 컨텍스트",
        "trend_ascendente": "상승 추세 🟢",
        "trend_descendente": "하락 추세 🔴",
        "trend_neutra": "중립 추세 🟡",
        "intervalos": {
            "1분": "1m", "5분": "5m", "15분": "15m",
            "30분": "30m", "1시간": "1h", "4시간": "4h",
            "1일": "1d", "1주": "1w"
        }
    },
    "Tiếng Việt": {
        "titulo": "🏦  BRICSVAULT PORTAL - Động cơ SMC + Fibonacci",
        "config_globais": "⚙️  Cài đặt toàn cầu",
        "selecione_cripto": "Chọn bất kỳ tiền mã hóa nào (/USDT):",
        "tempo_grafico": "Khung thời gian:",
        "modo_vivo": "Bật giám sát thời gian thực",
        "intervalo_refresh": "Khoảng thời gian làm mới (giây):",
        "preco_spot": "Giá hiện tại",
        "variacao_24h": "Biến động 24h",
        "volume_24h": "Khối lượng 24h (USDT)",
        "market_cap": "Vốn hóa thị trường (USD)",
        "stop_atr": "Dừng ATR",
        "compra_forte": "🟢  MUA MẠNH (SMC + FIBONACCI)",
        "venda_forte": "🔴  BÁN MẠNH (SMC + FIBONACCI)",
        "neutro": "🟡  TRUNG LẬP (CHỜ SMC)",
        "erro_dados": "Dữ liệu lịch sử không đủ. Chọn tài sản khác hoặc giảm khung thời gian.",
        "ctx_desconto": "Vùng chiết khấu Fibonacci (Tỷ lệ rủi ro/lợi nhuận tuyệt vời).",
        "ctx_premium": "Vùng cao cấp Fibonacci (Giá kéo dài, phù hợp để chốt lời).",
        "ctx_neutro": "Vùng trung tính Fibonacci (Vùng giá trị hợp lý).",
        "ultima_atualizacao": "Cập nhật cuối cùng",
        "proximo_refresh": "Làm mới tiếp theo trong",
        "segundos": "giây",
        "grafico_titulo": "📈  Biểu đồ giá tương tác",
        "buscando_marketcap": "🔍  Đang tìm vốn hóa thị trường...",
        "marketcap_nao_disponivel": "Không có sẵn",
        "idioma_label": "🌐  Ngôn ngữ / Language",
        "idioma_selecao": "Chọn ngôn ngữ giao diện:",
        "aviso_aquecimento": "⚠️ Nến làm nóng được sử dụng trong tính toán",
        "alvo_swing_title": "🎯 Dự báo Mục tiêu (Fibonacci / Smart Money)",
        "direcao_operacao": "Hướng",
        "entrada_projetada": "Điểm vào dự kiến",
        "stop_projetado": "Dừng lỗ dự kiến",
        "swing_alto": "Đỉnh dao động",
        "swing_baixo": "Đáy dao động",
        "range_label": "Phạm vi",
        "alvo_prefix": "MỤC TIÊU {n}",
        "sem_alvos": "Không có mục tiêu nào cho chuyển động này.",
        "contexto_smc": "Bối cảnh SMC",
        "trend_ascendente": "Xu hướng tăng 🟢",
        "trend_descendente": "Xu hướng giảm 🔴",
        "trend_neutra": "Xu hướng trung lập 🟡",
        "intervalos": {
            "1 Phút": "1m", "5 Phút": "5m", "15 Phút": "15m",
            "30 Phút": "30m", "1 Giờ": "1h", "4 Giờ": "4h",
            "1 Ngày": "1d", "1 Tuần": "1w"
        }
    },
    "Türkçe": {
        "titulo": "🏦  BRICSVAULT PORTAL - SMC + Fibonacci Motoru",
        "config_globais": "⚙️  Genel Ayarlar",
        "selecione_cripto": "Herhangi bir Kripto Para Birimi Seçin (/USDT):",
        "tempo_grafico": "Zaman Dilimi:",
        "modo_vivo": "Gerçek Zamanlı İzlemeyi Etkinleştir",
        "intervalo_refresh": "Yenileme Aralığı (Saniye):",
        "preco_spot": "Güncel Fiyat",
        "variacao_24h": "24 Saatlik Değişim",
        "volume_24h": "24 Saatlik Hacim (USDT)",
        "market_cap": "Piyasa Değeri (USD)",
        "stop_atr": "ATR Durdurma",
        "compra_forte": "🟢  GÜÇLÜ ALIM (SMC + FIBONACCI)",
        "venda_forte": "🔴  GÜÇLÜ SATIM (SMC + FIBONACCI)",
        "neutro": "🟡  NÖTR (SMC BEKLE)",
        "erro_dados": "Yetersiz geçmiş veri. Başka bir varlık seçin veya Zaman Dilimini azaltın.",
        "ctx_desconto": "Fibonacci İskonto Bölgesi (Mükemmel risk/getiri).",
        "ctx_premium": "Fibonacci Prim Bölgesi (Fiyat gerilmiş, kar alma için uygun).",
        "ctx_neutro": "Fibonacci nötr bölgesi (Fair Value Zone).",
        "ultima_atualizacao": "Son Güncelleme",
        "proximo_refresh": "Sonraki yenileme",
        "segundos": "saniye",
        "grafico_titulo": "📈  Etkileşimli Fiyat Grafiği",
        "buscando_marketcap": "🔍  Piyasa Değeri alınıyor...",
        "marketcap_nao_disponivel": "Mevcut değil",
        "idioma_label": "🌐  Dil / Language",
        "idioma_selecao": "Arayüz dilini seçin:",
        "aviso_aquecimento": "⚠️ Hesaplamada ısınma mumları kullanıldı",
        "alvo_swing_title": "🎯 Hedef Projeksiyonu (Fibonacci / Smart Money)",
        "direcao_operacao": "Yön",
        "entrada_projetada": "Projeksiyon Giriş",
        "stop_projetado": "Projeksiyon Durdurma",
        "swing_alto": "Swing Yüksek",
        "swing_baixo": "Swing Düşük",
        "range_label": "Aralık",
        "alvo_prefix": "HEDEF {n}",
        "sem_alvos": "Bu hareket için hedef yok.",
        "contexto_smc": "SMC Bağlamı",
        "trend_ascendente": "Yükseliş Trendi 🟢",
        "trend_descendente": "Düşüş Trendi 🔴",
        "trend_neutra": "Nötr Trend 🟡",
        "intervalos": {
            "1 Dakika": "1m", "5 Dakika": "5m", "15 Dakika": "15m",
            "30 Dakika": "30m", "1 Saat": "1h", "4 Saat": "4h",
            "1 Gün": "1d", "1 Hafta": "1w"
        }
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# FORMATAÇÃO
def formatar_preco(valor, prefixo="$ "):
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return f"{prefixo}—"
    if valor <= 0:
        return f"{prefixo}0.00"
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
        return "$ 0.00"
    if valor >= 1_000_000_000_000:
        return f"$ {valor / 1_000_000_000_000:.2f}T"
    elif valor >= 1_000_000_000:
        return f"$ {valor / 1_000_000_000:.2f}B"
    elif valor >= 1_000_000:
        return f"$ {valor / 1_000_000:.2f}M"
    else:
        return f"$ {valor:,.2f}"

# ─────────────────────────────────────────────────────────────────────────────
# GERENCIADOR DE EXCHANGES
class ExchangeManager:
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
# FUNÇÕES DE MERCADO
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
                if not result["volume"]:
                    result["volume"] = obter_volume_usd_direto(exchange_name, simbolo)
                if result["last"] is not None:
                    return result
        except Exception:
            continue
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
        elif exchange_name == "Gate.io":
            pair = simbolo.replace("/", "_")
            url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={pair}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    return float(data[0].get("quote_volume", 0))
    except:
        pass
    return None

# ─────────────────────────────────────────────────────────────────────────────
# NOME EXTENSO
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
# MARKET CAP
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
# FIBONACCI RETRAÇÃO (original)
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
# DETECTOR DE SWING
def detectar_swing(df, periodo=PERIODO_SWING_DEFAULT):
    if len(df) < periodo:
        periodo = len(df)
    df_swing = df.iloc[-periodo:].copy()
    return df_swing['high'].max(), df_swing['low'].min()

# ─────────────────────────────────────────────────────────────────────────────
# GERADOR DE SINAL FIBONACCI
def gerar_sinal_fibonacci(df, direcao, multiplicadores, periodo_swing):
    swing_high, swing_low = detectar_swing(df, periodo_swing)
    preco_atual = df['close'].iloc[-1]

    if direcao == "LONG":
        stop = swing_low
        risco = preco_atual - stop
        alvos = [preco_atual + mult * risco for mult in multiplicadores]
        alvos_validos = [a for a in alvos if a > preco_atual]
    else:  # SHORT
        stop = swing_high
        risco = stop - preco_atual
        alvos = [preco_atual - mult * risco for mult in multiplicadores]
        alvos_validos = [a for a in alvos if a < preco_atual]

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
# ANÁLISE DE CONFLUÊNCIA SMC (com parâmetros dinâmicos para assertividade)
def analisar_confluencia(df_completo, txt, limiar_sinal=9.0, periodo_aquecimento=100):
    # Usa o período de aquecimento passado como parâmetro (dinâmico)
    df_analise = df_completo.iloc[periodo_aquecimento:].copy()

    if df_analise.empty:
        return txt["neutro"], "#ffcc00", txt["ctx_neutro"], 0.0, 0.0, "NEUTRO"

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

    # Usa o limiar dinâmico para decidir o sinal forte
    if pontos_alta >= limiar_sinal:
        direcao = "LONG"
        return (txt["compra_forte"], "#00cc66",
                f"{contexto_fib} SMC + PPO Order Flow Bullish.",
                pontos_alta, pontos_baixa, direcao)
    elif pontos_baixa >= limiar_sinal:
        direcao = "SHORT"
        return (txt["venda_forte"], "#ff3333",
                f"{contexto_fib} SMC + PPO Order Flow Bearish.",
                pontos_alta, pontos_baixa, direcao)
    else:
        media_50 = df_analise['close'].rolling(50).mean().iloc[-1]
        if preco_atual > media_50:
            direcao = "LONG"
        else:
            direcao = "SHORT"
        return txt["neutro"], "#ffcc00", contexto_fib, pontos_alta, pontos_baixa, direcao

# ─────────────────────────────────────────────────────────────────────────────
# FUNÇÃO PARA CALCULAR ASSERTIVIDADE HISTÓRICA (BACKTEST RÁPIDO)
def calcular_assertividade_historica(df, limiar, periodo_aquecimento, txt):
    """
    Avalia quantos sinais fortes (acima do limiar) teriam acertado um alvo de 1%
    nos 5 candles seguintes. Isso dá uma noção da assertividade da configuração atual.
    """
    acertos = 0
    total = 0
    if len(df) < periodo_aquecimento + 50:
        return "Dados históricos insuficientes para testar a assertividade."
    
    df_back = df.iloc[periodo_aquecimento:].copy()
    if len(df_back) < 50:
        return "Dados insuficientes após o aquecimento."
    
    # Testa apenas os últimos 100 pontos para não pesar o processamento
    inicio = max(30, len(df_back) - 100)
    for i in range(inicio, len(df_back) - 5):
        fatia = df_back.iloc[:i+1]
        # Reconstrói o contexto completo (aquecimento + fatia atual)
        df_contexto = pd.concat([df.iloc[:periodo_aquecimento], fatia])
        try:
            _, _, _, pontos_alta, pontos_baixa, direcao = analisar_confluencia(
                df_contexto, txt, limiar, periodo_aquecimento
            )
        except Exception:
            continue
        
        # Verifica se é um sinal forte (compra ou venda)
        if (pontos_alta >= limiar and direcao == "LONG") or (pontos_baixa >= limiar and direcao == "SHORT"):
            total += 1
            preco_atual = fatia['close'].iloc[-1]
            futuros = df_back.iloc[i+1:i+6]  # próximos 5 candles
            if not futuros.empty:
                if direcao == "LONG" and (futuros['high'].max() >= preco_atual * 1.01):
                    acertos += 1
                elif direcao == "SHORT" and (futuros['low'].min() <= preco_atual * 0.99):
                    acertos += 1
    
    if total == 0:
        return "Nenhum sinal forte gerado no histórico recente. Tente reduzir a nota de corte."
    return f"Assertividade (acertou alvo de 1% nos próximos 5 candles): {acertos}/{total} ({acertos/total*100:.1f}%)"

# ─────────────────────────────────────────────────────────────────────────────
# CARREGAMENTO DE DADOS
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
        xaxis=dict(gridcolor='#1e293b', showgrid=True, rangeslider=dict(visible=False)),
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

# ─── NOVOS SLIDERS PARA ASSERTIVIDADE ───
st.sidebar.markdown("### ⚙️ Ajuste de Assertividade")
limiar_sinal = st.sidebar.slider(
    "Nota de corte para sinal forte (padrão 9.0):",
    min_value=5.0, max_value=12.0, value=9.0, step=0.5,
    help="Quanto maior, mais rigoroso. Para 1h, 9.0 é um bom equilíbrio entre filtro e oportunidades."
)
periodo_aquecimento_ui = st.sidebar.slider(
    "Velas de aquecimento (padrão 100):",
    min_value=50, max_value=300, value=100, step=10,
    help="Define quantas velas iniciais são ignoradas no cálculo. Para 1h, 100 velas = 4 dias."
)

# ─────────────────────────────────────────────────────────────────────────────
# PAINEL PRINCIPAL (com os novos parâmetros)
@st.fragment(run_every=intervalo_refresh if modo_vivo else None)
def painel_principal(simbolo_id, timeframe, txt, modo_vivo, intervalo_refresh,
                     multiplicadores, periodo_swing, limiar_sinal, periodo_aquecimento_ui):
    df_dados = carregar_dados(simbolo_id, timeframe)

    if df_dados is None or df_dados.empty:
        st.warning(txt["erro_dados"])
        return

    df_analise = df_dados.iloc[periodo_aquecimento_ui:]
    if df_analise.empty:
        st.warning(txt["erro_dados"])
        return

    ultimo_reg = df_analise.iloc[-1]
    preco_atual = ultimo_reg['close']

    # ─── PREÇO ATUAL EM DESTAQUE (CARD CENTRALIZADO) ───
    st.markdown("---")
    col_preco1, col_preco2, col_preco3 = st.columns([1, 2, 1])
    with col_preco2:
        nome_curto = simbolo_id.split('/')[0]
        st.markdown(
            f"""
            <div style="text-align: center; padding: 15px; background: #1e293b; border-radius: 12px; border: 1px solid #475569;">
                <span style="font-size: 32px; font-weight: bold; color: #e2e8f0;">
                    {formatar_preco(preco_atual)}
                </span>
                <br>
                <span style="font-size: 16px; color: #94a3b8;">
                    {nome_curto} / USDT – {txt['preco_spot']}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown("---")

    dados_24h = obter_dados_24h(simbolo_id)
    variacao_24h = dados_24h.get("change") if dados_24h else 0.0
    volume_24h = dados_24h.get("volume") if dados_24h else None
    market_cap = obter_market_cap_robusto(simbolo_id)

    # Chama a análise com os parâmetros dinâmicos
    recomendacao, cor_sinal, analise, pontos_alta, pontos_baixa, direcao = analisar_confluencia(
        df_dados, txt, limiar_sinal, periodo_aquecimento_ui
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

    sinal_fib = gerar_sinal_fibonacci(df_dados, direcao, multiplicadores, periodo_swing)

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

    # ─── PAINEL DE ASSERTIVIDADE (EXPANDIDO) ───
    with st.expander("📊 Ver Assertividade nos Últimos Dados"):
        resultado = calcular_assertividade_historica(df_dados, limiar_sinal, periodo_aquecimento_ui, txt)
        st.write(resultado)
        st.caption("💡 Quanto maior a porcentagem, mais confiável a configuração atual para o ativo e timeframe escolhidos.")

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
            f"{txt['aviso_aquecimento']}: {periodo_aquecimento_ui} | "
            f"Velas analisadas: {n_velas}"
        )
    else:
        st.info(
            f"⏸ {txt['ultima_atualizacao']}: {hora_atual} | "
            f"{txt['aviso_aquecimento']}: {periodo_aquecimento_ui} | "
            f"Velas analisadas: {n_velas}"
        )

    # ─── RODAPÉ ───
    st.markdown("---")
    st.caption(
        "💡 **Aceita uma sugestão?** Configure seu app para **1 Hora**, período do swing **50**, "
        "nota de corte **9.0** e veja a mágica acontecer! 🚀  \n"
        "⚠️ **Não é dica de investimento – faça a sua própria análise.**"
    )

# ─── CHAMADA FINAL COM OS NOVOS PARÂMETROS ───
painel_principal(simbolo_id, timeframe, txt, modo_vivo, intervalo_refresh,
                 multiplicadores, periodo_swing, limiar_sinal, periodo_aquecimento_ui)
