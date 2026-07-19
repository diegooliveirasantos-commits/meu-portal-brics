# -----------------------------------------------------------------------------
# BRICSVAULT PORTAL - Smart Money Concepts (SMC) Engine
# Versão 2.0 - Streamlit Dashboard
# Requisitos: streamlit, ccxt, pandas, numpy, requests, plotly, decimal
# -----------------------------------------------------------------------------

import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import requests
import math
from decimal import Decimal
import plotly.graph_objects as go
from typing import Optional, Dict, Any, List, Tuple, Union

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="BRICSVAULT PORTAL SMC",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# CONSTANTES GLOBAIS
# -----------------------------------------------------------------------------
VELAS_TOTAL: int = 500
PERIODO_AQUECIMENTO: int = 100
IDIOMA_PADRAO: str = "Português (BR)"
TTL_MERCADOS_SEGUNDOS: int = 3600
TTL_DADOS_LIVE_SEGUNDOS: int = 15
TTL_BOOK_SEGUNDOS: int = 12
EXCHANGE_TIMEOUT_MS: int = 10000

LIMITE_BOOK: int = 100
FAIXA_BOOK: float = 0.015
PASSO_AGRUPAMENTO: float = 0.0005

JANELA_BASE_WYCKOFF: int = 60
JANELA_EVENTO_WYCKOFF: int = 15

LIMIAR_SINAL_LIQUIDO: float = 32.0
PONTOS_MAX_WYCKOFF: float = 3.0

# -----------------------------------------------------------------------------
# DICIONÁRIO DE IDIOMAS (mantido exatamente como original)
# -----------------------------------------------------------------------------
_TEXTOS_BASE_PT_BR = {
    "titulo": "🏦 BRICSVAULT PORTAL - Motor de Smart Money Concepts (SMC)",
    "config_globais": "⚙️ Configurações Globais",
    "selecione_cripto": "Selecione Qualquer Criptomoeda (/USDT):",
    "tempo_grafico": "Tempo Gráfico:",
    "modo_vivo": "Ativar Monitoramento em Tempo Real",
    "intervalo_refresh": "Intervalo de Atualização (Segundos):",
    "preco_spot": "Preço Spot Real",
    "variacao_24h": "Variação 24h",
    "volume_24h": "Volume 24h (USDT)",
    "market_cap": "Market Cap (USDT)",
    "stop_atr": "Preço Stop ATR",
    "compra_forte": "🟢 COMPRA FORTE (SMC + FIBONACCI ALINHADOS)",
    "venda_forte": "🔴 VENDA FORTE (SMC + FIBONACCI ALINHADOS)",
    "neutro": "🟡 NEUTRO (AGUARDAR SMC)",
    "erro_dados": "Dados históricos insuficientes. Tente outro ativo ou reduza o Tempo Gráfico.",
    "ctx_desconto": "Ativo em Zona de Desconto de Fibonacci (Excelente risco/retorno para Institucionais).",
    "ctx_premium": "Ativo em Zona Premium de Fibonacci (Preço esticado, propício para realização de lucro).",
    "ctx_neutro": "Preço em zona neutra de Fibonacci (Fair Value Zone).",
    "ultima_atualizacao": "Última Atualização",
    "proximo_refresh": "Próximo refresh em",
    "segundos": "segundos",
    "pontos_compra": "Pontos de Compra",
    "pontos_venda": "Pontos de Venda",
    "grafico_titulo": "📈 Gráfico de Preço Interativo",
    "buscando_marketcap": "🔍 Buscando Market Cap...",
    "marketcap_nao_disponivel": "Não disponível",
    "idioma_label": "🌐 Idioma / Language",
    "idioma_selecao": "Selecione o idioma da interface:",
    "aviso_aquecimento": "⚠️ Velas de aquecimento usadas no cálculo",
    "escore_liquido": "Escore Líquido",
    "plano_trade": "🎯 Plano de Trade",
    "entrada": "Entrada",
    "stop_loss": "STOP LOSS",
    "alvo": "Alvo",
    "risco_retorno": "Risco/Retorno no Alvo 1",
    "base_stop": "Base do stop",
    "book_titulo": "📊 Livro de Ofertas Agregado",
    "zonas_compra": "MAIORES ZONAS DE COMPRA",
    "zonas_venda": "MAIORES ZONAS DE VENDA",
    "pressao_global": "PRESSÃO GLOBAL DE MERCADO",
    "compra": "COMPRA",
    "venda": "VENDA",
    "desequilibrio": "Desequilíbrio",
    "book_equilibrado": "MERCADO EQUILIBRADO",
    "book_comprador": "PRESSÃO COMPRADORA",
    "book_vendedor": "PRESSÃO VENDEDORA",
    "book_indisponivel": "Livro de ofertas indisponível no momento (nenhuma corretora respondeu). O escore segue válido sem este fator.",
    "profundidade": "PROFUNDIDADE AGREGADA (±1,5% do mid)",
    "wyckoff_titulo": "🧭 Estrutura Wyckoff",
    "wyckoff_sem_evento": "Nenhum evento de Fase C/D identificado na janela recente. Range em construção (Fase B) ou preço fora de range.",
    "wyckoff_range": "Trading Range",
    "wyckoff_evento": "Evento",
    "wyckoff_fase": "Fase",
    "wyckoff_teste": "Teste Secundário",
    "wyckoff_sos": "SOS / SOW",
    "wyckoff_lps": "LPS / LPSY",
    "confirmado": "confirmado",
    "nao_confirmado": "não confirmado",
    "alerta_muralha": "⚠️ Muralha de liquidez contrária relevante logo à frente do preço --- sinal rebaixado para NEUTRO até o rompimento.",
    "valor_memorizado": "último valor conhecido",
    "fontes_book": "Corretoras no book",
    "intervalos": {
        "1 Minuto": "1m", "5 Minutos": "5m", "15 Minutos": "15m", "30 Minutos": "30m",
        "1 Hora": "1h", "4 Horas": "4h", "1 Dia": "1d", "1 Semana": "1w"
    }
}

