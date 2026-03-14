"""
╔══════════════════════════════════════════════════════════════════════╗
║                    APEX TRADING AI  v3.0                             ║
║              trading_dashboard.py — Main Application                 ║
╠══════════════════════════════════════════════════════════════════════╣
║  Run:  streamlit run trading_dashboard.py                            ║
║  Deps: pip install streamlit pandas numpy requests ta anthropic      ║
║              plotly ccxt python-binance                              ║
╠══════════════════════════════════════════════════════════════════════╣
║  Features:                                                           ║
║   • Secure login (admin/apex2025 · trader1/trade123)                 ║
║   • Live Binance market data — BTCUSDT / ETHUSDT                     ║
║   • Multi-timeframe: 4H + 15M candlestick analysis                   ║
║   • 15+ technical indicators with AI-scored signals                  ║
║   • 6-provider AI analysis (Anthropic/OpenAI/Gemini/Groq/Ollama/Mistral)║
║   • 7-broker execution (Binance/Bybit/OKX/Kraken/Deribit/KuCoin/HL)  ║
║   • One-click bracket orders: Entry + TP + SL                        ║
║   • Live account: equity, margin, positions, unrealized PnL          ║
║   • Order book heatmap · Position monitoring panel                   ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
from ai_provider import (
    render_login, render_provider_selector, render_broker_selector,
    get_ai_analysis, place_trade, get_account_summary, refresh_account,
    BROKERS
)

# ══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="APEX TRADING AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&family=Orbitron:wght@700;900&display=swap');

:root {
    --bg-primary:   #020810;
    --bg-secondary: #050f1a;
    --bg-card:      #071525;
    --accent-cyan:  #00f5ff;
    --accent-green: #00ff88;
    --accent-red:   #ff2d5e;
    --accent-gold:  #ffd700;
    --accent-orange:#ff6b35;
    --text-primary: #e0f4ff;
    --text-dim:     #5a8fa8;
    --border:       rgba(0,245,255,0.12);
    --grid:         rgba(0,245,255,0.04);
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg-primary) !important;
    background-image:
        linear-gradient(var(--grid) 1px, transparent 1px),
        linear-gradient(90deg, var(--grid) 1px, transparent 1px);
    background-size: 40px 40px;
    font-family: 'Rajdhani', sans-serif;
    color: var(--text-primary);
}
[data-testid="stSidebar"] {
    background: var(--bg-secondary) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
h1,h2,h3 { font-family: 'Orbitron', sans-serif !important; }

/* ── Header ── */
.apex-header { text-align:center; padding:1.2rem 0 0.8rem; border-bottom:1px solid var(--border); margin-bottom:1.5rem; }
.apex-header h1 {
    font-family:'Orbitron',sans-serif; font-size:2rem; font-weight:900;
    background:linear-gradient(90deg,var(--accent-cyan),var(--accent-green),var(--accent-gold));
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    letter-spacing:5px; margin:0;
}
.apex-header .sub { font-family:'Share Tech Mono',monospace; color:var(--text-dim); font-size:0.68rem; letter-spacing:3px; margin-top:4px; }

/* ── Metric card ── */
.mc { background:var(--bg-card); border:1px solid var(--border); border-radius:4px; padding:0.9rem 1.1rem; position:relative; overflow:hidden; }
.mc::before { content:''; position:absolute; top:0; left:0; width:3px; height:100%; }
.mc.bull::before { background:var(--accent-green); box-shadow:0 0 8px var(--accent-green); }
.mc.bear::before { background:var(--accent-red);   box-shadow:0 0 8px var(--accent-red); }
.mc.neut::before { background:var(--accent-gold);  box-shadow:0 0 8px var(--accent-gold); }
.mc.info::before { background:var(--accent-cyan);  box-shadow:0 0 8px var(--accent-cyan); }
.mc-label { font-family:'Share Tech Mono',monospace; font-size:0.6rem; color:var(--text-dim); letter-spacing:2px; }
.mc-val   { font-family:'Orbitron',sans-serif; font-size:1.2rem; font-weight:700; margin-top:3px; }
.mc-delta { font-family:'Share Tech Mono',monospace; font-size:0.65rem; margin-top:2px; }
.green { color:var(--accent-green); } .red { color:var(--accent-red); }
.gold  { color:var(--accent-gold); }  .cyan { color:var(--accent-cyan); }

/* ── Signal box ── */
.sig-box { background:var(--bg-card); border:1px solid var(--border); border-radius:4px; padding:1.3rem 1.5rem; margin:1rem 0; }
.sig-box.long  { border-color:rgba(0,255,136,0.35); box-shadow:inset 0 0 30px rgba(0,255,136,0.03); }
.sig-box.short { border-color:rgba(255,45,94,0.35);  box-shadow:inset 0 0 30px rgba(255,45,94,0.03); }
.sig-box.wait  { border-color:rgba(255,215,0,0.25); }
.sig-hdr { font-family:'Orbitron',sans-serif; font-size:1rem; letter-spacing:3px; margin-bottom:0.8rem; }
.sig-hdr.long { color:var(--accent-green); } .sig-hdr.short { color:var(--accent-red); } .sig-hdr.wait { color:var(--accent-gold); }

/* ── Section title ── */
.sect { font-family:'Orbitron',sans-serif; font-size:0.7rem; letter-spacing:4px; color:var(--text-dim);
        border-bottom:1px solid var(--border); padding-bottom:0.4rem; margin:1.4rem 0 0.9rem; }

/* ── Indicator rows ── */
.ind-row { display:flex; gap:8px; align-items:center; margin:5px 0; font-family:'Share Tech Mono',monospace; font-size:0.7rem; }
.ind-n { color:var(--text-dim); width:110px; } .ind-v { color:var(--text-primary); flex:1; }
.badge { padding:2px 7px; border-radius:2px; font-size:0.6rem; font-weight:700; letter-spacing:1px; }
.badge.bull { background:rgba(0,255,136,0.12); color:var(--accent-green); border:1px solid rgba(0,255,136,0.25); }
.badge.bear { background:rgba(255,45,94,0.12);  color:var(--accent-red);   border:1px solid rgba(255,45,94,0.25); }
.badge.neut { background:rgba(255,215,0,0.08);  color:var(--accent-gold);  border:1px solid rgba(255,215,0,0.18); }

/* ── AI output ── */
.ai-box { background:var(--bg-card); border:1px solid rgba(0,245,255,0.18); border-radius:4px;
          padding:1.4rem; font-family:'Share Tech Mono',monospace; font-size:0.76rem;
          line-height:1.85; color:#a0d8ef; margin:0.8rem 0; white-space:pre-wrap; }
.ai-lbl { font-family:'Orbitron',sans-serif; font-size:0.62rem; color:var(--accent-cyan);
          letter-spacing:3px; margin-bottom:0.8rem; display:block; }

/* ── Execution panel ── */
.exec-box { background:var(--bg-card); border:1px solid rgba(255,215,0,0.2); border-radius:4px;
            padding:1.2rem 1.5rem; margin:1rem 0; }
.exec-hdr { font-family:'Orbitron',sans-serif; font-size:0.75rem; letter-spacing:3px;
            color:var(--accent-gold); margin-bottom:1rem; }

/* ── Position card ── */
.pos-card { background:rgba(0,245,255,0.03); border:1px solid var(--border); border-radius:3px;
            padding:0.7rem 1rem; margin:4px 0; font-family:'Share Tech Mono',monospace; font-size:0.68rem; }

/* ── Buttons ── */
.stButton>button { background:transparent !important; border:1px solid var(--accent-cyan) !important;
    color:var(--accent-cyan) !important; font-family:'Orbitron',sans-serif !important;
    font-size:0.68rem !important; letter-spacing:2px !important; border-radius:2px !important;
    padding:0.55rem 1.2rem !important; transition:all 0.2s !important; }
.stButton>button:hover { background:rgba(0,245,255,0.08) !important; box-shadow:0 0 12px rgba(0,245,255,0.25) !important; }

/* ── Inputs ── */
.stTextInput input, .stNumberInput input {
    background:var(--bg-card) !important; border-color:var(--border) !important;
    color:var(--text-primary) !important; font-family:'Share Tech Mono',monospace !important; font-size:0.75rem !important; }
.stSelectbox>div>div { background:var(--bg-card) !important; border-color:var(--border) !important;
    color:var(--text-primary) !important; font-family:'Share Tech Mono',monospace !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# BINANCE PUBLIC DATA LAYER
# ══════════════════════════════════════════════════════════════
BINANCE = "https://api.binance.com"

@st.cache_data(ttl=60)
def fetch_klines(symbol: str, interval: str, limit: int = 200) -> pd.DataFrame:
    try:
        r = requests.get(f"{BINANCE}/api/v3/klines",
                         params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=10)
        r.raise_for_status()
        cols = ["open_time","open","high","low","close","volume",
                "close_time","quote_vol","trades","taker_buy","taker_quote","_"]
        df = pd.DataFrame(r.json(), columns=cols)
        for c in ["open","high","low","close","volume"]:
            df[c] = df[c].astype(float)
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        return df.set_index("open_time")
    except Exception as e:
        st.error(f"Market data error: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=30)
def fetch_ticker(symbol: str) -> dict:
    try:
        r = requests.get(f"{BINANCE}/api/v3/ticker/24hr", params={"symbol": symbol}, timeout=5)
        return r.json()
    except:
        return {}

@st.cache_data(ttl=20)
def fetch_orderbook(symbol: str) -> dict:
    try:
        r = requests.get(f"{BINANCE}/api/v3/depth", params={"symbol": symbol, "limit": 20}, timeout=5)
        return r.json()
    except:
        return {}

# ══════════════════════════════════════════════════════════════
# TECHNICAL INDICATORS
# ══════════════════════════════════════════════════════════════
def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 50:
        return df
    c, h, lo, v = df["close"], df["high"], df["low"], df["volume"]

    df["ema9"]   = ta.trend.EMAIndicator(c, 9).ema_indicator()
    df["ema21"]  = ta.trend.EMAIndicator(c, 21).ema_indicator()
    df["ema50"]  = ta.trend.EMAIndicator(c, 50).ema_indicator()
    df["ema200"] = ta.trend.EMAIndicator(c, 200).ema_indicator()
    df["sma20"]  = ta.trend.SMAIndicator(c, 20).sma_indicator()

    df["rsi"]    = ta.momentum.RSIIndicator(c, 14).rsi()
    stoch = ta.momentum.StochasticOscillator(h, lo, c, 14, 3)
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()

    macd = ta.trend.MACD(c, 26, 12, 9)
    df["macd"]      = macd.macd()
    df["macd_sig"]  = macd.macd_signal()
    df["macd_hist"] = macd.macd_diff()

    bb = ta.volatility.BollingerBands(c, 20, 2)
    df["bb_up"]  = bb.bollinger_hband()
    df["bb_lo"]  = bb.bollinger_lband()
    df["bb_mid"] = bb.bollinger_mavg()
    df["bb_pct"] = bb.bollinger_pband()
    df["atr"]    = ta.volatility.AverageTrueRange(h, lo, c, 14).average_true_range()

    df["obv"]    = ta.volume.OnBalanceVolumeIndicator(c, v).on_balance_volume()
    df["vwap"]   = (c * v).cumsum() / v.cumsum()

    adx = ta.trend.ADXIndicator(h, lo, c, 14)
    df["adx"]     = adx.adx()
    df["adx_pos"] = adx.adx_pos()
    df["adx_neg"] = adx.adx_neg()

    return df

# ══════════════════════════════════════════════════════════════
# SIGNAL ENGINE
# ══════════════════════════════════════════════════════════════
def generate_signal(df4h: pd.DataFrame, df15m: pd.DataFrame) -> dict:
    blank = {"direction": "WAIT", "confidence": 0, "reasons": [],
             "tp": 0, "sl": 0, "rr": 0, "price": 0,
             "trend_strength": "WEAK", "adx": 0,
             "rsi_4h": 50, "rsi_15m": 50, "macd_hist_4h": 0,
             "atr": 0, "bb_pct": 0.5}
    if df4h.empty or df15m.empty:
        return blank

    r4, r15 = df4h.iloc[-1], df15m.iloc[-1]
    price   = r15["close"]
    reasons = []
    score   = 0

    # 4H EMA stack
    if r4["ema9"] > r4["ema21"] > r4["ema50"]:
        score += 3; reasons.append("4H EMA bullish stack ✓")
    elif r4["ema9"] < r4["ema21"] < r4["ema50"]:
        score -= 3; reasons.append("4H EMA bearish stack ✓")

    # 4H RSI
    if r4["rsi"] > 55:   score += 1; reasons.append(f"4H RSI bullish ({r4['rsi']:.1f})")
    elif r4["rsi"] < 45: score -= 1; reasons.append(f"4H RSI bearish ({r4['rsi']:.1f})")

    # 4H MACD
    if r4["macd"] > r4["macd_sig"] and r4["macd_hist"] > 0:
        score += 2; reasons.append("4H MACD bullish")
    elif r4["macd"] < r4["macd_sig"] and r4["macd_hist"] < 0:
        score -= 2; reasons.append("4H MACD bearish")

    # 15M momentum
    if r15["rsi"] > 50 and r15["stoch_k"] > r15["stoch_d"]:
        score += 2; reasons.append("15M momentum bullish")
    elif r15["rsi"] < 50 and r15["stoch_k"] < r15["stoch_d"]:
        score -= 2; reasons.append("15M momentum bearish")

    # 15M EMA
    if r15["ema9"] > r15["ema21"]:  score += 1; reasons.append("15M EMA9 > EMA21")
    elif r15["ema9"] < r15["ema21"]:score -= 1; reasons.append("15M EMA9 < EMA21")

    # Volume spike
    avg_vol = df15m["volume"].tail(20).mean()
    if r15["volume"] > avg_vol * 1.3:
        score += 1; reasons.append("Volume spike confirmation")

    # VWAP
    if r15["close"] > r15["vwap"]:  score += 1; reasons.append("Price above VWAP")
    elif r15["close"] < r15["vwap"]:score -= 1; reasons.append("Price below VWAP")

    adx_val = float(r4["adx"]) if not pd.isna(r4["adx"]) else 20
    atr     = float(r15["atr"]) if not pd.isna(r15["atr"]) else price * 0.005

    if score >= 4:
        direction, tp, sl = "LONG",  price + atr * 3, price - atr * 1.5
    elif score <= -4:
        direction, tp, sl = "SHORT", price - atr * 3, price + atr * 1.5
    else:
        direction, tp, sl = "WAIT",  price, price

    rr         = abs(tp - price) / abs(sl - price) if sl != price else 0
    confidence = min(abs(score) / 11 * 100, 95)

    return {
        "direction": direction, "confidence": confidence, "reasons": reasons,
        "tp": tp, "sl": sl, "rr": rr, "price": price,
        "trend_strength": "STRONG" if adx_val > 25 else "WEAK",
        "adx": adx_val, "rsi_4h": float(r4["rsi"]),
        "rsi_15m": float(r15["rsi"]), "macd_hist_4h": float(r4["macd_hist"]),
        "atr": atr, "bb_pct": float(r15["bb_pct"]),
    }

# ══════════════════════════════════════════════════════════════
# CHART BUILDER
# ══════════════════════════════════════════════════════════════
def build_chart(df: pd.DataFrame, symbol: str, tf: str, signal: dict = None) -> go.Figure:
    if df.empty:
        return go.Figure()

    fig = make_subplots(rows=3, cols=1, row_heights=[0.58, 0.22, 0.2],
                        vertical_spacing=0.025, shared_xaxes=True)

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"],
        name="Price",
        increasing_fillcolor="#00ff88", increasing_line_color="#00ff88",
        decreasing_fillcolor="#ff2d5e", decreasing_line_color="#ff2d5e",
        line=dict(width=1)
    ), row=1, col=1)

    for ema, color, dash in [("ema9","#00f5ff","solid"),("ema21","#ffd700","solid"),
                              ("ema50","#ff6b35","solid"),("ema200","#a855f7","dot")]:
        if ema in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[ema], name=ema.upper(),
                line=dict(color=color, width=1, dash=dash), opacity=0.85), row=1, col=1)

    if "bb_up" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_up"], showlegend=False,
            line=dict(color="rgba(0,245,255,0.25)", width=1, dash="dash")), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_lo"], showlegend=False,
            line=dict(color="rgba(0,245,255,0.25)", width=1, dash="dash"),
            fill="tonexty", fillcolor="rgba(0,245,255,0.02)"), row=1, col=1)

    if signal and signal.get("direction") != "WAIT":
        c_sig = "#00ff88" if signal["direction"] == "LONG" else "#ff2d5e"
        fig.add_hline(y=signal["tp"], line=dict(color="#00ff88", width=1, dash="dash"),
            annotation_text=f"TP ${signal['tp']:,.0f}", annotation_font_color="#00ff88", row=1, col=1)
        fig.add_hline(y=signal["sl"], line=dict(color="#ff2d5e", width=1, dash="dash"),
            annotation_text=f"SL ${signal['sl']:,.0f}", annotation_font_color="#ff2d5e", row=1, col=1)
        fig.add_hline(y=signal["price"], line=dict(color=c_sig, width=1.5),
            annotation_text=f"ENTRY ${signal['price']:,.0f}", annotation_font_color=c_sig, row=1, col=1)

    vol_c = ["#00ff88" if c >= o else "#ff2d5e" for c, o in zip(df["close"], df["open"])]
    fig.add_trace(go.Bar(x=df.index, y=df["volume"], showlegend=False,
        marker_color=vol_c, marker_opacity=0.55), row=2, col=1)

    if "rsi" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["rsi"], name="RSI",
            line=dict(color="#ffd700", width=1.5)), row=3, col=1)
        for lvl, clr in [(70, "rgba(255,45,94,0.4)"), (30, "rgba(0,255,136,0.4)"),
                         (50, "rgba(255,255,255,0.1)")]:
            fig.add_hline(y=lvl, line=dict(color=clr, width=1, dash="dot"), row=3, col=1)

    fig.update_layout(
        paper_bgcolor="#020810", plot_bgcolor="#07111e",
        font=dict(family="Share Tech Mono", size=10, color="#5a8fa8"),
        xaxis_rangeslider_visible=False, height=510,
        legend=dict(bgcolor="rgba(0,0,0,0)", font_size=9, orientation="h", y=1.02),
        margin=dict(l=60, r=20, t=30, b=20),
        title=dict(text=f"  {symbol} · {tf}", font=dict(family="Orbitron", size=11, color="#00f5ff"), x=0.01)
    )
    for ax in ["xaxis", "xaxis2", "xaxis3", "yaxis", "yaxis2", "yaxis3"]:
        fig.update_layout(**{ax: dict(gridcolor="rgba(0,245,255,0.04)", linecolor="rgba(0,245,255,0.08)")})

    return fig

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='font-family:Orbitron,sans-serif;font-size:0.95rem;color:#00f5ff;
                letter-spacing:4px;padding:0.4rem 0 1.2rem;
                border-bottom:1px solid rgba(0,245,255,0.12);margin-bottom:1rem;'>
    ⚡ APEX CONTROL
    </div>
    """, unsafe_allow_html=True)

    # ── LOGIN GATE ──────────────────────────
    render_login()

    # ── AI PROVIDER ─────────────────────────
    render_provider_selector()

    # ── BROKER ──────────────────────────────
    render_broker_selector()

    # ── MARKET SETTINGS ─────────────────────
    st.markdown('<div class="section-title">MARKET</div>', unsafe_allow_html=True)
    asset      = st.selectbox("Asset", ["BTCUSDT", "ETHUSDT"], label_visibility="collapsed")
    primary_tf = st.selectbox("Primary TF", ["4h", "15m", "1h", "1d"])

    # ── RISK SETTINGS ───────────────────────
    st.markdown('<div class="section-title">RISK MGMT</div>', unsafe_allow_html=True)
    account_size = st.number_input("Account ($)", value=100000, step=10000)
    risk_pct     = st.slider("Risk %", 0.5, 5.0, 1.5, 0.5)
    leverage     = st.slider("Leverage", 1, 50, 10)

    # ── AUTO REFRESH ────────────────────────
    st.markdown('<div class="section-title">REFRESH</div>', unsafe_allow_html=True)
    auto_refresh = st.checkbox("Auto (60s)", value=False)

    st.markdown('<br>', unsafe_allow_html=True)
    run_btn = st.button("▶  RUN ANALYSIS")

    st.markdown("""
    <div style='position:fixed;bottom:0.8rem;left:0;right:0;text-align:center;
                font-family:Share Tech Mono;font-size:0.55rem;color:#0d2233;letter-spacing:1px;'>
    APEX v3.0 · EDUCATIONAL USE ONLY<br>NOT FINANCIAL ADVICE
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div class="apex-header">
    <h1>⚡ APEX TRADING AI</h1>
    <div class="sub">MULTI-TIMEFRAME · MULTI-BROKER · AI-POWERED FUTURES INTELLIGENCE</div>
</div>
""", unsafe_allow_html=True)

