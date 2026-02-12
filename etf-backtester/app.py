import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, date
from backtester import ETFBacktester
from data_handler import DataHandler

# Page configuration
st.set_page_config(
    page_title="ETF Trading Strategy Backtester",
    page_icon="📈",
    layout="wide"
)

st.title("📈 ETF Trading Strategy Backtester")
st.markdown("Compare intraday vs overnight holding periods for each weekday")

# Sidebar for user inputs
st.sidebar.header("Strategy Parameters")

# ETF selection
etf_input = st.sidebar.text_input(
    "ETF Symbols (comma-separated)", 
    value="SPY", 
    help="Enter one or more ETF symbols separated by commas (e.g., SPY, QQQ, IWM)"
)
etf_symbols = [s.strip().upper() for s in etf_input.split(",") if s.strip()]

# Year selection
current_year = datetime.now().year
start_year = st.sidebar.selectbox(
    "Starting Year",
    options=list(range(2000, current_year + 1)),
    index=0,  # Default to 2000
    help="Select the starting year for backtesting"
)

# Date range display
end_date = datetime.now().date()
start_date = date(start_year, 1, 1)
st.sidebar.info(f"Backtesting period: {start_date} to {end_date}")

# Run backtest button
if st.sidebar.button("Run Backtest", type="primary"):
    st.session_state.run_backtest = True

# Initialize components
@st.cache_data
def load_all_data(symbols, start_year):
    """Load and cache data for all ETFs"""
    all_data = {}
    data_handler = DataHandler()
    for symbol in symbols:
        data = data_handler.fetch_data(symbol, start_year)
        if data is not None and not data.empty:
            all_data[symbol] = data
    return all_data

