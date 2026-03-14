"""
╔══════════════════════════════════════════════════════════════════════╗
║              APEX TRADING AI — PROVIDER & BROKER MODULE              ║
║                          ai_provider.py  v4.0                        ║
╠══════════════════════════════════════════════════════════════════════╣
║  AI Providers:                                                       ║
║   Anthropic Claude · OpenAI GPT · Google Gemini · Groq               ║
║   Ollama (Local) · Mistral AI                                        ║
╠══════════════════════════════════════════════════════════════════════╣
║  Brokers (CCXT — Global):                                            ║
║   Binance Futures · Bybit · OKX · Kraken · Deribit                   ║
║   KuCoin Futures · Hyperliquid                                       ║
╠══════════════════════════════════════════════════════════════════════╣
║  Brokers (Native REST — India):                                      ║
║   🇮🇳 Delta Exchange India  — crypto futures + options + perps       ║
║   🇮🇳 CoinDCX               — spot + margin trading                  ║
╠══════════════════════════════════════════════════════════════════════╣
║  Features:                                                           ║
║   • SHA-256 login gate                                               ║
║   • Per-broker custom REST clients (Delta, CoinDCX)                  ║
║   • CCXT unified layer for global brokers                            ║
║   • Unified place_trade() + get_account_summary() interface          ║
║   • Testnet / paper mode toggle                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import hashlib
import hmac
import time
import requests
import json
import pandas as pd
from datetime import datetime

# ══════════════════════════════════════════════════════════════
# 1. CREDENTIALS
# ══════════════════════════════════════════════════════════════

USERS: dict = {
    "admin": {
        "password_hash": hashlib.sha256("apex2025".encode()).hexdigest(),
        "role": "ADMIN", "display": "Admin",
    },
    "trader1": {
        "password_hash": hashlib.sha256("trade123".encode()).hexdigest(),
        "role": "TRADER", "display": "Trader One",
    },
}

# ══════════════════════════════════════════════════════════════
# 2. AI PROVIDER REGISTRY
# ══════════════════════════════════════════════════════════════

PROVIDERS: dict = {
    "Anthropic Claude": {
        "icon": "⚡", "key_placeholder": "sk-ant-api03-...",
        "free": False, "color": "#ff6b35",
        "models": ["claude-sonnet-4-20250514", "claude-haiku-4-5-20251001"],
        "model_default": "claude-sonnet-4-20250514",
        "docs": "https://docs.anthropic.com",
    },
    "OpenAI GPT": {
        "icon": "🤖", "key_placeholder": "sk-proj-...",
        "free": False, "color": "#10a37f",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"],
        "model_default": "gpt-4o-mini",
        "docs": "https://platform.openai.com",
    },
    "Google Gemini": {
        "icon": "💎", "key_placeholder": "AIzaSy...",
        "free": True, "color": "#4285f4",
        "models": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"],
        "model_default": "gemini-2.5-flash",
        "docs": "https://ai.google.dev",
    },
    "Groq (Free)": {
        "icon": "🚀", "key_placeholder": "gsk_...",
        "free": True, "color": "#f55036",
        "models": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "deepseek-r1-distill-llama-70b"],
        "model_default": "llama-3.3-70b-versatile",
        "docs": "https://console.groq.com",
    },
    "Ollama (Local)": {
        "icon": "🏠", "key_placeholder": "no key needed",
        "free": True, "color": "#00f5ff",
        "models": ["llama3.2", "mistral", "deepseek-r1:8b", "phi4"],
        "model_default": "llama3.2",
        "docs": "https://ollama.com",
    },
    "Mistral AI": {
        "icon": "🌊", "key_placeholder": "your-mistral-key",
        "free": False, "color": "#ff7000",
        "models": ["mistral-small-latest", "mistral-medium-latest", "open-mistral-7b"],
        "model_default": "mistral-small-latest",
        "docs": "https://console.mistral.ai",
    },
}

# ══════════════════════════════════════════════════════════════
# 3. BROKER REGISTRY
#    type: "ccxt"   → uses the CCXT unified library
#    type: "delta"  → uses Delta Exchange custom REST client
#    type: "coindcx"→ uses CoinDCX custom REST client
# ══════════════════════════════════════════════════════════════

BROKERS: dict = {
    # ── Indian Brokers (native REST, no CCXT needed) ──────────
    "Delta Exchange India 🇮🇳": {
        "type": "delta",
        "icon": "🔶",
        "futures": True,
        "needs_passphrase": False,
        "symbol_map": {
            "BTCUSDT": "BTCUSD",   # Delta uses BTCUSD symbol
            "ETHUSDT": "ETHUSD",
        },
        # Product IDs for Delta India perpetual futures
        # BTCUSD perp = 27, ETHUSD perp = 3
        "product_ids": {"BTCUSD": 27, "ETHUSD": 3},
        "testnet": True,
        "prod_url":    "https://api.india.delta.exchange",
        "testnet_url": "https://cdn-ind.testnet.deltaex.org",
        "leverage_max": 100,
        "fee_maker": 0.0002,
        "fee_taker": 0.0005,
        "docs": "https://docs.delta.exchange",
        "color": "#ff6b1a",
        "settlement": "USD / INR",
        "note": "FIU registered · INR settlement · Futures + Options + Perps",
    },
    "CoinDCX 🇮🇳": {
        "type": "coindcx",
        "icon": "🔷",
        "futures": False,  # CoinDCX is spot + margin (no perpetual futures)
        "needs_passphrase": False,
        "symbol_map": {
            "BTCUSDT": "BTCINR",   # CoinDCX trades in INR pairs
            "ETHUSDT": "ETHINR",
        },
        "testnet": False,  # CoinDCX has no public testnet
        "prod_url": "https://api.coindcx.com",
        "leverage_max": 5,
        "fee_maker": 0.001,
        "fee_taker": 0.002,
        "docs": "https://docs.coindcx.com",
        "color": "#0052cc",
        "settlement": "INR",
        "note": "Indian users only · Spot + Margin · INR pairs · KYC required",
    },
    # ── Global Brokers (CCXT) ─────────────────────────────────
    "Binance Futures": {
        "type": "ccxt", "ccxt_id": "binance",
        "icon": "🟡", "futures": True, "needs_passphrase": False,
        "symbol_map": {"BTCUSDT": "BTC/USDT:USDT", "ETHUSDT": "ETH/USDT:USDT"},
        "testnet": True, "leverage_max": 125,
        "fee_maker": 0.0002, "fee_taker": 0.0004,
        "docs": "https://binance-docs.github.io/apidocs/futures/en/",
        "color": "#f0b90b", "settlement": "USDT",
        "note": "World's largest futures exchange",
    },
    "Bybit": {
        "type": "ccxt", "ccxt_id": "bybit",
        "icon": "🟠", "futures": True, "needs_passphrase": False,
        "symbol_map": {"BTCUSDT": "BTC/USDT:USDT", "ETHUSDT": "ETH/USDT:USDT"},
        "testnet": True, "leverage_max": 100,
        "fee_maker": 0.0001, "fee_taker": 0.0006,
        "docs": "https://bybit-exchange.github.io/docs/",
        "color": "#f7941d", "settlement": "USDT",
        "note": "Low fees · strong API support",
    },
    "OKX": {
        "type": "ccxt", "ccxt_id": "okx",
        "icon": "⚫", "futures": True, "needs_passphrase": True,
        "symbol_map": {"BTCUSDT": "BTC/USDT:USDT", "ETHUSDT": "ETH/USDT:USDT"},
        "testnet": True, "leverage_max": 100,
        "fee_maker": 0.0002, "fee_taker": 0.0005,
        "docs": "https://www.okx.com/docs-v5/",
        "color": "#333333", "settlement": "USDT",
        "note": "Requires API passphrase",
    },
    "Kraken Futures": {
        "type": "ccxt", "ccxt_id": "krakenfutures",
        "icon": "🟣", "futures": True, "needs_passphrase": False,
        "symbol_map": {"BTCUSDT": "BTC/USD:USD", "ETHUSDT": "ETH/USD:USD"},
        "testnet": True, "leverage_max": 50,
        "fee_maker": 0.0002, "fee_taker": 0.0005,
        "docs": "https://docs.futures.kraken.com/",
        "color": "#5741d9", "settlement": "USD",
        "note": "EU regulated · conservative",
    },
    "Deribit": {
        "type": "ccxt", "ccxt_id": "deribit",
        "icon": "🔵", "futures": True, "needs_passphrase": False,
        "symbol_map": {"BTCUSDT": "BTC/USD:USD", "ETHUSDT": "ETH/USD:USD"},
        "testnet": True, "leverage_max": 100,
        "fee_maker": 0.0001, "fee_taker": 0.0005,
        "docs": "https://docs.deribit.com/",
        "color": "#1e88e5", "settlement": "USD",
        "note": "Best for options + perps",
    },
    "KuCoin Futures": {
        "type": "ccxt", "ccxt_id": "kucoinfutures",
        "icon": "🟢", "futures": True, "needs_passphrase": True,
        "symbol_map": {"BTCUSDT": "BTC/USDT:USDT", "ETHUSDT": "ETH/USDT:USDT"},
        "testnet": True, "leverage_max": 100,
        "fee_maker": 0.0002, "fee_taker": 0.0006,
        "docs": "https://docs.kucoin.com/futures/",
        "color": "#00b775", "settlement": "USDT",
        "note": "Wide altcoin range",
    },
    "Hyperliquid": {
        "type": "ccxt", "ccxt_id": "hyperliquid",
        "icon": "🌊", "futures": True, "needs_passphrase": False,
        "symbol_map": {"BTCUSDT": "BTC/USDC:USDC", "ETHUSDT": "ETH/USDC:USDC"},
        "testnet": True, "leverage_max": 50,
        "fee_maker": 0.0001, "fee_taker": 0.00035,
        "docs": "https://hyperliquid.gitbook.io/hyperliquid-docs/",
        "color": "#00f5ff", "settlement": "USDC",
        "note": "Decentralized on-chain perps",
    },
}

# ══════════════════════════════════════════════════════════════
# 4. LOGIN GATE
# ══════════════════════════════════════════════════════════════

def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def render_login() -> None:
    if st.session_state.get("authenticated"):
        _render_user_badge()
        return

    st.markdown("""
    <div style='text-align:center;padding:1.5rem 0 2rem;'>
        <div style='font-family:Orbitron,sans-serif;font-size:1.4rem;
                    color:#00f5ff;letter-spacing:6px;font-weight:900;'>⚡ APEX</div>
        <div style='font-family:Share Tech Mono,monospace;font-size:0.6rem;
                    color:#1a3a4a;letter-spacing:3px;margin-top:6px;'>SECURE ACCESS REQUIRED</div>
    </div>
    """, unsafe_allow_html=True)

    username = st.text_input("USERNAME", placeholder="admin  ·  trader1", key="_u")
    password = st.text_input("PASSWORD", type="password", placeholder="••••••••", key="_p")

    col1, col2 = st.columns(2)
    with col1:
        login_btn = st.button("▶  LOGIN", key="_login_btn")
    with col2:
        st.markdown(
            '<div style="font-family:Share Tech Mono;font-size:0.58rem;color:#1a3a4a;'
            'padding-top:0.75rem;line-height:1.6;">admin / apex2025<br>trader1 / trade123</div>',
            unsafe_allow_html=True
        )

    if login_btn:
        user = USERS.get(username.strip().lower())
        if user and user["password_hash"] == _hash(password):
            st.session_state.update({
                "authenticated": True,
                "username": username.strip().lower(),
                "user_display": user["display"],
                "user_role": user["role"],
            })
            st.rerun()
        else:
            st.markdown(
                '<div style="color:#ff2d5e;font-family:Share Tech Mono;font-size:0.7rem;'
                'margin-top:8px;text-align:center;">✗ INVALID CREDENTIALS</div>',
                unsafe_allow_html=True
            )
    st.stop()


def _render_user_badge() -> None:
    display = st.session_state.get("user_display", "User")
    role    = st.session_state.get("user_role", "TRADER")
    color   = "#ffd700" if role == "ADMIN" else "#00f5ff"

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div style='padding:0.4rem 0 1.2rem;border-bottom:1px solid rgba(0,245,255,0.08);margin-bottom:0.8rem;'>
            <div style='font-family:Share Tech Mono;font-size:0.58rem;color:#1a3a4a;letter-spacing:2px;'>SESSION</div>
            <div style='font-family:Orbitron,sans-serif;font-size:0.85rem;color:{color};margin-top:3px;'>{display}</div>
            <div style='font-family:Share Tech Mono;font-size:0.58rem;color:#1a3a4a;'>{role}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("⏏", key="_logout", help="Logout"):
            for k in ["authenticated","username","user_display","user_role",
                      "provider_api_key","ai_analysis","broker_client",
                      "broker_name","broker_account","broker_cfg"]:
                st.session_state.pop(k, None)
            st.rerun()


# ══════════════════════════════════════════════════════════════
# 5. AI PROVIDER SELECTOR
# ══════════════════════════════════════════════════════════════

def render_provider_selector() -> None:
    st.markdown('<div class="section-title" style="margin-top:0.2rem;">AI ENGINE</div>', unsafe_allow_html=True)

    names   = list(PROVIDERS.keys())
    current = st.session_state.get("ai_provider", "Anthropic Claude")
    idx     = names.index(current) if current in names else 0

    selected = st.selectbox("Provider", names, index=idx, key="_prov",
                            label_visibility="collapsed",
                            format_func=lambda x: f"{PROVIDERS[x]['icon']}  {x}")
    st.session_state["ai_provider"] = selected
    cfg = PROVIDERS[selected]

    free_html = (
        '<span style="background:rgba(0,255,136,0.12);color:#00ff88;border:1px solid '
        'rgba(0,255,136,0.25);padding:1px 7px;border-radius:2px;font-size:0.58rem;'
        'font-family:Share Tech Mono;">FREE</span>' if cfg["free"] else
        '<span style="background:rgba(255,107,53,0.12);color:#ff6b35;border:1px solid '
        'rgba(255,107,53,0.25);padding:1px 7px;border-radius:2px;font-size:0.58rem;'
        'font-family:Share Tech Mono;">PAID</span>'
    )
    st.markdown(
        f'<div style="margin:-4px 0 8px;display:flex;gap:8px;align-items:center;">'
        f'{free_html}&nbsp;<a href="{cfg["docs"]}" target="_blank" style="font-family:'
        f'Share Tech Mono;font-size:0.58rem;color:#1a3a4a;text-decoration:none;">docs ↗</a></div>',
        unsafe_allow_html=True
    )

    cur_model = st.session_state.get("ai_model", cfg["model_default"])
    midx = cfg["models"].index(cur_model) if cur_model in cfg["models"] else 0
    model = st.selectbox("Model", cfg["models"], index=midx, key=f"_mdl_{selected}")
    st.session_state["ai_model"] = model

    if selected != "Ollama (Local)":
        existing = st.session_state.get("provider_api_key", "")
        key_in = st.text_input("API Key", value=existing, type="password",
                               placeholder=cfg["key_placeholder"],
                               key=f"_ak_{selected}", label_visibility="collapsed")
        if key_in:
            st.session_state["provider_api_key"] = key_in
            st.markdown('<span style="color:#00ff88;font-family:Share Tech Mono;font-size:0.62rem;">✓ KEY STORED</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span style="color:#ff6b35;font-family:Share Tech Mono;font-size:0.62rem;">○ KEY REQUIRED</span>', unsafe_allow_html=True)
    else:
        host = st.text_input("Ollama Host",
                             value=st.session_state.get("ollama_host","http://localhost:11434"),
                             key="_ollama_host")
        st.session_state["ollama_host"] = host
        st.session_state["provider_api_key"] = "local"
        st.markdown('<span style="color:#00ff88;font-family:Share Tech Mono;font-size:0.62rem;">✓ LOCAL · NO KEY NEEDED</span>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# 6. BROKER SELECTOR + CONNECTION
# ══════════════════════════════════════════════════════════════

def render_broker_selector() -> None:
    st.markdown('<div class="section-title">BROKER</div>', unsafe_allow_html=True)

    broker_names    = list(BROKERS.keys())
    cur_broker      = st.session_state.get("broker_name", "Delta Exchange India 🇮🇳")
    bidx            = broker_names.index(cur_broker) if cur_broker in broker_names else 0

    selected_broker = st.selectbox("Broker", broker_names, index=bidx, key="_broker_sel",
                                   label_visibility="collapsed",
                                   format_func=lambda x: f"{BROKERS[x]['icon']}  {x}")
    bcfg = BROKERS[selected_broker]

    # Info row
    note = bcfg.get("note", "")
    st.markdown(
        f'<div style="font-family:Share Tech Mono;font-size:0.58rem;color:#1a3a4a;margin:-4px 0 6px;">'
        f'Lev: {bcfg["leverage_max"]}x · {bcfg.get("settlement","USDT")} · '
        f'<a href="{bcfg["docs"]}" target="_blank" style="color:#1a3a4a;text-decoration:none;">docs ↗</a><br>'
        f'{note}</div>',
        unsafe_allow_html=True
    )

    # Indian broker warning badge
    if bcfg["type"] in ("delta", "coindcx"):
        st.markdown(
            '<div style="background:rgba(255,107,53,0.1);border:1px solid rgba(255,107,53,0.3);'
            'border-radius:3px;padding:4px 8px;font-family:Share Tech Mono;font-size:0.6rem;'
            'color:#ff6b35;margin-bottom:6px;">🇮🇳 INDIAN BROKER · KYC + INR REQUIRED</div>',
            unsafe_allow_html=True
        )

    # Testnet toggle (not available for CoinDCX)
    if bcfg["type"] != "coindcx":
        testnet = st.checkbox("📋 Testnet / Paper Mode",
                              value=st.session_state.get("broker_testnet", True),
                              key="_testnet")
        st.session_state["broker_testnet"] = testnet
        if testnet:
            st.markdown('<div style="font-family:Share Tech Mono;font-size:0.6rem;color:#ffd700;">⚠ PAPER TRADING — NO REAL FUNDS</div>', unsafe_allow_html=True)
    else:
        st.session_state["broker_testnet"] = False
        st.markdown('<div style="font-family:Share Tech Mono;font-size:0.6rem;color:#ff6b35;">⚠ LIVE ONLY — CoinDCX has no testnet</div>', unsafe_allow_html=True)

    # Credential inputs
    bkey    = st.text_input("API Key",  type="password", placeholder="API Key",    key=f"_bk_{selected_broker}", label_visibility="collapsed")
    bsecret = st.text_input("Secret",   type="password", placeholder="API Secret", key=f"_bs_{selected_broker}", label_visibility="collapsed")

    bpass = ""
    if bcfg.get("needs_passphrase"):
        bpass = st.text_input("Passphrase", type="password", placeholder="Passphrase", key=f"_bp_{selected_broker}", label_visibility="collapsed")

    col1, col2 = st.columns(2)
    with col1:
        connect_btn = st.button("🔌 CONNECT", key="_broker_connect")
    with col2:
        if st.button("✗ CLEAR", key="_broker_disconnect"):
            for k in ["broker_client","broker_account","broker_cfg"]:
                st.session_state.pop(k, None)
            st.session_state["broker_name"] = selected_broker
            st.rerun()

    if connect_btn:
        with st.spinner(f"Connecting to {selected_broker}..."):
            client_obj, err = _connect_broker(selected_broker, bkey, bsecret, bpass,
                                              st.session_state.get("broker_testnet", True))
            if client_obj is not None:
                st.session_state["broker_client"]  = client_obj
                st.session_state["broker_name"]    = selected_broker
                st.session_state["broker_cfg"]     = bcfg
                acct = get_account_summary(client_obj, bcfg)
                st.session_state["broker_account"] = acct
                eq = acct.get("equity", 0)
                currency = "INR" if bcfg["type"] == "coindcx" else "USDT"
                st.markdown(
                    f'<div style="color:#00ff88;font-family:Share Tech Mono;font-size:0.65rem;margin-top:6px;">'
                    f'✓ CONNECTED · {currency} {eq:,.2f}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div style="color:#ff2d5e;font-family:Share Tech Mono;font-size:0.65rem;margin-top:6px;">'
                    f'✗ {err}</div>',
                    unsafe_allow_html=True
                )

    # Live account badge
    if st.session_state.get("broker_client") and st.session_state.get("broker_name") == selected_broker:
        acct   = st.session_state.get("broker_account", {})
        equity = acct.get("equity", 0)
        pnl    = acct.get("pnl", 0)
        curr   = "INR" if bcfg["type"] == "coindcx" else "$"
        pnl_c  = "#00ff88" if pnl >= 0 else "#ff2d5e"
        st.markdown(
            f'<div style="background:rgba(0,255,136,0.04);border:1px solid rgba(0,255,136,0.18);'
            f'border-radius:3px;padding:0.5rem 0.7rem;margin-top:6px;">'
            f'<div style="font-family:Share Tech Mono;font-size:0.58rem;color:#1a3a4a;">ACCOUNT</div>'
            f'<div style="font-family:Orbitron;font-size:0.9rem;color:#00f5ff;">{curr}{equity:,.2f}</div>'
            f'<div style="font-family:Share Tech Mono;font-size:0.6rem;color:{pnl_c};">'
            f'PnL {curr}{pnl:+,.2f}</div></div>',
            unsafe_allow_html=True
        )


# ══════════════════════════════════════════════════════════════
# 7. DELTA EXCHANGE INDIA — NATIVE REST CLIENT
# ══════════════════════════════════════════════════════════════

def _delta_signature(api_secret: str, method: str, path: str,
                     query_string: str = "", payload: str = "") -> tuple:
    """Returns (timestamp, signature) for Delta Exchange HMAC-SHA256 auth."""
    timestamp = str(int(time.time()))
    msg = method + timestamp + path + query_string + payload
    sig = hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return timestamp, sig


def _delta_headers(api_key: str, api_secret: str,
                   method: str, path: str,
                   query_string: str = "", payload: str = "") -> dict:
    ts, sig = _delta_signature(api_secret, method, path, query_string, payload)
    return {
        "api-key":        api_key,
        "timestamp":      ts,
        "signature":      sig,
        "Content-Type":   "application/json",
        "Accept":         "application/json",
    }


class DeltaClient:
    """
    Lightweight Delta Exchange India REST client.
    Mirrors the interface expected by get_account_summary() and place_trade().
    """

    def __init__(self, api_key: str, api_secret: str,
                 base_url: str = "https://api.india.delta.exchange"):
        self.api_key    = api_key
        self.api_secret = api_secret
        self.base_url   = base_url.rstrip("/")
        self.broker_type = "delta"

    def _get(self, path: str, params: dict = None) -> dict:
        qs = ""
        if params:
            qs = "?" + "&".join(f"{k}={v}" for k, v in params.items())
        headers = _delta_headers(self.api_key, self.api_secret, "GET", path, qs)
        r = requests.get(self.base_url + path + qs, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, body: dict) -> dict:
        payload = json.dumps(body, separators=(",", ":"))
        headers = _delta_headers(self.api_key, self.api_secret, "POST", path, "", payload)
        r = requests.post(self.base_url + path, headers=headers, data=payload, timeout=10)
        r.raise_for_status()
        return r.json()

    def _delete(self, path: str, body: dict = None) -> dict:
        payload = json.dumps(body or {}, separators=(",", ":"))
        headers = _delta_headers(self.api_key, self.api_secret, "DELETE", path, "", payload)
        r = requests.delete(self.base_url + path, headers=headers, data=payload, timeout=10)
        r.raise_for_status()
        return r.json()

    # ── Account ──
    def get_wallet_balance(self) -> dict:
        return self._get("/v2/wallet/balances")

    def get_positions(self) -> dict:
        return self._get("/v2/positions/margined")

    def get_open_orders(self, product_id: int) -> dict:
        return self._get("/v2/orders", {"product_id": product_id, "state": "open"})

    # ── Market data (public — no auth needed) ──
    def get_ticker(self, symbol: str) -> dict:
        r = requests.get(f"{self.base_url}/v2/tickers/{symbol}", timeout=5)
        r.raise_for_status()
        d = r.json()
        return d.get("result", d)

    def get_orderbook(self, symbol: str, depth: int = 10) -> dict:
        r = requests.get(f"{self.base_url}/v2/l2orderbook/{symbol}",
                         params={"depth": depth}, timeout=5)
        r.raise_for_status()
        return r.json().get("result", {})

    # ── Order placement ──
    def place_order(self, product_id: int, side: str, size: int,
                    order_type: str = "market_order",
                    limit_price: str = None,
                    reduce_only: bool = False) -> dict:
        body = {
            "product_id":  product_id,
            "side":        side,          # "buy" or "sell"
            "size":        size,          # number of contracts
            "order_type":  order_type,    # "market_order" or "limit_order"
            "reduce_only": reduce_only,
        }
        if limit_price:
            body["limit_price"] = limit_price
        return self._post("/v2/orders", body)

    def place_bracket_order(self, product_id: int, product_symbol: str,
                            sl_stop_price: str, tp_stop_price: str) -> dict:
        """Place bracket (TP + SL) via Delta's native bracket endpoint."""
        body = {
            "product_id":     product_id,
            "product_symbol": product_symbol,
            "stop_loss_order": {
                "order_type": "market_order",
                "stop_price": sl_stop_price,
            },
            "take_profit_order": {
                "order_type": "market_order",
                "stop_price": tp_stop_price,
            },
            "bracket_stop_trigger_method": "last_traded_price",
        }
        return self._post("/v2/orders/bracket", body)

    def cancel_order(self, order_id: int, product_id: int) -> dict:
        return self._delete("/v2/orders", {"id": order_id, "product_id": product_id})

    def set_leverage(self, product_id: int, leverage: int) -> dict:
        return self._post("/v2/products/orders/leverage", {
            "product_id": product_id,
            "leverage":   str(leverage),
        })

    def ping(self) -> bool:
        """Validate credentials by fetching wallet balance."""
        try:
            resp = self.get_wallet_balance()
            return resp.get("success", False) or "result" in resp
        except Exception:
            return False