if auto_refresh:
    time.sleep(1)
    st.rerun()

# ══════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════
if run_btn or "signal_cache" not in st.session_state:
    with st.spinner("FETCHING MARKET DATA..."):
        df4h_raw  = fetch_klines(asset, "4h", 200)
        df15m_raw = fetch_klines(asset, "15m", 200)
        ticker    = fetch_ticker(asset)
        ob        = fetch_orderbook(asset)
        df4h      = compute_indicators(df4h_raw.copy())
        df15m     = compute_indicators(df15m_raw.copy())
        signal    = generate_signal(df4h, df15m)

        st.session_state.update({
            "df4h": df4h, "df15m": df15m,
            "ticker": ticker, "ob": ob,
            "signal_cache": signal, "asset": asset,
            "last_update": datetime.now().strftime("%H:%M:%S"),
        })

df4h        = st.session_state.get("df4h",  pd.DataFrame())
df15m       = st.session_state.get("df15m", pd.DataFrame())
ticker      = st.session_state.get("ticker", {})
ob          = st.session_state.get("ob", {})
signal      = st.session_state.get("signal_cache", {"direction":"WAIT","confidence":0,"reasons":[],"tp":0,"sl":0,"rr":0,"price":0,"trend_strength":"WEAK","adx":0,"rsi_4h":50,"rsi_15m":50,"macd_hist_4h":0,"atr":0,"bb_pct":0.5})
last_update = st.session_state.get("last_update", "--:--:--")