_TRADUCOES = {
    IDIOMA_PADRAO: _TEXTOS_BASE_PT_BR,
    "English (EN)": {
        "titulo": "🏦 BRICSVAULT PORTAL - Smart Money Concepts (SMC) Engine",
        "config_globais": "⚙️ Global Settings",
        "selecione_cripto": "Select Any Cryptocurrency (/USDT):",
        "tempo_grafico": "Timeframe:",
        "modo_vivo": "Enable Real-Time Monitoring",
        "intervalo_refresh": "Refresh Interval (Seconds):",
        "preco_spot": "Real Spot Price",
        "variacao_24h": "24h Variation",
        "volume_24h": "24h Volume (USDT)",
        "market_cap": "Market Cap (USDT)",
        "stop_atr": "ATR Stop Price",
        "compra_forte": "🟢 STRONG BUY (SMC + FIBONACCI ALIGNED)",
        "venda_forte": "🔴 STRONG SELL (SMC + FIBONACCI ALIGNED)",
        "neutro": "🟡 NEUTRAL (AWAIT SMC)",
        "erro_dados": "Insufficient historical data. Try another asset or reduce the Timeframe.",
        "ctx_desconto": "Asset in Fibonacci Discount Zone (Excellent risk/reward for Institutionals).",
        "ctx_premium": "Asset in Fibonacci Premium Zone (Price stretched, suitable for profit-taking).",
        "ctx_neutro": "Price in neutral Fibonacci zone (Fair Value Zone).",
        "ultima_atualizacao": "Last Update",
        "proximo_refresh": "Next refresh in",
        "segundos": "seconds",
        "pontos_compra": "Buy Points",
        "pontos_venda": "Sell Points",
        "grafico_titulo": "📈 Interactive Price Chart",
        "buscando_marketcap": "🔍 Fetching Market Cap...",
        "marketcap_nao_disponivel": "Not available",
        "idioma_label": "🌐 Language / Idioma",
        "idioma_selecao": "Select Interface Language:",
        "aviso_aquecimento": "⚠️ Warm-up candles used in calculation",
        "escore_liquido": "Net Score",
        "plano_trade": "🎯 Trade Plan",
        "entrada": "Entry",
        "stop_loss": "STOP LOSS",
        "alvo": "Target",
        "risco_retorno": "Risk/Reward at Target 1",
        "base_stop": "Stop basis",
        "book_titulo": "📊 Aggregated Order Book",
        "zonas_compra": "LARGEST BUY ZONES",
        "zonas_venda": "LARGEST SELL ZONES",
        "pressao_global": "GLOBAL MARKET PRESSURE",
        "compra": "BUY",
        "venda": "SELL",
        "desequilibrio": "Imbalance",
        "book_equilibrado": "BALANCED MARKET",
        "book_comprador": "BUYING PRESSURE",
        "book_vendedor": "SELLING PRESSURE",
        "book_indisponivel": "Order book unavailable right now (no exchange responded). The score remains valid without this factor.",
        "profundidade": "AGGREGATED DEPTH (±1.5% of mid)",
        "wyckoff_titulo": "🧭 Wyckoff Structure",
        "wyckoff_sem_evento": "No Phase C/D event found in the recent window. Range still building (Phase B) or price outside a range.",
        "wyckoff_range": "Trading Range",
        "wyckoff_evento": "Event",
        "wyckoff_fase": "Phase",
        "wyckoff_teste": "Secondary Test",
        "wyckoff_sos": "SOS / SOW",
        "wyckoff_lps": "LPS / LPSY",
        "confirmado": "confirmed",
        "nao_confirmado": "not confirmed",
        "alerta_muralha": "⚠️ Significant opposing liquidity wall right ahead of price --- signal downgraded to NEUTRAL until it breaks.",
        "valor_memorizado": "last known value",
        "fontes_book": "Exchanges in book",
        "intervalos": {
            "1 Minute": "1m", "5 Minutes": "5m", "15 Minutes": "15m", "30 Minutes": "30m",
            "1 Hour": "1h", "4 Hours": "4h", "1 Day": "1d", "1 Week": "1w"
        }
    },
    "Español": {
        "titulo": "🏦 BRICSVAULT PORTAL - Motor de Smart Money Concepts (SMC)",
        "config_globais": "⚙️ Configuraciones Globales",
        "selecione_cripto": "Seleccione cualquier criptomoneda (/USDT):",
        "tempo_grafico": "Marco temporal:",
        "modo_vivo": "Activar monitoreo en tiempo real",
        "intervalo_refresh": "Intervalo de actualización (segundos):",
        "preco_spot": "Precio Spot Real",
        "variacao_24h": "Variación 24h",
        "volume_24h": "Volumen 24h (USDT)",
        "market_cap": "Capitalización (USDT)",
        "stop_atr": "Precio Stop ATR",
        "compra_forte": "🟢 COMPRA FUERTE (SMC + FIBONACCI ALINEADOS)",
        "venda_forte": "🔴 VENTA FUERTE (SMC + FIBONACCI ALINEADOS)",
        "neutro": "🟡 NEUTRO (ESPERAR SMC)",
        "erro_dados": "Datos históricos insuficientes. Pruebe con otro activo o reduzca el marco temporal.",
        "ctx_desconto": "Activo en Zona de Descuento de Fibonacci (Excelente riesgo/retorno para Institucionales).",
        "ctx_premium": "Activo en Zona Premium de Fibonacci (Precio estirado, propicio para toma de ganancias).",
        "ctx_neutro": "Precio en zona neutral de Fibonacci (Fair Value Zone).",
        "ultima_atualizacion": "Última actualización",
        "proximo_refresh": "Próxima actualización en",
        "segundos": "segundos",
        "pontos_compra": "Puntos de Compra",
        "pontos_venda": "Puntos de Venta",
        "grafico_titulo": "📈 Gráfico de Precio Interactivo",
        "buscando_marketcap": "🔍 Buscando Capitalización...",
        "marketcap_nao_disponivel": "No disponible",
        "idioma_label": "🌐 Idioma / Language",
        "idioma_selecao": "Seleccione el idioma de la interfaz:",
        "aviso_aquecimento": "⚠️ Velas de calentamiento usadas en el cálculo",
        "intervalos": {
            "1 Minuto": "1m", "5 Minutos": "5m", "15 Minutos": "15m", "30 Minutos": "30m",
            "1 Hora": "1h", "4 Horas": "4h", "1 Día": "1d", "1 Semana": "1w"
        }
    },
    "Français": {
        "titulo": "🏦 BRICSVAULT PORTAL - Moteur Smart Money Concepts (SMC)",
        "config_globais": "⚙️ Paramètres globaux",
        "selecione_cripto": "Sélectionnez une cryptomonnaie (/USDT):",
        "tempo_grafico": "Période:",
        "modo_vivo": "Activer la surveillance en temps réel",
        "intervalo_refresh": "Intervalle de rafraîchissement (secondes):",
        "preco_spot": "Cours Spot réel",
        "variacao_24h": "Variation 24h",
        "volume_24h": "Volume 24h (USDT)",
        "market_cap": "Capitalisation (USDT)",
        "stop_atr": "Prix Stop ATR",
        "compra_forte": "🟢 ACHAT FORT (SMC + FIBONACCI ALIGNÉS)",
        "venda_forte": "🔴 VENTE FORTE (SMC + FIBONACCI ALIGNÉS)",
        "neutro": "🟡 NEUTRE (ATTENDRE SMC)",
        "erro_dados": "Données historiques insuffisantes. Essayez un autre actif ou réduisez la période.",
        "ctx_desconto": "Actif en zone de discount de Fibonacci (Excellent risque/rendement pour les institutionnels).",
        "ctx_premium": "Actif en zone premium de Fibonacci (Prix étiré, propice à la prise de bénéfices).",
        "ctx_neutro": "Prix en zone neutre de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Dernière mise à jour",
        "proximo_refresh": "Prochain rafraîchissement dans",
        "segundos": "secondes",
        "pontos_compra": "Points d'achat",
        "pontos_venda": "Points de vente",
        "grafico_titulo": "📈 Graphique de prix interactif",
        "buscando_marketcap": "🔍 Recherche de la capitalisation...",
        "marketcap_nao_disponivel": "Indisponible",
        "idioma_label": "🌐 Langue / Language",
        "idioma_selecao": "Sélectionnez la langue de l'interface:",
        "aviso_aquecimento": "⚠️ Bougies de chauffe utilisées dans le calcul",
        "intervalos": {
            "1 Minute": "1m", "5 Minutes": "5m", "15 Minutes": "15m", "30 Minutes": "30m",
            "1 Heure": "1h", "4 Heures": "4h", "1 Jour": "1d", "1 Semaine": "1w"
        }
    },
    "Deutsch": {
        "titulo": "🏦 BRICSVAULT PORTAL - Smart Money Concepts (SMC) Motor",
        "config_globais": "⚙️ Globale Einstellungen",
        "selecione_cripto": "Wählen Sie eine Kryptowährung (/USDT):",
        "tempo_grafico": "Zeitrahmen:",
        "modo_vivo": "Echtzeit-Überwachung aktivieren",
        "intervalo_refresh": "Aktualisierungsintervall (Sekunden):",
        "preco_spot": "Echter Spot-Preis",
        "variacao_24h": "24h-Veränderung",
        "volume_24h": "24h-Volumen (USDT)",
        "market_cap": "Marktkapitalisierung (USDT)",
        "stop_atr": "ATR-Stop-Preis",
        "compra_forte": "🟢 STARKER KAUF (SMC + FIBONACCI AUSGERICHTET)",
        "venda_forte": "🔴 STARKER VERKAUF (SMC + FIBONACCI AUSGERICHTET)",
        "neutro": "🟡 NEUTRAL (SMC ABWARTEN)",
        "erro_dados": "Unzureichende historische Daten. Versuchen Sie es mit einem anderen Vermögenswert oder reduzieren Sie den Zeitrahmen.",
        "ctx_desconto": "Vermögenswert in Fibonacci-Discount-Zone (Ausgezeichnetes Risiko/Rendite für Institutionelle).",
        "ctx_premium": "Vermögenswert in Fibonacci-Premium-Zone (Preis gedehnt, gewinnmitnahme geeignet).",
        "ctx_neutro": "Preis in neutraler Fibonacci-Zone (Fair Value Zone).",
        "ultima_atualizacao": "Letzte Aktualisierung",
        "proximo_refresh": "Nächste Aktualisierung in",
        "segundos": "Sekunden",
        "pontos_compra": "Kaufpunkte",
        "pontos_venda": "Verkaufspunkte",
        "grafico_titulo": "📈 Interaktives Kursdiagramm",
        "buscando_marketcap": "🔍 Marktkapitalisierung wird abgerufen...",
        "marketcap_nao_disponivel": "Nicht verfügbar",
        "idioma_label": "🌐 Sprache / Language",
        "idioma_selecao": "Wählen Sie die Oberflächensprache:",
        "aviso_aquecimento": "⚠️ Aufwärm-Kerzen im Rechengang verwendet",
        "intervalos": {
            "1 Minute": "1m", "5 Minuten": "5m", "15 Minuten": "15m", "30 Minuten": "30m",
            "1 Stunde": "1h", "4 Stunden": "4h", "1 Tag": "1d", "1 Woche": "1w"
        }
    },
    "Italiano": {
        "titulo": "🏦 BRICSVAULT PORTAL - Motore Smart Money Concepts (SMC)",
        "config_globais": "⚙️ Impostazioni globali",
        "selecione_cripto": "Seleziona una criptovaluta (/USDT):",
        "tempo_grafico": "Timeframe:",
        "modo_vivo": "Attiva monitoraggio in tempo reale",
        "intervalo_refresh": "Intervallo di aggiornamento (secondi):",
        "preco_spot": "Prezzo Spot Reale",
        "variacao_24h": "Variazione 24h",
        "volume_24h": "Volume 24h (USDT)",
        "market_cap": "Capitalizzazione (USDT)",
        "stop_atr": "Prezzo Stop ATR",
        "compra_forte": "🟢 ACQUISTO FORTE (SMC + FIBONACCI ALLINEATI)",
        "venda_forte": "🔴 VENDITA FORTE (SMC + FIBONACCI ALLINEATI)",
        "neutro": "🟡 NEUTRO (ATTENDERE SMC)",
        "erro_dados": "Dati storici insufficienti. Prova un altro asset o riduci il timeframe.",
        "ctx_desconto": "Asset in Zona di Sconto di Fibonacci (Ottimo rischio/rendimento per Istituzionali).",
        "ctx_premium": "Asset in Zona Premium di Fibonacci (Prezzo allungato, adatto per presa di profitto).",
        "ctx_neutro": "Prezzo in zona neutrale di Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Ultimo aggiornamento",
        "proximo_refresh": "Prossimo aggiornamento tra",
        "segundos": "secondi",
        "pontos_compra": "Punti di Acquisto",
        "pontos_venda": "Punti di Vendita",
        "grafico_titulo": "📈 Grafico Prezzo Interattivo",
        "buscando_marketcap": "🔍 Ricerca Capitalizzazione...",
        "marketcap_nao_disponivel": "Non disponibile",
        "idioma_label": "🌐 Lingua / Language",
        "idioma_selecao": "Seleziona la lingua dell'interfaccia:",
        "aviso_aquecimento": "⚠️ Candele di riscaldamento utilizzate nel calcolo",
        "intervalos": {
            "1 Minuto": "1m", "5 Minuti": "5m", "15 Minuti": "15m", "30 Minuti": "30m",
            "1 Ora": "1h", "4 Ore": "4h", "1 Giorno": "1d", "1 Settimana": "1w"
        }
    },
    "Русский": {
        "titulo": "🏦 BRICSVAULT PORTAL - Двигатель Smart Money Concepts (SMC)",
        "config_globais": "⚙️ Глобальные настройки",
        "selecione_cripto": "Выберите криптовалюту (/USDT):",
        "tempo_grafico": "Таймфрейм:",
        "modo_vivo": "Включить мониторинг в реальном времени",
        "intervalo_refresh": "Интервал обновления (секунды):",
        "preco_spot": "Реальная спот-цена",
        "variacao_24h": "Изменение за 24ч",
        "volume_24h": "Объем за 24ч (USDT)",
        "market_cap": "Рыночная капитализация (USDT)",
        "stop_atr": "Цена стоп-лосса ATR",
        "compra_forte": "🟢 СИЛЬНАЯ ПОКУПКА (SMC + ФИБОНАЧЧИ СОГЛАСОВАНЫ)",
        "venda_forte": "🔴 СИЛЬНАЯ ПРОДАЖА (SMC + ФИБОНАЧЧИ СОГЛАСОВАНЫ)",
        "neutro": "🟡 НЕЙТРАЛЬНО (ОЖИДАТЬ SMC)",
        "erro_dados": "Недостаточно исторических данных. Попробуйте другой актив или уменьшите таймфрейм.",
        "ctx_desconto": "Актив в зоне скидки Фибоначчи (Отличное соотношение риск/доходность для институционалов).",
        "ctx_premium": "Актив в премиальной зоне Фибоначчи (Цена растянута, подходит для фиксации прибыли).",
        "ctx_neutro": "Цена в нейтральной зоне Фибоначчи (Fair Value Zone).",
        "ultima_atualizacao": "Последнее обновление",
        "proximo_refresh": "Следующее обновление через",
        "segundos": "секунд",
        "pontos_compra": "Очки покупки",
        "pontos_venda": "Очки продажи",
        "grafico_titulo": "📈 Интерактивный график цены",
        "buscando_marketcap": "🔍 Получение рыночной капитализации...",
        "marketcap_nao_disponivel": "Недоступно",
        "idioma_label": "🌐 Язык / Language",
        "idioma_selecao": "Выберите язык интерфейса:",
        "aviso_aquecimento": "⚠️ Используются свечи разогрева в расчетах",
        "intervalos": {
            "1 Минута": "1m", "5 Минут": "5m", "15 Минут": "15m", "30 Минут": "30m",
            "1 Час": "1h", "4 Часа": "4h", "1 День": "1d", "1 Неделя": "1w"
        }
    },
    "日本語": {
        "titulo": "🏦 BRICSVAULT PORTAL - スマートマネーコンセプト（SMC）エンジン",
        "config_globais": "⚙️ グローバル設定",
        "selecione_cripto": "暗号通貨を選択（/USDT）:",
        "tempo_grafico": "タイムフレーム:",
        "modo_vivo": "リアルタイム監視を有効にする",
        "intervalo_refresh": "更新間隔（秒）:",
        "preco_spot": "実勢スポット価格",
        "variacao_24h": "24時間変動",
        "volume_24h": "24時間出来高（USDT）",
        "market_cap": "時価総額（USDT）",
        "stop_atr": "ATRストップ価格",
        "compra_forte": "🟢 強い買い（SMC＋フィボナッチ整合）",
        "venda_forte": "🔴 強い売り（SMC＋フィボナッチ整合）",
        "neutro": "🟡 中立（SMC待機）",
        "erro_dados": "履歴データが不十分です。別の資産を選ぶか、タイムフレームを小さくしてください。",
        "ctx_desconto": "フィボナッチ割引ゾーンにある資産（機関投資家向けの優れたリスク/リターン）。",
        "ctx_premium": "フィボナッチプレミアムゾーンにある資産（価格が伸びており、利益確定に適している）。",
        "ctx_neutro": "フィボナッチ中立ゾーンの価格（フェアバリューゾーン）。",
        "ultima_atualizacao": "最終更新",
        "proximo_refresh": "次の更新まで",
        "segundos": "秒",
        "pontos_compra": "買いポイント",
        "pontos_venda": "売りポイント",
        "grafico_titulo": "📈 インタラクティブ価格チャート",
        "buscando_marketcap": "🔍 時価総額を取得中...",
        "marketcap_nao_disponivel": "利用不可",
        "idioma_label": "🌐 言語 / Language",
        "idioma_selecao": "インターフェース言語を選択:",
        "aviso_aquecimento": "⚠️ 計算にウォームアップローソクを使用",
        "intervalos": {
            "1分": "1m", "5分": "5m", "15分": "15m", "30分": "30m",
            "1時間": "1h", "4時間": "4h", "1日": "1d", "1週間": "1w"
        }
    },
    "中文 (简体)": {
        "titulo": "🏦 BRICSVAULT PORTAL - 智能资金概念（SMC）引擎",
        "config_globais": "⚙️ 全局设置",
        "selecione_cripto": "选择加密货币（/USDT）：",
        "tempo_grafico": "时间周期：",
        "modo_vivo": "启用实时监控",
        "intervalo_refresh": "刷新间隔（秒）：",
        "preco_spot": "实时现货价格",
        "variacao_24h": "24小时变化",
        "volume_24h": "24小时成交量（USDT）",
        "market_cap": "市值（USDT）",
        "stop_atr": "ATR止损价",
        "compra_forte": "🟢 强烈买入（SMC + 斐波那契一致）",
        "venda_forte": "🔴 强烈卖出（SMC + 斐波那契一致）",
        "neutro": "🟡 中性（等待SMC）",
        "erro_dados": "历史数据不足。请选择其他资产或缩短时间周期。",
        "ctx_desconto": "资产处于斐波那契折价区（机构级卓越风险/回报）。",
        "ctx_premium": "资产处于斐波那契溢价区（价格拉伸，适合获利了结）。",
        "ctx_neutro": "价格处于斐波那契中性区（公允价值区）。",
        "ultima_atualizacao": "最后更新",
        "proximo_refresh": "下次刷新于",
        "segundos": "秒",
        "pontos_compra": "买入点",
        "pontos_venda": "卖出点",
        "grafico_titulo": "📈 交互式价格图表",
        "buscando_marketcap": "🔍 正在获取市值...",
        "marketcap_nao_disponivel": "不可用",
        "idioma_label": "🌐 语言 / Language",
        "idioma_selecao": "选择界面语言：",
        "aviso_aquecimento": "⚠️ 计算中使用预热K线",
        "intervalos": {
            "1分钟": "1m", "5分钟": "5m", "15分钟": "15m", "30分钟": "30m",
            "1小时": "1h", "4小时": "4h", "1天": "1d", "1周": "1w"
        }
    },
    "हिन्दी": {
        "titulo": "🏦 BRICSVAULT PORTAL - स्मार्ट मनी कॉन्सेप्ट्स (SMC) इंजन",
        "config_globais": "⚙️ वैश्विक सेटिंग्स",
        "selecione_cripto": "कोई भी क्रिप्टोकरेंसी चुनें (/USDT):",
        "tempo_grafico": "टाइमफ्रेम:",
        "modo_vivo": "रीयल-टाइम मॉनिटरिंग सक्षम करें",
        "intervalo_refresh": "रिफ्रेश अंतराल (सेकंड):",
        "preco_spot": "वास्तविक स्पॉट मूल्य",
        "variacao_24h": "24 घंटे का बदलाव",
        "volume_24h": "24 घंटे का वॉल्यूम (USDT)",
        "market_cap": "बाजार पूंजीकरण (USDT)",
        "stop_atr": "ATR स्टॉप मूल्य",
        "compra_forte": "🟢 मजबूत खरीद (SMC + फिबोनाची संरेखित)",
        "venda_forte": "🔴 मजबूत बिक्री (SMC + फिबोनाची संरेखित)",
        "neutro": "🟡 तटस्थ (SMC की प्रतीक्षा करें)",
        "erro_dados": "अपर्याप्त ऐतिहासिक डेटा। कोई अन्य संपत्ति चुनें या टाइमफ्रेम कम करें।",
        "ctx_desconto": "संपत्ति फिबोनाची डिस्काउंट ज़ोन में (संस्थागतों के लिए उत्कृष्ट जोखिम/रिटर्न)।",
        "ctx_premium": "संपत्ति फिबोनाची प्रीमियम ज़ोन में (मूल्य खिंचा हुआ, लाभ-बुकिंग के लिए उपयुक्त)।",
        "ctx_neutro": "फिबोनाची तटस्थ क्षेत्र में मूल्य (Fair Value Zone)।",
        "ultima_atualizacao": "अंतिम अद्यतन",
        "proximo_refresh": "अगला रिफ्रेश",
        "segundos": "सेकंड",
        "pontos_compra": "खरीद अंक",
        "pontos_venda": "बिक्री अंक",
        "grafico_titulo": "📈 इंटरैक्टिव मूल्य चार्ट",
        "buscando_marketcap": "🔍 बाजार पूंजीकरण प्राप्त किया जा रहा है...",
        "marketcap_nao_disponivel": "उपलब्ध नहीं",
        "idioma_label": "🌐 भाषा / Language",
        "idioma_selecao": "इंटरफ़ेस भाषा चुनें:",
        "aviso_aquecimento": "⚠️ गणना में वार्म-अप मोमबत्तियों का उपयोग किया गया",
        "intervalos": {
            "1 मिनट": "1m", "5 मिनट": "5m", "15 मिनट": "15m", "30 मिनट": "30m",
            "1 घंटा": "1h", "4 घंटे": "4h", "1 दिन": "1d", "1 सप्ताह": "1w"
        }
    },
    "বাংলা": {
        "titulo": "🏦 BRICSVAULT PORTAL - স্মার্ট মানি কনসেপ্টস (SMC) ইঞ্জিন",
        "config_globais": "⚙️ গ্লোবাল সেটিংস",
        "selecione_cripto": "যেকোনো ক্রিপ্টোকারেন্সি নির্বাচন করুন (/USDT):",
        "tempo_grafico": "টাইমফ্রেম:",
        "modo_vivo": "রিয়েল-টাইম মনিটরিং সক্রিয় করুন",
        "intervalo_refresh": "রিফ্রেশ বিরতি (সেকেন্ড):",
        "preco_spot": "প্রকৃত স্পট মূল্য",
        "variacao_24h": "২৪ ঘণ্টার পরিবর্তন",
        "volume_24h": "২৪ ঘণ্টার ভলিউম (USDT)",
        "market_cap": "বাজার মূলধন (USDT)",
        "stop_atr": "ATR স্টপ মূল্য",
        "compra_forte": "🟢 শক্তিশালী ক্রয় (SMC + ফিবোনাচি সারিবদ্ধ)",
        "venda_forte": "🔴 শক্তিশালী বিক্রয় (SMC + ফিবোনাচি সারিবদ্ধ)",
        "neutro": "🟡 নিরপেক্ষ (SMC এর জন্য অপেক্ষা করুন)",
        "erro_dados": "অপর্যাপ্ত ঐতিহাসিক ডেটা। অন্য সম্পদ নির্বাচন করুন বা টাইমফ্রেম কমিয়ে দিন।",
        "ctx_desconto": "সম্পদ ফিবোনাচি ডিসকাউন্ট জোনে (প্রাতিষ্ঠানিকদের জন্য চমৎকার ঝুঁকি/রিটার্ন)।",
        "ctx_premium": "সম্পদ ফিবোনাচি প্রিমিয়াম জোনে (মূল্য প্রসারিত, মুনাফা গ্রহণের জন্য উপযুক্ত)।",
        "ctx_neutro": "ফিবোনাচি নিরপেক্ষ অঞ্চলে মূল্য (Fair Value Zone)।",
        "ultima_atualizacao": "শেষ আপডেট",
        "proximo_refresh": "পরবর্তী রিফ্রেশ",
        "segundos": "সেকেন্ড",
        "pontos_compra": "ক্রয় পয়েন্ট",
        "pontos_venda": "বিক্রয় পয়েন্ট",
        "grafico_titulo": "📈 ইন্টারেক্টিভ মূল্য চার্ট",
        "buscando_marketcap": "🔍 বাজার মূলধন সংগ্রহ করা হচ্ছে...",
        "marketcap_nao_disponivel": "উপলব্ধ নয়",
        "idioma_label": "🌐 ভাষা / Language",
        "idioma_selecao": "ইন্টারফেস ভাষা নির্বাচন করুন:",
        "aviso_aquecimento": "⚠️ গণনায় ওয়ার্ম-আপ মোমবাতি ব্যবহার করা হয়েছে",
        "intervalos": {
            "১ মিনিট": "1m", "৫ মিনিট": "5m", "১৫ মিনিট": "15m", "৩০ মিনিট": "30m",
            "১ ঘন্টা": "1h", "৪ ঘন্টা": "4h", "১ দিন": "1d", "১ সপ্তাহ": "1w"
        }
    },
    "العربية": {
        "titulo": "🏦 BRICSVAULT PORTAL - محرك مفاهيم الأموال الذكية (SMC)",
        "config_globais": "⚙️ الإعدادات العامة",
        "selecione_cripto": "اختر أي عملة مشفرة (/USDT):",
        "tempo_grafico": "الإطار الزمني:",
        "modo_vivo": "تفعيل المراقبة في الوقت الفعلي",
        "intervalo_refresh": "فترة التحديث (ثواني):",
        "preco_spot": "سعر الفوري الحقيقي",
        "variacao_24h": "تغير 24 ساعة",
        "volume_24h": "حجم التداول 24 ساعة (USDT)",
        "market_cap": "القيمة السوقية (USDT)",
        "stop_atr": "سعر وقف ATR",
        "compra_forte": "🟢 شراء قوي (SMC + فيبوناتشي متوافقة)",
        "venda_forte": "🔴 بيع قوي (SMC + فيبوناتشي متوافقة)",
        "neutro": "🟡 محايد (انتظار SMC)",
        "erro_dados": "بيانات تاريخية غير كافية. اختر أصلًا آخر أو قلل الإطار الزمني.",
        "ctx_desconto": "الأصل في منطقة خصم فيبوناتشي (مخاطرة/عائد ممتاز للمؤسسات).",
        "ctx_premium": "الأصل في منطقة فيبوناتشي الممتازة (السعر ممتد، مناسب لجني الأرباح).",
        "ctx_neutro": "السعر في منطقة فيبوناتشي المحايدة (منطقة القيمة العادلة).",
        "ultima_atualizacao": "آخر تحديث",
        "proximo_refresh": "التحديث التالي في",
        "segundos": "ثواني",
        "pontos_compra": "نقاط الشراء",
        "pontos_venda": "نقاط البيع",
        "grafico_titulo": "📈 مخطط الأسعار التفاعلي",
        "buscando_marketcap": "🔍 جاري الحصول على القيمة السوقية...",
        "marketcap_nao_disponivel": "غير متاح",
        "idioma_label": "🌐 اللغة / Language",
        "idioma_selecao": "اختر لغة الواجهة:",
        "aviso_aquecimento": "⚠️ تم استخدام شموع الإحماء في الحساب",
        "intervalos": {
            "دقيقة واحدة": "1m", "5 دقائق": "5m", "15 دقيقة": "15m", "30 دقيقة": "30m",
            "ساعة واحدة": "1h", "4 ساعات": "4h", "يوم واحد": "1d", "أسبوع واحد": "1w"
        }
    },
    "한국어": {
        "titulo": "🏦 BRICSVAULT PORTAL - 스마트 머니 컨셉(SMC) 엔진",
        "config_globais": "⚙️ 글로벌 설정",
        "selecione_cripto": "암호화폐 선택 (/USDT):",
        "tempo_grafico": "시간 프레임:",
        "modo_vivo": "실시간 모니터링 활성화",
        "intervalo_refresh": "새로 고침 간격(초):",
        "preco_spot": "실제 현물 가격",
        "variacao_24h": "24시간 변동",
        "volume_24h": "24시간 거래량 (USDT)",
        "market_cap": "시가총액 (USDT)",
        "stop_atr": "ATR 스탑 가격",
        "compra_forte": "🟢 강한 매수 (SMC + 피보나치 정렬)",
        "venda_forte": "🔴 강한 매도 (SMC + 피보나치 정렬)",
        "neutro": "🟡 중립 (SMC 대기)",
        "erro_dados": "과거 데이터가 부족합니다. 다른 자산을 선택하거나 시간 프레임을 줄이세요.",
        "ctx_desconto": "자산이 피보나치 할인 영역에 있습니다 (기관용 우수한 위험/수익률).",
        "ctx_premium": "자산이 피보나치 프리미엄 영역에 있습니다 (가격이 늘어나 있어 이익 실현에 적합).",
        "ctx_neutro": "피보나치 중립 영역의 가격 (공정 가치 영역).",
        "ultima_atualizacao": "마지막 업데이트",
        "proximo_refresh": "다음 새로 고침까지",
        "segundos": "초",
        "pontos_compra": "매수 포인트",
        "pontos_venda": "매도 포인트",
        "grafico_titulo": "📈 대화형 가격 차트",
        "buscando_marketcap": "🔍 시가총액 가져오는 중...",
        "marketcap_nao_disponivel": "사용 불가",
        "idioma_label": "🌐 언어 / Language",
        "idioma_selecao": "인터페이스 언어 선택:",
        "aviso_aquecimento": "⚠️ 계산에 워밍업 캔들 사용됨",
        "intervalos": {
            "1분": "1m", "5분": "5m", "15분": "15m", "30분": "30m",
            "1시간": "1h", "4시간": "4h", "1일": "1d", "1주": "1w"
        }
    },
    "Tiếng Việt": {
        "titulo": "🏦 BRICSVAULT PORTAL - Động cơ Khái niệm Tiền thông minh (SMC)",
        "config_globais": "⚙️ Cài đặt toàn cầu",
        "selecione_cripto": "Chọn bất kỳ tiền mã hóa nào (/USDT):",
        "tempo_grafico": "Khung thời gian:",
        "modo_vivo": "Bật giám sát thời gian thực",
        "intervalo_refresh": "Khoảng thời gian làm mới (giây):",
        "preco_spot": "Giá spot thực tế",
        "variacao_24h": "Biến động 24h",
        "volume_24h": "Khối lượng 24h (USDT)",
        "market_cap": "Vốn hóa thị trường (USDT)",
        "stop_atr": "Giá dừng ATR",
        "compra_forte": "🟢 MUA MẠNH (SMC + FIBONACCI CĂN CHỈNH)",
        "venda_forte": "🔴 BÁN MẠNH (SMC + FIBONACCI CĂN CHỈNH)",
        "neutro": "🟡 TRUNG LẬP (CHỜ SMC)",
        "erro_dados": "Dữ liệu lịch sử không đủ. Chọn tài sản khác hoặc giảm khung thời gian.",
        "ctx_desconto": "Tài sản nằm trong vùng chiết khấu Fibonacci (Tỷ lệ rủi ro/lợi nhuận tuyệt vời cho tổ chức).",
        "ctx_premium": "Tài sản nằm trong vùng cao cấp Fibonacci (Giá kéo dài, phù hợp để chốt lời).",
        "ctx_neutro": "Giá nằm trong vùng trung tính Fibonacci (Vùng giá trị hợp lý).",
        "ultima_atualizacao": "Cập nhật cuối cùng",
        "proximo_refresh": "Làm mới tiếp theo trong",
        "segundos": "giây",
        "pontos_compra": "Điểm mua",
        "pontos_venda": "Điểm bán",
        "grafico_titulo": "📈 Biểu đồ giá tương tác",
        "buscando_marketcap": "🔍 Đang tìm vốn hóa thị trường...",
        "marketcap_nao_disponivel": "Không có sẵn",
        "idioma_label": "🌐 Ngôn ngữ / Language",
        "idioma_selecao": "Chọn ngôn ngữ giao diện:",
        "aviso_aquecimento": "⚠️ Nến làm nóng được sử dụng trong tính toán",
        "intervalos": {
            "1 Phút": "1m", "5 Phút": "5m", "15 Phút": "15m", "30 Phút": "30m",
            "1 Giờ": "1h", "4 Giờ": "4h", "1 Ngày": "1d", "1 Tuần": "1w"
        }
    },
    "Türkçe": {
        "titulo": "🏦 BRICSVAULT PORTAL - Akıllı Para Kavramları (SMC) Motoru",
        "config_globais": "⚙️ Genel Ayarlar",
        "selecione_cripto": "Herhangi bir Kripto Para Birimi Seçin (/USDT):",
        "tempo_grafico": "Zaman Dilimi:",
        "modo_vivo": "Gerçek Zamanlı İzlemeyi Etkinleştir",
        "intervalo_refresh": "Yenileme Aralığı (Saniye):",
        "preco_spot": "Gerçek Spot Fiyat",
        "variacao_24h": "24 Saatlik Değişim",
        "volume_24h": "24 Saatlik Hacim (USDT)",
        "market_cap": "Piyasa Değeri (USDT)",
        "stop_atr": "ATR Durdurma Fiyatı",
        "compra_forte": "🟢 GÜÇLÜ ALIM (SMC + FIBONACCI UYUMLU)",
        "venda_forte": "🔴 GÜÇLÜ SATIM (SMC + FIBONACCI UYUMLU)",
        "neutro": "🟡 NÖTR (SMC BEKLE)",
        "erro_dados": "Yetersiz geçmiş veri. Başka bir varlık seçin veya Zaman Dilimini azaltın.",
        "ctx_desconto": "Varlık Fibonacci İskonto Bölgesinde (Kurumlar için mükemmel risk/getiri).",
        "ctx_premium": "Varlık Fibonacci Prim Bölgesinde (Fiyat gerilmiş, kar alma için uygun).",
        "ctx_neutro": "Fiyat Fibonacci nötr bölgesinde (Fair Value Zone).",
        "ultima_atualizacao": "Son Güncelleme",
        "proximo_refresh": "Sonraki yenileme",
        "segundos": "saniye",
        "pontos_compra": "Alım Noktaları",
        "pontos_venda": "Satım Noktaları",
        "grafico_titulo": "📈 Etkileşimli Fiyat Grafiği",
        "buscando_marketcap": "🔍 Piyasa Değeri alınıyor...",
        "marketcap_nao_disponivel": "Mevcut değil",
        "idioma_label": "🌐 Dil / Language",
        "idioma_selecao": "Arayüz dilini seçin:",
        "aviso_aquecimento": "⚠️ Hesaplamada ısınma mumları kullanıldı",
        "intervalos": {
            "1 Dakika": "1m", "5 Dakika": "5m", "15 Dakika": "15m", "30 Dakika": "30m",
            "1 Saat": "1h", "4 Saat": "4h", "1 Gün": "1d", "1 Hafta": "1w"
        }
    }
}

