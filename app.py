import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from urllib.parse import unquote
import yfinance as yf
import time
import json

# ─── PAGE CONFIG ───────────────────────────────────────────────
st.set_page_config(
    page_title="⚡ Synthetic GEX Lab",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── CUSTOM CSS (Dark Trading Terminal Theme) ──────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0a0e1a; }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom header */
    .gex-header {
        background: linear-gradient(135deg, #0f1729 0%, #1a1f3a 50%, #0f1729 100%);
        border: 1px solid #1e2d4a;
        border-radius: 8px;
        padding: 12px 20px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .gex-title {
        font-family: 'Courier New', monospace;
        font-size: 22px;
        font-weight: bold;
        color: #00d4ff;
        text-shadow: 0 0 10px rgba(0,212,255,0.3);
    }
    .gex-subtitle {
        font-family: 'Courier New', monospace;
        font-size: 11px;
        color: #5a6a8a;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #0f1729, #141e33);
        border: 1px solid #1e2d4a;
        border-radius: 6px;
        padding: 12px 16px;
        text-align: center;
    }
    .metric-label {
        font-family: 'Courier New', monospace;
        font-size: 10px;
        color: #5a6a8a;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .metric-value {
        font-family: 'Courier New', monospace;
        font-size: 20px;
        font-weight: bold;
        margin-top: 4px;
    }
    .metric-green { color: #00ff88; text-shadow: 0 0 8px rgba(0,255,136,0.3); }
    .metric-red { color: #ff4466; text-shadow: 0 0 8px rgba(255,68,102,0.3); }
    .metric-cyan { color: #00d4ff; text-shadow: 0 0 8px rgba(0,212,255,0.3); }
    .metric-gold { color: #ffd700; text-shadow: 0 0 8px rgba(255,215,0,0.3); }
    .metric-white { color: #e0e8f8; }
    
    /* Level cards */
    .level-card {
        background: linear-gradient(135deg, #0f1729, #141e33);
        border-left: 3px solid;
        border-radius: 4px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    .level-magnet { border-color: #00ff88; }
    .level-resist { border-color: #ff4466; }
    .level-support { border-color: #00d4ff; }
    .level-flip { border-color: #ffd700; }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #0f1729;
        border-radius: 6px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #141e33;
        border-radius: 4px;
        color: #5a6a8a;
        font-family: 'Courier New', monospace;
        font-size: 12px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e2d4a !important;
        color: #00d4ff !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0a0e1a;
        border-right: 1px solid #1e2d4a;
    }
    
    /* Selectbox & inputs */
    .stSelectbox > div > div { background-color: #141e33; color: #e0e8f8; }
    
    /* Dataframe */
    .stDataFrame { border: 1px solid #1e2d4a; border-radius: 6px; }
    
    /* Divider */
    hr { border-color: #1e2d4a !important; }
    
    /* Status badges */
    .status-live {
        display: inline-block;
        background: rgba(0,255,136,0.15);
        color: #00ff88;
        font-family: 'Courier New', monospace;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 10px;
        border: 1px solid rgba(0,255,136,0.3);
    }
    .status-stale {
        display: inline-block;
        background: rgba(255,215,0,0.15);
        color: #ffd700;
        font-family: 'Courier New', monospace;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 10px;
        border: 1px solid rgba(255,215,0,0.3);
    }
</style>
""", unsafe_allow_html=True)


# ─── DATA FETCHING ─────────────────────────────────────────────

@st.cache_data(ttl=300)  # Cache 5 minutes
def fetch_barchart_data(ticker_symbol, expiry_offset=0):
    """Fetch options chain with Greeks from Barchart"""
    error_log = []
    
    try:
        # Get spot price and expiry dates from yfinance
        ticker_yf = yf.Ticker(ticker_symbol)
        expiry_dates = list(ticker_yf.options)
        
        if not expiry_dates:
            error_log.append("ERROR: No expiry dates found")
            return None, error_log
        
        expiry_offset = min(expiry_offset, len(expiry_dates) - 1)
        next_expiry_date = expiry_dates[expiry_offset]
        error_log.append(f"✓ Selected expiry: {next_expiry_date}")
        
        hist = ticker_yf.history(period="5d")
        if hist.empty:
            error_log.append("ERROR: No price history")
            return None, error_log
        spot = hist['Close'].iloc[-1]
        error_log.append(f"✓ Spot price: ${spot:.2f}")
        
        # Barchart session setup
        if ticker_symbol == "SPX":
            geturl = f'https://www.barchart.com/stocks/quotes/$SPX/volatility-greeks'
        else:
            geturl = f'https://www.barchart.com/etfs-funds/quotes/{ticker_symbol}/volatility-greeks'
        apiurl = 'https://www.barchart.com/proxies/core-api/v1/options/get'
        
        getheaders = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        s = requests.Session()
        r = s.get(geturl, params={'page': 'all'}, headers=getheaders, timeout=15)
        r.raise_for_status()
        error_log.append(f"✓ Barchart page: {r.status_code}")
        
        cookies = s.cookies.get_dict()
        if 'XSRF-TOKEN' not in cookies:
            error_log.append("⚠ No XSRF-TOKEN, trying without...")
            xsrf = ''
        else:
            xsrf = unquote(cookies['XSRF-TOKEN'])
            error_log.append("✓ Got XSRF token")
        
        headers = {
            'accept': 'application/json',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9',
            'referer': geturl,
            'user-agent': getheaders['user-agent'],
            'x-xsrf-token': xsrf
        }
        
        # Fetch options chain
        if ticker_symbol == "SPX":
            base_sym = "$SPX"
        else:
            base_sym = ticker_symbol
            
        payload = {
            'baseSymbol': base_sym,
            'groupBy': 'optionType',
            'expirationDate': next_expiry_date,
            'orderBy': 'strikePrice',
            'orderDir': 'asc',
            'raw': '1',
            'fields': 'symbol,strikePrice,lastPrice,volatility,delta,gamma,theta,vega,volume,openInterest,optionType'
        }
        
        r = s.get(apiurl, params=payload, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        error_log.append(f"✓ API response received")
        
        data_list = []
        for option_type, options in data.get('data', {}).items():
            for option in options:
                option['optionType'] = option_type
                data_list.append(option)
        
        if not data_list:
            error_log.append("ERROR: No options data returned")
            return None, error_log
        
        df = pd.DataFrame(data_list)
        
        # Convert numeric columns
        numeric_cols = ['strikePrice', 'lastPrice', 'volatility', 'delta', 'gamma', 
                       'theta', 'vega', 'volume', 'openInterest']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        df['openInterest'] = df['openInterest'].astype(int)
        df['volume'] = df['volume'].astype(int)
        
        calls = df[df['optionType'] == 'Call'].copy()
        puts = df[df['optionType'] == 'Put'].copy()
        
        error_log.append(f"✓ Calls: {len(calls)}, Puts: {len(puts)}")
        
        return {
            'spot': spot,
            'expiry': next_expiry_date,
            'expiry_dates': expiry_dates,
            'calls': calls,
            'puts': puts,
            'raw_df': df
        }, error_log
        
    except Exception as e:
        error_log.append(f"ERROR: {str(e)}")
        return None, error_log


def compute_gex(calls, puts, spot, contract_mult=100):
    """Compute Gamma Exposure by strike"""
    all_strikes = sorted(set(calls['strikePrice'].tolist() + puts['strikePrice'].tolist()))
    
    records = []
    for K in all_strikes:
        if pd.isna(K) or K <= 0:
            continue
        
        call_row = calls[calls['strikePrice'] == K]
        put_row = puts[puts['strikePrice'] == K]
        
        call_oi = int(call_row['openInterest'].iloc[0]) if not call_row.empty else 0
        put_oi = int(put_row['openInterest'].iloc[0]) if not put_row.empty else 0
        call_gamma = float(call_row['gamma'].iloc[0]) if not call_row.empty else 0
        put_gamma = float(put_row['gamma'].iloc[0]) if not put_row.empty else 0
        call_delta = float(call_row['delta'].iloc[0]) if not call_row.empty else 0
        put_delta = float(put_row['delta'].iloc[0]) if not put_row.empty else 0
        call_vol = int(call_row['volume'].iloc[0]) if not call_row.empty else 0
        put_vol = int(put_row['volume'].iloc[0]) if not put_row.empty else 0
        call_iv = float(call_row['volatility'].iloc[0]) if not call_row.empty else 0
        put_iv = float(put_row['volatility'].iloc[0]) if not put_row.empty else 0
        
        # GEX = gamma * OI * 100 * spot
        # Calls positive, puts negative (MM hedging)
        call_gex = call_gamma * call_oi * contract_mult * spot
        put_gex = -put_gamma * put_oi * contract_mult * spot  # Negative for puts
        net_gex = call_gex + put_gex
        
        # Net delta exposure
        call_dex = call_delta * call_oi * contract_mult
        put_dex = put_delta * put_oi * contract_mult
        net_dex = call_dex + put_dex
        
        records.append({
            'strike': K,
            'call_gex': call_gex,
            'put_gex': put_gex,
            'net_gex': net_gex,
            'call_oi': call_oi,
            'put_oi': put_oi,
            'total_oi': call_oi + put_oi,
            'call_vol': call_vol,
            'put_vol': put_vol,
            'total_vol': call_vol + put_vol,
            'call_gamma': call_gamma,
            'put_gamma': put_gamma,
            'total_gamma': call_gamma * call_oi + put_gamma * put_oi,
            'call_delta': call_delta,
            'put_delta': put_delta,
            'net_dex': net_dex,
            'call_iv': call_iv,
            'put_iv': put_iv,
            'avg_iv': (call_iv + put_iv) / 2 if (call_iv + put_iv) > 0 else 0,
        })
    
    return pd.DataFrame(records)


def find_key_levels(gex_df, spot):
    """Identify key GEX levels: magnet, resistance, support, flip"""
    if gex_df.empty:
        return {}
    
    # Filter to reasonable range
    lower = spot * 0.95
    upper = spot * 1.05
    nearby = gex_df[(gex_df['strike'] >= lower) & (gex_df['strike'] <= upper)].copy()
    
    if nearby.empty:
        return {}
    
    # Gamma Flip: where net_gex crosses zero near spot
    flip_strike = None
    for i in range(len(nearby) - 1):
        if nearby.iloc[i]['net_gex'] * nearby.iloc[i+1]['net_gex'] < 0:
            s1, s2 = nearby.iloc[i]['strike'], nearby.iloc[i+1]['strike']
            if abs(s1 - spot) < spot * 0.03 or abs(s2 - spot) < spot * 0.03:
                flip_strike = (s1 + s2) / 2
                break
    
    # Magnet: highest positive net GEX (price pulled toward)
    pos_gex = nearby[nearby['net_gex'] > 0]
    magnet = pos_gex.loc[pos_gex['net_gex'].idxmax(), 'strike'] if not pos_gex.empty else None
    
    # Resistance: highest total GEX above spot
    above = nearby[nearby['strike'] > spot]
    resistance = above.loc[above['total_gamma'].idxmax(), 'strike'] if not above.empty else None
    
    # Support: highest total GEX below spot
    below = nearby[nearby['strike'] < spot]
    support = below.loc[below['total_gamma'].idxmax(), 'strike'] if not below.empty else None
    
    # Max Put Wall (major support)
    put_wall = nearby.loc[nearby['put_oi'].idxmax(), 'strike'] if nearby['put_oi'].max() > 0 else None
    
    # Max Call Wall (major resistance)
    call_wall = nearby.loc[nearby['call_oi'].idxmax(), 'strike'] if nearby['call_oi'].max() > 0 else None
    
    # Determine gamma regime
    spot_row = nearby.iloc[(nearby['strike'] - spot).abs().argsort()[:1]]
    gamma_regime = "POSITIVE" if (not spot_row.empty and spot_row.iloc[0]['net_gex'] > 0) else "NEGATIVE"
    
    return {
        'magnet': magnet,
        'resistance': resistance,
        'support': support,
        'flip': flip_strike,
        'put_wall': put_wall,
        'call_wall': call_wall,
        'gamma_regime': gamma_regime,
    }


# ─── HEADER ────────────────────────────────────────────────────
st.markdown("""
<div class="gex-header">
    <div>
        <span class="gex-title">⚡ SYNTHETIC GEX LAB</span>
        <span class="gex-subtitle"> &nbsp;v3.1 — Barchart Greeks</span>
    </div>
    <div class="gex-subtitle">Streamlit Edition</div>
</div>
""", unsafe_allow_html=True)


# ─── CONTROLS ──────────────────────────────────────────────────
ctrl_cols = st.columns([1, 1, 1, 1, 3])

with ctrl_cols[0]:
    ticker = st.selectbox("Asset", ["SPY", "QQQ", "IWM", "SPX"], index=0, label_visibility="collapsed")

with ctrl_cols[1]:
    expiry_idx = st.number_input("Expiry Offset (0=nearest)", min_value=0, max_value=10, value=0, label_visibility="collapsed")

with ctrl_cols[2]:
    strike_range_pct = st.selectbox("Range", ["±3%", "±5%", "±8%", "±10%", "±15%"], index=1, label_visibility="collapsed")
    range_pct = float(strike_range_pct.replace("±", "").replace("%", "")) / 100

with ctrl_cols[3]:
    refresh = st.button("🔄 Refresh", width="stretch")

with ctrl_cols[4]:
    auto_refresh = st.checkbox("Auto-refresh (5 min)", value=False)


# ─── FETCH DATA ────────────────────────────────────────────────
if refresh:
    st.cache_data.clear()

with st.spinner("Fetching live Greeks from Barchart..."):
    result, log = fetch_barchart_data(ticker, expiry_idx)

if result is None:
    st.error("❌ Failed to fetch data. See debug log below.")
    with st.expander("🔧 Debug Log"):
        for entry in log:
            st.text(entry)
    st.stop()

# Unpack
spot = result['spot']
expiry = result['expiry']
calls = result['calls']
puts = result['puts']

# Compute GEX
contract_mult = 100
gex_df = compute_gex(calls, puts, spot, contract_mult)

# Filter by range
lower_bound = spot * (1 - range_pct)
upper_bound = spot * (1 + range_pct)
gex_filtered = gex_df[(gex_df['strike'] >= lower_bound) & (gex_df['strike'] <= upper_bound)].copy()

# Key levels
levels = find_key_levels(gex_df, spot)

# ─── METRICS ROW ───────────────────────────────────────────────
regime = levels.get('gamma_regime', 'UNKNOWN')
regime_color = "metric-green" if regime == "POSITIVE" else "metric-red"
regime_desc = "Mean-Reverting • Stable" if regime == "POSITIVE" else "Trending • Volatile"

total_call_gex = gex_filtered['call_gex'].sum()
total_put_gex = gex_filtered['put_gex'].sum()
total_net_gex = gex_filtered['net_gex'].sum()
net_color = "metric-green" if total_net_gex > 0 else "metric-red"

mcols = st.columns(6)
with mcols[0]:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">SPOT</div>
        <div class="metric-value metric-white">${spot:.2f}</div>
    </div>""", unsafe_allow_html=True)
with mcols[1]:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">EXPIRY</div>
        <div class="metric-value metric-cyan">{expiry}</div>
    </div>""", unsafe_allow_html=True)
with mcols[2]:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">GAMMA MODE</div>
        <div class="metric-value {regime_color}">{regime}</div>
    </div>""", unsafe_allow_html=True)
with mcols[3]:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">NET GEX</div>
        <div class="metric-value {net_color}">{total_net_gex:,.0f}</div>
    </div>""", unsafe_allow_html=True)
with mcols[4]:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">CALL GEX</div>
        <div class="metric-value metric-green">{total_call_gex:,.0f}</div>
    </div>""", unsafe_allow_html=True)
with mcols[5]:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">PUT GEX</div>
        <div class="metric-value metric-red">{total_put_gex:,.0f}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ─── TABS ──────────────────────────────────────────────────────
tab_gex, tab_levels, tab_delta, tab_matrix, tab_data, tab_debug = st.tabs([
    "📊 GEX PROFILE", "🎯 KEY LEVELS", "🔥 DELTA", "🧱 MATRIX", "📋 DATA", "🔧 DEBUG"
])


# ═══ TAB 1: GEX PROFILE ═══════════════════════════════════════
with tab_gex:
    col_chart, col_info = st.columns([3, 1])
    
    with col_chart:
        # Horizontal bar chart (matching the original dashboard style)
        fig = go.Figure()
        
        # Put GEX bars (blue, going right)
        fig.add_trace(go.Bar(
            y=gex_filtered['strike'],
            x=gex_filtered['put_gex'],
            orientation='h',
            name='Put GEX',
            marker=dict(
                color='rgba(100, 180, 255, 0.75)',
                line=dict(color='rgba(70, 150, 255, 1)', width=0.5)
            ),
            hovertemplate='Strike: $%{y:.0f}<br>Put GEX: %{x:,.0f}<extra></extra>'
        ))
        
        # Call GEX bars (orange, going left — negative for visual)
        fig.add_trace(go.Bar(
            y=gex_filtered['strike'],
            x=-gex_filtered['call_gex'],
            orientation='h',
            name='Call GEX',
            marker=dict(
                color='rgba(255, 180, 50, 0.75)',
                line=dict(color='rgba(255, 150, 20, 1)', width=0.5)
            ),
            hovertemplate='Strike: $%{y:.0f}<br>Call GEX: %{x:,.0f}<extra></extra>'
        ))
        
        # Spot price line
        fig.add_hline(
            y=spot, line_dash="solid", line_color="#ffd700", line_width=3,
            annotation=dict(
                text=f"SPOT ${spot:.2f}",
                font=dict(size=11, color="#ffd700", family="Courier New"),
                bgcolor="rgba(0,0,0,0.8)", bordercolor="#ffd700", borderwidth=1
            ),
            annotation_position="right"
        )
        
        # Key level lines
        if levels.get('magnet'):
            fig.add_hline(y=levels['magnet'], line_dash="dot", line_color="#00ff88", line_width=1.5,
                         annotation=dict(text=f"🧲 MAGNET ${levels['magnet']:.0f}", 
                                        font=dict(size=9, color="#00ff88"), x=0.02))
        if levels.get('flip'):
            fig.add_hline(y=levels['flip'], line_dash="dash", line_color="#ffd700", line_width=1.5,
                         annotation=dict(text=f"⚖ FLIP ${levels['flip']:.0f}", 
                                        font=dict(size=9, color="#ffd700"), x=0.02))
        
        fig.update_layout(
            barmode='overlay',
            height=700,
            plot_bgcolor='#0a0e1a',
            paper_bgcolor='#0a0e1a',
            font=dict(color='#8b9dc3', size=10, family='Courier New'),
            title=dict(
                text=f"0DTE GEX Profile — {ticker} ({expiry})",
                font=dict(color='#00d4ff', size=14),
                x=0.5
            ),
            xaxis=dict(title="← Calls | Puts →", gridcolor='#1a2332', 
                       zerolinecolor='#2a3442', tickformat=','),
            yaxis=dict(title="", gridcolor='#1a2332', tickformat='$.0f', side='left'),
            showlegend=True,
            legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#8b9dc3', size=10)),
            margin=dict(l=60, r=20, t=40, b=40)
        )
        
        st.plotly_chart(fig, width="stretch", config={'displayModeBar': False})
    
    with col_info:
        st.markdown("#### 🎯 Key Levels")
        
        if levels.get('magnet'):
            st.markdown(f"""<div class="level-card level-magnet">
                <div class="metric-label">🧲 MAGNET</div>
                <div class="metric-value metric-green" style="font-size:16px">${levels['magnet']:.0f}</div>
                <div style="color:#5a6a8a;font-size:10px">Price pulled here</div>
            </div>""", unsafe_allow_html=True)
        
        if levels.get('call_wall'):
            st.markdown(f"""<div class="level-card level-resist">
                <div class="metric-label">🔴 CALL WALL</div>
                <div class="metric-value metric-red" style="font-size:16px">${levels['call_wall']:.0f}</div>
                <div style="color:#5a6a8a;font-size:10px">Max call OI resistance</div>
            </div>""", unsafe_allow_html=True)
        
        if levels.get('put_wall'):
            st.markdown(f"""<div class="level-card level-support">
                <div class="metric-label">🟢 PUT WALL</div>
                <div class="metric-value metric-cyan" style="font-size:16px">${levels['put_wall']:.0f}</div>
                <div style="color:#5a6a8a;font-size:10px">Max put OI support</div>
            </div>""", unsafe_allow_html=True)
        
        if levels.get('flip'):
            st.markdown(f"""<div class="level-card level-flip">
                <div class="metric-label">⚖ GAMMA FLIP</div>
                <div class="metric-value metric-gold" style="font-size:16px">${levels['flip']:.0f}</div>
                <div style="color:#5a6a8a;font-size:10px">Regime change zone</div>
            </div>""", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown(f"""
        **Gamma Regime: {regime}**
        
        {'📗 **Positive Gamma** — MMs sell rallies, buy dips. Price is stable and mean-reverting. Expect range-bound action.' if regime == 'POSITIVE' else '📕 **Negative Gamma** — MMs buy rallies, sell dips. Price moves amplified. Expect trending/volatile action.'}
        """)

    # Net GEX line chart
    st.markdown("#### Net GEX Distribution")
    fig_net = go.Figure()
    
    colors = ['#00ff88' if v > 0 else '#ff4466' for v in gex_filtered['net_gex']]
    fig_net.add_trace(go.Bar(
        x=gex_filtered['strike'], y=gex_filtered['net_gex'],
        marker_color=colors, name='Net GEX',
        hovertemplate='$%{x:.0f}<br>Net GEX: %{y:,.0f}<extra></extra>'
    ))
    fig_net.add_vline(x=spot, line_dash="dash", line_color="#ffd700", line_width=2,
                     annotation=dict(text=f"${spot:.2f}", font=dict(color="#ffd700", size=10)))
    
    fig_net.update_layout(
        height=350, plot_bgcolor='#0a0e1a', paper_bgcolor='#0a0e1a',
        font=dict(color='#8b9dc3', size=10, family='Courier New'),
        xaxis=dict(title="Strike", gridcolor='#1a2332', tickformat='$.0f'),
        yaxis=dict(title="Net GEX", gridcolor='#1a2332', tickformat=','),
        margin=dict(l=60, r=20, t=20, b=40)
    )
    st.plotly_chart(fig_net, width="stretch", config={'displayModeBar': False})


# ═══ TAB 2: KEY LEVELS ════════════════════════════════════════
with tab_levels:
    lev_col1, lev_col2 = st.columns(2)
    
    with lev_col1:
        st.markdown("### 🏛 OI Profile (Open Interest)")
        
        fig_oi = make_subplots(rows=1, cols=1)
        
        fig_oi.add_trace(go.Bar(
            x=gex_filtered['strike'], y=gex_filtered['call_oi'],
            name='Call OI', marker_color='rgba(255,180,50,0.7)',
            hovertemplate='$%{x:.0f}<br>Call OI: %{y:,.0f}<extra></extra>'
        ))
        fig_oi.add_trace(go.Bar(
            x=gex_filtered['strike'], y=-gex_filtered['put_oi'],
            name='Put OI', marker_color='rgba(100,180,255,0.7)',
            hovertemplate='$%{x:.0f}<br>Put OI: %{y:,.0f}<extra></extra>'
        ))
        
        fig_oi.add_vline(x=spot, line_dash="dash", line_color="#ffd700", line_width=2)
        
        fig_oi.update_layout(
            barmode='overlay', height=500,
            plot_bgcolor='#0a0e1a', paper_bgcolor='#0a0e1a',
            font=dict(color='#8b9dc3', family='Courier New'),
            xaxis=dict(gridcolor='#1a2332', tickformat='$.0f'),
            yaxis=dict(gridcolor='#1a2332', tickformat=','),
            legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#8b9dc3')),
            margin=dict(l=60, r=20, t=20, b=40)
        )
        st.plotly_chart(fig_oi, width="stretch", config={'displayModeBar': False})
    
    with lev_col2:
        st.markdown("### 📊 Volume Profile")
        
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Bar(
            x=gex_filtered['strike'], y=gex_filtered['call_vol'],
            name='Call Vol', marker_color='rgba(255,180,50,0.7)',
        ))
        fig_vol.add_trace(go.Bar(
            x=gex_filtered['strike'], y=-gex_filtered['put_vol'],
            name='Put Vol', marker_color='rgba(100,180,255,0.7)',
        ))
        fig_vol.add_vline(x=spot, line_dash="dash", line_color="#ffd700", line_width=2)
        
        fig_vol.update_layout(
            barmode='overlay', height=500,
            plot_bgcolor='#0a0e1a', paper_bgcolor='#0a0e1a',
            font=dict(color='#8b9dc3', family='Courier New'),
            xaxis=dict(gridcolor='#1a2332', tickformat='$.0f'),
            yaxis=dict(gridcolor='#1a2332', tickformat=','),
            legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#8b9dc3')),
            margin=dict(l=60, r=20, t=20, b=40)
        )
        st.plotly_chart(fig_vol, width="stretch", config={'displayModeBar': False})
    
    # Put/Call ratios
    st.markdown("### 📈 Put/Call Analysis")
    pc_cols = st.columns(4)
    total_call_oi = gex_filtered['call_oi'].sum()
    total_put_oi = gex_filtered['put_oi'].sum()
    total_call_vol = gex_filtered['call_vol'].sum()
    total_put_vol = gex_filtered['put_vol'].sum()
    
    pc_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0
    pc_vol = total_put_vol / total_call_vol if total_call_vol > 0 else 0
    
    with pc_cols[0]:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">P/C OI RATIO</div>
            <div class="metric-value {'metric-red' if pc_oi > 1.2 else 'metric-green' if pc_oi < 0.8 else 'metric-white'}">{pc_oi:.2f}</div>
        </div>""", unsafe_allow_html=True)
    with pc_cols[1]:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">P/C VOL RATIO</div>
            <div class="metric-value {'metric-red' if pc_vol > 1.2 else 'metric-green' if pc_vol < 0.8 else 'metric-white'}">{pc_vol:.2f}</div>
        </div>""", unsafe_allow_html=True)
    with pc_cols[2]:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">TOTAL OI</div>
            <div class="metric-value metric-cyan">{(total_call_oi + total_put_oi):,.0f}</div>
        </div>""", unsafe_allow_html=True)
    with pc_cols[3]:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">TOTAL VOLUME</div>
            <div class="metric-value metric-gold">{(total_call_vol + total_put_vol):,.0f}</div>
        </div>""", unsafe_allow_html=True)


# ═══ TAB 3: DELTA ═════════════════════════════════════════════
with tab_delta:
    st.markdown("### 🔥 Delta Exposure by Strike")
    
    fig_delta = go.Figure()
    
    delta_colors = ['#00ff88' if v > 0 else '#ff4466' for v in gex_filtered['net_dex']]
    fig_delta.add_trace(go.Bar(
        x=gex_filtered['strike'], y=gex_filtered['net_dex'],
        marker_color=delta_colors, name='Net Delta',
        hovertemplate='$%{x:.0f}<br>Net Δ: %{y:,.0f}<extra></extra>'
    ))
    fig_delta.add_vline(x=spot, line_dash="dash", line_color="#ffd700", line_width=2)
    
    fig_delta.update_layout(
        height=500, plot_bgcolor='#0a0e1a', paper_bgcolor='#0a0e1a',
        font=dict(color='#8b9dc3', family='Courier New'),
        xaxis=dict(title="Strike", gridcolor='#1a2332', tickformat='$.0f'),
        yaxis=dict(title="Net Delta Exposure", gridcolor='#1a2332', tickformat=','),
        margin=dict(l=60, r=20, t=20, b=40)
    )
    st.plotly_chart(fig_delta, width="stretch", config={'displayModeBar': False})
    
    # Delta summary
    total_net_dex = gex_filtered['net_dex'].sum()
    dex_color = "metric-green" if total_net_dex > 0 else "metric-red"
    
    d_cols = st.columns(3)
    with d_cols[0]:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">NET DELTA</div>
            <div class="metric-value {dex_color}">{total_net_dex:,.0f}</div>
        </div>""", unsafe_allow_html=True)
    with d_cols[1]:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">CALL DELTA EXP</div>
            <div class="metric-value metric-green">{gex_filtered['call_delta'].sum() * 100:,.0f}</div>
        </div>""", unsafe_allow_html=True)
    with d_cols[2]:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-label">PUT DELTA EXP</div>
            <div class="metric-value metric-red">{gex_filtered['put_delta'].sum() * 100:,.0f}</div>
        </div>""", unsafe_allow_html=True)
    
    # IV Smile
    st.markdown("### 📐 IV Smile")
    fig_iv = go.Figure()
    
    iv_data = gex_filtered[(gex_filtered['call_iv'] > 0) | (gex_filtered['put_iv'] > 0)]
    
    fig_iv.add_trace(go.Scatter(
        x=iv_data['strike'], y=iv_data['call_iv'],
        mode='lines+markers', name='Call IV',
        line=dict(color='#ffb832', width=2), marker=dict(size=4)
    ))
    fig_iv.add_trace(go.Scatter(
        x=iv_data['strike'], y=iv_data['put_iv'],
        mode='lines+markers', name='Put IV',
        line=dict(color='#64b4ff', width=2), marker=dict(size=4)
    ))
    fig_iv.add_vline(x=spot, line_dash="dash", line_color="#ffd700", line_width=2)
    
    fig_iv.update_layout(
        height=400, plot_bgcolor='#0a0e1a', paper_bgcolor='#0a0e1a',
        font=dict(color='#8b9dc3', family='Courier New'),
        xaxis=dict(title="Strike", gridcolor='#1a2332', tickformat='$.0f'),
        yaxis=dict(title="IV (%)", gridcolor='#1a2332'),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#8b9dc3')),
        margin=dict(l=60, r=20, t=20, b=40)
    )
    st.plotly_chart(fig_iv, width="stretch", config={'displayModeBar': False})


# ═══ TAB 4: MATRIX ════════════════════════════════════════════
with tab_matrix:
    st.markdown("### 🧱 Options Matrix")
    
    # Merge calls and puts into matrix view
    matrix_calls = calls[['strikePrice', 'lastPrice', 'volume', 'openInterest', 'delta', 'gamma', 'volatility']].copy()
    matrix_calls.columns = ['Strike', 'C_Last', 'C_Vol', 'C_OI', 'C_Delta', 'C_Gamma', 'C_IV']
    
    matrix_puts = puts[['strikePrice', 'lastPrice', 'volume', 'openInterest', 'delta', 'gamma', 'volatility']].copy()
    matrix_puts.columns = ['Strike', 'P_Last', 'P_Vol', 'P_OI', 'P_Delta', 'P_Gamma', 'P_IV']
    
    matrix = matrix_calls.merge(matrix_puts, on='Strike', how='outer').sort_values('Strike')
    matrix = matrix[(matrix['Strike'] >= lower_bound) & (matrix['Strike'] <= upper_bound)]
    
    # Compute net GEX for matrix
    matrix['Net_GEX'] = (matrix['C_Gamma'].fillna(0) * matrix['C_OI'].fillna(0) - 
                          matrix['P_Gamma'].fillna(0) * matrix['P_OI'].fillna(0)) * 100 * spot
    
    # Format display
    display_matrix = matrix[['P_OI', 'P_Vol', 'P_IV', 'P_Delta', 'P_Gamma', 'P_Last',
                            'Strike', 
                            'C_Last', 'C_Gamma', 'C_Delta', 'C_IV', 'C_Vol', 'C_OI', 'Net_GEX']].copy()
    
    st.dataframe(
        display_matrix.style.format({
            'Strike': '${:.0f}', 'C_Last': '${:.2f}', 'P_Last': '${:.2f}',
            'C_Vol': '{:,.0f}', 'P_Vol': '{:,.0f}',
            'C_OI': '{:,.0f}', 'P_OI': '{:,.0f}',
            'C_Delta': '{:.3f}', 'P_Delta': '{:.3f}',
            'C_Gamma': '{:.4f}', 'P_Gamma': '{:.4f}',
            'C_IV': '{:.1f}', 'P_IV': '{:.1f}',
            'Net_GEX': '{:,.0f}'
        }).background_gradient(subset=['Net_GEX'], cmap='RdYlGn', vmin=-abs(matrix['Net_GEX']).max(), vmax=abs(matrix['Net_GEX']).max()),
        width="stretch",
        height=700
    )


# ═══ TAB 5: DATA ══════════════════════════════════════════════
with tab_data:
    st.markdown("### 📋 GEX Data Table")
    
    display_df = gex_filtered[['strike', 'call_gex', 'put_gex', 'net_gex', 
                                'call_oi', 'put_oi', 'call_vol', 'put_vol',
                                'total_gamma', 'net_dex']].copy()
    display_df.columns = ['Strike', 'Call GEX', 'Put GEX', 'Net GEX', 
                          'Call OI', 'Put OI', 'Call Vol', 'Put Vol',
                          'Total Γ', 'Net Δ']
    display_df = display_df.sort_values('Total Γ', ascending=False)
    
    st.dataframe(
        display_df.style.format({
            'Strike': '${:.0f}', 'Call GEX': '{:,.0f}', 'Put GEX': '{:,.0f}',
            'Net GEX': '{:,.0f}', 'Call OI': '{:,.0f}', 'Put OI': '{:,.0f}',
            'Call Vol': '{:,.0f}', 'Put Vol': '{:,.0f}',
            'Total Γ': '{:,.4f}', 'Net Δ': '{:,.0f}'
        }),
        width="stretch", height=600
    )
    
    # Download
    csv = gex_filtered.to_csv(index=False)
    st.download_button("📥 Download CSV", csv, f"gex_{ticker}_{expiry}.csv", "text/csv")


# ═══ TAB 6: DEBUG ═════════════════════════════════════════════
with tab_debug:
    st.markdown("### 🔧 Debug / Fetch Log")
    for entry in log:
        if "ERROR" in entry:
            st.error(entry)
        elif "⚠" in entry:
            st.warning(entry)
        else:
            st.success(entry)
    
    st.markdown("### Raw Data Sample")
    with st.expander("Calls (first 10)"):
        st.dataframe(calls.head(10))
    with st.expander("Puts (first 10)"):
        st.dataframe(puts.head(10))


# ─── FOOTER ───────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:#5a6a8a; font-family:'Courier New'; font-size:11px;">
    💾 Data: Barchart.com | ⏰ {datetime.now().strftime('%H:%M:%S %Y-%m-%d')} | 
    📊 {ticker} {expiry} | ⚠️ Educational purposes only
</div>
""", unsafe_allow_html=True)


# ─── AUTO REFRESH ──────────────────────────────────────────────
if auto_refresh:
    time.sleep(300)
    st.rerun()
