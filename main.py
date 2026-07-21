# -----------------------------------------------------------------------------
# BRICSVAULT PORTAL - Smart Money Concepts (SMC) Engine
# Versão 2.0 - FILTRO DE STABLECOINS E DERIVATIVOS
# Requisitos: streamlit, ccxt, pandas, numpy, requests, plotly, decimal, zoneinfo
# -----------------------------------------------------------------------------

import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import requests
import math
import time
from decimal import Decimal
import plotly.graph_objects as go
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ==========================================================================
# CONFIGURAÇÃO DO TELEGRAM (SUBSTITUA PELOS SEUS DADOS)
# ==========================================================================
TELEGRAM_TOKEN = "8923739480:AAH8WXthla04LrEv4tT5horPzM7P5SYTT9s"
TELEGRAM_CHAT_ID = "1143799141"
# ==========================================================================

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
TTL_DADOS_LIVE_SEGUNDOS: int = 120
TTL_DADOS_INTERFACE_SEGUNDOS: int = 30
TTL_BOOK_SEGUNDOS: int = 30
TTL_TOP_ATIVOS: int = 7200

EXCHANGE_TIMEOUT_MS: int = 15000

LIMITE_BOOK: int = 100
FAIXA_BOOK: float = 0.015
PASSO_AGRUPAMENTO: float = 0.0005

JANELA_BASE_WYCKOFF: int = 60
JANELA_EVENTO_WYCKOFF: int = 15

LIMIAR_SINAL_LIQUIDO: float = 32.0
PONTOS_MAX_WYCKOFF: float = 3.0

TOP_ATIVOS_QTD: int = 50
TIMEFRAME_MONITORAMENTO: str = "4h"
INTERVALO_ENVIO_SINAIS: int = 7200
MAX_SINAIS_POR_ENVIO: int = 5

# ==========================================================================
# LISTA DE STABLECOINS E PALAVRAS-CHAVE DE DERIVATIVOS
# ==========================================================================
STABLECOINS = [
    "USDC", "BUSD", "DAI", "TUSD", "USDP", "GUSD", "PAX", "UST", "MIM",
    "LUSD", "FRAX", "USDN", "SUSD", "DOLA", "USDD", "CUSD", "USX", "USDT"
]

DERIVATIVE_KEYWORDS = ["PERP", "SWAP", "FUT", "FUNDING", "INDEX", "INV", "POOL"]

def is_stablecoin(symbol: str) -> bool:
    """Verifica se o par contém stablecoin."""
    try:
        base, quote = symbol.split('/')
        if quote in STABLECOINS or base in STABLECOINS:
            return True
        for sc in STABLECOINS:
            if sc in symbol:
                return True
        return False
    except:
        return False

def is_derivative(symbol: str) -> bool:
    """Verifica se o símbolo é de derivativos (perp, swap, etc.)."""
    symbol_upper = symbol.upper()
    for kw in DERIVATIVE_KEYWORDS:
        if kw in symbol_upper:
            return True
    return False

def is_valid_spot_pair(symbol: str) -> bool:
    """Verifica se o par é válido (spot, sem stablecoin, sem derivativo)."""
    if not symbol.endswith('/USDT'):
        return False
    if is_derivative(symbol):
        return False
    if is_stablecoin(symbol):
        return False
    return True