def construir_dicionario_com_fallback(traducoes: Dict, idioma_padrao: str = IDIOMA_PADRAO) -> Dict:
    """Preenche com os textos base para idiomas que não tenham todas as chaves."""
    base = traducoes[idioma_padrao]
    dicionario_final = {}
    for idioma, valores in traducoes.items():
        completo = dict(base)
        completo.update(valores)
        dicionario_final[idioma] = completo
    return dicionario_final

DICIONARIO_LINGUAS = construir_dicionario_com_fallback(_TRADUCOES)

# -----------------------------------------------------------------------------
# FUNÇÕES DE FORMATAÇÃO
# -----------------------------------------------------------------------------
def formatar_preco(valor: Optional[float], prefixo: str = "$ ") -> str:
    """Formata um valor numérico como preço com notação compacta."""
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return f"{prefixo}---"
    if valor == 0:
        return f"{prefixo}0.00"
    if valor < 0:
        return f"-{formatar_preco(abs(valor), prefixo)}"
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

def formatar_usdt_compacto(valor: Optional[float], sufixo: str = " USDT") -> str:
    """Formata um valor em USDT com abreviações K/M/B/T."""
    if valor is None or (isinstance(valor, float) and math.isnan(valor)) or valor <= 0:
        return "---"
    if valor >= 1_000_000_000_000:
        return f"{valor / 1_000_000_000_000:.2f}T{sufixo}"
    if valor >= 1_000_000_000:
        return f"{valor / 1_000_000_000:.2f}B{sufixo}"
    if valor >= 1_000_000:
        return f"{valor / 1_000_000:.2f}M{sufixo}"
    if valor >= 1_000:
        return f"{valor / 1_000:.2f}K{sufixo}"
    return f"{valor:,.2f}{sufixo}"

