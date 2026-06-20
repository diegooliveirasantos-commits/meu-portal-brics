import streamlit as st
import ccxt.async_support as ccxt_async
import pandas as pd
import numpy as np
import math
import asyncio
import requests
from decimal import Decimal
from functools import partial
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="BRICSVAULT PORTAL SMC PRO", page_icon="🏦",
                   layout="wide", initial_sidebar_state="expanded")

VELAS_TOTAL, PERIODO_AQUECIMENTO, PERIODO_SWING_DEFAULT = 500, 100, 50

# ─── DICIONÁRIO DE IDIOMAS ────────────────────────────────────────────────────
def _lang(titulo, compra, venda, neutro, ctx_d, ctx_p, ctx_n, trend_a, trend_d, trend_n, intervalos, extras={}):
    base = {
        "titulo": titulo, "config_globais": "⚙️ Configurações Globais",
        "selecione_cripto": "Selecione a Criptomoeda (/USDT):", "tempo_grafico": "Tempo Gráfico:",
        "modo_vivo": "Monitoramento em Tempo Real", "intervalo_refresh": "Intervalo (seg):",
        "preco_spot": "Preço Atual", "variacao_24h": "Variação 24h", "volume_24h": "Volume 24h (USDT)",
        "market_cap": "Market Cap (USD)", "stop_atr": "Stop ATR",
        "compra_forte": compra, "venda_forte": venda, "neutro": neutro,
        "erro_dados": "Dados insuficientes. Tente outro ativo ou timeframe.",
        "ctx_desconto": ctx_d, "ctx_premium": ctx_p, "ctx_neutro": ctx_n,
        "ultima_atualizacao": "Última Atualização", "proximo_refresh": "Próximo refresh em",
        "segundos": "segundos", "grafico_titulo": "📈 Gráfico Interativo",
        "buscando_marketcap": "🔍 Buscando Market Cap...", "marketcap_nao_disponivel": "N/D",
        "idioma_label": "🌐 Idioma", "idioma_selecao": "Selecione o idioma:",
        "aviso_aquecimento": "⚠️ Velas de aquecimento usadas",
        "alvo_swing_title": "🎯 Projeção de Alvos (Fibonacci / Smart Money)",
        "direcao_operacao": "Direção", "entrada_projetada": "Entrada Projetada",
        "stop_projetado": "Stop Loss", "swing_alto": "Topo Swing", "swing_baixo": "Fundo Swing",
        "range_label": "Range", "alvo_prefix": "ALVO {n}", "sem_alvos": "Nenhum alvo projetado.",
        "contexto_smc": "Contexto SMC", "trend_ascendente": trend_a,
        "trend_descendente": trend_d, "trend_neutra": trend_n, "intervalos": intervalos,
        **extras
    }
    return base

_IV = {"1 Minuto":"1m","5 Minutos":"5m","15 Minutos":"15m","30 Minutos":"30m",
       "1 Hora":"1h","4 Horas":"4h","1 Dia":"1d","1 Semana":"1w"}