# ==========================================================================
# DICIONÁRIOS DE IDIOMAS E RESUMOS WYCKOFF (mantidos completos)
# ==========================================================================
RESUMOS_WYCKOFF = {
    "SPRING": {
        "pt": "O preço furou o suporte, mas voltou rápido, indicando que compradores estão no controle.",
        "en": "Price broke support but quickly reversed, showing buyers are in control.",
        "es": "El precio rompió el soporte pero rebotó rápido, indicando que los compradores controlan.",
        "fr": "Le prix a cassé le support mais est revenu rapidement, montrant que les acheteurs contrôlent.",
        "de": "Der Preis durchbrach die Unterstützung, kehrte aber schnell zurück, was Käuferkontrollé zeigt.",
        "it": "Il prezzo ha rotto il supporto ma è tornato rapidamente, indicando che gli acquirenti controllano.",
        "ru": "Цена пробила поддержку, но быстро вернулась, показывая контроль покупателей.",
        "ja": "価格はサポートを割ったがすぐに戻り、買い手が支配していることを示す。",
        "zh": "价格跌破支撑但迅速回升，表明买家占据主导。",
        "hi": "कीमत समर्थन से नीचे गई लेकिन जल्दी वापस आ गई, दिखाता है कि खरीदार नियंत्रण में हैं।"
    },
    "SHAKEOUT": {
        "pt": "O preço caiu forte para derrubar stops, mas se recuperou, mostrando que a queda foi falsa.",
        "en": "Price dropped sharply to shake out stops, then recovered, showing the drop was false.",
        "es": "El precio cayó fuerte para sacar stops, pero se recuperó, mostrando que la caída fue falsa.",
        "fr": "Le prix a chuté fortement pour éliminer les stops, puis s'est repris, montrant que la baisse était fausse.",
        "de": "Der Preis fiel stark, um Stops auszulösen, erholte sich dann – zeigt, dass der Fall falsch war.",
        "it": "Il prezzo è sceso forte per far scattare gli stop, poi si è ripreso, mostrando che il calo era falso.",
        "ru": "Цена резко упала, чтобы выбить стопы, затем восстановилась, показывая ложность падения.",
        "ja": "価格はストップを取るために急落したが回復し、下落が偽物だったことを示す。",
        "zh": "价格急跌以触发止损，然后反弹，表明下跌是虚假的。",
        "hi": "कीमत स्टॉप हिट करने के लिए तेजी से गिरी, फिर वापस आई, दिखाता है कि गिरावट झूठी थी।"
    },
    "TSO": {
        "pt": "O preço testou o suporte com alto volume, mas não conseguiu romper, sinal de força.",
        "en": "Price tested support with high volume but failed to break, a sign of strength.",
        "es": "El precio probó el soporte con alto volumen pero no logró romper, señal de fuerza.",
        "fr": "Le prix a testé le support avec un volume élevé mais n'a pas réussi à casser, signe de force.",
        "de": "Der Preis testete die Unterstützung mit hohem Volumen, konnte aber nicht brechen – ein Zeichen der Stärke.",
        "it": "Il prezzo ha testato il supporto con alto volume ma non è riuscito a rompere, segno di forza.",
        "ru": "Цена протестировала поддержку с высоким объемом, но не смогла пробить – признак силы.",
        "ja": "価格は高ボリュームでサポートをテストしたが割れず、強さのサイン。",
        "zh": "价格在高成交量下测试支撑但未能跌破，表明强势。",
        "hi": "कीमत ने उच्च वॉल्यूम के साथ समर्थन का परीक्षण किया लेकिन तोड़ नहीं सकी, ताकत का संकेत।"
    },
    "UT": {
        "pt": "O preço tentou subir acima da resistência, mas foi rejeitado, mostrando pressão de venda.",
        "en": "Price tried to rise above resistance but was rejected, showing selling pressure.",
        "es": "El precio intentó subir por encima de la resistencia pero fue rechazado, mostrando presión de venta.",
        "fr": "Le prix a tenté de monter au-dessus de la résistance mais a été rejeté, montrant une pression de vente.",
        "de": "Der Preis versuchte, über den Widerstand zu steigen, wurde aber abgewiesen – Verkaufsdruck.",
        "it": "Il prezzo ha tentato di salire sopra la resistenza ma è stato respinto, mostrando pressione di vendita.",
        "ru": "Цена попыталась подняться выше сопротивления, но была отклонена, показывая давление продавцов.",
        "ja": "価格はレジスタンスを上抜けようとしたが跳ね返され、売り圧力を示す。",
        "zh": "价格试图突破阻力但被拒绝，表明卖压。",
        "hi": "कीमत ने प्रतिरोध से ऊपर जाने की कोशिश की लेकिन अस्वीकार कर दी गई, बिक्री दबाव दिखाता है।"
    },
    "UPTHRUST": {
        "pt": "O preço rompeu a resistência, mas voltou para baixo, indicando fraqueza dos compradores.",
        "en": "Price broke resistance but fell back, indicating buyer weakness.",
        "es": "El precio rompió la resistencia pero volvió a bajar, indicando debilidad de los compradores.",
        "fr": "Le prix a cassé la résistance mais est retombé, indiquant une faiblesse des acheteurs.",
        "de": "Der Preis durchbrach den Widerstand, fiel aber zurück – Schwäche der Käufer.",
        "it": "Il prezzo ha rotto la resistenza ma è risceso, indicando debolezza degli acquirenti.",
        "ru": "Цена пробила сопротивление, но упала обратно, указывая на слабость покупателей.",
        "ja": "価格はレジスタンスを抜けたが戻り、買い手の弱さを示す。",
        "zh": "价格突破阻力但回落，表明买方疲软。",
        "hi": "कीमत ने प्रतिरोध तोड़ा लेकिन वापस गिर गई, खरीदारों की कमजोरी दिखाता है।"
    },
    "UTAD": {
        "pt": "O preço testou a resistência com volume alto e caiu, sinal de que a alta foi falsa.",
        "en": "Price tested resistance with high volume and fell, signaling the rally was false.",
        "es": "El precio probó la resistencia con alto volumen y cayó, señal de que el repunte fue falso.",
        "fr": "Le prix a testé la résistance avec un volume élevé et a chuté, signalant une hausse fausse.",
        "de": "Der Preis testete den Widerstand mit hohem Volumen und fiel – Zeichen für falsche Rallye.",
        "it": "Il prezzo ha testato la resistenza con alto volume ed è caduto, segnale di un rialzo falso.",
        "ru": "Цена протестировала сопротивление с высоким объемом и упала, сигнализируя о ложном росте.",
        "ja": "価格は高ボリュームでレジスタンスをテストし下落、上昇が偽物だったサイン。",
        "zh": "价格在高成交量下测试阻力然后下跌，表明反弹是虚假的。",
        "hi": "कीमत ने उच्च वॉल्यूम के साथ प्रतिरोध का परीक्षण किया और गिर गई, संकेत है कि रैली झूठी थी।"
    }
}

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
    "book_indisponivel": "Livro de ofertas indisponível no momento. O escore segue válido.",
    "profundidade": "PROFUNDIDADE AGREGADA (±1,5% do mid)",
    "wyckoff_titulo": "🧭 Estrutura Wyckoff",
    "wyckoff_sem_evento": "Nenhum evento de Fase C/D identificado na janela recente.",
    "wyckoff_range": "Trading Range",
    "wyckoff_evento": "Evento",
    "wyckoff_fase": "Fase",
    "wyckoff_teste": "Teste Secundário",
    "wyckoff_sos": "SOS / SOW",
    "wyckoff_lps": "LPS / LPSY",
    "confirmado": "confirmado",
    "nao_confirmado": "não confirmado",
    "alerta_muralha": "⚠️ Muralha de liquidez contrária à frente do preço.",
    "valor_memorizado": "último valor conhecido",
    "fontes_book": "Corretoras no book",
    "intervalos": {
        "1 Minuto": "1m", "5 Minutos": "5m", "15 Minutos": "15m", "30 Minutos": "30m",
        "1 Hora": "1h", "4 Horas": "4h", "1 Dia": "1d", "1 Semana": "1w"
    },
    "medias_moveis": "📊 Médias Móveis (SMA)",
    "acima": "acima",
    "abaixo": "abaixo",
    "preco_atual": "Preço atual",
    "monitorando": "📡 Monitorando os 50 ativos mais líquidos (sem stablecoins/derivativos)",
    "top_ativos": "🏆 Top 50 por Volume (24h) - sem stablecoins/derivativos",
    "horario_brasilia": "🕒 Horário de Brasília (UTC-3)",
    "telegram_config": "📲 Configuração do Telegram",
    "telegram_status": "Status da conexão:",
    "testar_conexao": "🔍 Testar Conexão com Telegram",
    "conectado": "✅ Conexão com Telegram estabelecida!",
    "nao_configurado": "⚠️ Token ou Chat ID não configurados. Edite o código.",
    "erro_chat": "⚠️ Não foi possível enviar mensagem de boas-vindas. Envie /start para o bot manualmente.",
    "enviando_teste": "Enviando mensagem de teste...",
    "ultimo_envio": "Último envio:"
}

