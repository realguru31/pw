import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class ETFBacktester:
    """
    ETF backtesting engine for weekday trading strategies
    """
    
    def __init__(self, data):
        """
        Initialize backtester with price data
        
        Args:
            data (pd.DataFrame): DataFrame with OHLCV data and weekday column
        """
        self.data = data.copy()
        self.results = {}
        self.weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        
    def calculate_strategy_performance(self, trades_df):
        """
        Calculate performance metrics for a strategy
        
        Args:
            trades_df (pd.DataFrame): DataFrame with buy/sell prices and returns
            
        Returns:
            dict: Performance metrics
        """
        if trades_df.empty:
            return {
                'Total Return (%)': 0,
                'Win Rate (%)': 0,
                'Avg Return per Trade (%)': 0,
                'Median Return (%)': 0,
                'Total Trades': 0,
                'Volatility (%)': 0
            }
        
        # Calculate metrics
        total_return = (trades_df['Return'].add(1).prod() - 1) * 100
        win_rate = (trades_df['Return'] > 0).mean() * 100
        avg_return_per_trade = trades_df['Return'].mean() * 100
        median_return = trades_df['Return'].median() * 100
        total_trades = len(trades_df)
        volatility = trades_df['Return'].std() * np.sqrt(252) * 100  # Annualized volatility
        
        return {
            'Total Return (%)': total_return,
            'Win Rate (%)': win_rate,
            'Avg Return per Trade (%)': avg_return_per_trade,
            'Median Return (%)': median_return,
            'Total Trades': total_trades,
            'Volatility (%)': volatility
        }
    
    def intraday_strategy(self, weekday):
        """
        Buy at open, sell at close on the same weekday
        
        Args:
            weekday (str): Day of week to trade
            
        Returns:
            pd.DataFrame: Trading results
        """
        # Filter data for the specific weekday
        weekday_data = self.data[self.data['Weekday'] == weekday].copy()
        
        if weekday_data.empty:
            return pd.DataFrame()
        
        # Calculate returns (buy open, sell close)
        weekday_data['Return'] = (weekday_data['Close'] - weekday_data['Open']) / weekday_data['Open']
        weekday_data['Buy_Price'] = weekday_data['Open']
        weekday_data['Sell_Price'] = weekday_data['Close']
        
        return weekday_data[['Buy_Price', 'Sell_Price', 'Return']].copy()
    
    def overnight_strategy(self, buy_weekday):
        """
        Buy at open on buy_weekday, sell at open next trading day
        
        Args:
            buy_weekday (str): Day of week to buy
            
        Returns:
            pd.DataFrame: Trading results
        """
        # Get the next trading day
        weekday_mapping = {
            'Monday': 'Tuesday',
            'Tuesday': 'Wednesday', 
            'Wednesday': 'Thursday',
            'Thursday': 'Friday'
        }
        
        # Friday overnight strategy not supported (no Saturday trading)
        if buy_weekday == 'Friday':
            return pd.DataFrame()
        
        sell_weekday = weekday_mapping[buy_weekday]
        
        # Get buy and sell data
        buy_data = self.data[self.data['Weekday'] == buy_weekday].copy()
        sell_data = self.data[self.data['Weekday'] == sell_weekday].copy()
        
        if buy_data.empty or sell_data.empty:
            return pd.DataFrame()
        
        # Align dates for overnight trades
        trades = []
        
        for buy_date, buy_row in buy_data.iterrows():
            # Find the next trading day (should be the sell_weekday)
            next_trading_days = sell_data[sell_data.index > buy_date]
            
            if not next_trading_days.empty:
                sell_date = next_trading_days.index[0]
                sell_row = next_trading_days.iloc[0]
                
                # Calculate return (buy at buy_weekday open, sell at sell_weekday open)
                buy_price = buy_row['Open']
                sell_price = sell_row['Open']
                trade_return = (sell_price - buy_price) / buy_price
                
                trades.append({
                    'Buy_Date': buy_date,
                    'Sell_Date': sell_date,
                    'Buy_Price': buy_price,
                    'Sell_Price': sell_price,
                    'Return': trade_return
                })
        
        if not trades:
            return pd.DataFrame()
        
        trades_df = pd.DataFrame(trades)
        return trades_df[['Buy_Price', 'Sell_Price', 'Return']].copy()
    
    def run_all_strategies(self):
        """
        Run all trading strategies and compile results
        
        Returns:
        pd.DataFrame: Results for all strategies
        """
        results = []
        
        # Identify Previous Day Color (Green: Close > Open, Red: Close < Open)
        self.data['Prev_Color'] = (self.data['Close'].shift(1) > self.data['Open'].shift(1)).map({True: 'Green', False: 'Red'})
        
        # Run intraday strategies for each weekday
        for weekday in self.weekdays:
            # Base strategy
            trades = self.intraday_strategy(weekday)
            performance = self.calculate_strategy_performance(trades)
            performance['Strategy'] = f"{weekday} Open → {weekday} Close"
            results.append(performance)
            
            # Conditional strategies
            for color in ['Green', 'Red']:
                cond_trades = self.intraday_strategy_conditional(weekday, color)
                performance = self.calculate_strategy_performance(cond_trades)
                performance['Strategy'] = f"{weekday} Intraday (If Prev Day {color})"
                results.append(performance)
        
        # Run overnight strategies 
        for weekday in self.weekdays[:-1]:  # Exclude Friday (no weekend trading)
            # Base strategy
            trades = self.overnight_strategy(weekday)
            performance = self.calculate_strategy_performance(trades)
            
            weekday_mapping = {'Monday': 'Tuesday', 'Tuesday': 'Wednesday', 'Wednesday': 'Thursday', 'Thursday': 'Friday'}
            next_weekday = weekday_mapping[weekday]
            performance['Strategy'] = f"{weekday} Open → {next_weekday} Open"
            results.append(performance)
            
            # Conditional strategies
            for color in ['Green', 'Red']:
                cond_trades = self.overnight_strategy_conditional(weekday, color)
                performance = self.calculate_strategy_performance(cond_trades)
                performance['Strategy'] = f"{weekday} Open → {next_weekday} Open (If Prev Day {color})"
                results.append(performance)
        
        # Convert to DataFrame and sort by total return
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('Total Return (%)', ascending=False)
        
        # Reorder columns for better display
        column_order = [
            'Strategy', 
            'Total Return (%)', 
            'Win Rate (%)', 
            'Avg Return per Trade (%)', 
            'Median Return (%)',
            'Total Trades',
            'Volatility (%)'
        ]
        results_df = results_df[column_order]
        
        return results_df.reset_index(drop=True)

    def intraday_strategy_conditional(self, weekday, prev_color):
        """Buy at open, sell at close if previous day was prev_color"""
        weekday_data = self.data[(self.data['Weekday'] == weekday) & (self.data['Prev_Color'] == prev_color)].copy()
        if weekday_data.empty: return pd.DataFrame()
        weekday_data['Return'] = (weekday_data['Close'] - weekday_data['Open']) / weekday_data['Open']
        weekday_data['Buy_Price'] = weekday_data['Open']
        weekday_data['Sell_Price'] = weekday_data['Close']
        return weekday_data[['Buy_Price', 'Sell_Price', 'Return']].copy()

    def overnight_strategy_conditional(self, buy_weekday, prev_color):
        """Buy at open, sell next day open if previous day was prev_color"""
        weekday_mapping = {'Monday': 'Tuesday', 'Tuesday': 'Wednesday', 'Wednesday': 'Thursday', 'Thursday': 'Friday'}
        if buy_weekday == 'Friday': return pd.DataFrame()
        sell_weekday = weekday_mapping[buy_weekday]
        
        buy_data = self.data[(self.data['Weekday'] == buy_weekday) & (self.data['Prev_Color'] == prev_color)].copy()
        sell_data = self.data[self.data['Weekday'] == sell_weekday].copy()
        
        if buy_data.empty or sell_data.empty: return pd.DataFrame()
        
        trades = []
        for buy_date, buy_row in buy_data.iterrows():
            next_trading_days = sell_data[sell_data.index > buy_date]
            if not next_trading_days.empty:
                sell_row = next_trading_days.iloc[0]
                trades.append({
                    'Return': (sell_row['Open'] - buy_row['Open']) / buy_row['Open'],
                    'Buy_Price': buy_row['Open'],
                    'Sell_Price': sell_row['Open']
                })
        
        return pd.DataFrame(trades) if trades else pd.DataFrame()

    def get_strategy_details(self, strategy_name):
        """
        Get detailed trade-by-trade results for a specific strategy
        
        Args:
            strategy_name (str): Name of the strategy to analyze
            
        Returns:
            pd.DataFrame: Detailed trade results
        """
        # Parse strategy name to determine type and weekday
        if "→" in strategy_name:
            parts = strategy_name.split(" → ")
            buy_part = parts[0].strip()
            sell_part = parts[1].strip()
            
            buy_weekday = buy_part.split()[0]
            
            if "Close" in sell_part and buy_weekday in sell_part:
                # Intraday strategy
                return self.intraday_strategy(buy_weekday)
            else:
                # Overnight strategy  
                return self.overnight_strategy(buy_weekday)
        
        return pd.DataFrame()