DICIONARIO_LINGUAS = {
    "Português (BR)": _lang(
        "🏦 BRICSVAULT PORTAL - Motor SMC + Fibonacci PRO",
        "🟢 COMPRA FORTE (SMC + FIBONACCI)", "🔴 VENDA FORTE (SMC + FIBONACCI)", "🟡 NEUTRO (AGUARDAR SMC)",
        "Zona de Desconto Fibonacci (Ótimo risco/retorno).",
        "Zona Premium Fibonacci (Preço esticado, propício para realização).",
        "Zona neutra Fibonacci (Fair Value Zone).",
        "Tendência de Alta 🟢", "Tendência de Baixa 🔴", "Tendência Neutra 🟡", _IV),
    "English (EN)": _lang(
        "🏦 BRICSVAULT PORTAL - SMC + Fibonacci Engine PRO",
        "🟢 STRONG BUY (SMC + FIBONACCI)", "🔴 STRONG SELL (SMC + FIBONACCI)", "🟡 NEUTRAL (AWAIT SMC)",
        "Fibonacci Discount Zone (Excellent risk/reward).",
        "Fibonacci Premium Zone (Price stretched, suitable for profit-taking).",
        "Neutral Fibonacci Zone (Fair Value Zone).",
        "Uptrend 🟢", "Downtrend 🔴", "Neutral Trend 🟡",
        {"1 Minute":"1m","5 Minutes":"5m","15 Minutes":"15m","30 Minutes":"30m",
         "1 Hour":"1h","4 Hours":"4h","1 Day":"1d","1 Week":"1w"},
        {"selecione_cripto":"Select Cryptocurrency (/USDT):","tempo_grafico":"Timeframe:",
         "modo_vivo":"Enable Real-Time Monitoring","intervalo_refresh":"Refresh Interval (sec):",
         "ultima_atualizacao":"Last Update","proximo_refresh":"Next refresh in","segundos":"seconds",
         "grafico_titulo":"📈 Interactive Chart","alvo_swing_title":"🎯 Target Projection (Fibonacci / Smart Money)",
         "direcao_operacao":"Direction","entrada_projetada":"Projected Entry","stop_projetado":"Stop Loss",
         "swing_alto":"Swing High","swing_baixo":"Swing Low","alvo_prefix":"TARGET {n}",
         "sem_alvos":"No targets projected.","market_cap":"Market Cap (USD)","stop_atr":"ATR Stop",
         "marketcap_nao_disponivel":"N/A","idioma_label":"🌐 Language","idioma_selecao":"Select language:"}),
    "Español": _lang(
        "🏦 BRICSVAULT PORTAL - Motor SMC + Fibonacci PRO",
        "🟢 COMPRA FUERTE (SMC + FIBONACCI)", "🔴 VENTA FUERTE (SMC + FIBONACCI)", "🟡 NEUTRO (ESPERAR SMC)",
        "Zona de Descuento Fibonacci (Excelente riesgo/retorno).",
        "Zona Premium Fibonacci (Precio estirado, propicio para toma de ganancias).",
        "Zona neutral Fibonacci (Fair Value Zone).",
        "Tendencia Alcista 🟢", "Tendencia Bajista 🔴", "Tendencia Neutral 🟡",
        {"1 Minuto":"1m","5 Minutos":"5m","15 Minutos":"15m","30 Minutos":"30m",
         "1 Hora":"1h","4 Horas":"4h","1 Día":"1d","1 Semana":"1w"}),
    "Français": _lang(
        "🏦 BRICSVAULT PORTAL - Moteur SMC + Fibonacci PRO",
        "🟢 ACHAT FORT (SMC + FIBONACCI)", "🔴 VENTE FORTE (SMC + FIBONACCI)", "🟡 NEUTRE (ATTENDRE SMC)",
        "Zone de discount Fibonacci (Excellent risque/rendement).",
        "Zone premium Fibonacci (Prix étiré, propice à la prise de bénéfices).",
        "Zone neutre Fibonacci (Fair Value Zone).",
        "Tendance Haussière 🟢", "Tendance Baissière 🔴", "Tendance Neutre 🟡",
        {"1 Minute":"1m","5 Minutes":"5m","15 Minutes":"15m","30 Minutes":"30m",
         "1 Heure":"1h","4 Heures":"4h","1 Jour":"1d","1 Semaine":"1w"}),
    "Deutsch": _lang(
        "🏦 BRICSVAULT PORTAL - SMC + Fibonacci Motor PRO",
        "🟢 STARKER KAUF (SMC + FIBONACCI)", "🔴 STARKER VERKAUF (SMC + FIBONACCI)", "🟡 NEUTRAL (SMC ABWARTEN)",
        "Fibonacci-Discount-Zone (Ausgezeichnetes Risiko/Rendite).",
        "Fibonacci-Premium-Zone (Preis gedehnt, Gewinnmitnahme geeignet).",
        "Neutrale Fibonacci-Zone (Fair Value Zone).",
        "Aufwärtstrend 🟢", "Abwärtstrend 🔴", "Neutraler Trend 🟡",
        {"1 Minute":"1m","5 Minuten":"5m","15 Minuten":"15m","30 Minuten":"30m",
         "1 Stunde":"1h","4 Stunden":"4h","1 Tag":"1d","1 Woche":"1w"}),
    "Italiano": _lang(
        "🏦 BRICSVAULT PORTAL - Motore SMC + Fibonacci PRO",
        "🟢 ACQUISTO FORTE (SMC + FIBONACCI)", "🔴 VENDITA FORTE (SMC + FIBONACCI)", "🟡 NEUTRO (ATTENDERE SMC)",
        "Zona di Sconto Fibonacci (Ottimo rischio/rendimento).",
        "Zona Premium Fibonacci (Prezzo allungato, adatto per presa di profitto).",
        "Zona neutrale Fibonacci (Fair Value Zone).",
        "Tendenza Rialzista 🟢", "Tendenza Ribassista 🔴", "Tendenza Neutra 🟡",
        {"1 Minuto":"1m","5 Minuti":"5m","15 Minuti":"15m","30 Minuti":"30m",
         "1 Ora":"1h","4 Ore":"4h","1 Giorno":"1d","1 Settimana":"1w"}),
    "Русский": _lang(
        "🏦 BRICSVAULT PORTAL - Двигатель SMC + Фибоначчи PRO",
        "🟢 СИЛЬНАЯ ПОКУПКА (SMC + ФИБОНАЧЧИ)", "🔴 СИЛЬНАЯ ПРОДАЖА (SMC + ФИБОНАЧЧИ)", "🟡 НЕЙТРАЛЬНО (ОЖИДАНИЕ SMC)",
        "Зона скидки Фибоначчи (Отличное соотношение риск/прибыль).",
        "Премиум-зона Фибоначчи (Цена растянута, подходит для фиксации прибыли).",
        "Нейтральная зона Фибоначчи (Зона справедливой стоимости).",
        "Восходящий тренд 🟢", "Нисходящий тренд 🔴", "Нейтральный тренд 🟡",
        {"1 Минута":"1m","5 Минут":"5m","15 Минут":"15m","30 Минут":"30m",
         "1 Час":"1h","4 Часа":"4h","1 День":"1d","1 Неделя":"1w"}),
    "简体中文": _lang(
        "🏦 BRICSVAULT PORTAL - SMC + 斐波那契引擎 PRO",
        "🟢 强力买入 (SMC + 斐波那契)", "🔴 强力卖出 (SMC + 斐波那契)", "🟡 中性 (等待SMC)",
        "斐波那契折扣区 (优秀的风险/回报).", "斐波那契溢价区 (价格过高，适合获利了结).", "斐波那契中性区 (公允价值区).",
        "上升趋势 🟢", "下降趋势 🔴", "中性趋势 🟡",
        {"1 分钟":"1m","5 分钟":"5m","15 分钟":"15m","30 分钟":"30m",
         "1 小时":"1h","4 小时":"4h","1 天":"1d","1 周":"1w"}),
    "繁體中文": _lang(
        "🏦 BRICSVAULT PORTAL - SMC + 斐波那契引擎 PRO",
        "🟢 強力買入 (SMC + 斐波那契)", "🔴 強力賣出 (SMC + 斐波那契)", "🟡 中性 (等待SMC)",
        "斐波那契折扣區 (優秀的風險/回報).", "斐波那契溢價區 (價格過高，適合獲利了結).", "斐波那契中性區 (公允價值區).",
        "上升趨勢 🟢", "下降趨勢 🔴", "中性趨勢 🟡",
        {"1 分鐘":"1m","5 分鐘":"5m","15 分鐘":"15m","30 分鐘":"30m",
         "1 小時":"1h","4 小時":"4h","1 天":"1d","1 週":"1w"}),
    "日本語": _lang(
        "🏦 BRICSVAULT PORTAL - SMC + フィボナッチエンジン PRO",
        "🟢 強力買い (SMC + フィボナッチ)", "🔴 強力売り (SMC + フィボナッチ)", "🟡 中立 (SMC待ち)",
        "フィボナッチ割引ゾーン (優れたリスク/リターン).", "フィボナッチプレミアムゾーン (価格が伸びており利益確定に適).", "フィボナッチ中立ゾーン (公正価値ゾーン).",
        "上昇トレンド 🟢", "下降トレンド 🔴", "中立トレンド 🟡",
        {"1 分":"1m","5 分":"5m","15 分":"15m","30 分":"30m",
         "1 時間":"1h","4 時間":"4h","1 日":"1d","1 週":"1w"}),
    "한국어": _lang(
        "🏦 BRICSVAULT PORTAL - SMC + 피보나치 엔진 PRO",
        "🟢 강한 매수 (SMC + 피보나치)", "🔴 강한 매도 (SMC + 피보나치)", "🟡 중립 (SMC 대기)",
        "피보나치 할인 영역 (우수한 위험/수익률).", "피보나치 프리미엄 영역 (이익 실현에 적합).", "피보나치 중립 영역 (공정 가치 영역).",
        "상승 추세 🟢", "하락 추세 🔴", "중립 추세 🟡",
        {"1분":"1m","5분":"5m","15분":"15m","30분":"30m",
         "1시간":"1h","4시간":"4h","1일":"1d","1주":"1w"}),
    "Tiếng Việt": _lang(
        "🏦 BRICSVAULT PORTAL - Động cơ SMC + Fibonacci PRO",
        "🟢 MUA MẠNH (SMC + FIBONACCI)", "🔴 BÁN MẠNH (SMC + FIBONACCI)", "🟡 TRUNG LẬP (CHỜ SMC)",
        "Vùng chiết khấu Fibonacci (Tỷ lệ rủi ro/lợi nhuận tuyệt vời).",
        "Vùng cao cấp Fibonacci (Giá kéo dài, phù hợp để chốt lời).",
        "Vùng trung tính Fibonacci (Vùng giá trị hợp lý).",
        "Xu hướng tăng 🟢", "Xu hướng giảm 🔴", "Xu hướng trung lập 🟡",
        {"1 Phút":"1m","5 Phút":"5m","15 Phút":"15m","30 Phút":"30m",
         "1 Giờ":"1h","4 Giờ":"4h","1 Ngày":"1d","1 Tuần":"1w"}),
    "Türkçe": _lang(
        "🏦 BRICSVAULT PORTAL - SMC + Fibonacci Motoru PRO",
        "🟢 GÜÇLÜ ALIM (SMC + FIBONACCI)", "🔴 GÜÇLÜ SATIM (SMC + FIBONACCI)", "🟡 NÖTR (SMC BEKLE)",
        "Fibonacci İskonto Bölgesi (Mükemmel risk/getiri).",
        "Fibonacci Prim Bölgesi (Fiyat gerilmiş, kar alma için uygun).",
        "Fibonacci nötr bölgesi (Fair Value Zone).",
        "Yükseliş Trendi 🟢", "Düşüş Trendi 🔴", "Nötr Trend 🟡",
        {"1 Dakika":"1m","5 Dakika":"5m","15 Dakika":"15m","30 Dakika":"30m",
         "1 Saat":"1h","4 Saat":"4h","1 Gün":"1d","1 Hafta":"1w"}),
}

