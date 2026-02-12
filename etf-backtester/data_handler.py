import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, date
import streamlit as st

class DataHandler:
    
    def __init__(self):
        self.data = None
        
    def fetch_data(self, symbol, start_year):
        try:
            start_date = date(start_year, 1, 1)
            end_date = datetime.now().date()
            
            ticker = yf.Ticker(symbol)
            data = ticker.history(
                start=start_date,
                end=end_date,
                auto_adjust=True
            )
            
            if data.empty:
                st.error(f"No data found for symbol {symbol}")
                return None
                
            data = self.preprocess_data(data)
            data = self.add_weekday_info(data)
            data = self.filter_trading_days(data)
            
            if data.empty:
                st.error(f"No trading day data available for {symbol}")
                return None
                
            return data
            
        except Exception as e:
            st.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def preprocess_data(self, data):
        data = data.dropna()
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        for col in required_columns:
            if col not in data.columns:
                raise ValueError(f"Missing required column: {col}")
        
        return data.sort_index()
    
    def add_weekday_info(self, data):
        data['Weekday'] = data.index.day_name()
        data['Weekday_Num'] = data.index.weekday
        return data
    
    def filter_trading_days(self, data):
        trading_days = data[data['Weekday_Num'] <= 4].copy()
        trading_days = trading_days[trading_days['Volume'] > 0]
        return trading_days
