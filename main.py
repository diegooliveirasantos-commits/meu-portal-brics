import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import requests
import math
from decimal import Decimal
import json
import re
from bs4 import BeautifulSoup

# Configuração da Página do Streamlit
st.set_page_config(
    page_title="BRICSVAULT PORTAL SMC",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sistema completo de tradução multilíngue
DICIONARIO_LINGUAS = {
    "Português (BR)": {
        "titulo": "🏦 BRICSVAULT PORTAL - Motor de Smart Money Concepts (SMC)",
        "config_globais": "⚙️ Configurações Globais",
        "selecione_cripto": "Selecione Qualquer Criptomoeda (/USDT):",
        "tempo_grafico": "Tempo Gráfico:",
        "modo_vivo": "Ativar Monitoramento em Tempo Real",
        "intervalo_refresh": "Intervalo de Atualização (Segundos):",
        "preco_spot": "Preço Spot Real",
        "variacao_24h": "Variação 24h (Exchange)",
        "market_cap": "Market Cap (USD)",
        "stop_atr": "Preço Stop ATR",
        "compra_forte": "🟢 COMPRA FORTE (SMC + FIBONACCI ALINHADOS)",
        "venda_forte": "🔴 VENDA FORTE (SMC + FIBONACCI ALINHADOS)",
        "neutro": "🟡 NEUTRO (AGUARDAR SMC)",
        "erro_dados": "Dados históricos insuficientes nesta Exchange para calcular a confluência estrutural SMC. Escolha outro Ativo ou reduza o Tempo Gráfico.",
        "ctx_desconto": "Ativo posicionado em Zona de Desconto de Fibonacci (Excelente risco/retorno para Institucionais).",
        "ctx_premium": "Ativo posicionado em Zona Premium de Fibonacci (Preço esticado, propício para realização de lucro).",
        "ctx_neutro": "Preço em zona neutra de equilíbrio de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Última Atualização",
        "proximo_refresh": "Próximo refresh em",
        "segundos": "segundos",
        "pontos_compra": "Pontos de Compra",
        "pontos_venda": "Pontos de Venda",
        "grafico_titulo": "📈 Gráfico de Preço com Indicadores SMC",
        "buscando_marketcap": "🔍 Buscando Market Cap em USD...",
        "marketcap_nao_disponivel": "Não disponível",
        "idioma_label": "🌐 Language / Idioma / Langue / Sprache / Lingua / Язык / 语言 / भाषा",
        "idioma_selecao": "Selecione o idioma da interface:",
    },
    "English (EN)": {
        "titulo": "🏦 BRICSVAULT PORTAL - Smart Money Concepts (SMC) Engine",
        "config_globais": "⚙️ Global Settings",
        "selecione_cripto": "Select Any Cryptocurrency (/USDT):",
        "tempo_grafico": "Timeframe:",
        "modo_vivo": "Enable Real-Time Monitoring",
        "intervalo_refresh": "Refresh Interval (Seconds):",
        "preco_spot": "Real Spot Price",
        "variacao_24h": "24h Variation (Exchange)",
        "market_cap": "Market Cap (USD)",
        "stop_atr": "ATR Stop Price",
        "compra_forte": "🟢 STRONG BUY (SMC + FIBONACCI ALIGNED)",
        "venda_forte": "🔴 STRONG SELL (SMC + FIBONACCI ALIGNED)",
        "neutro": "🟡 NEUTRAL (AWAIT SMC)",
        "erro_dados": "Insufficient historical data on this Exchange to calculate SMC structural confluence. Choose another Asset or reduce the Timeframe.",
        "ctx_desconto": "Asset positioned in Fibonacci Discount Zone (Excellent risk/reward for Institutionals).",
        "ctx_premium": "Asset positioned in Fibonacci Premium Zone (Price stretched, suitable for profit-taking).",
        "ctx_neutro": "Price in neutral Fibonacci equilibrium zone (Fair Value Zone).",
        "ultima_atualizacao": "Last Update",
        "proximo_refresh": "Next refresh in",
        "segundos": "seconds",
        "pontos_compra": "Buy Points",
        "pontos_venda": "Sell Points",
        "grafico_titulo": "📈 Price Chart with SMC Indicators",
        "buscando_marketcap": "🔍 Searching Market Cap in USD...",
        "marketcap_nao_disponivel": "Not available",
        "idioma_label": "🌐 Language / Idioma / Langue / Sprache / Lingua / Язык / 语言 / भाषा",
        "idioma_selecao": "Select Interface Language:",
    },
    "Français (FR)": {
        "titulo": "🏦 BRICSVAULT PORTAL - Moteur Smart Money Concepts (SMC)",
        "config_globais": "⚙️ Paramètres Globaux",
        "selecione_cripto": "Sélectionnez une Crypto-monnaie (/USDT):",
        "tempo_grafico": "Unité de Temps:",
        "modo_vivo": "Activer le Suivi en Temps Réel",
        "intervalo_refresh": "Intervalle de Rafraîchissement (Secondes):",
        "preco_spot": "Prix Spot Réel",
        "variacao_24h": "Variation 24h (Exchange)",
        "market_cap": "Capitalisation Boursière (USD)",
        "stop_atr": "Prix Stop ATR",
        "compra_forte": "🟢 ACHAT FORT (SMC + FIBONACCI ALIGNÉS)",
        "venda_forte": "🔴 VENTE FORTE (SMC + FIBONACCI ALIGNÉS)",
        "neutro": "🟡 NEUTRE (ATTENTE SMC)",
        "erro_dados": "Données historiques insuffisantes sur cet Exchange pour calculer la confluence structurelle SMC. Choisissez un autre Actif ou réduisez l'unité de temps.",
        "ctx_desconto": "Actif positionné dans la Zone de Discount de Fibonacci (Excellent rapport risque/rendement pour les Institutionnels).",
        "ctx_premium": "Actif positionné dans la Zone Premium de Fibonacci (Prix étiré, propice à la prise de bénéfices).",
        "ctx_neutro": "Prix dans la zone d'équilibre neutre de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Dernière mise à jour",
        "proximo_refresh": "Prochain rafraîchissement dans",
        "segundos": "secondes",
        "pontos_compra": "Points d'Achat",
        "pontos_venda": "Points de Vente",
        "grafico_titulo": "📈 Graphique de Prix avec Indicateurs SMC",
        "buscando_marketcap": "🔍 Recherche de la capitalisation boursière en USD...",
        "marketcap_nao_disponivel": "Non disponible",
        "idioma_label": "🌐 Language / Idioma / Langue / Sprache / Lingua / Язык / 语言 / भाषा",
        "idioma_selecao": "Sélectionnez la langue de l'interface:",
    },
    "Italiano (IT)": {
        "titulo": "🏦 BRICSVAULT PORTAL - Motore Smart Money Concepts (SMC)",
        "config_globais": "⚙️ Impostazioni Globali",
        "selecione_cripto": "Seleziona Qualsiasi Criptovaluta (/USDT):",
        "tempo_grafico": "Intervallo Temporale:",
        "modo_vivo": "Attiva Monitoraggio in Tempo Reale",
        "intervalo_refresh": "Intervallo di Aggiornamento (Secondi):",
        "preco_spot": "Prezzo Spot Reale",
        "variacao_24h": "Variazione 24h (Exchange)",
        "market_cap": "Capitalizzazione di Mercato (USD)",
        "stop_atr": "Prezzo Stop ATR",
        "compra_forte": "🟢 ACQUISTO FORTE (SMC + FIBONACCI ALLINEATI)",
        "venda_forte": "🔴 VENDITA FORTE (SMC + FIBONACCI ALLINEATI)",
        "neutro": "🟡 NEUTRO (ATTENDERE SMC)",
        "erro_dados": "Dati storici insufficienti su questo Exchange per calcolare la confluenza strutturale SMC. Scegli un altro Asset o riduci l'intervallo temporale.",
        "ctx_desconto": "Asset posizionato nella Zona di Sconto di Fibonacci (Eccellente rischio/rendimento per gli Istituzionali).",
        "ctx_premium": "Asset posizionato nella Zona Premium di Fibonacci (Prezzo esteso, adatto per la presa di profitto).",
        "ctx_neutro": "Prezzo nella zona neutra di equilibrio di Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Ultimo Aggiornamento",
        "proximo_refresh": "Prossimo aggiornamento tra",
        "segundos": "secondi",
        "pontos_compra": "Punti di Acquisto",
        "pontos_venda": "Punti di Vendita",
        "grafico_titulo": "📈 Grafico dei Prezzi con Indicatori SMC",
        "buscando_marketcap": "🔍 Ricerca Capitalizzazione di Mercato in USD...",
        "marketcap_nao_disponivel": "Non disponibile",
        "idioma_label": "🌐 Language / Idioma / Langue / Sprache / Lingua / Язык / 语言 / भाषा",
        "idioma_selecao": "Seleziona la lingua dell'interfaccia:",
    },
    "Deutsch (DE)": {
        "titulo": "🏦 BRICSVAULT PORTAL - Smart Money Concepts (SMC) Engine",
        "config_globais": "⚙️ Globale Einstellungen",
        "selecione_cripto": "Wählen Sie eine Kryptowährung (/USDT):",
        "tempo_grafico": "Zeitrahmen:",
        "modo_vivo": "Echtzeit-Überwachung aktivieren",
        "intervalo_refresh": "Aktualisierungsintervall (Sekunden):",
        "preco_spot": "Echter Spot-Preis",
        "variacao_24h": "24h-Änderung (Exchange)",
        "market_cap": "Marktkapitalisierung (USD)",
        "stop_atr": "ATR Stop-Preis",
        "compra_forte": "🟢 STARKER KAUF (SMC + FIBONACCI AUSGERICHTET)",
        "venda_forte": "🔴 STARKER VERKAUF (SMC + FIBONACCI AUSGERICHTET)",
        "neutro": "🟡 NEUTRAL (AUF SMC WARTEN)",
        "erro_dados": "Unzureichende historische Daten an dieser Börse, um die strukturelle SMC-Konfluenz zu berechnen. Wählen Sie einen anderen Vermögenswert oder reduzieren Sie den Zeitrahmen.",
        "ctx_desconto": "Vermögenswert in der Fibonacci-Discount-Zone positioniert (Ausgezeichnetes Risiko/Rendite-Verhältnis für Institutionelle).",
        "ctx_premium": "Vermögenswert in der Fibonacci-Premium-Zone positioniert (Überdehnter Preis, geeignet für Gewinnmitnahmen).",
        "ctx_neutro": "Preis in der neutralen Fibonacci-Gleichgewichtszone (Fair Value Zone).",
        "ultima_atualizacao": "Letzte Aktualisierung",
        "proximo_refresh": "Nächste Aktualisierung in",
        "segundos": "Sekunden",
        "pontos_compra": "Kaufpunkte",
        "pontos_venda": "Verkaufspunkte",
        "grafico_titulo": "📈 Preisdiagramm mit SMC-Indikatoren",
        "buscando_marketcap": "🔍 Suche Marktkapitalisierung in USD...",
        "marketcap_nao_disponivel": "Nicht verfügbar",
        "idioma_label": "🌐 Language / Idioma / Langue / Sprache / Lingua / Язык / 语言 / भाषा",
        "idioma_selecao": "Wählen Sie die Sprache der Benutzeroberfläche:",
    },
    "Русский (RUS) - Rússia": {
        "titulo": "🏦 BRICSVAULT ПОРТАЛ - Алгоритм Smart Money Concepts (SMC)",
        "config_globais": "⚙️ Глобальные настройки",
        "selecione_cripto": "Выберите криптовалюту (/USDT):",
        "tempo_grafico": "Таймфрейм:",
        "modo_vivo": "Включить мониторинг в реальном времени",
        "intervalo_refresh": "Интервал обновления (сек):",
        "preco_spot": "Текущая спотовая цена",
        "variacao_24h": "Изменение за 24ч (Биржа)",
        "market_cap": "Рыночная капитализация (USD)",
        "stop_atr": "Цена ATR Stop",
        "compra_forte": "🟢 АКТИВНАЯ ПОКУПКА (SMC + ФИБОНАЧЧИ СОГЛАСОВАНЫ)",
        "venda_forte": "🔴 АКТИВНАЯ ПРОДАЖА (SMC + ФИБОНАЧЧИ СОГЛАСОВАНЫ)",
        "neutro": "🟡 НЕЙТРАЛЬНО (ОЖИДАНИЕ SMC)",
        "erro_dados": "Недостаточно исторических данных на этой бирже для расчета структурного слияния SMC. Выберите другой актив или уменьшите таймфрейм.",
        "ctx_desconto": "Актив находится в дисконтной зоне Фибоначчи (Отличное соотношение риск/прибыль для институциональных инвесторов).",
        "ctx_premium": "Актив находится в премиум-зоне Фибоначчи (Цена завышена, подходит для фиксации прибыли).",
        "ctx_neutro": "Цена находится в нейтральной зоне равновесия Фибоначчи (Fair Value Zone).",
        "ultima_atualizacao": "Последнее обновление",
        "proximo_refresh": "Следующее обновление через",
        "segundos": "сек",
        "pontos_compra": "Очки покупки",
        "pontos_venda": "Очки продажи",
        "grafico_titulo": "📈 График цены с индикаторами SMC",
        "buscando_marketcap": "🔍 Поиск рыночной капитализации в USD...",
        "marketcap_nao_disponivel": "Недоступно",
        "idioma_label": "🌐 Language / Idioma / Langue / Sprache / Lingua / Язык / 语言 / भाषा",
        "idioma_selecao": "Выберите язык интерфейса:",
    },
    "中文 (ZH) - China": {
        "titulo": "🏦 BRICSVAULT 门户 - 聪明的钱概念 (SMC) 引擎",
        "config_globais": "⚙️ 全局设置",
        "selecione_cripto": "选择任何加密货币 (/USDT):",
        "tempo_grafico": "时间框架:",
        "modo_vivo": "启用实时监控",
        "intervalo_refresh": "刷新间隔（秒）:",
        "preco_spot": "实时现货价格",
        "variacao_24h": "24小时涨跌幅 (交易所)",
        "market_cap": "市值 (USD)",
        "stop_atr": "ATR 止损价",
        "compra_forte": "🟢 强力买入 (SMC + 斐波那契共振)",
        "venda_forte": "🔴 强力卖出 (SMC + 斐波那契共振)",
        "neutro": "🟡 中性 (等待 SMC 信号)",
        "erro_dados": "该交易所的历史数据不足，无法计算 SMC 结构共振。请选择其他资产或缩短时间框架。",
        "ctx_desconto": "资产处于斐波那契折扣区（对机构投资者而言极佳的风险回报比）。",
        "ctx_premium": "资产处于斐波那契溢价区（价格拉升过高，适合获利了结）。",
        "ctx_neutro": "价格处于斐波那契中性平衡区 (公允价值区域)。",
        "ultima_atualizacao": "最后更新",
        "proximo_refresh": "下次刷新",
        "segundos": "秒",
        "pontos_compra": "买入分数",
        "pontos_venda": "卖出分数",
        "grafico_titulo": "📈 带SMC指标的价格图表",
        "buscando_marketcap": "🔍 正在搜索以USD计价的市值...",
        "marketcap_nao_disponivel": "不可用",
        "idioma_label": "🌐 Language / Idioma / Langue / Sprache / Lingua / Язык / 语言 / भाषा",
        "idioma_selecao": "选择界面语言:",
    },
    "हिन्दी (HI) - Índia": {
        "titulo": "🏦 BRICSVAULT पोर्टल - स्मार्ट मनी कॉन्सेप्ट्स (SMC) इंजन",
        "config_globais": "⚙️ वैश्विक सेटिंग्स",
        "selecione_cripto": "कोई भी क्रिप्टोकरेंसी चुनें (/USDT):",
        "tempo_grafico": "समय सीमा:",
        "modo_vivo": "रीयल-टाइम मॉनिटरिंग सक्षम करें",
        "intervalo_refresh": "रीफ्रेश अंतराल (सेकंड):",
        "preco_spot": "वास्तविक स्पॉट मूल्य",
        "variacao_24h": "24 घंटे का बदलाव (एक्सचेंज)",
        "market_cap": "मार्केट कैप (USD)",
        "stop_atr": "ATR स्टॉप मूल्य",
        "compra_forte": "🟢 मजबूत खरीदारी (SMC + फिबोनाची संरेखित)",
        "venda_forte": "🔴 मजबूत बिक्री (SMC + फिबोनाची संरेखित)",
        "neutro": "🟡 तटस्थ (SMC की प्रतीक्षा करें)",
        "erro_dados": "इस एक्सचेंज पर SMC संरचनात्मक संगम की गणना करने के लिए अपर्याप्त ऐतिहासिक डेटा। कृपया कोई अन्य परिसंपत्ति चुनें या समय सीमा कम करें।",
        "ctx_desconto": "परिसंपत्ति फिबोनाची डिस्काउंट ज़ोन में स्थित है (संस्थागत निवेशकों के लिए उत्कृष्ट जोखिम/रिटर्न)।",
        "ctx_premium": "परिसंपत्ति फिबोनाची प्रीमियम ज़ोन में स्थित है (मूल्य बढ़ा हुआ है, लाभ लेने के लिए उपयुक्त)।",
        "ctx_neutro": "मूल्य तटस्थ फिबोनाची संतुलन क्षेत्र में है (उचित मूल्य क्षेत्र)।",
        "ultima_atualizacao": "अंतिम अपडेट",
        "proximo_refresh": "अगला रीफ्रेश",
        "segundos": "सेकंड में",
        "pontos_compra": "खरीदारी के अंक",
        "pontos_venda": "बिक्री के अंक",
        "grafico_titulo": "📈 SMC संकेतकों के साथ मूल्य चार्ट",
        "buscando_marketcap": "🔍 USD में मार्केट कैप खोजा जा रहा है...",
        "marketcap_nao_disponivel": "उपलब्ध नहीं है",
        "idioma_label": "🌐 Language / Idioma / Langue / Sprache / Lingua / Язык / 语言 / भाषा",
        "idioma_selecao": "इंटरफ़ेस भाषा चुनें:",
    }
}

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
    elif valor < 1000:
        return f"{prefixo}{valor:,.2f}"
    else:
        return f"{prefixo}{valor:,.2f}"

def formatar_market_cap(valor):
    """
    Formata o Market Cap SEMPRE em USD.
    Independente do idioma, a unidade monetária é USD.
    """
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
        return f"$ {valor/1_000_000_000_000:.2f}T"
    elif valor >= 1_000_000_000:
        return f"$ {valor/1_000_000_000:.2f}B"
    elif valor >= 1_000_000:
        return f"$ {valor/1_000_000:.2f}M"
    elif valor >= 1_000:
        return f"$ {valor/1_000:.2f}K"
    else:
        return f"$ {valor:,.2f}"

# Conexão com Exchange
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

# ============================================
# SISTEMA ROBUSTO DE MARKET CAP EM USD
# ============================================

@st.cache_data(ttl=300)
def obter_market_cap_coingecko(simbolo):
    """Fonte 1: CoinGecko API - Retorna Market Cap em USD"""
    try:
        url_lista = "https://api.coingecko.com/api/v3/coins/list"
        response = requests.get(url_lista, timeout=15)
        
        if response.status_code == 200:
            moedas = response.json()
            simbolo_lower = simbolo.lower()
            
            coin_id = None
            for moeda in moedas:
                if moeda.get('symbol', '') == simbolo_lower:
                    coin_id = moeda['id']
                    break
            
            if coin_id:
                url_dados = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&community_data=false&developer_data=false"
                response_dados = requests.get(url_dados, timeout=15)
                
                if response_dados.status_code == 200:
                    dados = response_dados.json()
                    market_data = dados.get('market_data', {})
                    market_cap = market_data.get('market_cap', {}).get('usd')
                    
                    if market_cap and market_cap > 0:
                        return float(market_cap)
        
        return None
    except Exception:
        return None

@st.cache_data(ttl=300)
def obter_market_cap_coinmarketcap(simbolo):
    """Fonte 2: CoinMarketCap - Retorna Market Cap em USD"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        url = f"https://coinmarketcap.com/currencies/{simbolo.lower()}/"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'marketCap' in script.string:
                    match = re.search(r'"marketCap":(\d+\.?\d*)', script.string)
                    if match:
                        valor = float(match.group(1))
                        if valor > 0:
                            return valor
        
        return None
    except Exception:
        return None

@st.cache_data(ttl=300)
def obter_market_cap_coinpaprika(simbolo):
    """Fonte 3: CoinPaprika API - Retorna Market Cap em USD"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        url_search = f"https://api.coinpaprika.com/v1/search?q={simbolo}&c=currencies&limit=10"
        response = requests.get(url_search, headers=headers, timeout=15)
        
        if response.status_code == 200:
            dados = response.json()
            currencies = dados.get('currencies', [])
            
            coin_id = None
            for currency in currencies:
                if currency.get('symbol', '').upper() == simbolo.upper():
                    coin_id = currency['id']
                    break
            
            if coin_id:
                url_coin = f"https://api.coinpaprika.com/v1/coins/{coin_id}"
                response_coin = requests.get(url_coin, headers=headers, timeout=15)
                
                if response_coin.status_code == 200:
                    dados_coin = response_coin.json()
                    market_cap = dados_coin.get('market_cap')
                    if market_cap and market_cap > 0:
                        return float(market_cap)
        
        return None
    except Exception:
        return None

def obter_market_cap_robusto(simbolo_id):
    """Sistema principal - Garante Market Cap SEMPRE em USD"""
    simbolo = simbolo_id.split('/')[0]
    
    fontes = [
        ("CoinGecko", obter_market_cap_coingecko),
        ("CoinMarketCap", obter_market_cap_coinmarketcap),
        ("CoinPaprika", obter_market_cap_coinpaprika),
    ]
    
    for nome_fonte, funcao in fontes:
        try:
            resultado = funcao(simbolo)
            if resultado is not None and resultado > 0:
                if simbolo.upper() in ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE']:
                    if resultado < 1_000_000:
                        continue
                return float(resultado)
        except Exception:
            continue
    
    try:
        ticker = gateio_client.fetch_ticker(simbolo_id)
        if ticker:
            volume_usd = ticker.get('quoteVolume', 0)
            if volume_usd > 0:
                estimativa = volume_usd * 500
                if estimativa > 0:
                    return float(estimativa)
    except Exception:
        pass
    
    return None

# Indicadores técnicos
def calcular_rsi(df, col, periodo=14):
    delta = df[col].diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)
    ma_ganho = ganho.ewm(span=periodo, adjust=False).mean()
    ma_perda = perda.ewm(span=periodo, adjust=False).mean()
    return 100 - (100 / (1 + (ma_ganho / ma_perda.replace(0, 1e-10))))