_TRADUCOES = {
    "Português (BR)": _TEXTOS_BASE_PT_BR,
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
        "book_indisponivel": "Order book unavailable right now. The score remains valid.",
        "profundidade": "AGGREGATED DEPTH (±1.5% of mid)",
        "wyckoff_titulo": "🧭 Wyckoff Structure",
        "wyckoff_sem_evento": "No Phase C/D event found in the recent window.",
        "wyckoff_range": "Trading Range",
        "wyckoff_evento": "Event",
        "wyckoff_fase": "Phase",
        "wyckoff_teste": "Secondary Test",
        "wyckoff_sos": "SOS / SOW",
        "wyckoff_lps": "LPS / LPSY",
        "confirmado": "confirmed",
        "nao_confirmado": "not confirmed",
        "alerta_muralha": "⚠️ Significant opposing liquidity wall ahead of price.",
        "valor_memorizado": "last known value",
        "fontes_book": "Exchanges in book",
        "intervalos": {
            "1 Minute": "1m", "5 Minutes": "5m", "15 Minutes": "15m", "30 Minutes": "30m",
            "1 Hour": "1h", "4 Hours": "4h", "1 Day": "1d", "1 Week": "1w"
        },
        "medias_moveis": "📊 Moving Averages (SMA)",
        "acima": "above",
        "abaixo": "below",
        "preco_atual": "Current price",
        "monitorando": "📡 Monitoring the top 50 most liquid assets (no stablecoins/derivatives)",
        "top_ativos": "🏆 Top 50 by Volume (24h) - no stablecoins/derivatives",
        "horario_brasilia": "🕒 Brasília Time (UTC-3)",
        "telegram_config": "📲 Telegram Configuration",
        "telegram_status": "Connection status:",
        "testar_conexao": "🔍 Test Telegram Connection",
        "conectado": "✅ Telegram connection established!",
        "nao_configurado": "⚠️ Token or Chat ID not configured. Edit the code.",
        "erro_chat": "⚠️ Could not send welcome message. Send /start to the bot manually.",
        "enviando_teste": "Sending test message...",
        "ultimo_envio": "Last send:"
    }
}

def construir_dicionario_com_fallback(traducoes: Dict, idioma_padrao: str = IDIOMA_PADRAO) -> Dict:
    base = traducoes[idioma_padrao]
    dicionario_final = {}
    for idioma, valores in traducoes.items():
        completo = dict(base)
        completo.update(valores)
        dicionario_final[idioma] = completo
    return dicionario_final

DICIONARIO_LINGUAS = construir_dicionario_com_fallback(_TRADUCOES)

def obter_resumo_wyckoff(evento_tipo: str, idioma: str) -> str:
    chave_idioma = {
        "Português (BR)": "pt",
        "English (EN)": "en",
        "Español": "es",
        "Français": "fr",
        "Deutsch": "de",
        "Italiano": "it",
        "Русский": "ru",
        "日本語": "ja",
        "中文 (简体)": "zh",
        "हिन्दी": "hi"
    }.get(idioma, "pt")
    return RESUMOS_WYCKOFF.get(evento_tipo, {}).get(chave_idioma, "Evento Wyckoff detectado")

def horario_brasilia() -> datetime:
    return datetime.now(ZoneInfo("America/Sao_Paulo"))

def formatar_horario_brasilia(dt: datetime) -> str:
    return dt.strftime("%d/%m/%Y %H:%M:%S")

def enviar_sinal_telegram(mensagem: str) -> Tuple[bool, str]:
    if TELEGRAM_TOKEN == "SEU_TOKEN_AQUI" or TELEGRAM_CHAT_ID == "SEU_CHAT_ID_AQUI":
        return False, "⚠️ Configuração do Telegram não realizada."
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "HTML"}
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return True, "✅ Enviado com sucesso!"
        else:
            error_data = response.json()
            error_desc = error_data.get("description", "Erro desconhecido")
            if "chat not found" in error_desc.lower():
                return False, "❌ Chat não encontrado! Envie uma mensagem para o bot e tente novamente."
            return False, f"❌ Erro {response.status_code}: {error_desc}"
    except Exception:
        return False, "❌ Falha na conexão."

def testar_conexao_telegram() -> Tuple[bool, str]:
    msg = "🔍 Teste de conexão do BRICSVAULT. Monitoramento automático ativo!"
    return enviar_sinal_telegram(msg)

# -----------------------------------------------------------------------------
# FUNÇÕES DE FORMATAÇÃO
# -----------------------------------------------------------------------------
def formatar_preco(valor: Optional[float], prefixo: str = "$ ") -> str:
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
# MEMÓRIA DE SESSÃO
# -----------------------------------------------------------------------------
def valor_com_memoria(chave: str, valor: Optional[float]) -> Tuple[Optional[float], bool]:
    memoria = st.session_state.setdefault("_memoria_metricas", {})
    if valor is not None and not (isinstance(valor, float) and math.isnan(valor)) and valor > 0:
        memoria[chave] = float(valor)
        return float(valor), False
    if chave in memoria:
        return memoria[chave], True
    return None, False