# -----------------------------------------------------------------------------
# MEMÓRIA DE SESSÃO (para valores que podem falhar)
# -----------------------------------------------------------------------------
def valor_com_memoria(chave: str, valor: Optional[float]) -> Tuple[Optional[float], bool]:
    """Retorna o valor ou o último válido armazenado na sessão."""
    memoria = st.session_state.setdefault("_memoria_metricas", {})
    if valor is not None and not (isinstance(valor, float) and math.isnan(valor)) and valor > 0:
        memoria[chave] = float(valor)
        return float(valor), False
    if chave in memoria:
        return memoria[chave], True
    return None, False

# -----------------------------------------------------------------------------
# GERENCIADOR DE EXCHANGES (com cache)
# -----------------------------------------------------------------------------
PRIORITY_EXCHANGES = ["Gate.io", "Kraken", "MEXC", "KuCoin"]
SIGLAS_EXCHANGES = {"Gate.io": "GATE", "Kraken": "KRK", "MEXC": "MEXC", "KuCoin": "KUC"}
VERSAO_MANAGER = 2

class ExchangeManager:
    EXCHANGES = {
        "Gate.io": {
            "class": ccxt.gate,
            "config": {"enableRateLimit": True, "timeout": EXCHANGE_TIMEOUT_MS,
                       "options": {"defaultType": "spot"}},
        },
        "Kraken": {
            "class": ccxt.kraken,
            "config": {"enableRateLimit": True, "timeout": EXCHANGE_TIMEOUT_MS},
        },
        "MEXC": {
            "class": ccxt.mexc,
            "config": {"enableRateLimit": True, "timeout": EXCHANGE_TIMEOUT_MS},
        },
        "KuCoin": {
            "class": ccxt.kucoin,
            "config": {"enableRateLimit": True, "timeout": EXCHANGE_TIMEOUT_MS},
        }
    }

    def __init__(self):
        self.clients = {}
        self._init_clients()

    def _init_clients(self) -> None:
        for name, config in self.EXCHANGES.items():
            try:
                self.clients[name] = config["class"](config["config"])
            except Exception:
                pass

    def get_client(self, exchange_name: str):
        return self.clients.get(exchange_name)

@st.cache_resource
def _construir_exchange_manager(versao: int) -> ExchangeManager:
    return ExchangeManager()

def obter_exchange_manager() -> ExchangeManager:
    return _construir_exchange_manager(VERSAO_MANAGER)

# -----------------------------------------------------------------------------
# FUNÇÕES DE MERCADO (dados, ticker, book, etc.)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=TTL_MERCADOS_SEGUNDOS, show_spinner=False)
def obter_todos_pares_usdt() -> List[str]:
    """Obtém a lista de todos os pares /USDT disponíveis na Gate.io."""
    manager = obter_exchange_manager()
    client = manager.get_client("Gate.io")
    padrao = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]
    if not client:
        return padrao
    try:
        markets = client.load_markets()
        pairs = [s for s in markets.keys() if s.endswith('/USDT')]
        return sorted(pairs) if pairs else padrao
    except Exception:
        return padrao