# ══════════════════════════════════════════════════════════════
# TOP METRICS
# ══════════════════════════════════════════════════════════════
price_now = float(ticker.get("lastPrice", 0))
price_chg = float(ticker.get("priceChangePercent", 0))
high_24h  = float(ticker.get("highPrice", 0))
low_24h   = float(ticker.get("lowPrice", 0))
chg_color = "green" if price_chg >= 0 else "red"
chg_arrow = "▲" if price_chg >= 0 else "▼"

sig_dir       = signal.get("direction", "WAIT")
sig_card_cls  = "bull" if sig_dir == "LONG" else ("bear" if sig_dir == "SHORT" else "neut")
sig_val_color = "green" if sig_dir == "LONG" else ("red" if sig_dir == "SHORT" else "gold")

# Position sizing
risk_usd = account_size * (risk_pct / 100)
sl_dist  = abs(signal.get("price", 0) - signal.get("sl", 0))
pos_size = risk_usd / sl_dist if sl_dist > 0 else 0
pos_usd  = pos_size * signal.get("price", 0)

# Account equity (if broker connected)
acct   = st.session_state.get("broker_account", {})
equity = acct.get("equity", 0)
upnl   = acct.get("pnl", 0)

cols = st.columns(6)
metrics = [
    (st.session_state.get("asset", asset), f"${price_now:,.2f}",        f"{chg_arrow} {abs(price_chg):.2f}%", chg_color, "info"),
    ("24H HIGH",      f"${high_24h:,.2f}",  "",                           "cyan",            "info"),
    ("24H LOW",       f"${low_24h:,.2f}",   "",                           "cyan",            "info"),
    ("SIGNAL",        sig_dir,              f"{signal.get('confidence',0):.0f}% conf",        sig_val_color, sig_card_cls),
    ("R : R",         f"{signal.get('rr',0):.2f}x", "per trade",         "gold",            "neut"),
    ("POSITION",      f"${pos_usd:,.0f}",   f"{pos_size:.4f} units",      "cyan",            "info"),
]
for col, (lbl, val, dlt, vc, cc) in zip(cols, metrics):
    with col:
        st.markdown(f'<div class="mc {cc}"><div class="mc-label">{lbl}</div>'
                    f'<div class="mc-val {vc}">{val}</div>'
                    f'<div class="mc-delta" style="color:#5a8fa8;">{dlt}</div></div>',
                    unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# SIGNAL BOX
# ══════════════════════════════════════════════════════════════
sig_cls  = sig_dir.lower() if sig_dir in ["LONG","SHORT"] else "wait"
sig_icon = "▲ " if sig_dir == "LONG" else ("▼ " if sig_dir == "SHORT" else "⏸ ")
ep, tp, sl = signal.get("price",0), signal.get("tp",0), signal.get("sl",0)
tp_pct = ((tp-ep)/ep*100) if ep > 0 else 0
sl_pct = ((sl-ep)/ep*100) if ep > 0 else 0

reasons_html = "".join([f'<span style="display:block;margin:2px 0;color:#5a8fa8;">→ {r}</span>'
                         for r in signal.get("reasons", [])])

st.markdown(f"""
<div class="sig-box {sig_cls}">
    <div class="sig-hdr {sig_cls}">{sig_icon}APEX SIGNAL: {sig_dir} &nbsp;|&nbsp; CONFIDENCE: {signal.get('confidence',0):.0f}%</div>
    <div style="display:flex;gap:2.5rem;flex-wrap:wrap;margin-bottom:0.8rem;">
        <div><span class="mc-label">ENTRY</span><br>
             <span style="font-family:Orbitron;font-size:0.95rem;color:#e0f4ff;">${ep:,.2f}</span></div>
        <div><span class="mc-label">TAKE PROFIT</span><br>
             <span style="font-family:Orbitron;font-size:0.95rem;color:#00ff88;">${tp:,.2f} ({tp_pct:+.2f}%)</span></div>
        <div><span class="mc-label">STOP LOSS</span><br>
             <span style="font-family:Orbitron;font-size:0.95rem;color:#ff2d5e;">${sl:,.2f} ({sl_pct:+.2f}%)</span></div>
        <div><span class="mc-label">R:R</span><br>
             <span style="font-family:Orbitron;font-size:0.95rem;color:#ffd700;">{signal.get('rr',0):.2f}x</span></div>
        <div><span class="mc-label">ADX</span><br>
             <span style="font-family:Orbitron;font-size:0.95rem;color:#a855f7;">{signal.get('adx',0):.1f} ({signal.get('trend_strength','—')})</span></div>
    </div>
    <div style="font-family:Share Tech Mono;font-size:0.7rem;">{reasons_html}</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# MAIN TABS
# ══════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 4H CHART", "📊 15M CHART", "📈 INDICATORS",
    "⚡ AI ANALYSIS", "🏦 EXECUTION"
])

# ── TAB 1: 4H ──
with tab1:
    fig4h = build_chart(df4h, asset, "4H", signal if primary_tf == "4h" else None)
    st.plotly_chart(fig4h, use_container_width=True)

# ── TAB 2: 15M ──
with tab2:
    fig15m = build_chart(df15m, asset, "15M", signal if primary_tf == "15m" else None)
    st.plotly_chart(fig15m, use_container_width=True)

# ── TAB 3: INDICATORS ──
with tab3:
    if not df4h.empty and not df15m.empty:
        r4, r15 = df4h.iloc[-1], df15m.iloc[-1]

        def _badge(v, bull, bear, inv=False):
            if inv: return "bull" if v < bear else ("bear" if v > bull else "neut")
            return "bull" if v > bull else ("bear" if v < bear else "neut")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="sect">4H TIMEFRAME</div>', unsafe_allow_html=True)
            for nm, vl, bc in [
                ("RSI(14)",    f"{r4['rsi']:.1f}",          _badge(r4['rsi'],55,45)),
                ("MACD Hist",  f"{r4['macd_hist']:.2f}",    "bull" if r4['macd_hist']>0 else "bear"),
                ("ADX",        f"{r4['adx']:.1f}",          "bull" if r4['adx']>25 else "neut"),
                ("EMA9",       f"${r4['ema9']:,.0f}",        "bull" if r4['close']>r4['ema9'] else "bear"),
                ("EMA21",      f"${r4['ema21']:,.0f}",       "bull" if r4['close']>r4['ema21'] else "bear"),
                ("EMA50",      f"${r4['ema50']:,.0f}",       "bull" if r4['close']>r4['ema50'] else "bear"),
                ("EMA200",     f"${r4['ema200']:,.0f}",      "bull" if r4['close']>r4['ema200'] else "bear"),
                ("BB %B",      f"{r4['bb_pct']:.2f}",        _badge(r4['bb_pct'],0.8,0.2)),
                ("ADX+DI",     f"{r4['adx_pos']:.1f}",       "bull" if r4['adx_pos']>r4['adx_neg'] else "bear"),
            ]:
                lbl = "BULL" if bc=="bull" else ("BEAR" if bc=="bear" else "NEUT")
                st.markdown(f'<div class="ind-row"><span class="ind-n">{nm}</span>'
                            f'<span class="ind-v">{vl}</span>'
                            f'<span class="badge {bc}">{lbl}</span></div>', unsafe_allow_html=True)

        with col_b:
            st.markdown('<div class="sect">15M TIMEFRAME</div>', unsafe_allow_html=True)
            for nm, vl, bc in [
                ("RSI(14)",    f"{r15['rsi']:.1f}",          _badge(r15['rsi'],55,45)),
                ("Stoch %K",   f"{r15['stoch_k']:.1f}",      _badge(r15['stoch_k'],60,40)),
                ("Stoch %D",   f"{r15['stoch_d']:.1f}",      _badge(r15['stoch_d'],60,40)),
                ("MACD Hist",  f"{r15['macd_hist']:.2f}",    "bull" if r15['macd_hist']>0 else "bear"),
                ("ATR",        f"${r15['atr']:,.2f}",         "neut"),
                ("EMA9",       f"${r15['ema9']:,.0f}",        "bull" if r15['close']>r15['ema9'] else "bear"),
                ("EMA21",      f"${r15['ema21']:,.0f}",       "bull" if r15['close']>r15['ema21'] else "bear"),
                ("VWAP",       f"${r15['vwap']:,.0f}",        "bull" if r15['close']>r15['vwap'] else "bear"),
                ("BB %B",      f"{r15['bb_pct']:.2f}",        _badge(r15['bb_pct'],0.8,0.2)),
            ]:
                lbl = "BULL" if bc=="bull" else ("BEAR" if bc=="bear" else "NEUT")
                st.markdown(f'<div class="ind-row"><span class="ind-n">{nm}</span>'
                            f'<span class="ind-v">{vl}</span>'
                            f'<span class="badge {bc}">{lbl}</span></div>', unsafe_allow_html=True)

    # Order Book
    st.markdown('<div class="sect">ORDER BOOK DEPTH</div>', unsafe_allow_html=True)
    if ob and "bids" in ob:
        bids = pd.DataFrame(ob["bids"][:15], columns=["price","qty"]).astype(float)
        asks = pd.DataFrame(ob["asks"][:15], columns=["price","qty"]).astype(float)
        fig_ob = go.Figure()
        fig_ob.add_trace(go.Bar(x=bids["price"], y=bids["qty"], name="BIDS",
            marker_color="rgba(0,255,136,0.55)", marker_line_color="rgba(0,255,136,0.8)", marker_line_width=0.5))
        fig_ob.add_trace(go.Bar(x=asks["price"], y=asks["qty"], name="ASKS",
            marker_color="rgba(255,45,94,0.55)",  marker_line_color="rgba(255,45,94,0.8)", marker_line_width=0.5))
        fig_ob.update_layout(paper_bgcolor="#020810", plot_bgcolor="#07111e",
            font=dict(family="Share Tech Mono", size=10, color="#5a8fa8"),
            height=200, margin=dict(l=40,r=20,t=15,b=25),
            barmode="overlay", legend=dict(orientation="h", y=1.08))
        fig_ob.update_xaxes(gridcolor="rgba(0,245,255,0.04)")
        fig_ob.update_yaxes(gridcolor="rgba(0,245,255,0.04)")
        st.plotly_chart(fig_ob, use_container_width=True)

# ── TAB 4: AI ANALYSIS ──
with tab4:
    st.markdown('<div class="sect">AI HEDGE FUND ANALYSIS</div>', unsafe_allow_html=True)

    # Provider + model status
    prov  = st.session_state.get("ai_provider", "—")
    mdl   = st.session_state.get("ai_model",    "—")
    has_key = bool(st.session_state.get("provider_api_key"))
    status_color = "#00ff88" if has_key else "#ff2d5e"
    status_txt   = f"✓ {prov} · {mdl}" if has_key else f"✗ No key — {prov}"

    st.markdown(
        f'<div style="font-family:Share Tech Mono;font-size:0.65rem;color:{status_color};'
        f'margin-bottom:1rem;">{status_txt}</div>',
        unsafe_allow_html=True
    )

    col_a1, col_a2 = st.columns([2, 1])
    with col_a1:
        if st.button("⚡  GENERATE AI ANALYSIS", key="_ai_run"):
            with st.spinner(f"APEX AI ({prov}) ANALYZING..."):
                analysis = get_ai_analysis(asset, signal, df4h, df15m)
                st.session_state["ai_analysis"] = analysis
    with col_a2:
        st.markdown(f'<div style="font-family:Share Tech Mono;font-size:0.62rem;'
                    f'color:#1a3a4a;padding-top:0.8rem;">UPDATED: {last_update}</div>',
                    unsafe_allow_html=True)

    if "ai_analysis" in st.session_state:
        st.markdown(f"""
        <div class="ai-box">
            <span class="ai-lbl">◈ APEX AI · MARKET INTELLIGENCE REPORT</span>
{st.session_state["ai_analysis"]}
        </div>
        """, unsafe_allow_html=True)

# ── TAB 5: EXECUTION ──
with tab5:
    st.markdown('<div class="sect">TRADE EXECUTION</div>', unsafe_allow_html=True)

    broker_client  = st.session_state.get("broker_client")
    broker_name    = st.session_state.get("broker_name", "—")
    broker_testnet = st.session_state.get("broker_testnet", True)
    broker_cfg     = st.session_state.get("broker_cfg", {})
    broker_type    = broker_cfg.get("type", "ccxt")

    if broker_client:
        acct_live = st.session_state.get("broker_account", {})
        eq    = acct_live.get("equity", 0)
        free  = acct_live.get("free_margin", 0)
        pnl   = acct_live.get("pnl", 0)
        npos  = acct_live.get("position_count", 0)
        curr  = acct_live.get("currency", "USDT")
        pnl_c = "#00ff88" if pnl >= 0 else "#ff2d5e"

        # ── Indian broker badge ──
        if broker_type in ("delta", "coindcx"):
            ind_note = (
                "Futures + Perpetuals + Options · INR settlement · Up to 100x leverage"
                if broker_type == "delta" else
                "Spot + Margin · INR pairs · Up to 5x leverage · KYC verified users only"
            )
            st.markdown(
                f'<div style="background:rgba(255,107,53,0.08);border:1px solid rgba(255,107,53,0.25);'
                f'border-radius:3px;padding:0.5rem 1rem;margin-bottom:0.8rem;'
                f'font-family:Share Tech Mono;font-size:0.62rem;color:#ff6b35;">'
                f'🇮🇳 {broker_name}<br><span style="color:#5a8fa8;">{ind_note}</span></div>',
                unsafe_allow_html=True
            )

        # Mode badge
        mode_badge = (
            '<span style="background:rgba(255,215,0,0.15);color:#ffd700;border:1px solid rgba(255,215,0,0.3);'
            'padding:2px 8px;border-radius:2px;font-size:0.6rem;font-family:Share Tech Mono;">TESTNET</span>'
            if broker_testnet else
            '<span style="background:rgba(255,45,94,0.15);color:#ff2d5e;border:1px solid rgba(255,45,94,0.3);'
            'padding:2px 8px;border-radius:2px;font-size:0.6rem;font-family:Share Tech Mono;">🔴 LIVE</span>'
        )

        # ── Account summary banner ──
        st.markdown(f"""
        <div style="background:rgba(0,255,136,0.04);border:1px solid rgba(0,255,136,0.2);
                    border-radius:4px;padding:1rem 1.5rem;margin-bottom:1.2rem;display:flex;gap:2.5rem;flex-wrap:wrap;">
            <div><span class="mc-label">BROKER</span><br>
                 <span style="font-family:Orbitron;font-size:0.85rem;color:#00f5ff;">{broker_name}</span>
                 &nbsp;{mode_badge}</div>
            <div><span class="mc-label">EQUITY ({curr})</span><br>
                 <span style="font-family:Orbitron;font-size:0.9rem;color:#e0f4ff;">{eq:,.2f}</span></div>
            <div><span class="mc-label">FREE MARGIN</span><br>
                 <span style="font-family:Orbitron;font-size:0.9rem;color:#e0f4ff;">{free:,.2f}</span></div>
            <div><span class="mc-label">UNREALIZED PnL</span><br>
                 <span style="font-family:Orbitron;font-size:0.9rem;color:{pnl_c};">{pnl:+,.2f}</span></div>
            <div><span class="mc-label">POSITIONS / HOLDINGS</span><br>
                 <span style="font-family:Orbitron;font-size:0.9rem;color:#ffd700;">{npos}</span></div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔄  REFRESH ACCOUNT", key="_acct_refresh"):
            with st.spinner("Refreshing..."):
                refresh_account()
                st.rerun()

        # ── Positions / Holdings ──────────────────────────────────
        positions = acct_live.get("positions", [])
        if positions:
            if broker_type == "coindcx":
                # CoinDCX shows spot holdings
                st.markdown('<div class="sect">SPOT HOLDINGS (CoinDCX)</div>', unsafe_allow_html=True)
                for h in positions:
                    sym_h = h.get("symbol","")
                    bal_h = h.get("balance", 0)
                    lck_h = h.get("locked", 0)
                    st.markdown(
                        f'<div class="pos-card">'
                        f'<span style="color:#00f5ff;font-weight:700;">{sym_h}</span>'
                        f'&nbsp;·&nbsp;Balance: {bal_h:,.8f}'
                        f'&nbsp;·&nbsp;Locked: {lck_h:,.8f}</div>',
                        unsafe_allow_html=True
                    )

            elif broker_type == "delta":
                # Delta shows futures positions
                st.markdown('<div class="sect">FUTURES POSITIONS (Delta Exchange)</div>', unsafe_allow_html=True)
                for pos in positions:
                    sym_p  = pos.get("product_symbol", pos.get("symbol",""))
                    side_p = "LONG" if float(pos.get("size", 0) or 0) > 0 else "SHORT"
                    size_p = abs(float(pos.get("size", 0) or 0))
                    ep_p   = float(pos.get("entry_price", 0) or 0)
                    liq_p  = float(pos.get("liquidation_price", 0) or 0)
                    upnl_p = float(pos.get("unrealized_pnl", 0) or 0)
                    pnl_cp = "#00ff88" if upnl_p >= 0 else "#ff2d5e"
                    side_cp= "#00ff88" if side_p == "LONG" else "#ff2d5e"
                    st.markdown(
                        f'<div class="pos-card">'
                        f'<span style="color:{side_cp};font-weight:700;">{side_p}</span>'
                        f'&nbsp;{sym_p}&nbsp;·&nbsp;Size: {size_p}'
                        f'&nbsp;·&nbsp;Entry: ${ep_p:,.2f}'
                        f'&nbsp;·&nbsp;Liq: ${liq_p:,.2f}'
                        f'&nbsp;·&nbsp;<span style="color:{pnl_cp};">PnL ${upnl_p:+,.2f}</span></div>',
                        unsafe_allow_html=True
                    )

            else:
                # CCXT generic positions
                st.markdown('<div class="sect">OPEN POSITIONS</div>', unsafe_allow_html=True)
                for pos in positions:
                    sym_p  = pos.get("symbol","")
                    side_p = pos.get("side","")
                    size_p = pos.get("contracts", pos.get("size", 0))
                    upnl_p = float(pos.get("unrealizedPnl", 0) or 0)
                    ep_p   = float(pos.get("entryPrice", 0) or 0)
                    liq_p  = float(pos.get("liquidationPrice", 0) or 0)
                    pnl_cp = "#00ff88" if upnl_p >= 0 else "#ff2d5e"
                    side_cp= "#00ff88" if side_p == "long" else "#ff2d5e"
                    st.markdown(
                        f'<div class="pos-card">'
                        f'<span style="color:{side_cp};font-weight:700;">{side_p.upper()}</span>'
                        f'&nbsp;{sym_p}&nbsp;·&nbsp;Size: {size_p}'
                        f'&nbsp;·&nbsp;Entry: ${ep_p:,.2f}'
                        f'&nbsp;·&nbsp;Liq: ${liq_p:,.2f}'
                        f'&nbsp;·&nbsp;<span style="color:{pnl_cp};">PnL ${upnl_p:+,.2f}</span></div>',
                        unsafe_allow_html=True
                    )

        # ── CoinDCX-specific note ─────────────────────────────────
        if broker_type == "coindcx":
            st.markdown(
                '<div style="background:rgba(0,82,204,0.1);border:1px solid rgba(0,82,204,0.3);'
                'border-radius:3px;padding:0.8rem 1rem;margin:0.8rem 0;'
                'font-family:Share Tech Mono;font-size:0.68rem;color:#5a8fa8;">'
                '<b style="color:#00f5ff;">ℹ CoinDCX Trading Notes:</b><br>'
                '• Spot orders execute immediately at market price<br>'
                '• Margin orders support SL + Target Price natively<br>'
                '• Max leverage: 5x on margin pairs<br>'
                '• All pairs priced in INR (₹)<br>'
                '• Signal TP/SL are approximate — set exact values in CoinDCX app for precision</div>',
                unsafe_allow_html=True
            )

        # ── Order placement panel ─────────────────────────────────
        st.markdown('<div class="sect">PLACE ORDER</div>', unsafe_allow_html=True)

        if sig_dir == "WAIT":
            st.markdown(
                '<div style="font-family:Share Tech Mono;font-size:0.72rem;color:#ffd700;">'
                '⏸ Signal is WAIT — no trade conditions met. Run analysis first.</div>',
                unsafe_allow_html=True
            )
        else:
            sig_c = "#00ff88" if sig_dir == "LONG" else "#ff2d5e"

            # Show different order details depending on broker type
            if broker_type == "coindcx":
                order_type_label = "MARGIN ORDER (Spot with leverage)"
                qty_label        = "QTY (coins)"
                lev_label        = f"LEVERAGE (max {broker_cfg.get('leverage_max',5)}x)"
                qty_display      = f"{pos_size:.5f}"
                sym_display      = broker_cfg.get("symbol_map", {}).get(asset, asset)
            elif broker_type == "delta":
                order_type_label = "FUTURES BRACKET ORDER"
                qty_label        = "CONTRACTS (lots)"
                lev_label        = f"LEVERAGE (max {broker_cfg.get('leverage_max',100)}x)"
                qty_display      = f"{max(1, int(pos_size))}"
                sym_display      = broker_cfg.get("symbol_map", {}).get(asset, "BTCUSD")
            else:
                order_type_label = "FUTURES BRACKET ORDER"
                qty_label        = "QTY"
                lev_label        = "LEVERAGE"
                qty_display      = f"{pos_size:.5f}"
                sym_display      = asset

            st.markdown(f"""
            <div class="exec-box">
                <div class="exec-hdr">{order_type_label}</div>
                <div style="display:flex;gap:2rem;flex-wrap:wrap;font-family:Share Tech Mono;font-size:0.72rem;">
                    <div><span class="mc-label">SYMBOL</span><br>
                         <span style="font-family:Orbitron;font-size:0.85rem;color:#a855f7;">{sym_display}</span></div>
                    <div><span class="mc-label">DIRECTION</span><br>
                         <span style="font-family:Orbitron;font-size:1rem;color:{sig_c};">{sig_dir}</span></div>
                    <div><span class="mc-label">ENTRY</span><br>
                         <span style="font-family:Orbitron;color:#e0f4ff;">${ep:,.2f}</span></div>
                    <div><span class="mc-label">TAKE PROFIT</span><br>
                         <span style="font-family:Orbitron;color:#00ff88;">${tp:,.2f}</span></div>
                    <div><span class="mc-label">STOP LOSS</span><br>
                         <span style="font-family:Orbitron;color:#ff2d5e;">${sl:,.2f}</span></div>
                    <div><span class="mc-label">{qty_label}</span><br>
                         <span style="font-family:Orbitron;color:#ffd700;">{qty_display}</span></div>
                    <div><span class="mc-label">{lev_label}</span><br>
                         <span style="font-family:Orbitron;color:#a855f7;">{min(leverage, broker_cfg.get('leverage_max',100))}x</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            confirm = st.checkbox(
                f"✓ I confirm this {'TESTNET' if broker_testnet else '⚠ LIVE'} order on {broker_name}",
                key="_confirm_trade"
            )

            actual_qty = max(1, int(pos_size)) if broker_type == "delta" else round(pos_size, 5)

            if st.button("⚡  EXECUTE ORDER", key="_execute"):
                if not confirm:
                    st.warning("Check the confirmation box before executing.")
                else:
                    with st.spinner(f"PLACING ORDER on {broker_name}..."):
                        result = place_trade(
                            signal=signal, symbol=asset,
                            quantity=actual_qty,
                            leverage=min(leverage, broker_cfg.get("leverage_max", 100))
                        )
                    if result.get("success"):
                        eid   = result.get("entry", {}).get("id", "N/A")
                        tp_id = result.get("take_profit", {}).get("id", "—")
                        sl_id = result.get("stop_loss", {}).get("id", "—")
                        note  = result.get("note", "")
                        msg   = f"✓ ORDER PLACED — Entry ID: {eid}"
                        if tp_id != "—": msg += f" | TP: {tp_id}"
                        if sl_id != "—": msg += f" | SL: {sl_id}"
                        if note:         msg += f"\n{note}"
                        st.success(msg)
                        st.session_state["last_order"] = result
                        refresh_account()
                    else:
                        st.error(f"✗ ORDER FAILED: {result.get('error','Unknown error')}")

            if "last_order" in st.session_state:
                lo = st.session_state["last_order"]
                st.markdown('<div class="sect">LAST ORDER RESULT</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div style="font-family:Share Tech Mono;font-size:0.65rem;'
                    f'background:var(--bg-card);border:1px solid var(--border);'
                    f'border-radius:3px;padding:0.8rem 1rem;white-space:pre-wrap;color:#a0d8ef;">'
                    f'{json_pretty(lo)}</div>',
                    unsafe_allow_html=True
                )

    else:
        # No broker connected — show comparison table
        st.markdown("""
        <div style="text-align:center;padding:2.5rem 1rem;font-family:Share Tech Mono;color:#1a3a4a;">
            <div style="font-size:2rem;margin-bottom:1rem;">🏦</div>
            <div style="color:#5a8fa8;letter-spacing:2px;font-size:0.75rem;">NO BROKER CONNECTED</div>
            <div style="margin-top:0.5rem;font-size:0.65rem;">Connect a broker in the sidebar to enable execution.</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sect">SUPPORTED BROKERS</div>', unsafe_allow_html=True)
        rows = []
        for name, cfg in BROKERS.items():
            rows.append({
                "Broker":      f"{cfg['icon']} {name}",
                "Region":      "🇮🇳 India" if cfg.get("type") in ("delta","coindcx") else "🌐 Global",
                "Type":        "Futures/Perps/Options" if cfg["futures"] else "Spot/Margin",
                "Settlement":  cfg.get("settlement","USDT"),
                "Leverage":    f"{cfg['leverage_max']}x",
                "Maker Fee":   f"{cfg['fee_maker']*100:.2f}%",
                "Taker Fee":   f"{cfg['fee_taker']*100:.2f}%",
                "Testnet":     "✓" if cfg.get("testnet") else "✗",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
# JSON pretty helper (used in last order display)
# ══════════════════════════════════════════════════════════════
import json

def json_pretty(obj: dict) -> str:
    try:
        return json.dumps(obj, indent=2, default=str)
    except:
        return str(obj)

# ══════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════
st.markdown("""
<div style='text-align:center;padding:2rem 0 0.5rem;font-family:Share Tech Mono;
            font-size:0.58rem;color:#0d2233;letter-spacing:2px;
            border-top:1px solid rgba(0,245,255,0.04);margin-top:2rem;'>
APEX TRADING AI v4.0 · Delta Exchange India 🇮🇳 · CoinDCX 🇮🇳 · FOR EDUCATIONAL USE ONLY · NOT FINANCIAL ADVICE
</div>
""", unsafe_allow_html=True)