# ─── FORMATAÇÃO ───────────────────────────────────────────────────────────────
def formatar_preco(valor, prefixo="$ "):
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return f"{prefixo}—"
    if valor <= 0: return f"{prefixo}0.00"
    if valor < 0.001:
        d = Decimal(str(valor)); s = f"{d:.20f}".rstrip("0")
        p = s.split(".")
        if len(p) != 2: return f"{prefixo}{valor}"
        dec = p[1]; nz = len(dec) - len(dec.lstrip("0"))
        return f"{prefixo}0.0{nz}x{dec.lstrip('0')}"
    elif valor < 1: return f"{prefixo}{valor:.6f}"
    return f"{prefixo}{valor:,.2f}"

def formatar_market_cap(valor):
    if valor is None: return "$ —"
    if isinstance(valor, str):
        try: valor = float(valor.replace('$','').replace(',','').strip())
        except: return "$ —"
    if valor <= 0: return "$ 0.00"
    for lim, sfx in [(1e12,"T"),(1e9,"B"),(1e6,"M")]:
        if valor >= lim: return f"$ {valor/lim:.2f}{sfx}"
    return f"$ {valor:,.2f}"

# ─── EXCHANGE MANAGER ─────────────────────────────────────────────────────────
class ExchangeManager:
    EXCHANGES = {
        "Gate.io": {"class": ccxt_async.gate, "config": {"enableRateLimit": True, "options": {"defaultType": "spot"}}},
        "Kraken":  {"class": ccxt_async.kraken, "config": {"enableRateLimit": True}},
        "MEXC":    {"class": ccxt_async.mexc,   "config": {"enableRateLimit": True}},
        "KuCoin":  {"class": ccxt_async.kucoin, "config": {"enableRateLimit": True}},
    }
    PRIORITY = ["Gate.io", "Kraken", "MEXC", "KuCoin"]

    def __init__(self):
        self.clients = {n: c["class"](c["config"]) for n, c in self.EXCHANGES.items()
                        if self._try_init(c["class"], c["config"])}

    def _try_init(self, cls, cfg):
        try: cls(cfg); return True
        except: return False

    async def get_client(self, name): return self.clients.get(name)

    def get_symbol_format(self, name, symbol):
        if name == "MEXC": return symbol.replace("/", "")
        if name == "KuCoin": return symbol.replace("/", "-")
        return symbol

@st.cache_resource
def get_exchange_manager(): return ExchangeManager()