# ══════════════════════════════════════════════════════════════
# 8. COINDCX — NATIVE REST CLIENT
# ══════════════════════════════════════════════════════════════

class CoinDCXClient:
    """
    CoinDCX REST client (spot + margin trading).
    Uses HMAC-SHA256 over JSON body for authentication.
    """

    BASE_URL = "https://api.coindcx.com"

    def __init__(self, api_key: str, api_secret: str):
        self.api_key    = api_key
        self.api_secret = api_secret.encode()
        self.broker_type = "coindcx"

    def _signed_headers(self, body: dict) -> tuple[str, dict]:
        ts          = int(round(time.time() * 1000))
        body["timestamp"] = ts
        json_body   = json.dumps(body, separators=(",", ":"))
        signature   = hmac.new(self.api_secret, json_body.encode(), hashlib.sha256).hexdigest()
        headers     = {
            "Content-Type":    "application/json",
            "X-AUTH-APIKEY":   self.api_key,
            "X-AUTH-SIGNATURE": signature,
        }
        return json_body, headers

    def _post(self, path: str, body: dict) -> dict:
        json_body, headers = self._signed_headers(body)
        r = requests.post(self.BASE_URL + path, data=json_body, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()

    # ── Account ──
    def get_balances(self) -> list:
        return self._post("/exchange/v1/users/balances", {})

    def get_info(self) -> dict:
        return self._post("/exchange/v1/users/info", {})

    # ── Orders ──
    def place_order(self, market: str, side: str, order_type: str,
                    quantity: float, price_per_unit: float = None) -> dict:
        """
        Place a spot order on CoinDCX.
        market: e.g. "BTCINR", "ETHINR"
        side: "buy" or "sell"
        order_type: "market_order" or "limit_order"
        """
        body = {
            "side":       side,
            "order_type": order_type,
            "market":     market,
            "total_quantity": quantity,
            "client_order_id": f"apex_{int(time.time())}",
        }
        if price_per_unit and order_type == "limit_order":
            body["price_per_unit"] = price_per_unit
        return self._post("/exchange/v1/orders/create", body)

    def place_margin_order(self, market: str, side: str, order_type: str,
                           quantity: float, leverage: int = 2,
                           price: float = None,
                           sl_price: float = None,
                           target_price: float = None) -> dict:
        """Place a CoinDCX margin order with optional TP/SL."""
        body = {
            "side":       side,
            "order_type": order_type,
            "market":     market,
            "quantity":   quantity,
            "leverage":   leverage,
        }
        if price:       body["price"]        = price
        if sl_price:    body["sl_price"]     = sl_price
        if target_price:body["target_price"] = target_price
        return self._post("/exchange/v1/margin/create", body)

    def cancel_order(self, order_id: str) -> dict:
        return self._post("/exchange/v1/orders/cancel", {"id": order_id})

    def get_active_orders(self, market: str = None) -> list:
        body = {}
        if market:
            body["market"] = market
        return self._post("/exchange/v1/orders/active_orders", body)

    # ── Market data (public) ──
    def get_ticker(self, market: str) -> dict:
        r = requests.get(f"{self.BASE_URL}/exchange/ticker", timeout=5)
        r.raise_for_status()
        tickers = r.json()
        for t in tickers:
            if t.get("market") == market:
                return t
        return {}

    def ping(self) -> bool:
        try:
            resp = self.get_balances()
            return isinstance(resp, list)
        except Exception:
            return False


# ══════════════════════════════════════════════════════════════
# 9. BROKER CONNECTION FACTORY
# ══════════════════════════════════════════════════════════════

def _connect_broker(broker_name: str, api_key: str, secret: str,
                    passphrase: str = "", testnet: bool = True):
    """Returns (client_object, None) on success or (None, error_string)."""
    bcfg = BROKERS[broker_name]

    if not api_key or not secret:
        return None, "API Key and Secret are required"

    # ── Delta Exchange India ─────────────────────────────────
    if bcfg["type"] == "delta":
        base_url = bcfg["testnet_url"] if testnet else bcfg["prod_url"]
        try:
            client = DeltaClient(api_key, secret, base_url)
            if not client.ping():
                return None, "AUTH FAILED — check API key/secret or environment"
            return client, None
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response else "?"
            if code in (401, 403): return None, f"AUTH FAILED ({code}) — Invalid credentials"
            return None, f"HTTP {code} — Delta Exchange"
        except Exception as e:
            return None, str(e)[:80]

    # ── CoinDCX ──────────────────────────────────────────────
    if bcfg["type"] == "coindcx":
        try:
            client = CoinDCXClient(api_key, secret)
            if not client.ping():
                return None, "AUTH FAILED — check API key/secret"
            return client, None
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response else "?"
            if code in (401, 403): return None, f"AUTH FAILED ({code})"
            return None, f"HTTP {code} — CoinDCX"
        except Exception as e:
            return None, str(e)[:80]

    # ── CCXT (global brokers) ─────────────────────────────────
    try:
        import ccxt
        ExCls  = getattr(ccxt, bcfg["ccxt_id"])
        params = {
            "apiKey": api_key, "secret": secret,
            "options": {"defaultType": "future"},
        }
        if bcfg.get("needs_passphrase") and passphrase:
            params["password"] = passphrase
        if testnet:
            params["sandbox"] = True
        client = ExCls(params)
        client.fetch_balance()
        return client, None
    except ImportError:
        return None, "ccxt not installed — run: pip install ccxt"
    except Exception as e:
        err = str(e)
        if "401" in err or "authentication" in err.lower(): return None, "AUTH FAILED"
        if "sandbox" in err.lower():                        return None, "Testnet not supported for this broker"
        return None, err[:80]


# ══════════════════════════════════════════════════════════════
# 10. UNIFIED ACCOUNT SUMMARY
# ══════════════════════════════════════════════════════════════

def get_account_summary(client=None, bcfg: dict = None) -> dict:
    if client is None:
        client = st.session_state.get("broker_client")
    if bcfg is None:
        bcfg = st.session_state.get("broker_cfg", {})
    if not client:
        return {}

    broker_type = getattr(client, "broker_type", bcfg.get("type", "ccxt"))

    # ── Delta Exchange ────────────────────────────────────────
    if broker_type == "delta":
        try:
            bal_resp  = client.get_wallet_balance()
            pos_resp  = client.get_positions()
            balances  = bal_resp.get("result", []) if isinstance(bal_resp, dict) else []
            positions = pos_resp.get("result", []) if isinstance(pos_resp, dict) else []

            # Sum USD wallet balance
            equity = 0.0
            free   = 0.0
            for b in balances:
                asset = b.get("asset_symbol", "")
                if asset in ("USD", "USDT", "INR"):
                    equity += float(b.get("available_balance", 0) or 0)
                    equity += float(b.get("blocked_margin", 0) or 0)
                    free   += float(b.get("available_balance", 0) or 0)

            open_pos = [p for p in positions if float(p.get("size", 0) or 0) != 0]
            pnl = sum(float(p.get("unrealized_pnl", 0) or 0) for p in open_pos)

            return {
                "equity":         equity,
                "free_margin":    free,
                "used_margin":    equity - free,
                "positions":      open_pos,
                "open_orders":    [],
                "pnl":            pnl,
                "position_count": len(open_pos),
                "currency":       "USD",
                "broker_type":    "delta",
            }
        except Exception as e:
            return {"error": str(e), "broker_type": "delta"}

    # ── CoinDCX ───────────────────────────────────────────────
    if broker_type == "coindcx":
        try:
            balances = client.get_balances()
            inr_bal  = next((b for b in balances if b.get("currency_short_name") == "INR"), {})
            btc_bal  = next((b for b in balances if b.get("currency_short_name") == "BTC"), {})
            eth_bal  = next((b for b in balances if b.get("currency_short_name") == "ETH"), {})

            equity = float(inr_bal.get("balance", 0) or 0)
            free   = float(inr_bal.get("balance", 0) or 0)

            holdings = []
            for b in balances:
                if float(b.get("balance", 0) or 0) > 0:
                    holdings.append({
                        "symbol":    b.get("currency_short_name"),
                        "balance":   float(b.get("balance", 0) or 0),
                        "locked":    float(b.get("locked_balance", 0) or 0),
                    })

            return {
                "equity":         equity,
                "free_margin":    free,
                "used_margin":    0,
                "positions":      holdings,
                "open_orders":    [],
                "pnl":            0,
                "position_count": len([h for h in holdings if h["symbol"] not in ("INR","USDT")]),
                "currency":       "INR",
                "broker_type":    "coindcx",
                "btc_balance":    float(btc_bal.get("balance", 0) or 0),
                "eth_balance":    float(eth_bal.get("balance", 0) or 0),
            }
        except Exception as e:
            return {"error": str(e), "broker_type": "coindcx"}

    # ── CCXT ──────────────────────────────────────────────────
    try:
        balance   = client.fetch_balance()
        positions = client.fetch_positions() if hasattr(client, "fetch_positions") else []
        orders    = client.fetch_open_orders() if hasattr(client, "fetch_open_orders") else []

        open_pos  = [p for p in positions
                     if p and float(p.get("contracts", p.get("size", 0)) or 0) != 0]

        usdt_total = (balance.get("total", {}).get("USDT")
                      or balance.get("total", {}).get("USD") or 0)
        usdt_free  = (balance.get("free", {}).get("USDT")
                      or balance.get("free", {}).get("USD") or 0)

        return {
            "equity":         float(usdt_total),
            "free_margin":    float(usdt_free),
            "used_margin":    float(usdt_total) - float(usdt_free),
            "positions":      open_pos,
            "open_orders":    orders,
            "pnl":            sum(float(p.get("unrealizedPnl", 0) or 0) for p in open_pos),
            "position_count": len(open_pos),
            "currency":       "USDT",
            "broker_type":    "ccxt",
        }
    except Exception as e:
        return {"error": str(e), "broker_type": "ccxt"}


def refresh_account() -> None:
    client = st.session_state.get("broker_client")
    bcfg   = st.session_state.get("broker_cfg", {})
    if client:
        st.session_state["broker_account"] = get_account_summary(client, bcfg)


# ══════════════════════════════════════════════════════════════
# 11. UNIFIED TRADE PLACEMENT
# ══════════════════════════════════════════════════════════════

def place_trade(signal: dict, symbol: str, quantity: float, leverage: int = 10) -> dict:
    """
    Unified bracket order: entry + TP + SL.
    Routes to the correct broker-specific implementation.
    """
    client   = st.session_state.get("broker_client")
    bcfg     = st.session_state.get("broker_cfg", {})
    testnet  = st.session_state.get("broker_testnet", True)

    if not client:
        return {"success": False, "error": "No broker connected"}
    if signal.get("direction") == "WAIT":
        return {"success": False, "error": "Signal is WAIT"}

    broker_type = getattr(client, "broker_type", bcfg.get("type", "ccxt"))
    results     = {
        "timestamp":   datetime.now().isoformat(),
        "broker":      st.session_state.get("broker_name"),
        "broker_type": broker_type,
        "testnet":     testnet,
        "symbol":      symbol,
        "direction":   signal["direction"],
    }

    # ── Delta Exchange India ──────────────────────────────────
    if broker_type == "delta":
        delta_sym  = bcfg["symbol_map"].get(symbol, "BTCUSD")
        product_id = bcfg["product_ids"].get(delta_sym, 27)
        side       = "buy" if signal["direction"] == "LONG" else "sell"
        # Delta uses integer lot sizes (1 lot = 0.001 BTC for BTCUSD)
        size       = max(1, int(quantity))

        try:
            # Set leverage
            try:
                client.set_leverage(product_id, leverage)
            except Exception:
                pass

            # Market entry
            entry = client.place_order(product_id, side, size, "market_order")
            results["entry"] = {
                "id":     entry.get("result", {}).get("id"),
                "status": entry.get("result", {}).get("state"),
                "side":   side,
                "size":   size,
            }

            # Bracket TP + SL (Delta's native bracket API)
            try:
                close_side = "sell" if side == "buy" else "buy"
                tp_side    = close_side
                sl_side    = close_side

                # Place TP as limit order (reduce-only)
                tp = client.place_order(
                    product_id, tp_side, size, "limit_order",
                    limit_price=str(round(signal["tp"], 1)), reduce_only=True
                )
                results["take_profit"] = {
                    "id": tp.get("result", {}).get("id"),
                    "price": signal["tp"],
                }

                # Place SL as stop order via bracket
                bracket = client.place_bracket_order(
                    product_id, delta_sym,
                    sl_stop_price=str(round(signal["sl"], 1)),
                    tp_stop_price=str(round(signal["tp"], 1)),
                )
                results["bracket"] = {"id": bracket.get("result", {}).get("id")}

            except Exception as e:
                results["tp_sl_note"] = f"Manual TP/SL needed: {str(e)[:60]}"

            results["success"] = True

        except Exception as e:
            results["success"] = False
            results["error"]   = str(e)

        return results

    # ── CoinDCX (spot + margin) ───────────────────────────────
    if broker_type == "coindcx":
        dcx_market = bcfg["symbol_map"].get(symbol, "BTCINR")
        side       = "buy" if signal["direction"] == "LONG" else "sell"

        try:
            # CoinDCX margin order with TP/SL
            order = client.place_margin_order(
                market=dcx_market,
                side=side,
                order_type="market_order",
                quantity=quantity,
                leverage=min(leverage, bcfg["leverage_max"]),
                sl_price=signal["sl"] if signal["sl"] > 0 else None,
                target_price=signal["tp"] if signal["tp"] > 0 else None,
            )
            results["entry"]   = order
            results["success"] = True
            results["note"]    = "CoinDCX margin order with SL/TP — INR settled"

        except Exception as e:
            results["success"] = False
            results["error"]   = str(e)

        return results

    # ── CCXT (global brokers) ─────────────────────────────────
    unified_sym = bcfg.get("symbol_map", {}).get(symbol, symbol)
    side        = "buy"  if signal["direction"] == "LONG" else "sell"
    close_side  = "sell" if side == "buy" else "buy"

    try:
        try:
            client.set_leverage(leverage, unified_sym)
        except Exception:
            pass

        entry_order = client.create_order(
            symbol=unified_sym, type="market",
            side=side, amount=quantity
        )
        results["entry"] = {
            "id":    entry_order.get("id"),
            "side":  side, "qty": quantity,
            "price": entry_order.get("average", signal["price"]),
        }

        try:
            tp_order = client.create_order(
                unified_sym, "limit", close_side, quantity,
                price=signal["tp"], params={"reduceOnly": True}
            )
            results["take_profit"] = {"id": tp_order.get("id"), "price": signal["tp"]}
        except Exception as e:
            results["take_profit"] = {"error": str(e)[:60]}

        try:
            sl_order = client.create_order(
                unified_sym, "stop_market", close_side, quantity,
                params={"stopPrice": signal["sl"], "reduceOnly": True}
            )
            results["stop_loss"] = {"id": sl_order.get("id"), "price": signal["sl"]}
        except Exception as e:
            results["stop_loss"] = {"error": str(e)[:60]}

        results["success"] = True

    except Exception as e:
        results["success"] = False
        results["error"]   = str(e)

    return results


# ══════════════════════════════════════════════════════════════
# 12. AI ANALYSIS — UNIFIED MULTI-PROVIDER
# ══════════════════════════════════════════════════════════════

def _build_prompt(symbol: str, signal: dict, df4h: pd.DataFrame, df15m: pd.DataFrame) -> str:
    r4, r15 = df4h.iloc[-1], df15m.iloc[-1]
    broker_name = st.session_state.get("broker_name", "")
    acct        = st.session_state.get("broker_account", {})
    broker_ctx  = ""
    if acct:
        curr = acct.get("currency", "USDT")
        broker_ctx = (
            f"\nACCOUNT [{broker_name}]: Equity {curr}{acct.get('equity',0):,.2f} · "
            f"PnL {curr}{acct.get('pnl',0):+,.2f} · "
            f"Open Positions: {acct.get('position_count',0)}"
        )

    return f"""You are APEX — an elite quantitative hedge fund AI trading analyst managing a $50M BTC/ETH futures book.

CURRENT MARKET DATA FOR {symbol}:{broker_ctx}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Price: ${signal['price']:,.2f} | Signal: {signal['direction']} | Confidence: {signal['confidence']:.1f}%

4H INDICATORS:
EMA9/21/50: ${r4['ema9']:,.0f} / ${r4['ema21']:,.0f} / ${r4['ema50']:,.0f}
RSI: {signal['rsi_4h']:.1f} | MACD Hist: {signal['macd_hist_4h']:.2f} | ADX: {signal['adx']:.1f} ({signal['trend_strength']})

15M INDICATORS:
RSI: {signal['rsi_15m']:.1f} | BB%B: {signal['bb_pct']:.2f} | ATR: ${signal['atr']:,.2f}

SIGNAL CONFLUENCE: {', '.join(signal['reasons'])}

TRADE SETUP:
Entry: ${signal['price']:,.2f} | TP: ${signal['tp']:,.2f} ({((signal['tp']-signal['price'])/signal['price']*100):+.2f}%)
SL: ${signal['sl']:,.2f} ({((signal['sl']-signal['price'])/signal['price']*100):+.2f}%) | R:R = {signal['rr']:.2f}x
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Provide hedge fund analysis in 4 sections:
1. MARKET STRUCTURE — trend context, key levels, regime
2. SIGNAL ASSESSMENT — validate/challenge signal, timeframe confluence
3. EXECUTION PLAN — entry type, sizing (1-3% risk), scaling
4. RISK FACTORS — invalidation levels, macro risks

Concise, data-driven, decisive. Real numbers only."""


def _call_anthropic(p, k, m):
    import anthropic as ant
    c = ant.Anthropic(api_key=k)
    r = c.messages.create(model=m, max_tokens=900,
                          messages=[{"role":"user","content":p}])
    return r.content[0].text

def _call_openai(p, k, m):
    r = requests.post("https://api.openai.com/v1/chat/completions",
                      headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
                      json={"model": m, "messages": [{"role":"user","content":p}], "max_tokens": 900},
                      timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def _call_gemini(p, k, m):
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={k}",
        json={"contents": [{"parts": [{"text": p}]}]}, timeout=30)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

def _call_groq(p, k, m):
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
                      json={"model": m, "messages": [{"role":"user","content":p}], "max_tokens": 900},
                      timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def _call_ollama(p, m, host):
    r = requests.post(f"{host}/api/generate",
                      json={"model": m, "prompt": p, "stream": False}, timeout=90)
    r.raise_for_status()
    return r.json()["response"]

def _call_mistral(p, k, m):
    r = requests.post("https://api.mistral.ai/v1/chat/completions",
                      headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
                      json={"model": m, "messages": [{"role":"user","content":p}], "max_tokens": 900},
                      timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def get_ai_analysis(symbol: str, signal: dict,
                    df4h: pd.DataFrame, df15m: pd.DataFrame) -> str:
    if not st.session_state.get("authenticated"):
        return "[ LOGIN REQUIRED ]"

    provider = st.session_state.get("ai_provider", "Anthropic Claude")
    model    = st.session_state.get("ai_model",    "claude-sonnet-4-20250514")
    api_key  = st.session_state.get("provider_api_key", "")

    if provider != "Ollama (Local)" and not api_key:
        return f"[ No API key for {provider} ]"
    if df4h.empty or df15m.empty:
        return "[ Insufficient data ]"

    prompt = _build_prompt(symbol, signal, df4h, df15m)

    try:
        if   provider == "Anthropic Claude": text = _call_anthropic(prompt, api_key, model)
        elif provider == "OpenAI GPT":       text = _call_openai(prompt, api_key, model)
        elif provider == "Google Gemini":    text = _call_gemini(prompt, api_key, model)
        elif provider == "Groq (Free)":      text = _call_groq(prompt, api_key, model)
        elif provider == "Ollama (Local)":
            text = _call_ollama(prompt, model, st.session_state.get("ollama_host", "http://localhost:11434"))
        elif provider == "Mistral AI":       text = _call_mistral(prompt, api_key, model)
        else: return f"[ Unknown provider: {provider} ]"

        return f"[{provider} · {model}]\n\n{text}"

    except requests.exceptions.ConnectionError:
        return f"✗ CONNECTION ERROR — {provider}"
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response else "?"
        if code == 401: return f"✗ AUTH ERROR — Invalid key for {provider}"
        if code == 429: return f"✗ RATE LIMITED — {provider}"
        return f"✗ HTTP {code} — {provider}"
    except Exception as e:
        return f"✗ ERROR [{provider}]: {str(e)[:120]}"
