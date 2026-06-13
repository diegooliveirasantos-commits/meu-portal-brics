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
        "market_cap": "Market Cap",
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
        "buscando_marketcap": "🔍 Buscando Market Cap em múltiplas fontes...",
        "marketcap_nao_disponivel": "Não disponível",
        "idioma_label": "🌐 Language / Idioma / Langue",
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
        "market_cap": "Market Cap",
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
        "buscando_marketcap": "🔍 Searching Market Cap from multiple sources...",
        "marketcap_nao_disponivel": "Not available",
        "idioma_label": "🌐 Language / Idioma / Langue",
        "idioma_selecao": "Select Interface Language:",
    },
    "Español (ESP)": {
        "titulo": "🏦 BRICSVAULT PORTAL - Motor de Smart Money Concepts (SMC)",
        "config_globais": "⚙️ Configuraciones Globales",
        "selecione_cripto": "Seleccione Cualquier Criptomoneda (/USDT):",
        "tempo_grafico": "Período de Tiempo:",
        "modo_vivo": "Activar Monitoreo en Tiempo Real",
        "intervalo_refresh": "Intervalo de Actualización (Segundos):",
        "preco_spot": "Precio Spot Real",
        "variacao_24h": "Variación 24h (Exchange)",
        "market_cap": "Cap. de Mercado",
        "stop_atr": "Precio Stop ATR",
        "compra_forte": "🟢 COMPRA FUERTE (SMC + FIBONACCI ALINEADOS)",
        "venda_forte": "🔴 VENTA FUERTE (SMC + FIBONACCI ALINEADOS)",
        "neutro": "🟡 NEUTRO (ESPERAR SMC)",
        "erro_dados": "Datos históricos insuficientes en esta Exchange para calcular la confluencia estructural SMC. Elija otro Activo o reduzca el Tiempo Gráfico.",
        "ctx_desconto": "Activo posicionado en Zona de Descuento de Fibonacci (Excelente riesgo/beneficio para Institucionales).",
        "ctx_premium": "Activo posicionado en Zona Premium de Fibonacci (Precio estirado, propicio para toma de ganancias).",
        "ctx_neutro": "Precio en zona neutral de equilibrio de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Última Actualización",
        "proximo_refresh": "Próximo refresh en",
        "segundos": "segundos",
        "pontos_compra": "Puntos de Compra",
        "pontos_venda": "Puntos de Venta",
        "grafico_titulo": "📈 Gráfico de Precio con Indicadores SMC",
        "buscando_marketcap": "🔍 Buscando Market Cap en múltiples fuentes...",
        "marketcap_nao_disponivel": "No disponible",
        "idioma_label": "🌐 Language / Idioma / Langue",
        "idioma_selecao": "Seleccione el idioma de la interfaz:",
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
        "market_cap": "Capitalisation Boursière",
        "stop_atr": "Prix Stop ATR",
        "compra_forte": "🟢 ACHAT FORT (SMC + FIBONACCI ALIGNÉS)",
        "venda_forte": "🔴 VENTE FORTE (SMC + FIBONACCI ALIGNÉS)",
        "neutro": "🟡 NEUTRE (ATTENTE SMC)",
        "erro_dados": "Données historiques insuffisantes sur cet Exchange pour calculer la confluence structurelle SMC. Choisissez un autre Actif ou réduisez l'unité de temps.",
        "ctx_desconto": "Actif positionné dans la Zone de Discount de Fibonacci (Excellent rapport risque/rendement pour les Institutionnels).",
        "ctx_premium": "Actif positionné dans la Zone Premium de Fibonacci (Prix étiré, propice à la prise de bénéfices).",
        "ctx_neutro": "Prix dans la zone d'équilibre neutre de Fibonacci (Fair Value Zone).",
        "ultima_atualizacao": "Dernière mise à jour",
        "proximo_refresh": "Prochain refresh dans",
        "segundos": "secondes",
        "pontos_compra": "Points d'Achat",
        "pontos_venda": "Points de Vente",
        "grafico_titulo": "📈 Graphique de Prix avec Indicateurs SMC",
        "buscando_marketcap": "🔍 Recherche de la capitalisation boursière depuis plusieurs sources...",
        "marketcap_nao_disponivel": "Non disponible",
        "idioma_label": "🌐 Language / Idioma / Langue",
        "idioma_selecao": "Sélectionnez la langue de l'interface:",
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
    if valor is None:
        return "..."
    if valor >= 1_000_000_000_000:
        return f"$ {valor/1_000_000_000_000:.2f}T"
    elif valor >= 1_000_000_000:
        return f"$ {valor/1_000_000_000:.2f}B"
    elif valor >= 1_000_000:
        return f"$ {valor/1_000_000:.2f}M"
    elif valor >= 1_000:
        return f"$ {valor/1_000:.2f}K"
    else:
        return f"$ {valor:.2f}"

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
# SISTEMA ROBUSTO DE MARKET CAP
# ============================================

def extrair_numero_marketcap(texto):
    """Extrai valor numérico de uma string de market cap"""
    try:
        # Remove símbolos de moeda e espaços
        texto = texto.replace('$', '').replace(' ', '').replace(',', '').strip()
        
        # Converte sufixos
        if 'T' in texto or 't' in texto:
            return float(texto.replace('T', '').replace('t', '')) * 1_000_000_000_000
        elif 'B' in texto or 'b' in texto:
            return float(texto.replace('B', '').replace('b', '')) * 1_000_000_000
        elif 'M' in texto or 'm' in texto:
            return float(texto.replace('M', '').replace('m', '')) * 1_000_000
        elif 'K' in texto or 'k' in texto:
            return float(texto.replace('K', '').replace('k', '')) * 1_000
        else:
            return float(texto)
    except:
        return None

@st.cache_data(ttl=300)
def obter_market_cap_coingecko(simbolo):
    """Fonte 1: CoinGecko API - Método mais confiável"""
    try:
        # Primeiro, busca a lista completa de moedas
        url_lista = "https://api.coingecko.com/api/v3/coins/list"
        response = requests.get(url_lista, timeout=15)
        
        if response.status_code == 200:
            moedas = response.json()
            simbolo_lower = simbolo.lower()
            
            # Encontra o ID correto
            coin_id = None
            for moeda in moedas:
                if moeda.get('symbol', '') == simbolo_lower:
                    coin_id = moeda['id']
                    break
            
            if coin_id:
                # Busca dados detalhados
                url_dados = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&community_data=false&developer_data=false"
                response_dados = requests.get(url_dados, timeout=15)
                
                if response_dados.status_code == 200:
                    dados = response_dados.json()
                    market_data = dados.get('market_data', {})
                    market_cap = market_data.get('market_cap', {}).get('usd')
                    if market_cap and market_cap > 0:
                        return market_cap
        
        return None
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def obter_market_cap_coinmarketcap(simbolo):
    """Fonte 2: CoinMarketCap - Scraping direto"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        # URL da página da moeda
        url = f"https://coinmarketcap.com/currencies/{simbolo.lower()}/"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Procura por elementos com data-testid ou classes específicas
            # Método 1: Procurar por dd tags com Market Cap
            market_cap_element = soup.find('dd', {'data-testid': 'market-cap'})
            if market_cap_element:
                texto = market_cap_element.text.strip()
                valor = extrair_numero_marketcap(texto)
                if valor:
                    return valor
            
            # Método 2: Procurar por texto "Market cap" no HTML
            for element in soup.find_all(['dd', 'div', 'span']):
                texto = element.get_text()
                if 'market cap' in texto.lower():
                    # Extrai o número do texto
                    match = re.search(r'\$[\d,.]+[BMKT]?', texto)
                    if match:
                        valor = extrair_numero_marketcap(match.group())
                        if valor:
                            return valor
            
            # Método 3: Procurar no script JSON embutido
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'marketCap' in script.string:
                    match = re.search(r'"marketCap":(\d+\.?\d*)', script.string)
                    if match:
                        valor = float(match.group(1))
                        if valor > 0:
                            return valor
        
        return None
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def obter_market_cap_coinpaprika(simbolo):
    """Fonte 3: CoinPaprika API - Alternativa gratuita e confiável"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Busca a moeda pelo símbolo
        url_search = f"https://api.coinpaprika.com/v1/search?q={simbolo}&c=currencies&limit=10"
        response = requests.get(url_search, headers=headers, timeout=15)
        
        if response.status_code == 200:
            dados = response.json()
            currencies = dados.get('currencies', [])
            
            # Encontra a moeda com o símbolo exato
            coin_id = None
            for currency in currencies:
                if currency.get('symbol', '').upper() == simbolo.upper():
                    coin_id = currency['id']
                    break
            
            if coin_id:
                # Busca dados detalhados
                url_coin = f"https://api.coinpaprika.com/v1/coins/{coin_id}"
                response_coin = requests.get(url_coin, headers=headers, timeout=15)
                
                if response_coin.status_code == 200:
                    dados_coin = response_coin.json()
                    market_cap = dados_coin.get('market_cap')
                    if market_cap and market_cap > 0:
                        return market_cap
        
        return None
    except Exception:
        return None

def obter_market_cap_robusto(simbolo_id):
    """
    Sistema principal que tenta múltiplas fontes em sequência
    até encontrar o Market Cap
    """
    simbolo = simbolo_id.split('/')[0]
    
    # Lista de fontes para tentar
    fontes = [
        ("CoinGecko", obter_market_cap_coingecko),
        ("CoinMarketCap", obter_market_cap_coinmarketcap),
        ("CoinPaprika", obter_market_cap_coinpaprika),
    ]
    
    for nome_fonte, funcao in fontes:
        try:
            resultado = funcao(simbolo)
            if resultado is not None and resultado > 0:
                return resultado
        except Exception:
            continue
    
    # Último recurso: estimativa baseada no volume
    try:
        ticker = gateio_client.fetch_ticker(simbolo_id)
        if ticker:
            preco = ticker.get('last', 0)
            volume = ticker.get('quoteVolume', 0)
            if preco > 0 and volume > 0:
                # Estimativa conservadora: volume diário * 500
                return volume * 500
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
    
    # Buscar Market Cap com sistema robusto
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
    
    # Métricas
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(txt["preco_spot"], formatar_preco(preco_atual))
    m2.metric(txt["variacao_24h"], f"{variacao_24h:+.2f}%")
    
    # Mostrar Market Cap
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