def calcular_macd(df, col):
    ema_rapida = df[col].ewm(span=12, adjust=False).mean()
    ema_lenta = df[col].ewm(span=26, adjust=False).mean()
    macd = ema_rapida - ema_lenta
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
    df['ssl_dir'] = ssl_dir
    df['SSL_Baseline'] = np.where(df['ssl_dir'] == 1, sma_high, sma_low)
    return df

def calcular_atr_stop(df, periodo=14, multiplicador=3.0):
    high, low, close = df['high'], df['low'], df['close']
    tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.ewm(span=periodo, adjust=False).mean()
    atr_stop = np.zeros(len(df))
    tendencia = np.zeros(len(df), dtype=int)
    close_arr = close.values
    atr_arr = atr.values
    for i in range(1, len(df)):
        if i == 1:
            atr_stop[i] = close_arr[i] - (atr_arr[i] * multiplicador)
            tendencia[i] = 1
            continue
        if tendencia[i-1] == 1:
            if close_arr[i] < atr_stop[i-1]:
                tendencia[i] = -1
                atr_stop[i] = close_arr[i] + (atr_arr[i] * multiplicador)
            else:
                tendencia[i] = 1
                atr_stop[i] = max(atr_stop[i-1], close_arr[i] - (atr_arr[i] * multiplicador))
        else:
            if close_arr[i] > atr_stop[i-1]:
                tendencia[i] = 1
                atr_stop[i] = close_arr[i] - (atr_arr[i] * multiplicador)
            else:
                tendencia[i] = -1
                atr_stop[i] = min(atr_stop[i-1], close_arr[i] + (atr_arr[i] * multiplicador))
    df['ATR_Stop'] = atr_stop
    df['atr_dir'] = tendencia
    return df