# Main content
if hasattr(st.session_state, 'run_backtest') and st.session_state.run_backtest:
    with st.spinner(f"Fetching data and running backtest for {', '.join(etf_symbols)}..."):
        try:
            # Load data
            all_etf_data = load_all_data(etf_symbols, start_year)
            
            if not all_etf_data:
                st.error("No data found for any of the symbols provided. Please check the symbols and try again.")
                st.stop()
            
            # For multiple tickers, we'll provide a selector or aggregate
            selected_ticker = st.selectbox("Select Ticker to View", options=list(all_etf_data.keys()))
            data = all_etf_data[selected_ticker]
            
            # Display data info
            st.success(f"✅ Successfully loaded {len(data)} trading days of {selected_ticker} data")
            
            # Run backtest
            backtester = ETFBacktester(data)
            results = backtester.run_all_strategies()
            
            if results is None:
                st.error(f"Failed to run backtest for {selected_ticker}. Please try again.")
                st.stop()

            # Global Top 5 Strategies across all tickers (if multiple)
            if len(all_etf_data) > 1:
                st.header("🏆 Global Top 5 Strategies")
                all_results = []
                for ticker, ticker_data in all_etf_data.items():
                    t_backtester = ETFBacktester(ticker_data)
                    t_results = t_backtester.run_all_strategies()
                    t_results['Ticker'] = ticker
                    all_results.append(t_results)
                
                combined_results = pd.concat(all_results).sort_values('Total Return (%)', ascending=False)
                top_5 = combined_results.head(5)[['Ticker', 'Strategy', 'Total Return (%)', 'Win Rate (%)', 'Median Return (%)']]
                st.table(top_5.style.format({'Total Return (%)': '{:.2f}%', 'Win Rate (%)': '{:.1f}%', 'Median Return (%)': '{:.2f}%'}))
            
            # Display results
            st.header(f"🎯 Results for {selected_ticker}")
            
            # Summary metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            best_strategy = results.loc[results['Total Return (%)'].idxmax()]
            worst_strategy = results.loc[results['Total Return (%)'].idxmin()]
            avg_return = results['Total Return (%)'].mean()
            avg_win_rate = results['Win Rate (%)'].mean()
            median_ret = results['Median Return (%)'].mean()
            
            with col1:
                st.metric(
                    "Best Strategy",
                    f"{best_strategy['Strategy']}",
                    f"{best_strategy['Total Return (%)']:.2f}%"
                )
            
            with col2:
                st.metric(
                    "Worst Strategy",
                    f"{worst_strategy['Strategy']}",
                    f"{worst_strategy['Total Return (%)']:.2f}%"
                )
            
            with col3:
                st.metric(
                    "Average Return",
                    f"{avg_return:.2f}%"
                )
            
            with col4:
                st.metric(
                    "Median Return",
                    f"{median_ret:.2f}%"
                )

            with col5:
                st.metric(
                    "Average Win Rate",
                    f"{avg_win_rate:.1f}%"
                )
            
            # Results table
            st.subheader("📊 Strategy Comparison")
            
            # Format the results table for display
            display_results = results.copy()
            display_results = display_results.round(2)
            
            # Color coding for the table
            def style_dataframe(df):
                def color_returns(val):
                    if isinstance(val, (int, float)):
                        color = 'red' if val < 0 else 'green' if val > 0 else 'black'
                        return f'color: {color}'
                    return ''
                
                def color_strategy(val):
                    if "Green" in str(val):
                        return 'background-color: rgba(0, 255, 0, 0.1); color: green'
                    if "Red" in str(val):
                        return 'background-color: rgba(255, 0, 0, 0.1); color: red'
                    return ''
                    
                return df.style.applymap(color_returns, subset=['Total Return (%)', 'Avg Return per Trade (%)', 'Median Return (%)']) \
                               .applymap(color_strategy, subset=['Strategy'])
            
            st.dataframe(
                style_dataframe(display_results),
                use_container_width=True
            )

            # Period Bucketing Analysis
            st.subheader("⏳ Period Analysis (5-Year Buckets)")
            
            data_years = data.index.year.unique()
            buckets = []
            max_year = data.index.year.max()
            min_year = data.index.year.min()
            
            for end_y in range(max_year, min_year - 1, -5):
                start_y = max(min_year, end_y - 4)
                bucket_data = data[(data.index.year >= start_y) & (data.index.year <= end_y)]
                if len(bucket_data) > 20: # Ensure enough data
                    bucket_backtester = ETFBacktester(bucket_data)
                    bucket_results = bucket_backtester.run_all_strategies()
                    bucket_best = bucket_results.iloc[0]
                    buckets.append({
                        'Period': f"{start_y}-{end_y}",
                        'Best Strategy': bucket_best['Strategy'],
                        'Best Return (%)': bucket_best['Total Return (%)'],
                        'Win Rate (%)': bucket_best['Win Rate (%)']
                    })
            
            if buckets:
                st.dataframe(pd.DataFrame(buckets), use_container_width=True)
            
            # Visualizations
            st.subheader("📈 Performance Visualizations")
            
            # Create tabs for different views
            tab1, tab2, tab3, tab4 = st.tabs(["Return Comparison", "Win Rate Analysis", "Risk-Return", "Trade Statistics"])
            
            with tab1:
                # Total return comparison
                fig_returns = px.bar(
                    results,
                    x='Strategy',
                    y='Total Return (%)',
                    title='Total Return by Strategy',
                    color='Total Return (%)',
                    color_continuous_scale='RdYlGn'
                )
                fig_returns.update_layout(xaxis_tickangle=-45)
                # Color the labels based on Strategy type
                colors = ['green' if 'Green' in s else 'red' if 'Red' in s else 'black' for s in results['Strategy']]
                st.plotly_chart(fig_returns, use_container_width=True)
                
                # Separate intraday vs overnight
                results['Strategy Type'] = results['Strategy'].apply(
                    lambda x: 'Intraday' if 'intraday' in x.lower() or 'close' in x.lower() else 'Overnight'
                )
                results['Weekday'] = results['Strategy'].apply(
                    lambda x: x.split()[1] if len(x.split()) > 1 else x.split()[0]
                )
                
                fig_comparison = px.bar(
                    results,
                    x='Weekday',
                    y='Total Return (%)',
                    color='Strategy Type',
                    barmode='group',
                    title='Intraday vs Overnight Returns by Weekday'
                )
                st.plotly_chart(fig_comparison, use_container_width=True)
            
            with tab2:
                # Win rate analysis
                fig_winrate = px.bar(
                    results,
                    x='Strategy',
                    y='Win Rate (%)',
                    title='Win Rate by Strategy',
                    color='Win Rate (%)',
                    color_continuous_scale='Blues'
                )
                fig_winrate.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_winrate, use_container_width=True)
            
            with tab3:
                # Risk-return scatter
                fig_risk_return = px.scatter(
                    results,
                    x='Volatility (%)',
                    y='Total Return (%)',
                    color='Strategy Type',
                    size='Total Trades',
                    hover_data=['Strategy', 'Win Rate (%)'],
                    title='Risk-Return Profile'
                )
                st.plotly_chart(fig_risk_return, use_container_width=True)
            
            with tab4:
                # Trade statistics
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_trades = px.bar(
                        results,
                        x='Strategy',
                        y='Total Trades',
                        title='Total Trades by Strategy'
                    )
                    fig_trades.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_trades, use_container_width=True)
                
                with col2:
                    fig_avg_return = px.bar(
                        results,
                        x='Strategy',
                        y='Avg Return per Trade (%)',
                        title='Average Return per Trade',
                        color='Avg Return per Trade (%)',
                        color_continuous_scale='RdYlGn'
                    )
                    fig_avg_return.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_avg_return, use_container_width=True)
            
            # Download results
            st.subheader("💾 Download Results")
            csv = results.to_csv(index=False)
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name=f"{selected_ticker}_backtest_results_{start_year}.csv",
                mime="text/csv"
            )
            
            # Key insights
            st.subheader("🔍 Key Insights")
            
            # Real-time Action Advisor
            st.divider()
            st.subheader("💡 Real-time Action Advisor")
            
            # Use US Eastern time for market hours
            import pytz
            eastern = pytz.timezone('US/Eastern')
            now_est = datetime.now(eastern)
            today_weekday = now_est.strftime('%A')
            
            # Define market hours in EST
            market_open_time = now_est.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close_time = now_est.replace(hour=16, minute=0, second=0, microsecond=0)
            
            if today_weekday in ['Saturday', 'Sunday']:
                st.info(f"Markets are closed today ({today_weekday}). Check back on Monday morning!")
            else:
                # Get last close color
                last_day = data.iloc[-1]
                last_color = 'Green' if last_day['Close'] > last_day['Open'] else 'Red'
                
                is_trading_hours = market_open_time <= now_est <= market_close_time
                is_pre_market = now_est < market_open_time
                
                st.write(f"**Current Status (EST)**: {today_weekday} {now_est.strftime('%H:%M')} | Last Trading Day: {last_color}")
                
                # Filter best strategies for today based on previous color
                today_strategies = results[results['Strategy'].str.contains(today_weekday)]
                conditional_strategies = today_strategies[today_strategies['Strategy'].str.contains(last_color)]
                
                if not conditional_strategies.empty:
                    best_for_today = conditional_strategies.iloc[0]
                    st.success(f"**Recommended Strategy for {today_weekday} (given {last_color} yesterday)**: {best_for_today['Strategy']}")
                    st.write(f"Historical Total Return: {best_for_today['Total Return (%)']:.2f}% | Win Rate: {best_for_today['Win Rate (%)']:.1f}%")
                    
                    if is_trading_hours:
                        # Logic adjustment: If today is Wednesday and the strategy is "Tuesday Open -> Wednesday Open", 
                        # it means the exit happened at Wednesday's open.
                        if "Open →" in best_for_today['Strategy'] and f"→ {today_weekday} Open" in best_for_today['Strategy']:
                            st.info(f"🏁 **Strategy Complete**: The {best_for_today['Strategy']} strategy exit happened at today's open.")
                        else:
                            st.warning("⚠️ **Active Trading Hours**: If you followed the strategy, you should be in a trade or looking for the close.")
                    elif is_pre_market:
                        st.info(f"🕒 **Pre-market**: Prepare to execute the {best_for_today['Strategy']} at the 9:30 AM EST open.")
                    else:
                        # After hours
                        st.info(f"🌙 **After Hours**: Market is closed. Today's strategy results are now part of history.")
                else:
                    # Fallback to general today strategy if no conditional match
                    if not today_strategies.empty:
                        best_for_today = today_strategies.iloc[0]
                        st.info(f"Today is {today_weekday}. Best general strategy: {best_for_today['Strategy']}")

            # Calculate insights
            intraday_avg = results[results['Strategy Type'] == 'Intraday']['Total Return (%)'].mean()
            overnight_avg = results[results['Strategy Type'] == 'Overnight']['Total Return (%)'].mean()
            
            best_weekday = results.groupby('Weekday')['Total Return (%)'].mean().idxmax()
            worst_weekday = results.groupby('Weekday')['Total Return (%)'].mean().idxmin()
            
            insights = [
                f"**Strategy Performance**: {'Intraday' if intraday_avg > overnight_avg else 'Overnight'} strategies performed better on average ({max(intraday_avg, overnight_avg):.2f}% vs {min(intraday_avg, overnight_avg):.2f}%)",
                f"**Best Weekday**: {best_weekday} showed the highest average returns across strategies",
                f"**Worst Weekday**: {worst_weekday} showed the lowest average returns across strategies",
                f"**Total Period**: Analyzed {len(data)} trading days from {start_date} to {end_date}",
                f"**Data Coverage**: {((end_date - start_date).days / 365.25):.1f} years of market data"
            ]
            
            for insight in insights:
                st.write(f"• {insight}")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Please check your inputs and try again.")