# -----------------------------------------------------------------------------
# GERENCIADOR DE EXCHANGES
# -----------------------------------------------------------------------------
PRIORITY_EXCHANGES = ["Gate.io", "Kraken", "MEXC", "KuCoin"]
SIGLAS_EXCHANGES = {"Gate.io": "GATE", "Kraken": "KRK", "MEXC": "MEXC", "KuCoin": "KUC"}
VERSAO_MANAGER = 2

class ExchangeManager:
    EXCHANGES = {
        "Gate.io": {"class": ccxt.gate, "config": {"enableRateLimit": True, "timeout": EXCHANGE_TIMEOUT_MS, "options": {"defaultType": "spot"}}},
        "Kraken": {"class": ccxt.kraken, "config": {"enableRateLimit": True, "timeout": EXCHANGE_TIMEOUT_MS}},
        "MEXC": {"class": ccxt.mexc, "config": {"enableRateLimit": True, "timeout": EXCHANGE_TIMEOUT_MS}},
        "KuCoin": {"class": ccxt.kucoin, "config": {"enableRateLimit": True, "timeout": EXCHANGE_TIMEOUT_MS}}
    }
    def __init__(self):
        self.clients = {}
        self._init_clients()
    def _init_clients(self):
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

# ==========================================================================
# FUNÇÃO PARA OBTER OS TOP 50 ATIVOS POR VOLUME (FILTRANDO)
# ==========================================================================
@st.cache_data(ttl=TTL_TOP_ATIVOS, show_spinner=False)
def obter_top_ativos_por_volume(quantidade: int = TOP_ATIVOS_QTD) -> List[str]:
    manager = obter_exchange_manager()
    client = manager.get_client("Gate.io")
    padrao = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT",
              "ADA/USDT", "DOT/USDT", "AVAX/USDT", "MATIC/USDT", "LINK/USDT"]
    # Filtra o padrão
    padrao_filtrado = [p for p in padrao if is_valid_spot_pair(p)]
    if not client:
        return padrao_filtrado[:quantidade]
    try:
        tickers = client.fetch_tickers()
        usdt_pairs = {symbol: ticker for symbol, ticker in tickers.items() if symbol.endswith('/USDT')}
        # Filtra validando spot pair
        usdt_pairs = {symbol: ticker for symbol, ticker in usdt_pairs.items() if is_valid_spot_pair(symbol)}
        if not usdt_pairs:
            return padrao_filtrado[:quantidade]
        sorted_pairs = sorted(usdt_pairs.items(), key=lambda x: x[1].get('quoteVolume', 0) or 0, reverse=True)
        top_symbols = [symbol for symbol, _ in sorted_pairs[:quantidade]]
        return top_symbols if top_symbols else padrao_filtrado[:quantidade]
    except Exception:
        return padrao_filtrado[:quantidade]

# -----------------------------------------------------------------------------
# FUNÇÕES DE MERCADO (REST e OHLCV)
# -----------------------------------------------------------------------------
def _obter_dados_24h_rest_direto(exchange_name: str, simbolo: str) -> Optional[Dict]:
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

def carregar_dados_interface(simbolo_id: str, timeframe_selecionado: str) -> Optional[pd.DataFrame]:
    @st.cache_data(ttl=TTL_DADOS_INTERFACE_SEGUNDOS, show_spinner=False)
    def _carregar(simbolo, timeframe):
        return _carregar_dados_interno(simbolo, timeframe)
    return _carregar(simbolo_id, timeframe_selecionado)

def carregar_dados_monitoramento(simbolo_id: str, timeframe_selecionado: str) -> Optional[pd.DataFrame]:
    @st.cache_data(ttl=TTL_DADOS_LIVE_SEGUNDOS, show_spinner=False)
    def _carregar(simbolo, timeframe):
        return _carregar_dados_interno(simbolo, timeframe)
    return _carregar(simbolo_id, timeframe_selecionado)

def _carregar_dados_interno(simbolo_id: str, timeframe_selecionado: str) -> Optional[pd.DataFrame]:
    manager = obter_exchange_manager()
    for exchange_name in PRIORITY_EXCHANGES:
        try:
            client = manager.get_client(exchange_name)
            if not client:
                continue
            velas = client.fetch_ohlcv(simbolo_id, timeframe=timeframe_selecionado, limit=VELAS_TOTAL)
            if velas and len(velas) >= PERIODO_AQUECIMENTO + 50:
                df = pd.DataFrame(velas, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
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
                df['SMA_8'] = df['close'].rolling(8).mean()
                df['SMA_21'] = df['close'].rolling(21).mean()
                df['SMA_50'] = df['close'].rolling(50).mean()
                df['SMA_200'] = df['close'].rolling(200).mean()
                df['VOL_MA_20'] = df['volume'].rolling(20).mean()
                df['OBV'] = calcular_obv(df)
                df['OBV_MA_20'] = df['OBV'].rolling(20).mean()
                df['SSL_Baseline'] = df['SSL_Baseline'].ffill()
                df['ATR_Stop'] = df['ATR_Stop'].replace(0, np.nan).ffill()
                return df.dropna(subset=['close']).reset_index(drop=True)
        except Exception:
            continue
    return None

# -----------------------------------------------------------------------------
# INDICADORES TÉCNICOS (funções mantidas)
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
    tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
    atr = tr.ewm(span=periodo, adjust=False).mean()
    atr_stop = np.zeros(len(df))
    tendencia = np.zeros(len(df), dtype=int)
    close_arr = close.values
    atr_arr = atr.values
    if len(df) > 0:
        atr_stop[0] = close_arr[0] - (atr_arr[0] * multiplicador) if not np.isnan(atr_arr[0]) else close_arr[0]
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
        'fib_0': maxima, 'fib_236': maxima - 0.236 * diff,
        'fib_382': maxima - 0.382 * diff, 'fib_500': maxima - 0.500 * diff,
        'fib_618': maxima - 0.618 * diff, 'fib_786': maxima - 0.786 * diff,
        'fib_100': minima
    }