def _obter_dados_24h_rest_direto(exchange_name: str, simbolo: str) -> Optional[Dict]:
    """Fallback: obtém dados de 24h via API REST direta."""
    try:
        if exchange_name == "Gate.io":
            pair = simbolo.replace("/", "_")
            url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={pair}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    d = data[0]
                    return {
                        "last": float(d.get("last", 0)),
                        "change": float(d.get("change_percentage", 0)),
                        "quote_volume": float(d.get("quote_volume", 0)),
                        "base_volume": float(d.get("base_volume", 0)),
                        "high": float(d.get("high_24h", 0)),
                        "low": float(d.get("low_24h", 0))
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
                    "quote_volume": float(d.get("quoteVolume", 0)),
                    "base_volume": float(d.get("volume", 0)),
                    "high": float(d.get("highPrice", 0)),
                    "low": float(d.get("lowPrice", 0))
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
                        "quote_volume": float(d.get("volValue", 0)),
                        "base_volume": float(d.get("vol", 0)),
                        "high": float(d.get("high", 0)),
                        "low": float(d.get("low", 0))
                    }
        elif exchange_name == "Kraken":
            pair = simbolo.replace("/", "")
            url = f"https://api.kraken.com/0/public/Ticker?pair={pair}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("result", {})
                if data:
                    d = list(data.values())[0]
                    last = float(d["c"][0])
                    open_ = float(d["o"])
                    change = ((last - open_) / open_ * 100) if open_ else 0.0
                    base_vol = float(d["v"][1])
                    return {
                        "last": last,
                        "change": change,
                        "quote_volume": base_vol * last,
                        "base_volume": base_vol,
                        "high": float(d["h"][1]),
                        "low": float(d["l"][1])
                    }
    except Exception:
        pass
    return None

@st.cache_data(ttl=TTL_DADOS_LIVE_SEGUNDOS, show_spinner=False)
def obter_dados_24h(simbolo: str) -> Optional[Dict]:
    """Obtém dados de 24h (ticker) usando exchanges prioritárias."""
    manager = obter_exchange_manager()
    for exchange_name in PRIORITY_EXCHANGES:
        try:
            client = manager.get_client(exchange_name)
            if not client:
                continue
            ticker = client.fetch_ticker(simbolo)
            if ticker and ticker.get("last") is not None:
                return {
                    "last": ticker.get("last"),
                    "change": ticker.get("percentage"),
                    "quote_volume": ticker.get("quoteVolume"),
                    "base_volume": ticker.get("baseVolume"),
                    "high": ticker.get("high"),
                    "low": ticker.get("low"),
                    "fonte": exchange_name
                }
        except Exception:
            continue
    # Fallback REST
    for exchange_name in PRIORITY_EXCHANGES:
        resultado = _obter_dados_24h_rest_direto(exchange_name, simbolo)
        if resultado and resultado.get("last"):
            resultado["fonte"] = exchange_name
            return resultado
    return None

def resolver_volume_usdt(dados_24h: Optional[Dict], preco_atual: float,
                         dados_gecko: Optional[Dict]) -> Optional[float]:
    """Resolve o volume em USDT a partir de diferentes fontes."""
    if dados_24h:
        qv = dados_24h.get("quote_volume")
        if qv and qv > 0:
            return float(qv)
        bv = dados_24h.get("base_volume")
        if bv and bv > 0 and preco_atual and preco_atual > 0:
            return float(bv) * float(preco_atual)
    if dados_gecko and dados_gecko.get("total_volume"):
        return float(dados_gecko["total_volume"])
    return None

# -----------------------------------------------------------------------------
# MARKET CAP (CoinGecko e CoinPaprika)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def obter_id_coingecko(simbolo: str) -> Optional[str]:
    try:
        resp = requests.get(
            "https://api.coingecko.com/api/v3/search",
            params={"query": simbolo},
            headers={"Accept": "application/json"},
            timeout=10
        )
        if resp.status_code != 200:
            return None
        coins = resp.json().get("coins", [])
        alvo = simbolo.upper()
        for coin in coins:
            if coin.get("symbol", "").upper() == alvo:
                return coin.get("id")
        return coins[0].get("id") if coins else None
    except Exception:
        return None

@st.cache_data(ttl=600, show_spinner=False)
def obter_dados_coingecko(simbolo: str) -> Optional[Dict]:
    coin_id = obter_id_coingecko(simbolo)
    if not coin_id:
        return None
    try:
        resp = requests.get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={
                "vs_currency": "usd",
                "ids": coin_id,
                "order": "market_cap_desc",
                "per_page": 1,
                "page": 1,
                "sparkline": "false"
            },
            headers={"Accept": "application/json"},
            timeout=10
        )
        if resp.status_code != 200:
            return None
        dados = resp.json()
        if not dados:
            return None
        d = dados[0]
        return {
            "market_cap": float(d["market_cap"]) if d.get("market_cap") else None,
            "total_volume": float(d["total_volume"]) if d.get("total_volume") else None,
            "circulating_supply": float(d["circulating_supply"]) if d.get("circulating_supply") else None,
            "current_price": float(d["current_price"]) if d.get("current_price") else None,
        }
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def obter_id_coinpaprika(simbolo: str) -> Optional[str]:
    try:
        resp = requests.get("https://api.coinpaprika.com/v1/coins", timeout=12)
        if resp.status_code != 200:
            return None
        alvo = simbolo.upper()
        candidatos = [
            c for c in resp.json()
            if c.get("symbol", "").upper() == alvo and c.get("is_active")
        ]
        if not candidatos:
            return None
        candidatos.sort(key=lambda c: c.get("rank") or 10**9)
        return candidatos[0].get("id")
    except Exception:
        return None

@st.cache_data(ttl=600, show_spinner=False)
def obter_dados_coinpaprika(simbolo: str) -> Optional[Dict]:
    coin_id = obter_id_coinpaprika(simbolo)
    if not coin_id:
        return None
    try:
        resp = requests.get(
            f"https://api.coinpaprika.com/v1/tickers/{coin_id}",
            timeout=12
        )
        if resp.status_code != 200:
            return None
        quotes = resp.json().get("quotes", {}).get("USD", {})
        mc = quotes.get("market_cap")
        vol = quotes.get("volume_24h")
        return {
            "market_cap": float(mc) if mc else None,
            "total_volume": float(vol) if vol else None,
            "circulating_supply": None,
            "current_price": None,
        }
    except Exception:
        return None

def resolver_market_cap(simbolo_base: str, preco_atual: float,
                        dados_gecko: Optional[Dict],
                        dados_paprika: Optional[Dict]) -> Optional[float]:
    if dados_gecko:
        mc = dados_gecko.get("market_cap")
        if mc and mc > 0:
            return mc
        supply = dados_gecko.get("circulating_supply")
        if supply and supply > 0 and preco_atual and preco_atual > 0:
            return float(supply) * float(preco_atual)
    if dados_paprika:
        mc = dados_paprika.get("market_cap")
        if mc and mc > 0:
            return mc
    return None

# -----------------------------------------------------------------------------
# LIVRO DE OFERTAS AGREGADO
# -----------------------------------------------------------------------------
@st.cache_data(ttl=TTL_BOOK_SEGUNDOS, show_spinner=False)
def obter_book_agregado(simbolo: str, faixa: float = FAIXA_BOOK) -> Optional[Dict]:
    """Agrega livros de ofertas de várias exchanges dentro de uma faixa em torno do mid."""
    manager = obter_exchange_manager()
    livros = []
    for nome in PRIORITY_EXCHANGES:
        cliente = manager.get_client(nome)
        if cliente is None:
            continue
        try:
            ob = cliente.fetch_order_book(simbolo, limit=LIMITE_BOOK)
        except Exception:
            continue
        bids = [[float(b[0]), float(b[1])] for b in (ob.get("bids") or []) if b and len(b) >= 2 and b[0] and b[1]]
        asks = [[float(a[0]), float(a[1])] for a in (ob.get("asks") or []) if a and len(a) >= 2 and a[0] and a[1]]
        if not bids or not asks:
            continue
        livros.append((nome, bids, asks))
    if not livros:
        return None
    mids = [(b[0][0] + a[0][0]) / 2.0 for _, b, a in livros]
    mid = float(np.median(mids))
    if mid <= 0:
        return None
    piso, teto = mid * (1 - faixa), mid * (1 + faixa)
    passo = max(mid * PASSO_AGRUPAMENTO, 1e-12)
    baldes_bid, baldes_ask = {}, {}
    total_bid = 0.0
    total_ask = 0.0
    for nome, bids, asks in livros:
        sigla = SIGLAS_EXCHANGES.get(nome, nome[:4].upper())
        for nivel in bids:
            preco, qtd = float(nivel[0]), float(nivel[1])
            if preco < piso or preco > mid:
                continue
            notional = preco * qtd
            total_bid += notional
            chave = round(preco / passo) * passo
            b = baldes_bid.setdefault(chave, {"usdt": 0.0, "base": 0.0, "fontes": set()})
            b["usdt"] += notional
            b["base"] += qtd
            b["fontes"].add(sigla)
        for nivel in asks:
            preco, qtd = float(nivel[0]), float(nivel[1])
            if preco > teto or preco < mid:
                continue
            notional = preco * qtd
            total_ask += notional
            chave = round(preco / passo) * passo
            a = baldes_ask.setdefault(chave, {"usdt": 0.0, "base": 0.0, "fontes": set()})
            a["usdt"] += notional
            a["base"] += qtd
            a["fontes"].add(sigla)
    if total_bid <= 0 or total_ask <= 0:
        return None

    def _muralhas(baldes, n=4):
        itens = [
            {
                "preco": float(p),
                "usdt": float(v["usdt"]),
                "base": float(v["base"]),
                "fontes": sorted(v["fontes"])
            }
            for p, v in baldes.items()
        ]
        itens.sort(key=lambda x: x["usdt"], reverse=True)
        return itens[:n]

    desequilibrio = (total_bid - total_ask) / (total_bid + total_ask)
    return {
        "mid": mid,
        "total_bid": total_bid,
        "total_ask": total_ask,
        "desequilibrio": desequilibrio,
        "pct_bid": total_bid / (total_bid + total_ask) * 100,
        "pct_ask": total_ask / (total_bid + total_ask) * 100,
        "muralhas_compra": _muralhas(baldes_bid),
        "muralhas_venda": _muralhas(baldes_ask),
        "fontes": [SIGLAS_EXCHANGES.get(n, n) for n, _, _ in livros],
    }

def detectar_muralha_bloqueante(book: Optional[Dict], direcao: str, preco: float,
                                limite_pct: float = 0.006, fator: float = 2.5) -> bool:
    """Verifica se há uma muralha de liquidez contrária muito grande bloqueando o movimento."""
    if not book:
        return False
    if direcao == "long":
        contrarias = book["muralhas_venda"]
        favoraveis = book["muralhas_compra"]
        proximas = [m for m in contrarias if 0 < (m["preco"] - preco) / preco <= limite_pct]
    else:
        contrarias = book["muralhas_compra"]
        favoraveis = book["muralhas_venda"]
        proximas = [m for m in contrarias if 0 < (preco - m["preco"]) / preco <= limite_pct]
    if not proximas or not favoraveis:
        return False
    maior_contraria = max(m["usdt"] for m in proximas)
    maior_favoravel = max(m["usdt"] for m in favoraveis)
    return maior_favoravel > 0 and maior_contraria >= fator * maior_favoravel

# -----------------------------------------------------------------------------
# WYCKOFF DETECTION
# -----------------------------------------------------------------------------
_PONTOS_EVENTO = {
    "SPRING": 2.0,
    "SHAKEOUT": 1.5,
    "TSO": 1.0,
    "UT": 2.0,
    "UPTHRUST": 1.5,
    "UTAD": 1.0,
}
_BUFFER_STOP_EVENTO = {
    "SPRING": 0.005,
    "SHAKEOUT": 0.015,
    "TSO": 0.035,
    "UT": 0.005,
    "UPTHRUST": 0.015,
    "UTAD": 0.035,
}