def calcular_retracao_fibonacci(df):
    maxima = df['high'].max()
    minima = df['low'].min()
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

def carregar_dados(simbolo_id, timeframe_selecionado):
    try:
        velas = gateio_client.fetch_ohlcv(simbolo_id, timeframe=timeframe_selecionado, limit=200)
        if not velas:
            return None
        df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['RSI_14'] = calcular_rsi(df, 'close', 14)
        macd, sinal, hist = calcular_macd(df, 'close')
        df['MACD'] = macd
        df['MACD_SIGNAL'] = sinal
        df['MACD_HIST'] = hist
        df['MFI'] = calcular_mfi(df)
        df = calcular_ssl_hybrid(df)
        df = calcular_atr_stop(df)
        return df.dropna(subset=['close', 'SSL_Baseline'])
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

def obter_variacao_24h(simbolo_id):
    try:
        dados_24h = gateio_client.fetch_ohlcv(simbolo_id, timeframe='1d', limit=2)
        if dados_24h and len(dados_24h) >= 2:
            close_hoje = dados_24h[-1][4]
            close_ontem = dados_24h[-2][4]
            return ((close_hoje - close_ontem) / close_ontem) * 100
    except Exception:
        pass
    return 0.0

def analisar_confluencia(df, fib_niveis, txt):
    u = df.iloc[-1]
    preco_atual = u['close']
    pontos_alta = 0.0
    pontos_baixa = 0.0
    
    if u['RSI_14'] < 40:
        pontos_alta += 2
    elif u['RSI_14'] > 60:
        pontos_baixa += 2
    
    if u['MACD_HIST'] > 0:
        pontos_alta += 2
    else:
        pontos_baixa += 2
    
    if u['MFI'] > 50:
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
    
    if preco_atual <= fib_niveis['fib_618']:
        pontos_alta += 2.0
        contexto_fib = txt["ctx_desconto"]
    elif preco_atual >= fib_niveis['fib_382']:
        pontos_baixa += 2.0
        contexto_fib = txt["ctx_premium"]
    else:
        contexto_fib = txt["ctx_neutro"]
    
    if pontos_alta >= 7.5:
        return txt["compra_forte"], "#00cc66", f"{contexto_fib} SMC Order Flow Bullish Structure.", pontos_alta, pontos_baixa
    elif pontos_baixa >= 7.5:
        return txt["venda_forte"], "#ff3333", f"{contexto_fib} SMC Order Flow Bearish Structure.", pontos_alta, pontos_baixa
    else:
        return txt["neutro"], "#ffcc00", contexto_fib, pontos_alta, pontos_baixa