# -----------------------------------------------------------------------------
# LIVRO DE OFERTAS AGREGADO
# -----------------------------------------------------------------------------
@st.cache_data(ttl=TTL_BOOK_SEGUNDOS, show_spinner=False)
def obter_book_agregado(simbolo: str, faixa: float = FAIXA_BOOK) -> Optional[Dict]:
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
        itens = [{"preco": float(p), "usdt": float(v["usdt"]), "base": float(v["base"]), "fontes": sorted(v["fontes"])}
                 for p, v in baldes.items()]
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
    "SPRING": 2.0, "SHAKEOUT": 1.5, "TSO": 1.0, "UT": 2.0, "UPTHRUST": 1.5, "UTAD": 1.0
}
_BUFFER_STOP_EVENTO = {
    "SPRING": 0.005, "SHAKEOUT": 0.015, "TSO": 0.035, "UT": 0.005, "UPTHRUST": 0.015, "UTAD": 0.035
}

def detectar_wyckoff(df: pd.DataFrame, janela_base: int = JANELA_BASE_WYCKOFF,
                     janela_evento: int = JANELA_EVENTO_WYCKOFF) -> Optional[Dict]:
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
        return {"range_valido": False, "suporte": suporte, "resistencia": resistencia,
                "meio": meio, "evento": None, "pontos": 0.0, "direcao": 0}
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
            evento = {"tipo": tipo, "direcao": 1, "idx": i, "extremo": float(v['low']),
                      "penetracao": pen, "vol_rel": vol_rel}
        if float(v['high']) > resistencia and float(v['close']) < resistencia:
            pen = (float(v['high']) - resistencia) / resistencia
            if pen >= 0.03 or vol_rel >= 2.0:
                tipo = "UTAD"
            elif pen >= 0.01:
                tipo = "UPTHRUST"
            else:
                tipo = "UT"
            evento = {"tipo": tipo, "direcao": -1, "idx": i, "extremo": float(v['high']),
                      "penetracao": pen, "vol_rel": vol_rel}
        if evento is not None:
            break
    if evento is None:
        return {"range_valido": True, "suporte": suporte, "resistencia": resistencia,
                "meio": meio, "evento": None, "pontos": 0.0, "direcao": 0}
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
        "range_valido": True, "suporte": suporte, "resistencia": resistencia, "meio": meio,
        "altura": altura, "evento": evento, "teste_ok": teste_ok, "sos": sos, "lps": lps,
        "fase": fase, "pontos": float(pontos), "direcao": evento["direcao"],
        "stop_estrutural": float(stop_estrutural)
    }

# -----------------------------------------------------------------------------
# ANÁLISE DE CONFLUÊNCIA
# -----------------------------------------------------------------------------
PESOS = {
    "rsi": 2.0, "stoch": 1.5, "macd": 2.0, "mfi": 1.0, "ssl": 1.0, "atr": 1.0,
    "ppo": 1.5, "fib": 2.0, "book": 2.0, "wyckoff": PONTOS_MAX_WYCKOFF,
    "ma_curta": 1.5, "ma_longa": 2.0, "volume": 1.0, "obv": 1.0
}
MAXIMO_POSSIVEL = sum(PESOS.values())

def analisar_confluencia(df_completo: pd.DataFrame, txt: Dict,
                         book: Optional[Dict], wyk: Optional[Dict]) -> Dict:
    df_analise = df_completo.iloc[PERIODO_AQUECIMENTO:].copy()
    if df_analise.empty:
        return {"recomendacao": txt["neutro"], "cor": "#ffcc00", "contexto": txt["ctx_neutro"],
                "alta": 0.0, "baixa": 0.0, "liquido": 0.0, "direcao": "neutro", "bloqueado": False}
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

    return {"recomendacao": recomendacao, "cor": cor, "contexto": contexto,
            "alta": alta, "baixa": baixa, "liquido": liquido,
            "direcao": direcao, "bloqueado": bloqueado}

# -----------------------------------------------------------------------------
# PLANO DE TRADE (stop, alvos)
# -----------------------------------------------------------------------------
def escolher_stop(direcao: str, entrada: float, atr: float,
                  atr_stop_val: float, wyk: Optional[Dict],
                  book: Optional[Dict]) -> Tuple[float, str]:
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
        for pct in (0.03, 0.05, 0.08, 0.13, 0.21, 0.34, 0.55, 0.89):
            candidatos.add(entrada * (1 + pct))
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
        for pct in (0.03, 0.05, 0.08, 0.13, 0.21, 0.34, 0.55):
            candidatos.add(entrada * (1 - pct))
        niveis = sorted((x for x in candidatos if 0 < x < entrada * 0.996), reverse=True)
    finais = []
    for x in niveis:
        if not finais or abs(x / finais[-1] - 1) > 0.006:
            finais.append(float(x))
            if len(finais) == n:
                break
    if not finais:
        if direcao == "long":
            for pct in (0.03, 0.05, 0.08, 0.13, 0.21, 0.34, 0.55):
                finais.append(entrada * (1 + pct))
        else:
            for pct in (0.03, 0.05, 0.08, 0.13, 0.21, 0.34, 0.55):
                finais.append(entrada * (1 - pct))
        finais = sorted(finais) if direcao == "long" else sorted(finais, reverse=True)
    return finais[:n]