# ─── FUNÇÕES ASYNC ────────────────────────────────────────────────────────────
async def obter_todos_pares_usdt_async():
    mgr = get_exchange_manager()
    client = await mgr.get_client("Gate.io")
    if not client: return ["BTC/USDT","ETH/USDT","SOL/USDT","XRP/USDT","BNB/USDT"]
    try:
        markets = await client.load_markets()
        return sorted(s for s in markets if s.endswith("/USDT"))
    except: return ["BTC/USDT","ETH/USDT","SOL/USDT","XRP/USDT","BNB/USDT"]
    finally: await client.close()

async def obter_volume_usd_direto_async(exchange_name, simbolo):
    try:
        if exchange_name == "MEXC":
            r = await asyncio.to_thread(requests.get, f"https://api.mexc.com/api/v3/ticker/24hr?symbol={simbolo.replace('/','')}", timeout=10)
            if r.status_code == 200: return float(r.json().get("quoteVolume", 0))
        elif exchange_name == "KuCoin":
            r = await asyncio.to_thread(requests.get, f"https://api.kucoin.com/api/v1/market/stats?symbol={simbolo.replace('/','-')}", timeout=10)
            if r.status_code == 200:
                d = r.json()
                if d.get("code") == "200000": return float(d.get("data",{}).get("volValue",0))
        elif exchange_name == "Gate.io":
            r = await asyncio.to_thread(requests.get, f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={simbolo.replace('/','_')}", timeout=10)
            if r.status_code == 200:
                d = r.json()
                if d: return float(d[0].get("quote_volume", 0))
    except: pass
    return None

async def fetch_from_exchange_24h(exchange_name, manager, simbolo):
    client = None
    try:
        client = await manager.get_client(exchange_name)
        if not client: return None
        t = await client.fetch_ticker(manager.get_symbol_format(exchange_name, simbolo))
        if not t: return None
        result = {"last": t.get("last"), "change": t.get("percentage"),
                  "volume": t.get("quoteVolume") or t.get("baseVolume"),
                  "high": t.get("high"), "low": t.get("low"),
                  "bid": t.get("bid"), "ask": t.get("ask")}
        if not result["volume"]:
            result["volume"] = await obter_volume_usd_direto_async(exchange_name, simbolo)
        return result if result["last"] is not None else None
    except: return None
    finally:
        if client: await client.close()

async def obter_dados_24h_async(simbolo):
    mgr = get_exchange_manager()
    tasks = [asyncio.create_task(fetch_from_exchange_24h(n, mgr, simbolo)) for n in mgr.PRIORITY]
    for f in asyncio.as_completed(tasks):
        r = await f
        if r: return r
    return None

async def obter_market_cap_coingecko_async(simbolo):
    try:
        base = simbolo.split("/")[0]
        r = await asyncio.to_thread(requests.get, "https://api.coingecko.com/api/v3/search",
                                    params={"query": base}, headers={"Accept":"application/json"}, timeout=10)
        if r.status_code != 200: return None
        coins = r.json().get("coins", [])
        coin_id = next((c["id"] for c in coins if c.get("symbol","").upper() == base.upper()), None)
        if not coin_id and coins: coin_id = coins[0]["id"]
        if not coin_id: return None
        r2 = await asyncio.to_thread(requests.get, "https://api.coingecko.com/api/v3/coins/markets",
                                     params={"vs_currency":"usd","ids":coin_id,"per_page":1,"page":1},
                                     headers={"Accept":"application/json"}, timeout=10)
        if r2.status_code == 200:
            d = r2.json()
            if d:
                mc = d[0].get("market_cap")
                if mc and float(mc) > 1_000_000: return float(mc)
    except: pass
    return None

async def obter_market_cap_coincap_async(simbolo):
    base = simbolo.split("/")[0].lower()
    try:
        for url, key in [
            (f"https://api.coincap.io/v2/assets/{base}", lambda d: d.get("data",{}).get("marketCapUsd")),
            ("https://api.coincap.io/v2/assets", lambda d: next((i.get("marketCapUsd") for i in d.get("data",[]) if i.get("symbol","").upper()==base.upper()), None))
        ]:
            params = {"limit":2000} if "assets" in url and base not in url else {}
            r = await asyncio.to_thread(requests.get, url, params=params, timeout=10)
            if r.status_code == 200:
                mc = key(r.json())
                if mc and float(mc) > 1_000_000: return float(mc)
    except: pass
    return None

async def obter_market_cap_robusto_async(simbolo_id):
    mc_cg, mc_cc = await asyncio.gather(
        obter_market_cap_coingecko_async(simbolo_id),
        obter_market_cap_coincap_async(simbolo_id),
        return_exceptions=True
    )
    vals = [v for v in (mc_cg, mc_cc) if isinstance(v, (int, float)) and v > 0]
    return sum(vals)/len(vals) if vals else None

# ─── CACHE SYNC ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def obter_todos_pares_usdt(): return asyncio.run(obter_todos_pares_usdt_async())

@st.cache_data(ttl=60)
def obter_dados_24h(s): return asyncio.run(obter_dados_24h_async(s))

@st.cache_data(ttl=600)
def obter_market_cap_robusto(s): return asyncio.run(obter_market_cap_robusto_async(s))

# ─── INDICADORES ─────────────────────────────────────────────────────────────
def calcular_rsi(s, p=14):
    d = s.diff(); g = d.clip(lower=0); l = -d.clip(upper=0)
    mg = g.ewm(span=p, adjust=False).mean(); ml = l.ewm(span=p, adjust=False).mean()
    return 100 - (100 / (1 + mg / ml.replace(0, 1e-10)))

def calcular_macd(s):
    e12 = s.ewm(span=12,adjust=False).mean(); e26 = s.ewm(span=26,adjust=False).mean()
    m = e12 - e26; sig = m.ewm(span=9,adjust=False).mean()
    return m, sig, m - sig

def calcular_mfi(df, p=14):
    tp = (df['high']+df['low']+df['close'])/3; rmf = tp*df['volume']
    ts = tp.shift(1)
    pf = rmf.where(tp>ts,0.0); nf = rmf.where(tp<ts,0.0)
    ps = pf.rolling(p).sum(); ns = nf.rolling(p).sum().replace(0,1e-10)
    return 100-(100/(1+ps/ns))

def calcular_ssl_hybrid(df, p=20):
    sh = df['high'].rolling(p).mean(); sl = df['low'].rolling(p).mean()
    c, sh_a, sl_a = df['close'].values, sh.values, sl.values
    sd = np.ones(len(df),dtype=int); cur = 1
    for i in range(len(df)):
        if np.isnan(sh_a[i]) or np.isnan(sl_a[i]): sd[i]=cur; continue
        if c[i]>sh_a[i]: cur=1
        elif c[i]<sl_a[i]: cur=-1
        sd[i]=cur
    df = df.copy(); df['ssl_dir']=sd
    df['SSL_Baseline'] = np.where(sd==1, sh, sl)
    return df

def calcular_atr_stop(df, p=14, mult=3.0):
    h,l,c = df['high'],df['low'],df['close']
    tr = pd.concat([h-l,(h-c.shift(1)).abs(),(l-c.shift(1)).abs()],axis=1).max(axis=1)
    atr = tr.ewm(span=p,adjust=False).mean()
    stop = np.zeros(len(df)); trend = np.zeros(len(df),dtype=int)
    ca, aa = c.values, atr.values
    stop[0] = (ca[0]-(aa[0]*mult)) if not np.isnan(aa[0]) else ca[0]; trend[0]=1
    for i in range(1,len(df)):
        if np.isnan(aa[i]): stop[i]=stop[i-1]; trend[i]=trend[i-1]; continue
        if trend[i-1]==1:
            if ca[i]<stop[i-1]: trend[i]=-1; stop[i]=ca[i]+(aa[i]*mult)
            else: trend[i]=1; stop[i]=max(stop[i-1],ca[i]-(aa[i]*mult))
        else:
            if ca[i]>stop[i-1]: trend[i]=1; stop[i]=ca[i]-(aa[i]*mult)
            else: trend[i]=-1; stop[i]=min(stop[i-1],ca[i]+(aa[i]*mult))
    df = df.copy(); df['ATR_Stop']=stop; df['atr_dir']=trend
    return df

def calcular_ppo(df, col='close', r=12, l=26, s=9):
    er = df[col].ewm(span=r,adjust=False).mean(); el = df[col].ewm(span=l,adjust=False).mean()
    df = df.copy(); df['PPO'] = ((er-el)/el)*100; df['PPO_Signal'] = df['PPO'].ewm(span=s,adjust=False).mean()
    return df

# ─── SMC ─────────────────────────────────────────────────────────────────────
def identificar_fractais(df, w=2):
    df['fractal_high'] = df['high'].rolling(w*2+1,center=True).apply(
        lambda x: x.iloc[w] if x.iloc[w]==x.max() else np.nan, raw=False)
    df['fractal_low'] = df['low'].rolling(w*2+1,center=True).apply(
        lambda x: x.iloc[w] if x.iloc[w]==x.min() else np.nan, raw=False)
    return df

def identificar_swing_smc(df):
    df = identificar_fractais(df.copy())
    sh = df[df['fractal_high'].notna()]['high']
    sl = df[df['fractal_low'].notna()]['low']
    if sh.empty or sl.empty: return None
    hi, li = sh.index[-1], sl.index[-1]
    if hi > li:
        low_cands = sl[sl.index<hi]
        sw_low = low_cands.iloc[-1] if not low_cands.empty else df['low'].min()
        swli = low_cands.index[-1] if not low_cands.empty else df['low'].idxmin()
        return {'swing_high':sh.iloc[-1],'swing_low':sw_low,'swing_high_idx':hi,'swing_low_idx':swli,'direction_from_swing':'SHORT'}
    else:
        high_cands = sh[sh.index<li]
        sw_high = high_cands.iloc[-1] if not high_cands.empty else df['high'].max()
        swhi = high_cands.index[-1] if not high_cands.empty else df['high'].idxmax()
        return {'swing_high':sw_high,'swing_low':sl.iloc[-1],'swing_high_idx':swhi,'swing_low_idx':li,'direction_from_swing':'LONG'}

def fib_niveis(sh, sl):
    d = sh - sl
    return {f'fib_{k}': sh - r*d for k,r in
            [('0',0),('236',.236),('382',.382),('500',.5),('618',.618),('786',.786),('100',1)]}

def gerar_sinal_fibonacci(df, direcao, mults, periodo_swing):
    info = identificar_swing_smc(df.iloc[PERIODO_AQUECIMENTO:])
    preco = df['close'].iloc[-1]
    if not info:
        sh, sl = df['high'].max(), df['low'].min()
        return {'direcao':direcao,'entrada':preco,'stop':sl if direcao=="LONG" else sh,
                'swing_high':sh,'swing_low':sl,'alvos':[]}
    sh, sl = info['swing_high'], info['swing_low']
    fibs = fib_niveis(sh, sl)
    if direcao=="LONG":
        entrada = min(fibs['fib_618'], preco); stop = sl
        risco = entrada - stop
        alvos = sorted([a for a in [entrada+m*risco for m in mults] if a>entrada])
    else:
        entrada = max(fibs['fib_382'], preco); stop = sh
        risco = stop - entrada
        alvos = sorted([a for a in [entrada-m*risco for m in mults] if a<entrada], reverse=True)
    return {'direcao':direcao,'swing_high':sh,'swing_low':sl,'entrada':entrada,
            'stop':stop,'risco':risco,'alvos':alvos[:8],'multiplicadores':mults[:len(alvos[:8])]}

def analisar_confluencia(df, txt, limiar=9.0, periodo_aq=100):
    df_a = df.iloc[periodo_aq:]
    if df_a.empty: return txt["neutro"],"#ffcc00",txt["err_dados"],0,0,"NEUTRO"
    u = df_a.iloc[-1]; pa = pontos_alta = pontos_baixa = 0
    ctx = txt["ctx_neutro"]
    info = identificar_swing_smc(df)
    if info:
        sh, sl = info['swing_high'], info['swing_low']
        fibs = fib_niveis(sh, sl)
        pc = u['close']
        if fibs['fib_382'] <= pc <= fibs['fib_0']: pontos_baixa+=2.5; ctx=txt["ctx_premium"]
        elif fibs['fib_100'] <= pc <= fibs['fib_618']: pontos_alta+=2.5; ctx=txt["ctx_desconto"]
        if info['direction_from_swing']=='LONG': pontos_alta+=1.0
        else: pontos_baixa+=1.0
    def _safe(v): return 0 if (v is None or (isinstance(v,float) and math.isnan(v))) else v
    rsi = _safe(u['RSI_14'])
    if rsi<40: pontos_alta+=2.5
    elif rsi>60: pontos_baixa+=2.5
    mh = _safe(u['MACD_HIST'])
    if mh>0: pontos_alta+=2
    else: pontos_baixa+=2
    mfi = _safe(u['MFI'])
    if mfi<40: pontos_alta+=1.5
    elif mfi>60: pontos_baixa+=1.5
    if u['ssl_dir']==1: pontos_alta+=1.5
    else: pontos_baixa+=1.5
    if u['atr_dir']==1: pontos_alta+=1.5
    else: pontos_baixa+=1.5
    ppo, pposs = _safe(u['PPO']), _safe(u['PPO_Signal'])
    if ppo>pposs: pontos_alta+=2
    else: pontos_baixa+=2
    media50 = df_a['close'].rolling(50).mean().iloc[-1]
    direcao = "LONG" if u['close']>=media50 else "SHORT"
    if pontos_alta>=limiar and pontos_alta>pontos_baixa:
        return txt["compra_forte"],"#00cc66",f"{ctx} SMC + Confluência Bullish.",pontos_alta,pontos_baixa,"LONG"
    elif pontos_baixa>=limiar and pontos_baixa>pontos_alta:
        return txt["venda_forte"],"#ff3333",f"{ctx} SMC + Confluência Bearish.",pontos_alta,pontos_baixa,"SHORT"
    return txt["neutro"],"#ffcc00",ctx,pontos_alta,pontos_baixa,direcao

# ─── CARREGAMENTO OHLCV ───────────────────────────────────────────────────────
async def carregar_dados_async(simbolo_id, timeframe):
    mgr = get_exchange_manager()
    cache = st.session_state.setdefault('ohlcv_data', {})
    cached = cache.setdefault(simbolo_id, {}).setdefault(timeframe, pd.DataFrame())
    since = int(cached['timestamp'].iloc[-1])+1 if not cached.empty else None
    limit = max(1, VELAS_TOTAL-len(cached)) if not cached.empty else VELAS_TOTAL
    velas = []
    for name in mgr.PRIORITY:
        client = None
        try:
            client = await mgr.get_client(name)
            if not client: continue
            velas = await client.fetch_ohlcv(mgr.get_symbol_format(name,simbolo_id), timeframe, limit=limit, since=since)
            if velas: break
        except: continue
        finally:
            if client: await client.close()
    if not velas and cached.empty: return None
    df_new = pd.DataFrame(velas, columns=['timestamp','open','high','low','close','volume'])
    df_new['time'] = pd.to_datetime(df_new['timestamp'], unit='ms')
    df = pd.concat([cached, df_new]).drop_duplicates('timestamp').sort_values('timestamp').reset_index(drop=True)
    if len(df) > VELAS_TOTAL: df = df.iloc[-VELAS_TOTAL:].reset_index(drop=True)
    if len(df) < PERIODO_AQUECIMENTO+50: return None
    df['RSI_14'] = calcular_rsi(df['close'])
    df['MACD'], df['MACD_SIGNAL'], df['MACD_HIST'] = calcular_macd(df['close'])
    df['MFI'] = calcular_mfi(df)
    df = calcular_ssl_hybrid(df); df = calcular_atr_stop(df); df = calcular_ppo(df)
    df['SSL_Baseline'] = df['SSL_Baseline'].ffill()
    df['ATR_Stop'] = df['ATR_Stop'].replace(0,np.nan).ffill()
    cache[simbolo_id][timeframe] = df.dropna(subset=['close']).reset_index(drop=True)
    return cache[simbolo_id][timeframe]

# ─── BACKTEST ─────────────────────────────────────────────────────────────────
def calcular_assertividade_historica_robusta(df, limiar, periodo_aq, txt, tp_pct=1.0, la=5):
    inicio = periodo_aq + PERIODO_SWING_DEFAULT
    if len(df) < inicio+la:
        return "Dados insuficientes para backtest.", {}
    acertos = total = lucro_t = risco_t = 0; ops = []
    for i in range(inicio, len(df)-la):
        ctx = df.iloc[:i+1]
        try:
            *_, pa, pb, direcao = analisar_confluencia(ctx, txt, limiar, periodo_aq)
            if not ((direcao=="LONG" and pa>=limiar) or (direcao=="SHORT" and pb>=limiar)): continue
            sf = gerar_sinal_fibonacci(ctx, direcao, [1.0], PERIODO_SWING_DEFAULT)
            ent, sl = sf['entrada'], sf['stop']
            total += 1
            fut = df.iloc[i+1:i+1+la]
            if fut.empty: continue
            if direcao=="LONG":
                rp = ((ent-sl)/ent)*100 if ent>0 else 0
                alvo = ent*(1+tp_pct/100)
                acerto = fut['high'].max()>=alvo
                lr = tp_pct if acerto else ((fut['close'].iloc[-1]-ent)/ent)*100
            else:
                rp = ((sl-ent)/ent)*100 if ent>0 else 0
                alvo = ent*(1-tp_pct/100)
                acerto = fut['low'].min()<=alvo
                lr = tp_pct if acerto else ((ent-fut['close'].iloc[-1])/ent)*100
            if acerto: acertos+=1
            lucro_t+=lr; risco_t+=rp
            ops.append({'timestamp':ctx['timestamp'].iloc[-1],'direcao':direcao,'entrada':ent,
                        'stop_loss':sl,'alvo_preco':alvo,'lucro_realizado_pct':lr,'risco_pct':rp,'acerto':acerto})
        except: continue
    if total==0: return "Nenhum sinal gerado para backtest. Reduza a nota de corte.", {}
    ass = (acertos/total)*100
    lm = lucro_t/total; rm = risco_t/total
    ganhos = sum(o['lucro_realizado_pct'] for o in ops if o['lucro_realizado_pct']>0)
    perdas = sum(abs(o['lucro_realizado_pct']) for o in ops if o['lucro_realizado_pct']<0)
    fl = ganhos/perdas if perdas>0 else (ganhos/1e-10 if ganhos>0 else 0)
    eq=[100]; pk=100; md=0
    for o in ops:
        eq.append(eq[-1]*(1+o['lucro_realizado_pct']/100))
        if eq[-1]>pk: pk=eq[-1]
        dd=(pk-eq[-1])/pk*100
        if dd>md: md=dd
    txt_r = f"""**Resultados do Backtest:**
- Sinais: {total} | Acertos: {acertos} | Assertividade: {ass:.1f}%
- Lucro Médio/Op: {lm:.2f}% | Risco Médio/Op: {rm:.2f}%
- Fator de Lucro: {fl:.2f} | Drawdown Máximo: {md:.2f}%
- Relação R/R Média: {lm/rm if rm>0 else 0:.2f}:1"""
    return txt_r, {'equity_curve':eq,'operacoes':ops}

# ─── GRÁFICO ─────────────────────────────────────────────────────────────────
def renderizar_grafico_plotly(df, simbolo_id, la, ops_bt=None):
    df_g = df.iloc[PERIODO_AQUECIMENTO:]
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df_g['time'],open=df_g['open'],high=df_g['high'],
                                  low=df_g['low'],close=df_g['close'],name=simbolo_id,
                                  increasing_line_color='#10b981',decreasing_line_color='#ef4444',
                                  increasing_fillcolor='#10b981',decreasing_fillcolor='#ef4444'))
    fig.add_trace(go.Scatter(x=df_g['time'],y=df_g['SSL_Baseline'],mode='lines',
                             name='SMC Baseline (SSL)',line=dict(color='#00aaff',width=2)))
    fig.add_trace(go.Scatter(x=df_g['time'],y=df_g['ATR_Stop'],mode='lines',
                             name='ATR Trailing Stop',line=dict(color='#ffaa00',width=1,dash='dash')))
    if ops_bt:
        dt = df_g['time'].diff().mean() or pd.Timedelta(minutes=5)
        delta = dt * la
        for op in ops_bt:
            t = pd.to_datetime(op['timestamp'],unit='ms')
            is_long = op['direcao']=='LONG'
            fig.add_trace(go.Scatter(x=[t],y=[op['entrada']],mode='markers',showlegend=False,
                                     marker=dict(symbol='triangle-up' if is_long else 'triangle-down',
                                                 size=10,color='green' if is_long else 'red')))
            if op['acerto']:
                fig.add_trace(go.Scatter(x=[t+delta],y=[op['alvo_preco']],mode='markers',showlegend=False,
                                         marker=dict(symbol='star',size=10,color='lime' if is_long else 'orange')))
            fig.add_trace(go.Scatter(x=[t],y=[op['stop_loss']],mode='markers',showlegend=False,
                                     marker=dict(symbol='x',size=10,color='red' if is_long else 'green')))
    fig.update_layout(paper_bgcolor='#0b0f19',plot_bgcolor='#0b0f19',font=dict(color='#e2e8f0'),
                      xaxis=dict(gridcolor='#1e293b',showgrid=True,rangeslider=dict(visible=False)),
                      yaxis=dict(gridcolor='#1e293b',showgrid=True),
                      legend=dict(bgcolor='#1e293b',bordercolor='#475569',borderwidth=1),
                      margin=dict(l=10,r=10,t=30,b=10),height=520)
    st.plotly_chart(fig, use_container_width=True)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