def construir_grafico(df, fib_niveis, simbolo_id):
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.5, 0.25, 0.25],
        vertical_spacing=0.05,
        subplot_titles=(f"{simbolo_id} - Preço", "RSI", "MACD")
    )
    
    fig.add_trace(go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name="OHLC"
    ), row=1, col=1)
    
    ssl_colors = df['ssl_dir'].apply(lambda d: '#00aaff' if d == 1 else '#ff6600')
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['SSL_Baseline'],
        mode='lines', line=dict(width=1.5),
        marker=dict(color=ssl_colors), name="SSL"
    ), row=1, col=1)
    
    atr_colors = df['atr_dir'].apply(lambda d: '#00cc66' if d == 1 else '#ff3333')
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['ATR_Stop'],
        mode='markers', marker=dict(color=atr_colors, size=3),
        name="ATR Stop"
    ), row=1, col=1)
    
    for chave, cor in [('fib_0', 'red'), ('fib_236', 'orange'), ('fib_382', 'yellow'),
                        ('fib_500', 'gray'), ('fib_618', 'green'), ('fib_786', 'blue'), ('fib_100', 'purple')]:
        fig.add_hline(y=fib_niveis[chave], line_dash="dot", line_color=cor, line_width=1, row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['RSI_14'],
        line=dict(color='yellow', width=1.5), name="RSI 14"
    ), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", line_width=0.8, row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", line_width=0.8, row=2, col=1)
    
    hist_colors = df['MACD_HIST'].apply(lambda v: 'green' if v >= 0 else 'red')
    fig.add_trace(go.Bar(
        x=df['time'], y=df['MACD_HIST'],
        marker_color=hist_colors, name="MACD Hist"
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['MACD'],
        line=dict(color='blue', width=1), name="MACD"
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=df['time'], y=df['MACD_SIGNAL'],
        line=dict(color='orange', width=1), name="Signal"
    ), row=3, col=1)
    
    fig.update_layout(
        height=800,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        margin=dict(l=60, r=60, t=40, b=20)
    )
    
    return fig