else:
    # Initial page content
    st.markdown("""
    ## Welcome to the ETF Trading Strategy Backtester! 👋
    
    This tool helps you analyze the performance of different weekday trading strategies:
    
    ### 📋 What it does:
    - Tests **10 different strategies** across all weekdays
    - Compares **intraday** vs **overnight** holding periods
    - Provides comprehensive **performance metrics**
    - Shows **interactive visualizations** of results
    
    ### 🎯 Strategies Tested:
    **Intraday Strategies** (buy open, sell close same day):
    - Monday Open → Monday Close
    - Tuesday Open → Tuesday Close
    - Wednesday Open → Wednesday Close
    - Thursday Open → Thursday Close
    - Friday Open → Friday Close
    
    **Overnight Strategies** (buy open, sell next day open):
    - Monday Open → Tuesday Open
    - Tuesday Open → Wednesday Open
    - Wednesday Open → Thursday Open
    - Thursday Open → Friday Open
    
    ### 📊 Metrics Calculated:
    - Total Return (%)
    - Win Rate (%)
    - Average Return per Trade (%)
    - Total Number of Trades
    - Volatility (%)
    
    ### 🚀 Get Started:
    1. Enter your ETF symbol (default: SPY)
    2. Select starting year (default: 2000)
    3. Click "Run Backtest" to analyze
    
    """)
    
    # Sample data info
    st.info("💡 **Tip**: SPY data is available from 1993. Popular ETFs include SPY, QQQ, IWM, VTI, etc.")