def detectar_wyckoff(df: pd.DataFrame,
                     janela_base: int = JANELA_BASE_WYCKOFF,
                     janela_evento: int = JANELA_EVENTO_WYCKOFF) -> Optional[Dict]:
    """
    Detecta eventos Wyckoff (spring, shakeout, upthrust, etc.) em uma janela recente.
    Retorna dicionário com estrutura, evento, fase e pontuação.
    """
    if len(df) < janela_base + janela_evento + 5:
        return None
    base = df.iloc[-(janela_base + janela_evento):-janela_evento]
    recentes = df.iloc[-janela_evento:].reset_index(drop=True)
    suporte = float(base['low'].min())
    resistencia = float(base['high'].max())
    if suporte <= 0 or resistencia <= suporte:
        return None
    altura = resistencia - suporte
    meio = (resistencia + suporte) / 2.0
    vol_base = float(base['volume'].mean())
    if vol_base <= 0:
        vol_base = 1e-9
    if altura / meio > 0.40:
        return {
            "range_valido": False, "suporte": suporte, "resistencia": resistencia,
            "meio": meio, "evento": None, "pontos": 0.0, "direcao": 0
        }
    evento = None
    for i in range(len(recentes)):
        v = recentes.iloc[i]
        vol_rel = float(v['volume']) / vol_base
        if float(v['low']) < suporte and float(v['close']) > suporte:
            pen = (suporte - float(v['low'])) / suporte
            if pen >= 0.03 or vol_rel >= 2.0:
                tipo = "TSO"
            elif pen >= 0.01:
                tipo = "SHAKEOUT"
            else:
                tipo = "SPRING"
            evento = {
                "tipo": tipo, "direcao": 1, "idx": i,
                "extremo": float(v['low']), "penetracao": pen,
                "vol_rel": vol_rel
            }
        if float(v['high']) > resistencia and float(v['close']) < resistencia:
            pen = (float(v['high']) - resistencia) / resistencia
            if pen >= 0.03 or vol_rel >= 2.0:
                tipo = "UTAD"
            elif pen >= 0.01:
                tipo = "UPTHRUST"
            else:
                tipo = "UT"
            evento = {
                "tipo": tipo, "direcao": -1, "idx": i,
                "extremo": float(v['high']), "penetracao": pen,
                "vol_rel": vol_rel
            }
        if evento is not None:
            break

    if evento is None:
        return {
            "range_valido": True, "suporte": suporte, "resistencia": resistencia,
            "meio": meio, "evento": None, "pontos": 0.0, "direcao": 0
        }

    vol_evento = float(recentes.iloc[evento["idx"]]['volume'])
    depois = recentes.iloc[evento["idx"] + 1:]
    teste_ok = False
    sos = False
    lps = False
    for j in range(len(depois)):
        c = depois.iloc[j]
        vol = float(c['volume'])
        if evento["direcao"] == 1:
            if float(c['low']) > evento["extremo"] and vol < 0.6 * vol_evento and float(c['close']) > suporte:
                teste_ok = True
            if float(c['close']) > meio and vol > 1.2 * vol_base:
                sos = True
            if sos and float(c['close']) > suporte and vol < 0.8 * vol_base and float(c['close']) < float(c['open']):
                lps = True
        else:
            if float(c['high']) < evento["extremo"] and vol < 0.6 * vol_evento and float(c['close']) < resistencia:
                teste_ok = True
            if float(c['close']) < meio and vol > 1.2 * vol_base:
                sos = True
            if sos and float(c['close']) < resistencia and vol < 0.8 * vol_base and float(c['close']) > float(c['open']):
                lps = True

    pontos = _PONTOS_EVENTO.get(evento["tipo"], 1.0)
    if teste_ok:
        pontos += 1.0
    if sos:
        pontos += 1.0
    if lps:
        pontos = PONTOS_MAX_WYCKOFF
    pontos = min(pontos, PONTOS_MAX_WYCKOFF)

    buffer_stop = _BUFFER_STOP_EVENTO.get(evento["tipo"], 0.02)
    if evento["direcao"] == 1:
        stop_estrutural = evento["extremo"] * (1 - buffer_stop)
    else:
        stop_estrutural = evento["extremo"] * (1 + buffer_stop)

    if lps:
        fase = "D (LPS/LPSY)"
    elif sos:
        fase = "D (SOS/SOW)"
    else:
        fase = "C"

    return {
        "range_valido": True,
        "suporte": suporte,
        "resistencia": resistencia,
        "meio": meio,
        "altura": altura,
        "evento": evento,
        "teste_ok": teste_ok,
        "sos": sos,
        "lps": lps,
        "fase": fase,
        "pontos": float(pontos),
        "direcao": evento["direcao"],
        "stop_estrutural": float(stop_estrutural),
    }

# -----------------------------------------------------------------------------
# INDICADORES TÉCNICOS
# -----------------------------------------------------------------------------
def calcular_rsi(serie: pd.Series, periodo: int = 14) -> pd.Series:
    delta = serie.diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    ma_ganho = ganho.ewm(span=periodo, adjust=False).mean()
    ma_perda = perda.ewm(span=periodo, adjust=False).mean()
    return 100 - (100 / (1 + (ma_ganho / ma_perda.replace(0, 1e-10))))

def calcular_rsi_estocastico(serie: pd.Series, periodo_rsi: int = 14,
                             periodo_stoch: int = 14, suavizacao: int = 3) -> Tuple[pd.Series, pd.Series]:
    rsi = calcular_rsi(serie, periodo_rsi)
    minimo = rsi.rolling(window=periodo_stoch).min()
    maximo = rsi.rolling(window=periodo_stoch).max()
    stoch = 100 * (rsi - minimo) / (maximo - minimo).replace(0, 1e-10)
    k = stoch.rolling(window=suavizacao).mean()
    d = k.rolling(window=suavizacao).mean()
    return k, d