# ========== INTERFACE PRINCIPAL ==========

# Seletor de idioma na sidebar
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

intervalos = {
    "1 Minuto": "1m", "5 Minutos": "5m", "15 Minutos": "15m",
    "30 Minutos": "30m", "1 Hora": "1h", "4 Horas": "4h",
    "1 Dia": "1d", "1 Semana": "1w"
}
intervalo_escolhido = st.sidebar.selectbox(txt["tempo_grafico"], list(intervalos.keys()), index=5)
timeframe = intervalos[intervalo_escolhido]

st.sidebar.markdown("---")
modo_vivo = st.sidebar.toggle(txt["modo_vivo"], value=False)
intervalo_refresh = st.sidebar.slider(txt["intervalo_refresh"], min_value=5, max_value=60, value=15)

# Carregar dados
status_placeholder = st.empty()
df_dados = carregar_dados(simbolo_id, timeframe)

if df_dados is None or df_dados.empty:
    st.warning(txt["erro_dados"])
else:
    ultimo_reg = df_dados.iloc[-1]
    preco_atual = ultimo_reg['close']
    fib_niveis = calcular_retracao_fibonacci(df_dados)
    variacao_24h = obter_variacao_24h(simbolo_id)
    
    # Buscar Market Cap SEMPRE em USD
    with st.spinner(txt["buscando_marketcap"]):
        market_cap = obter_market_cap_robusto(simbolo_id)
    
    recomendacao, cor_sinal, analise, pontos_alta, pontos_baixa = analisar_confluencia(df_dados, fib_niveis, txt)
    
    # Painel de recomendação
    st.markdown(f"""
    <div style="background:{cor_sinal}22;padding:20px;border-radius:10px;border:2px solid {cor_sinal};margin-bottom:20px;">
        <h2 style="margin:0;color:{cor_sinal};">{recomendacao}</h2>
        <p style="margin:8px 0 0 0;color:#ddd;">{analise}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Métricas - Market Cap sempre em USD
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(txt["preco_spot"], formatar_preco(preco_atual))
    m2.metric(txt["variacao_24h"], f"{variacao_24h:+.2f}%")
    
    # Market Cap garantido em USD
    if market_cap is not None:
        m3.metric(txt["market_cap"], formatar_market_cap(market_cap))
    else:
        m3.metric(txt["market_cap"], txt["marketcap_nao_disponivel"])
    
    m4.metric(txt["pontos_compra"], f"{pontos_alta:.1f}")
    m5.metric(txt["pontos_venda"], f"{pontos_baixa:.1f}")
    
    # Gráfico
    st.markdown(f"### {txt['grafico_titulo']}")
    fig = construir_grafico(df_dados, fib_niveis, simbolo_id)
    st.plotly_chart(fig, use_container_width=True)
    
    # Status
    hora_atual = pd.Timestamp.now().strftime("%H:%M:%S")
    if modo_vivo:
        status_placeholder.info(f"🟢 {txt['ultima_atualizacao']}: {hora_atual} | {txt['proximo_refresh']} {intervalo_refresh} {txt['segundos']}")
        time.sleep(intervalo_refresh)
        st.rerun()
    else:
        status_placeholder.info(f"⏸ {txt['ultima_atualizacao']}: {hora_atual}")