def lucro_percentual(direcao: str, entrada: float, alvo: float) -> float:
    if entrada <= 0:
        return 0.0
    if direcao == "long":
        return (alvo / entrada - 1) * 100
    return (entrada / alvo - 1) * 100

# ==========================================================================
# FUNÇÃO DE MONITORAMENTO AUTOMÁTICO (COM CONTROLE DE ESTADO)
# ==========================================================================
def monitorar_ativos(ativos: List[str], timeframe: str, txt: Dict) -> None:
    if not ativos:
        return

    if "_estado_ativo" not in st.session_state:
        st.session_state["_estado_ativo"] = {}
    if "_sinais_acumulados" not in st.session_state:
        st.session_state["_sinais_acumulados"] = []
    if "_ultimo_envio" not in st.session_state:
        st.session_state["_ultimo_envio"] = horario_brasilia() - timedelta(seconds=INTERVALO_ENVIO_SINAIS)

    agora = horario_brasilia()
    sinais = []

    for simbolo in ativos:
        try:
            df = carregar_dados_monitoramento(simbolo, timeframe)
            if df is None or df.empty:
                continue

            book = obter_book_agregado(simbolo)
            wyk = detectar_wyckoff(df.iloc[PERIODO_AQUECIMENTO:].reset_index(drop=True))
            res = analisar_confluencia(df, txt, book, wyk)
            preco_atual = float(df.iloc[-1]['close'])

            estado_atual = st.session_state["_estado_ativo"].get(simbolo, "neutro")

            if res["direcao"] in ("long", "short") and estado_atual == "neutro":
                atr_atual = float(df.iloc[-1]['ATR']) if not math.isnan(df.iloc[-1]['ATR']) else preco_atual * 0.01
                stop, base_stop = escolher_stop(res["direcao"], preco_atual, atr_atual,
                                                df.iloc[-1]['ATR_Stop'], wyk, book)
                alvos = construir_alvos(res["direcao"], preco_atual, atr_atual, wyk, book)

                st.session_state["_estado_ativo"][simbolo] = res["direcao"]

                sinais.append({
                    "simbolo": simbolo,
                    "direcao": res["direcao"],
                    "preco": preco_atual,
                    "liquido": res["liquido"],
                    "contexto": res["contexto"],
                    "stop": stop,
                    "base_stop": base_stop,
                    "alvos": alvos,
                })

            elif res["direcao"] == "neutro" and estado_atual != "neutro":
                st.session_state["_estado_ativo"][simbolo] = "neutro"

        except Exception:
            continue

    if sinais:
        st.session_state["_sinais_acumulados"].extend(sinais)

    if (agora - st.session_state["_ultimo_envio"]).total_seconds() >= INTERVALO_ENVIO_SINAIS:
        if st.session_state["_sinais_acumulados"]:
            st.session_state["_sinais_acumulados"].sort(key=lambda x: abs(x["liquido"]), reverse=True)
            top_sinais = st.session_state["_sinais_acumulados"][:MAX_SINAIS_POR_ENVIO]

            if top_sinais:
                mensagem = f"<b>🚨 BRICSVAULT - TOP {len(top_sinais)} SINAIS DO PERÍODO</b>\n\n"
                for idx, sinal in enumerate(top_sinais, start=1):
                    lado = "🟢 COMPRA (LONG)" if sinal["direcao"] == "long" else "🔴 VENDA (SHORT)"
                    mensagem += (
                        f"<b>{idx}.</b> 📌 <b>{sinal['simbolo']}</b>\n"
                        f"   📊 {lado}\n"
                        f"   💰 Preço: {formatar_preco(sinal['preco'])}\n"
                        f"   📈 Escore: {sinal['liquido']:.1f}/100\n"
                        f"   📋 Contexto: {sinal['contexto']}\n"
                        f"   🛑 Stop: {formatar_preco(sinal['stop'])}\n"
                    )
                    if sinal["alvos"]:
                        mensagem += "   🎯 Alvos:\n"
                        for i, alvo in enumerate(sinal["alvos"], start=1):
                            pct = lucro_percentual(sinal["direcao"], sinal["preco"], alvo)
                            mensagem += f"      {i}) {formatar_preco(alvo)} ({pct:+.2f}%)\n"
                    mensagem += "\n"

                mensagem += f"🕒 {formatar_horario_brasilia(agora)} (Horário de Brasília)"

                enviar_sinal_telegram(mensagem)

            st.session_state["_sinais_acumulados"] = []
            st.session_state["_ultimo_envio"] = agora

# -----------------------------------------------------------------------------
# RENDERIZAÇÃO (UI)
# -----------------------------------------------------------------------------
def renderizar_card_plano(txt: Dict, simbolo_id: str, direcao: str,
                          entrada: float, stop: float, alvos: List[float],
                          base_stop: str, preco_atual: float) -> None:
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
    grade = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px;">' + "".join(linhas) + "</div>"
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