async def main():
    idiomas = list(DICIONARIO_LINGUAS.keys())
    st.sidebar.markdown(f"### {DICIONARIO_LINGUAS['Português (BR)']['idioma_label']}")
    idioma = st.sidebar.selectbox(DICIONARIO_LINGUAS['Português (BR)']['idioma_selecao'], idiomas, index=0)
    txt = DICIONARIO_LINGUAS[idioma]
    st.title(txt["titulo"])
    st.sidebar.header(txt["config_globais"])

    pares = obter_todos_pares_usdt() or ["BTC/USDT","ETH/USDT","SOL/USDT","XRP/USDT","BNB/USDT"]
    simbolo = st.sidebar.selectbox(txt["selecione_cripto"], pares,
                                   index=pares.index("SOL/USDT") if "SOL/USDT" in pares else 0)
    ivs = txt["intervalos"]
    tf_label = st.sidebar.selectbox(txt["tempo_grafico"], list(ivs.keys()), index=5)
    timeframe = ivs[tf_label]

    st.sidebar.markdown("---")
    modo_vivo = st.sidebar.toggle(txt["modo_vivo"], value=False)
    intervalo_refresh = st.sidebar.slider(txt["intervalo_refresh"], 15, 120, 30)

    st.sidebar.markdown("### 🎯 Configuração dos Alvos")
    mults_str = st.sidebar.text_input("Multiplicadores (separados por vírgula):",
                                       value="0.236,0.5,0.786,1.272,2.236,3.618,5.0,8.0")
    try:
        mults = [float(x.strip()) for x in mults_str.split(",") if x.strip()] or [.236,.5,.786,1.272,2.236,3.618,5,8]
    except: mults = [.236,.5,.786,1.272,2.236,3.618,5,8]

    periodo_swing = st.sidebar.slider("Período do Swing (velas):", 10, 200, PERIODO_SWING_DEFAULT)
    st.sidebar.markdown("### ⚙️ Ajuste de Assertividade")
    limiar = st.sidebar.slider("Nota de corte (padrão 9.0):", 5.0, 12.0, 9.0, 0.5)
    periodo_aq = st.sidebar.slider("Velas de aquecimento:", 50, 300, 100, 10)
    tp_pct = st.sidebar.slider("Alvo de Lucro p/ Backtest (%):", 0.5, 5.0, 1.0, 0.1)
    la = st.sidebar.slider("Velas para Buscar Alvo no Backtest:", 3, 20, 5)
    st.sidebar.markdown("---\n**BRICSVAULT PORTAL SMC PRO**\nVersão: 2.1 (Otimizada)")

    @st.fragment(run_every=intervalo_refresh if modo_vivo else None)
    async def painel(simbolo, timeframe, txt, modo_vivo, intervalo_refresh, mults, periodo_swing, limiar, periodo_aq, tp_pct, la):
        df = await carregar_dados_async(simbolo, timeframe)
        if df is None or df.empty: st.warning(txt["erro_dados"]); return

        preco = df.iloc[periodo_aq:].iloc[-1]['close']
        _, col_c, _ = st.columns([1,2,1])
        with col_c:
            st.markdown(f"""<div style="text-align:center;padding:15px;background:#1e293b;border-radius:12px;border:1px solid #475569;">
                <span style="font-size:32px;font-weight:bold;color:#e2e8f0;">{formatar_preco(preco)}</span><br>
                <span style="font-size:16px;color:#94a3b8;">{simbolo.split('/')[0]} / USDT – {txt['preco_spot']}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("---")

        dados24 = obter_dados_24h(simbolo)
        var24 = dados24.get("change",0) if dados24 else 0
        vol24 = dados24.get("volume") if dados24 else None
        mc = obter_market_cap_robusto(simbolo)

        rec, cor, analise, pa, pb, direcao = analisar_confluencia(df, txt, limiar, periodo_aq)
        u = df.iloc[periodo_aq:].iloc[-1]
        ppo_v, ppo_s = u['PPO'], u['PPO_Signal']
        ppo_txt = f"PPO: {ppo_v:.3f} / Signal: {ppo_s:.3f}" if not (math.isnan(ppo_v) or math.isnan(ppo_s)) else "PPO: —"

        st.markdown(f"""<div style="background:{cor}22;padding:20px;border-radius:10px;border:2px solid {cor};margin-bottom:20px;">
            <h2 style="margin:0;color:{cor};">{rec}</h2>
            <p style="margin:8px 0 0;color:#ddd;">{analise} | <b>{ppo_txt}</b></p>
        </div>""", unsafe_allow_html=True)

        sf = gerar_sinal_fibonacci(df, direcao, mults, periodo_swing)
        st.markdown(f"### {txt['alvo_swing_title']}")
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric(txt["direcao_operacao"], f"{sf['direcao']} 🚀")
        c2.metric(txt["entrada_projetada"], formatar_preco(sf['entrada']))
        c3.metric(txt["stop_projetado"], formatar_preco(sf['stop']),
                  delta=f"{((sf['stop']-sf['entrada'])/sf['entrada']*100):+.2f}%")
        c4.metric(txt["swing_alto"], formatar_preco(sf['swing_high']))
        c5.metric(txt["swing_baixo"], formatar_preco(sf['swing_low']))

        if sf['alvos']:
            st.markdown("**🎯 Projeção dos Alvos:**")
            cols = st.columns(4)
            for i, alvo in enumerate(sf['alvos']):
                pct = ((alvo-sf['entrada'])/sf['entrada'])*100 if direcao=="LONG" else ((sf['entrada']-alvo)/sf['entrada'])*100
                cols[i%4].metric(txt["alvo_prefix"].format(n=i+1), formatar_preco(alvo), delta=f"{pct:+.2f}%")
        else: st.info(txt["sem_alvos"])

        st.divider()
        with st.expander("📊 Backtest Robusto"):
            res_bt, bt_m = calcular_assertividade_historica_robusta(df, limiar, periodo_aq, txt, tp_pct, la)
            st.markdown(res_bt)
            st.caption("💡 Quanto maior a porcentagem, mais confiável a configuração.")
            if bt_m.get('equity_curve') and len(bt_m['equity_curve'])>1:
                fig_eq = go.Figure(go.Scatter(y=bt_m['equity_curve'],mode='lines'))
                fig_eq.update_layout(title='Equity Curve',xaxis_title='Operações',yaxis_title='Capital (%)',
                                     paper_bgcolor='#0b0f19',plot_bgcolor='#0b0f19',font=dict(color='#e2e8f0'))
                st.plotly_chart(fig_eq, use_container_width=True)

        st.markdown(f"### {txt['grafico_titulo']}")
        renderizar_grafico_plotly(df, simbolo, la, bt_m.get('operacoes') if isinstance(bt_m,dict) else None)

        st.markdown("---")
        ci1,ci2,ci3 = st.columns(3)
        ci1.metric(txt["preco_spot"], formatar_preco(preco))
        ci2.metric(txt["variacao_24h"], f"{var24:.2f}%", delta=f"{var24:.2f}%")
        ci3.metric(txt["volume_24h"], formatar_market_cap(vol24))
        st.metric(txt["market_cap"], formatar_market_cap(mc) if mc else txt["marketcap_nao_disponivel"])

        if modo_vivo:
            st.markdown(f"<p style='text-align:right;color:#94a3b8;'>{txt['ultima_atualizacao']}: {datetime.now():%H:%M:%S}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:right;color:#94a3b8;'>{txt['proximo_refresh']} {intervalo_refresh} {txt['segundos']}</p>", unsafe_allow_html=True)

    await painel(simbolo, timeframe, txt, modo_vivo, intervalo_refresh, mults, periodo_swing, limiar, periodo_aq, tp_pct, la)

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except RuntimeError:
        asyncio.run(main())