def calcular_macd(serie: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema12 = serie.ewm(span=12, adjust=False).mean()
    ema26 = serie.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    sinal = macd.ewm(span=9, adjust=False).mean()
    return macd, sinal, macd - sinal

def calcular_mfi(df: pd.DataFrame, periodo: int = 14) -> pd.Series:
    tp = (df['high'] + df['low'] + df['close']) / 3
    rmf = tp * df['volume']
    tp_shift = tp.shift(1)
    pos_flow = rmf.where(tp > tp_shift, 0.0)
    neg_flow = rmf.where(tp < tp_shift, 0.0)
    pos_sum = pos_flow.rolling(window=periodo).sum()
    neg_sum = neg_flow.rolling(window=periodo).sum().replace(0, 1e-10)
    return 100 - (100 / (1 + pos_sum / neg_sum))

def calcular_ssl_hybrid(df: pd.DataFrame, periodo: int = 20) -> pd.DataFrame:
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

def calcular_atr_stop(df: pd.DataFrame, periodo: int = 14, multiplicador: float = 3.0) -> pd.DataFrame:
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
    df['ATR'] = atr
    df['ATR_Stop'] = atr_stop
    df['atr_dir'] = tendencia
    return df

def calcular_ppo(df: pd.DataFrame, col: str = 'close', rapido: int = 12,
                 lento: int = 26, sinal_periodo: int = 9) -> pd.DataFrame:
    ema_rapida = df[col].ewm(span=rapido, adjust=False).mean()
    ema_lenta = df[col].ewm(span=lento, adjust=False).mean()
    df = df.copy()
    df['PPO'] = ((ema_rapida - ema_lenta) / ema_lenta) * 100
    df['PPO_Signal'] = df['PPO'].ewm(span=sinal_periodo, adjust=False).mean()
    return df

def calcular_obv(df: pd.DataFrame) -> np.ndarray:
    """On-Balance Volume (OBV) - acumula volume positivo/negativo."""
    obv = np.zeros(len(df))
    obv[0] = df['volume'].iloc[0]
    for i in range(1, len(df)):
        if df['close'].iloc[i] > df['close'].iloc[i-1]:
            obv[i] = obv[i-1] + df['volume'].iloc[i]
        elif df['close'].iloc[i] < df['close'].iloc[i-1]:
            obv[i] = obv[i-1] - df['volume'].iloc[i]
        else:
            obv[i] = obv[i-1]
    return obv

def calcular_retracao_fibonacci(df_analise: pd.DataFrame) -> Dict[str, float]:
    maxima = df_analise['high'].max()
    minima = df_analise['low'].min()
    diff = maxima - minima
    return {
        'fib_0': maxima,
        'fib_236': maxima - 0.236 * diff,
        'fib_382': maxima - 0.382 * diff,
        'fib_500': maxima - 0.500 * diff,
        'fib_618': maxima - 0.618 * diff,
        'fib_786': maxima - 0.786 * diff,
        'fib_100': minima
    }

# -----------------------------------------------------------------------------
# CARREGAMENTO DE DADOS (com todos os indicadores e OBV)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=TTL_DADOS_LIVE_SEGUNDOS, show_spinner=False)
def carregar_dados(simbolo_id: str, timeframe_selecionado: str) -> Optional[pd.DataFrame]:
    """Carrega dados OHLCV e calcula todos os indicadores."""
    manager = obter_exchange_manager()
    for exchange_name in PRIORITY_EXCHANGES:
        try:
            client = manager.get_client(exchange_name)
            if not client:
                continue
            velas = client.fetch_ohlcv(
                simbolo_id,
                timeframe=timeframe_selecionado,
                limit=VELAS_TOTAL
            )
            if velas and len(velas) >= PERIODO_AQUECIMENTO + 50:
                df = pd.DataFrame(
                    velas,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
                # Indicadores
                df['RSI_14'] = calcular_rsi(df['close'], 14)
                k, d = calcular_rsi_estocastico(df['close'])
                df['STOCH_K'] = k
                df['STOCH_D'] = d
                macd, sinal, hist = calcular_macd(df['close'])
                df['MACD'] = macd
                df['MACD_SIGNAL'] = sinal
                df['MACD_HIST'] = hist
                df['MFI'] = calcular_mfi(df)
                df = calcular_ssl_hybrid(df)
                df = calcular_atr_stop(df)
                df = calcular_ppo(df)
                # Médias móveis
                df['SMA_8'] = df['close'].rolling(8).mean()
                df['SMA_21'] = df['close'].rolling(21).mean()
                df['SMA_50'] = df['close'].rolling(50).mean()
                df['SMA_200'] = df['close'].rolling(200).mean()
                df['VOL_MA_20'] = df['volume'].rolling(20).mean()
                # OBV
                df['OBV'] = calcular_obv(df)
                df['OBV_MA_20'] = df['OBV'].rolling(20).mean()

                df['SSL_Baseline'] = df['SSL_Baseline'].ffill()
                df['ATR_Stop'] = df['ATR_Stop'].replace(0, np.nan).ffill()
                return df.dropna(subset=['close']).reset_index(drop=True)
        except Exception:
            continue
    return None

# -----------------------------------------------------------------------------
# ANÁLISE DE CONFLUÊNCIA (com pesos e OBV)
# -----------------------------------------------------------------------------
PESOS = {
    "rsi": 2.0,
    "stoch": 1.5,
    "macd": 2.0,
    "mfi": 1.0,
    "ssl": 1.0,
    "atr": 1.0,
    "ppo": 1.5,
    "fib": 2.0,
    "book": 2.0,
    "wyckoff": PONTOS_MAX_WYCKOFF,
    "ma_curta": 1.5,
    "ma_longa": 2.0,
    "volume": 1.0,
    "obv": 1.0,
}
MAXIMO_POSSIVEL = sum(PESOS.values())

def analisar_confluencia(df_completo: pd.DataFrame, txt: Dict,
                         book: Optional[Dict], wyk: Optional[Dict]) -> Dict:
    """
    Calcula pontuação de alta/baixa com base em múltiplos indicadores e retorna
    recomendação, contexto e escore líquido.
    """
    df_analise = df_completo.iloc[PERIODO_AQUECIMENTO:].copy()
    if df_analise.empty:
        return {
            "recomendacao": txt["neutro"], "cor": "#ffcc00", "contexto": txt["ctx_neutro"],
            "alta": 0.0, "baixa": 0.0, "liquido": 0.0, "direcao": "neutro",
            "bloqueado": False
        }

    u = df_analise.iloc[-1]
    preco_atual = float(u['close'])

    fib = calcular_retracao_fibonacci(df_analise)

    alta = 0.0
    baixa = 0.0
    contexto = txt["ctx_neutro"]

    # RSI
    rsi_val = u['RSI_14']
    if not math.isnan(rsi_val):
        if rsi_val < 40:
            alta += PESOS["rsi"]
        elif rsi_val > 60:
            baixa += PESOS["rsi"]
        if rsi_val > 50:
            alta += 0.5
        elif rsi_val < 50:
            baixa += 0.5

    # Stoch RSI
    k, d = u['STOCH_K'], u['STOCH_D']
    if not (math.isnan(k) or math.isnan(d)):
        if k < 20 and k > d:
            alta += PESOS["stoch"]
        elif k > 80 and k < d:
            baixa += PESOS["stoch"]
        elif k > d:
            alta += PESOS["stoch"] / 2
        else:
            baixa += PESOS["stoch"] / 2

    # MACD
    macd_hist = u['MACD_HIST']
    if not math.isnan(macd_hist):
        if macd_hist > 0:
            alta += PESOS["macd"]
        else:
            baixa += PESOS["macd"]
    macd_line = u['MACD']
    macd_signal = u['MACD_SIGNAL']
    if not (math.isnan(macd_line) or math.isnan(macd_signal)):
        if macd_line > macd_signal:
            alta += 0.5
        else:
            baixa += 0.5

    # MFI
    mfi_val = u['MFI']
    if not math.isnan(mfi_val):
        if mfi_val > 50:
            alta += PESOS["mfi"]
        else:
            baixa += PESOS["mfi"]

    # SSL
    if u['ssl_dir'] == 1:
        alta += PESOS["ssl"]
    else:
        baixa += PESOS["ssl"]

    # ATR
    if u['atr_dir'] == 1:
        alta += PESOS["atr"]
    else:
        baixa += PESOS["atr"]

    # PPO
    ppo_val, ppo_sig = u['PPO'], u['PPO_Signal']
    if not (math.isnan(ppo_val) or math.isnan(ppo_sig)):
        if ppo_val > ppo_sig:
            alta += PESOS["ppo"]
        else:
            baixa += PESOS["ppo"]

    # Fibonacci
    if preco_atual >= fib['fib_382']:
        baixa += PESOS["fib"]
        contexto = txt["ctx_premium"]
    elif preco_atual <= fib['fib_618']:
        alta += PESOS["fib"]
        contexto = txt["ctx_desconto"]
    else:
        contexto = txt["ctx_neutro"]

    # Book
    if book:
        des = book["desequilibrio"]
        if des >= 0.10:
            alta += PESOS["book"]
        elif des >= 0.04:
            alta += PESOS["book"] / 2
        elif des <= -0.10:
            baixa += PESOS["book"]
        elif des <= -0.04:
            baixa += PESOS["book"] / 2

    # Wyckoff
    if wyk and wyk.get("evento"):
        if wyk["direcao"] == 1:
            alta += wyk["pontos"]
        elif wyk["direcao"] == -1:
            baixa += wyk["pontos"]

    # Médias móveis curtas
    sma8 = u['SMA_8']
    sma21 = u['SMA_21']
    if not (math.isnan(sma8) or math.isnan(sma21)):
        if preco_atual > sma8 and sma8 > sma21:
            alta += PESOS["ma_curta"]
        elif preco_atual < sma8 and sma8 < sma21:
            baixa += PESOS["ma_curta"]
        if len(df_analise) >= 2:
            ant = df_analise.iloc[-2]
            if not (math.isnan(ant['SMA_8']) or math.isnan(ant['SMA_21'])):
                if ant['SMA_8'] <= ant['SMA_21'] and sma8 > sma21:
                    alta += 0.5
                elif ant['SMA_8'] >= ant['SMA_21'] and sma8 < sma21:
                    baixa += 0.5

    # Médias móveis longas
    sma50 = u['SMA_50']
    sma200 = u['SMA_200']
    if not (math.isnan(sma50) or math.isnan(sma200)):
        if preco_atual > sma50 and sma50 > sma200:
            alta += PESOS["ma_longa"]
        elif preco_atual < sma50 and sma50 < sma200:
            baixa += PESOS["ma_longa"]
        if len(df_analise) >= 2:
            ant = df_analise.iloc[-2]
            if not (math.isnan(ant['SMA_50']) or math.isnan(ant['SMA_200'])):
                if ant['SMA_50'] <= ant['SMA_200'] and sma50 > sma200:
                    alta += 0.5
                elif ant['SMA_50'] >= ant['SMA_200'] and sma50 < sma200:
                    baixa += 0.5

    # Volume
    vol_atual = u['volume']
    vol_ma = u['VOL_MA_20']
    if not (math.isnan(vol_atual) or math.isnan(vol_ma)) and vol_ma > 0:
        if vol_atual >= 1.5 * vol_ma:
            if float(u['close']) > float(u['open']):
                alta += PESOS["volume"]
            elif float(u['close']) < float(u['open']):
                baixa += PESOS["volume"]
        elif vol_atual >= 1.2 * vol_ma:
            if float(u['close']) > float(u['open']):
                alta += 0.5
            elif float(u['close']) < float(u['open']):
                baixa += 0.5

    # OBV
    obv_atual = u['OBV']
    obv_ma = u['OBV_MA_20']
    if not (math.isnan(obv_atual) or math.isnan(obv_ma)) and obv_ma > 0:
        if obv_atual > obv_ma:
            alta += PESOS["obv"]
        else:
            baixa += PESOS["obv"]
        # Divergência simples nas últimas 10 velas
        if len(df_analise) >= 10:
            preco_ultimos = df_analise['close'].iloc[-10:]
            obv_ultimos = df_analise['OBV'].iloc[-10:]
            max_preco_idx = preco_ultimos.idxmax()
            min_preco_idx = preco_ultimos.idxmin()
            max_obv_idx = obv_ultimos.idxmax()
            min_obv_idx = obv_ultimos.idxmin()
            if preco_ultimos[min_preco_idx] < preco_ultimos.iloc[0] and obv_ultimos[min_obv_idx] > obv_ultimos.iloc[0]:
                alta += 0.5
            if preco_ultimos[max_preco_idx] > preco_ultimos.iloc[0] and obv_ultimos[max_obv_idx] < obv_ultimos.iloc[0]:
                baixa += 0.5

    liquido = (alta - baixa) / MAXIMO_POSSIVEL * 100.0

    if liquido >= LIMIAR_SINAL_LIQUIDO:
        direcao = "long"
        recomendacao, cor = txt["compra_forte"], "#00cc66"
    elif liquido <= -LIMIAR_SINAL_LIQUIDO:
        direcao = "short"
        recomendacao, cor = txt["venda_forte"], "#ff3333"
    else:
        direcao = "neutro"
        recomendacao, cor = txt["neutro"], "#ffcc00"

    bloqueado = False
    if direcao in ("long", "short") and detectar_muralha_bloqueante(book, direcao, preco_atual):
        bloqueado = True
        direcao = "neutro"
        recomendacao, cor = txt["neutro"], "#ffcc00"

    return {
        "recomendacao": recomendacao,
        "cor": cor,
        "contexto": contexto,
        "alta": alta,
        "baixa": baixa,
        "liquido": liquido,
        "direcao": direcao,
        "bloqueado": bloqueado,
    }

# -----------------------------------------------------------------------------
# PLANO DE TRADE (stop, alvos)
# -----------------------------------------------------------------------------
def escolher_stop(direcao: str, entrada: float, atr: float,
                  atr_stop_val: float, wyk: Optional[Dict],
                  book: Optional[Dict]) -> Tuple[float, str]:
    """Escolhe o stop loss com base em Wyckoff, book ou ATR."""
    base = "ATR"
    candidatos = []
    if wyk and wyk.get("evento") and wyk.get("stop_estrutural"):
        if (direcao == "long" and wyk["direcao"] == 1) or (direcao == "short" and wyk["direcao"] == -1):
            candidatos.append((wyk["stop_estrutural"], f"Wyckoff {wyk['evento']['tipo']}"))
    if book:
        if direcao == "long":
            abaixo = [m["preco"] for m in book["muralhas_compra"] if m["preco"] < entrada]
            if abaixo:
                candidatos.append((max(abaixo) * 0.997, "Muralha de liquidez"))
        else:
            acima = [m["preco"] for m in book["muralhas_venda"] if m["preco"] > entrada]
            if acima:
                candidatos.append((min(acima) * 1.003, "Muralha de liquidez"))
    if atr_stop_val and not math.isnan(atr_stop_val):
        if (direcao == "long" and atr_stop_val < entrada) or (direcao == "short" and atr_stop_val > entrada):
            candidatos.append((float(atr_stop_val), "ATR Trailing Stop"))

    distancia_minima = 0.8 * atr if atr and atr > 0 else entrada * 0.01
    if direcao == "long":
        validos = [(p, b) for p, b in candidatos if entrada - p >= distancia_minima]
    else:
        validos = [(p, b) for p, b in candidatos if p - entrada >= distancia_minima]
    if validos:
        stop, base = validos[0]
    else:
        folga = max(distancia_minima, 2 * atr if atr else entrada * 0.02)
        stop = entrada - folga if direcao == "long" else entrada + folga
    return float(stop), base

def construir_alvos(direcao: str, entrada: float, atr: float,
                    wyk: Optional[Dict], book: Optional[Dict],
                    n: int = 8) -> List[float]:
    """Constrói lista de alvos de take profit com base em várias referências."""
    candidatos = set()
    atr = atr if (atr and atr > 0 and not math.isnan(atr)) else entrada * 0.01
    if direcao == "long":
        if wyk and wyk.get("range_valido") and wyk.get("altura"):
            res, altura = wyk["resistencia"], wyk["altura"]
            for k in (0.0, 0.382, 0.618, 1.0, 1.618, 2.618):
                candidatos.add(res + altura * k)
        if book:
            for m in book["muralhas_venda"]:
                candidatos.add(m["preco"])
        for k in (1, 1.5, 2, 3, 4, 5, 6.5, 8, 10, 13):
            candidatos.add(entrada + k * atr)
        for k in (0.03, 0.05, 0.08, 0.13, 0.21, 0.34, 0.55, 0.89):
            candidatos.add(entrada * (1 + k))
        niveis = sorted(x for x in candidatos if x > entrada * 1.004)
    else:
        if wyk and wyk.get("range_valido") and wyk.get("altura"):
            sup, altura = wyk["suporte"], wyk["altura"]
            for k in (0.0, 0.382, 0.618, 1.0, 1.618, 2.618):
                candidatos.add(max(sup - altura * k, entrada * 0.02))
        if book:
            for m in book["muralhas_compra"]:
                candidatos.add(m["preco"])
        for k in (1, 1.5, 2, 3, 4, 5, 6.5, 8, 10, 13):
            candidatos.add(entrada - k * atr)
        for k in (0.03, 0.05, 0.08, 0.13, 0.21, 0.34, 0.55):
            candidatos.add(entrada * (1 - k))
        niveis = sorted((x for x in candidatos if 0 < x < entrada * 0.996), reverse=True)

    finais = []
    for x in niveis:
        if not finais or abs(x / finais[-1] - 1) > 0.006:
            finais.append(float(x))
            if len(finais) == n:
                break
    return finais

def lucro_percentual(direcao: str, entrada: float, alvo: float) -> float:
    if entrada <= 0:
        return 0.0
    if direcao == "long":
        return (alvo / entrada - 1) * 100
    return (entrada / alvo - 1) * 100

# -----------------------------------------------------------------------------
# RENDERIZAÇÃO (UI)
# -----------------------------------------------------------------------------
def renderizar_card_plano(txt: Dict, simbolo_id: str, direcao: str,
                          entrada: float, stop: float, alvos: List[float],
                          base_stop: str, preco_atual: float) -> None:
    """Exibe o plano de trade em um card estilizado."""
    lado = "LONG" if direcao == "long" else "SHORT"
    cor = "#22c55e" if direcao == "long" else "#f43f5e"
    ticker = simbolo_id.replace("/", "")
    risco = abs(entrada - stop)
    rr = (abs(alvos[0] - entrada) / risco) if (alvos and risco > 0) else 0.0
    linhas = []
    for i, alvo in enumerate(alvos, start=1):
        atingido = (direcao == "long" and preco_atual >= alvo) or (direcao == "short" and preco_atual <= alvo)
        marca = " ✓" if atingido else ""
        estilo_borda = f"1px solid {cor}55" if atingido else "1px solid #ffffff14"
        fundo = f"{cor}14" if atingido else "#ffffff05"
        cor_txt = cor if atingido else "#94a3b8"
        linhas.append(
            f'<div style="background:{fundo};border:{estilo_borda};border-radius:12px;'
            f'padding:12px 16px;display:flex;justify-content:space-between;'
            f'font-family:ui-monospace,SFMono-Regular,Menlo,monospace;">'
            f'<span style="color:#64748b;">{txt["alvo"]} {i}</span>'
            f'<span style="color:{cor_txt};font-weight:600;">'
            f'{formatar_preco(alvo, "")}{marca} '
            f'<span style="color:#475569;font-size:0.85em;">'
            f'({lucro_percentual(direcao, entrada, alvo):+.2f}%)</span></span></div>'
        )
    grade = (
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px;">'
        + "".join(linhas) + "</div>"
    )
    st.markdown(
        f"""
        <div style="background:#0b0f19;border:1px solid #1e293b;border-radius:18px;padding:22px;">
            <div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;">
                <div style="border:1px solid {cor};color:{cor};border-radius:12px;padding:10px 18px;
                    font-family:ui-monospace,monospace;font-weight:700;letter-spacing:1px;">{lado}</div>
                <div style="font-size:1.5em;font-weight:700;color:#e2e8f0;
                    font-family:ui-monospace,monospace;letter-spacing:1px;">{ticker}</div>
            </div>
            <div style="background:#ffffff06;border:1px solid #ffffff10;border-radius:14px;padding:16px;
                font-family:ui-monospace,monospace;">
                <div style="display:flex;justify-content:space-between;color:#94a3b8;">
                    <span>{txt["entrada"]}</span><span style="color:#e2e8f0;">{formatar_preco(entrada)}</span></div>
                <div style="display:flex;justify-content:space-between;color:#94a3b8;margin-top:6px;">
                    <span>{txt["risco_retorno"]}</span><span style="color:{cor};">{rr:.2f} : 1</span></div>
                <div style="display:flex;justify-content:space-between;color:#94a3b8;margin-top:6px;">
                    <span>{txt["base_stop"]}</span><span style="color:#e2e8f0;">{base_stop}</span></div>
            </div>
            {grade}
            <div style="margin-top:14px;background:#f43f5e12;border:1px solid #f43f5e40;border-radius:14px;
                padding:14px 18px;display:flex;justify-content:space-between;
                font-family:ui-monospace,monospace;">
                <span style="color:#fb7185;letter-spacing:1px;">{txt["stop_loss"]}</span>
                <span style="color:#fb7185;font-weight:700;font-size:1.15em;">{formatar_preco(stop, "")}
                <span style="font-size:0.75em;color:#9f1239;">({lucro_percentual(direcao, entrada, stop):+.2f}%)</span></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def _chips(fontes: List[str]) -> str:
    return "".join(
        f'<span style="border:1px solid #ffffff18;border-radius:6px;padding:2px 6px;'
        f'margin-right:4px;font-size:0.7em;color:#94a3b8;'
        f'font-family:ui-monospace,monospace;">{f}</span>'
        for f in fontes
    )

def renderizar_book(txt: Dict, book: Optional[Dict]) -> None:
    if not book:
        st.info(txt["book_indisponivel"])
        return
    des_pct = abs(book["desequilibrio"]) * 100
    if book["desequilibrio"] > 0.06:
        veredicto, cor_v = txt["book_comprador"], "#22c55e"
    elif book["desequilibrio"] < -0.06:
        veredicto, cor_v = txt["book_vendedor"], "#f43f5e"
    else:
        veredicto, cor_v = txt["book_equilibrado"], "#94a3b8"
    st.markdown(
        f"""
        <div style="background:#0b0f19;border:1px solid #1e293b;border-radius:18px;padding:22px;margin-bottom:16px;">
            <div style="color:#64748b;letter-spacing:2px;font-size:0.75em;
                font-family:ui-monospace,monospace;">VEREDICTO · PRESSÃO DO BOOK</div>
            <div style="font-size:1.9em;font-weight:800;color:{cor_v};margin:6px 0 4px 0;">● {veredicto}</div>
            <div style="color:#64748b;font-family:ui-monospace,monospace;">
                {txt["desequilibrio"]}: {des_pct:.1f}%</div>
            <div style="display:flex;justify-content:space-between;margin-top:18px;
                font-family:ui-monospace,monospace;">
                <div><div style="color:#22c55e;font-size:0.75em;letter-spacing:1px;">{txt["compra"]}</div>
                <div style="color:#22c55e;font-size:1.3em;font-weight:700;">
                {formatar_usdt_compacto(book["total_bid"], "")}</div></div>
                <div style="text-align:right;">
                <div style="color:#f43f5e;font-size:0.75em;letter-spacing:1px;">{txt["venda"]}</div>
                <div style="color:#f43f5e;font-size:1.3em;font-weight:700;">
                {formatar_usdt_compacto(book["total_ask"], "")}</div></div>
            </div>
            <div style="height:8px;border-radius:6px;margin-top:12px;background:linear-gradient(90deg,
                #22c55e 0%, #22c55e {book["pct_bid"]:.1f}%, #f43f5e {book["pct_bid"]:.1f}%, #f43f5e 100%);"></div>
            <div style="display:flex;justify-content:space-between;margin-top:6px;font-size:0.75em;
                color:#64748b;font-family:ui-monospace,monospace;">
                <span>BID {book["pct_bid"]:.1f}%</span>
                <span>{txt["profundidade"]}</span>
                <span>ASK {book["pct_ask"]:.1f}%</span>
            </div>
            <div style="margin-top:12px;font-size:0.75em;color:#475569;">
                {txt["fontes_book"]}: {_chips(book["fontes"])}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    col_c, col_v = st.columns(2)
    def _bloco(coluna, titulo, muralhas, cor):
        with coluna:
            html = (f'<div style="color:{cor};letter-spacing:2px;font-size:0.75em;'
                    f'font-family:ui-monospace,monospace;margin-bottom:8px;">● {titulo}</div>')
            for i, m in enumerate(muralhas):
                tag = ('<span style="background:%s22;color:%s;border-radius:6px;padding:1px 7px;'
                       'font-size:0.65em;margin-left:8px;">MAIOR</span>' % (cor, cor)) if i == 0 else ""
                html += (
                    f'<div style="background:{cor}0d;border:1px solid {cor}33;border-radius:14px;'
                    f'padding:14px;margin-bottom:8px;font-family:ui-monospace,monospace;">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                    f'<span style="color:{cor};font-size:1.15em;font-weight:700;">'
                    f'{formatar_preco(m["preco"], "$ ")}{tag}</span>'
                    f'<span style="color:#e2e8f0;font-weight:600;">'
                    f'{formatar_usdt_compacto(m["usdt"], "")}</span></div>'
                    f'<div style="margin-top:8px;">{_chips(m["fontes"])}</div></div>'
                )
            st.markdown(html, unsafe_allow_html=True)
    _bloco(col_c, txt["zonas_compra"], book["muralhas_compra"], "#22c55e")
    _bloco(col_v, txt["zonas_venda"], book["muralhas_venda"], "#f43f5e")

def renderizar_wyckoff(txt: Dict, wyk: Optional[Dict]) -> None:
    if not wyk or not wyk.get("evento"):
        st.info(txt["wyckoff_sem_evento"])
        return
    ev = wyk["evento"]
    cor = "#22c55e" if wyk["direcao"] == 1 else "#f43f5e"
    st.markdown(
        f"""
        <div style="background:#0b0f19;border:1px solid #1e293b;border-radius:18px;padding:20px;
            font-family:ui-monospace,monospace;">
            <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;">
                <div><div style="color:#64748b;font-size:0.75em;letter-spacing:1px;">{txt["wyckoff_evento"]}</div>
                <div style="color:{cor};font-size:1.4em;font-weight:800;">{ev["tipo"]}</div></div>
                <div><div style="color:#64748b;font-size:0.75em;letter-spacing:1px;">{txt["wyckoff_fase"]}</div>
                <div style="color:#e2e8f0;font-size:1.2em;">{wyk["fase"]}</div></div>
                <div><div style="color:#64748b;font-size:0.75em;letter-spacing:1px;">{txt["wyckoff_range"]}</div>
                <div style="color:#e2e8f0;">{formatar_preco(wyk["suporte"], "")} ---
                {formatar_preco(wyk["resistencia"], "")}</div></div>
            </div>
            <div style="display:flex;gap:22px;margin-top:16px;flex-wrap:wrap;font-size:0.85em;">
                <span style="color:#94a3b8;">Penetração: <b style="color:#e2e8f0;">
                {ev["penetracao"]*100:.2f}%</b></span>
                <span style="color:#94a3b8;">Volume rel.: <b style="color:#e2e8f0;">
                {ev["vol_rel"]:.2f}×</b></span>
                <span style="color:#94a3b8;">{txt["wyckoff_teste"]}: <b style="color:#e2e8f0;">
                {txt["confirmado"] if wyk["teste_ok"] else txt["nao_confirmado"]}</b></span>
                <span style="color:#94a3b8;">{txt["wyckoff_sos"]}: <b style="color:#e2e8f0;">
                {txt["confirmado"] if wyk["sos"] else txt["nao_confirmado"]}</b></span>
                <span style="color:#94a3b8;">{txt["wyckoff_lps"]}: <b style="color:#e2e8f0;">
                {txt["confirmado"] if wyk["lps"] else txt["nao_confirmado"]}</b></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def renderizar_grafico_plotly(df_completo: pd.DataFrame, simbolo_id: str,
                              wyk: Optional[Dict], book: Optional[Dict],
                              stop_loss: Optional[float] = None) -> None:
    """Gera gráfico de velas com indicadores e níveis."""
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

# -----------------------------------------------------------------------------
# PAINEL PRINCIPAL (fragmento com refresh automático)
# -----------------------------------------------------------------------------
@st.fragment(run_every=0)  # O tempo será definido dinamicamente
def painel_principal(simbolo_id: str, timeframe: str, txt: Dict,
                     modo_vivo: bool, intervalo_refresh: int) -> None:
    """Função principal que monta o dashboard e é executada periodicamente."""
    # Força o refresh no tempo configurado
    if modo_vivo:
        st.cache_data.clear()
        # O fragmento já usa run_every; aqui apenas garantimos que os dados sejam recarregados.
        # O cache_data com TTL cuida da atualização.

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

# -----------------------------------------------------------------------------
# MAIN - Interface e execução
# -----------------------------------------------------------------------------
def main() -> None:
    """Ponto de entrada principal do aplicativo Streamlit."""
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

    lista_criptos = obter_todos_pares_usdt()
    simbolo_id = st.sidebar.selectbox(
        txt["selecione_cripto"],
        lista_criptos,
        index=lista_criptos.index("SOL/USDT") if "SOL/USDT" in lista_criptos else 0
    )
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

    # Executa o painel principal com o fragmento que se atualiza
    painel_principal(simbolo_id, timeframe, txt, modo_vivo, intervalo_refresh)

if __name__ == "__main__":
    main()