def renderizar_wyckoff(txt: Dict, wyk: Optional[Dict], idioma: str) -> None:
    if not wyk or not wyk.get("evento"):
        st.info(txt["wyckoff_sem_evento"])
        return
    ev = wyk["evento"]
    cor = "#22c55e" if wyk["direcao"] == 1 else "#f43f5e"
    resumo = obter_resumo_wyckoff(ev["tipo"], idioma)
    st.markdown(
        f"""
        <div style="background:#0b0f19;border:1px solid #1e293b;border-radius:18px;padding:20px;
            font-family:ui-monospace,monospace;">
            <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;">
                <div>
                    <div style="color:#64748b;font-size:0.75em;letter-spacing:1px;">{txt["wyckoff_evento"]}</div>
                    <div style="color:{cor};font-size:1.4em;font-weight:800;">
                        {ev["tipo"]}
                        <span style="font-size:0.55em;font-weight:400;color:#94a3b8;margin-left:12px;">
                            — {resumo}
                        </span>
                    </div>
                </div>
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

# ==========================================================================
# FUNÇÕES AUXILIARES
# ==========================================================================
@st.cache_data(ttl=600, show_spinner=False)
def obter_dados_24h(simbolo: str) -> Optional[Dict]:
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
    for exchange_name in PRIORITY_EXCHANGES:
        resultado = _obter_dados_24h_rest_direto(exchange_name, simbolo)
        if resultado and resultado.get("last"):
            resultado["fonte"] = exchange_name
            return resultado
    return None

def resolver_volume_usdt(dados_24h: Optional[Dict], preco_atual: float,
                         dados_gecko: Optional[Dict]) -> Optional[float]:
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

@st.cache_data(ttl=3600, show_spinner=False)
def obter_id_coingecko(simbolo: str) -> Optional[str]:
    try:
        resp = requests.get("https://api.coingecko.com/api/v3/search", params={"query": simbolo},
                            headers={"Accept": "application/json"}, timeout=10)
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
        resp = requests.get("https://api.coingecko.com/api/v3/coins/markets",
                            params={"vs_currency": "usd", "ids": coin_id, "order": "market_cap_desc",
                                    "per_page": 1, "page": 1, "sparkline": "false"},
                            headers={"Accept": "application/json"}, timeout=10)
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
        candidatos = [c for c in resp.json() if c.get("symbol", "").upper() == alvo and c.get("is_active")]
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
        resp = requests.get(f"https://api.coinpaprika.com/v1/tickers/{coin_id}", timeout=12)
        if resp.status_code != 200:
            return None
        quotes = resp.json().get("quotes", {}).get("USD", {})
        mc = quotes.get("market_cap")
        vol = quotes.get("volume_24h")
        return {"market_cap": float(mc) if mc else None, "total_volume": float(vol) if vol else None,
                "circulating_supply": None, "current_price": None}
    except Exception:
        return None

def resolver_market_cap(simbolo_base: str, preco_atual: float,
                        dados_gecko: Optional[Dict], dados_paprika: Optional[Dict]) -> Optional[float]:
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

@st.cache_data(ttl=TTL_MERCADOS_SEGUNDOS, show_spinner=False)
def obter_todos_pares_usdt() -> List[str]:
    manager = obter_exchange_manager()
    client = manager.get_client("Gate.io")
    padrao = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "BNB/USDT"]
    if not client:
        return [p for p in padrao if is_valid_spot_pair(p)]
    try:
        markets = client.load_markets()
        pairs = [s for s in markets.keys() if s.endswith('/USDT')]
        pairs = [p for p in pairs if is_valid_spot_pair(p)]
        return sorted(pairs) if pairs else [p for p in padrao if is_valid_spot_pair(p)]
    except Exception:
        return [p for p in padrao if is_valid_spot_pair(p)]

# ==========================================================================
# PAINEL PRINCIPAL
# ==========================================================================
@st.fragment(run_every=0)
def painel_principal(simbolo_selecionado: str, timeframe_interface: str, txt: Dict,
                     modo_vivo: bool, intervalo_refresh: int, idioma_selecionado: str) -> None:
    if modo_vivo:
        top_ativos = obter_top_ativos_por_volume(TOP_ATIVOS_QTD)
        with st.spinner("🔄 Analisando os 50 ativos mais líquidos (sem stablecoins/derivativos)..."):
            monitorar_ativos(top_ativos, TIMEFRAME_MONITORAMENTO, txt)

    df_dados = carregar_dados_interface(simbolo_selecionado, timeframe_interface)
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
    simbolo_base = simbolo_selecionado.split('/')[0]

    book = obter_book_agregado(simbolo_selecionado)
    wyk = detectar_wyckoff(df_analise.reset_index(drop=True))
    dados_24h = obter_dados_24h(simbolo_selecionado)
    variacao_24h = dados_24h.get("change") if dados_24h else None
    dados_gecko = obter_dados_coingecko(simbolo_base)
    dados_paprika = None
    if not dados_gecko or not dados_gecko.get("market_cap"):
        dados_paprika = obter_dados_coinpaprika(simbolo_base)

    volume_bruto = resolver_volume_usdt(dados_24h, preco_atual, dados_gecko)
    volume_usdt, volume_da_memoria = valor_com_memoria(f"vol::{simbolo_selecionado}", volume_bruto)
    mc_bruto = resolver_market_cap(simbolo_base, preco_atual, dados_gecko, dados_paprika)
    market_cap, mc_da_memoria = valor_com_memoria(f"mc::{simbolo_selecionado}", mc_bruto)

    res = analisar_confluencia(df_dados, txt, book, wyk)

    # Cabeçalho
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

    # Métricas
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric(f"{simbolo_base} | {txt['preco_spot']}", formatar_preco(preco_atual))
    m2.metric(txt["variacao_24h"], f"{variacao_24h:+.2f}%" if variacao_24h is not None else "---")
    m3.metric(txt["volume_24h"], formatar_usdt_compacto(volume_usdt),
              delta=txt["valor_memorizado"] if volume_da_memoria else None, delta_color="off")
    m4.metric(txt["market_cap"], formatar_usdt_compacto(market_cap) if market_cap else txt["marketcap_nao_disponivel"],
              delta=txt["valor_memorizado"] if mc_da_memoria else None, delta_color="off")
    m5.metric(txt["pontos_compra"], f"{res['alta']:.1f}")
    m6.metric(txt["pontos_venda"], f"{res['baixa']:.1f}")

    # Médias Móveis
    st.markdown(f"### {txt['medias_moveis']}")
    sma8 = ultimo['SMA_8']
    sma21 = ultimo['SMA_21']
    sma50 = ultimo['SMA_50']
    sma200 = ultimo['SMA_200']

    def _ma_label(valor, nome):
        if math.isnan(valor):
            return f"{nome}: ---"
        status = txt["acima"] if preco_atual > valor else txt["abaixo"]
        cor = "#22c55e" if preco_atual > valor else "#f43f5e"
        return f"**{nome}** {formatar_preco(valor, '')}  <span style='color:{cor};font-size:0.9em;'>({status})</span>"

    cols_ma = st.columns(4)
    with cols_ma[0]:
        st.markdown(_ma_label(sma8, "SMA 8"), unsafe_allow_html=True)
    with cols_ma[1]:
        st.markdown(_ma_label(sma21, "SMA 21"), unsafe_allow_html=True)
    with cols_ma[2]:
        st.markdown(_ma_label(sma50, "SMA 50"), unsafe_allow_html=True)
    with cols_ma[3]:
        st.markdown(_ma_label(sma200, "SMA 200"), unsafe_allow_html=True)

    # Outros indicadores
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

    # Wyckoff
    st.markdown(f"### {txt['wyckoff_titulo']}")
    renderizar_wyckoff(txt, wyk, idioma_selecionado)

    # Book
    st.markdown(f"### {txt['book_titulo']}")
    renderizar_book(txt, book)

    # Plano de trade
    stop = None
    alvos = []
    base_stop = ""
    if res["direcao"] in ("long", "short"):
        stop, base_stop = escolher_stop(res["direcao"], preco_atual, atr_atual,
                                        ultimo['ATR_Stop'], wyk, book)
        alvos = construir_alvos(res["direcao"], preco_atual, atr_atual, wyk, book)
        if alvos:
            st.markdown(f"### {txt['plano_trade']}")
            renderizar_card_plano(txt, simbolo_selecionado, res["direcao"], preco_atual,
                                  stop, alvos, base_stop, preco_atual)

    # Rodapé
    agora_br = horario_brasilia()
    hora_br = formatar_horario_brasilia(agora_br)
    prefixo = "🟢" if modo_vivo else "⏸"
    extra = f" | {txt['proximo_refresh']} {intervalo_refresh} {txt['segundos']}" if modo_vivo else ""
    info_monitoramento = f" | {txt['monitorando']}" if modo_vivo else ""
    st.info(
        f"{prefixo} {txt['ultima_atualizacao']}: {hora_br} (Brasília){extra}{info_monitoramento} | "
        f"{txt['aviso_aquecimento']}: {PERIODO_AQUECIMENTO} | "
        f"Velas analisadas: {len(df_analise)}"
    )

# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
def main() -> None:
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

    # Config Telegram
    with st.sidebar.expander("📲 Configuração do Telegram", expanded=False):
        st.write("**Status da conexão:**")
        if TELEGRAM_TOKEN == "SEU_TOKEN_AQUI" or TELEGRAM_CHAT_ID == "SEU_CHAT_ID_AQUI":
            st.error("⚠️ Token ou Chat ID não configurados. Edite o código.")
        else:
            if st.button("🔍 Testar Conexão com Telegram", use_container_width=True):
                with st.spinner("Enviando mensagem de teste..."):
                    sucesso, msg = testar_conexao_telegram()
                    if sucesso:
                        st.success(msg)
                    else:
                        st.error(msg)
            if not st.session_state.get("_telegram_initialized", False):
                msg_welcome = "🤖 *BRICSVAULT conectado!*\n\nMonitorando top 50 ativos (sem stablecoins/derivativos)."
                sucesso, _ = enviar_sinal_telegram(msg_welcome)
                if sucesso:
                    st.session_state["_telegram_initialized"] = True
                    st.success("✅ Conexão com Telegram estabelecida! Você receberá os sinais aqui.")
                else:
                    st.warning("⚠️ Não foi possível enviar mensagem de boas-vindas. Envie /start para o bot manualmente.")

    # Seleção de ativo
    todos_ativos = obter_todos_pares_usdt()
    if not todos_ativos:
        st.warning("Nenhum par spot válido encontrado. Verifique sua conexão com a exchange.")
        return
    indice_padrao = todos_ativos.index("SOL/USDT") if "SOL/USDT" in todos_ativos else 0
    simbolo_selecionado = st.sidebar.selectbox(
        txt["selecione_cripto"],
        todos_ativos,
        index=indice_padrao
    )

    intervalos = txt["intervalos"]
    valores_intervalos = list(intervalos.values())
    indice_padrao_timeframe = valores_intervalos.index("4h") if "4h" in valores_intervalos else 0
    intervalo_escolhido = st.sidebar.selectbox(
        txt["tempo_grafico"],
        list(intervalos.keys()),
        index=indice_padrao_timeframe
    )
    timeframe_interface = intervalos[intervalo_escolhido]

    st.sidebar.markdown("---")
    modo_vivo = st.sidebar.toggle(txt["modo_vivo"], value=False)
    intervalo_refresh = st.sidebar.slider(
        txt["intervalo_refresh"], min_value=20, max_value=120, value=30
    )

    # Top 50
    with st.sidebar.expander(txt["top_ativos"], expanded=False):
        top_ativos = obter_top_ativos_por_volume(TOP_ATIVOS_QTD)
        for i, ativo in enumerate(top_ativos, start=1):
            st.write(f"{i}. {ativo}")

    painel_principal(simbolo_selecionado, timeframe_interface, txt, modo_vivo, intervalo_refresh, idioma_selecionado)

if __name__ == "__main__":
    main()
