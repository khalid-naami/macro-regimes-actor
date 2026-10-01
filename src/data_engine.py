"""Cross-Asset Data Engine for fetching commodities, treasury yields, and macro proxies."""

import logging
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
import yfinance as yf

logger = logging.getLogger(__name__)

class MacroDataEngine:
    """Fetches and cleans historical cross-asset market data."""

    def __init__(self, gold_symbol: str = "GC=F", copper_symbol: str = "HG=F"):
        self.gold_symbol = gold_symbol.strip()
        self.copper_symbol = copper_symbol.strip()
        self.fallback_map = {
            "GC=F": "GLD",
            "HG=F": "CPER",
            "CL=F": "USO",
            "DX-Y.NYB": "UUP"
        }

    def fetch_regime_data(self, period: str = "2y") -> Optional[pd.DataFrame]:
        """Fetch historical daily prices for Gold, Copper, 10Y Yield, 30Y Yield, and Macro Proxies."""
        tickers = [self.gold_symbol, self.copper_symbol, "^TNX", "^TYX"]
        logger.info(f"Fetching cross-asset data for {tickers} over period={period}...")

        try:
            raw_data = yf.download(tickers, period=period, interval="1d", progress=False, auto_adjust=False)
            
            # Extract 'Close' prices
            if isinstance(raw_data.columns, pd.MultiIndex):
                if 'Close' in raw_data.columns.levels[0]:
                    close_df = raw_data['Close']
                else:
                    close_df = raw_data.xs('Close', axis=1, level=0)
            else:
                close_df = raw_data.get('Close', raw_data)

        except Exception as e:
            logger.warning(f"Batch yfinance download failed: {e}. Falling back to individual downloads.")
            close_df = pd.DataFrame()

        df = pd.DataFrame(index=close_df.index if not close_df.empty else None)

        for ticker in tickers:
            col_series = None
            if not close_df.empty and ticker in close_df.columns:
                series = close_df[ticker].dropna()
                if len(series) > 10:
                    col_series = close_df[ticker]

            # If missing or incomplete, try direct or fallback
            if col_series is None:
                try:
                    logger.info(f"Fetching individual ticker {ticker}...")
                    t_data = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=False)
                    if not t_data.empty:
                        col_series = t_data['Close'] if 'Close' in t_data else t_data.iloc[:, 0]
                except Exception:
                    pass

            # If still missing, try fallback proxy
            if col_series is None and ticker in self.fallback_map:
                fb_ticker = self.fallback_map[ticker]
                try:
                    logger.info(f"Using fallback proxy {fb_ticker} for {ticker}...")
                    fb_data = yf.download(fb_ticker, period=period, interval="1d", progress=False, auto_adjust=False)
                    if not fb_data.empty:
                        col_series = fb_data['Close'] if 'Close' in fb_data else fb_data.iloc[:, 0]
                except Exception as ex:
                    logger.warning(f"Fallback {fb_ticker} also failed: {ex}")

            if col_series is not None:
                if df.empty:
                    df = pd.DataFrame(index=col_series.index)
                df[ticker] = col_series

        # Clean and forward-fill
        df = df.ffill().bfill().dropna()

        if df.empty or len(df) < 30:
            logger.error("Insufficient macro regime data retrieved.")
            return None

        # Standardize column mapping
        clean_df = pd.DataFrame(index=df.index)
        clean_df['gold'] = df[self.gold_symbol] if self.gold_symbol in df else df.iloc[:, 0]
        clean_df['copper'] = df[self.copper_symbol] if self.copper_symbol in df else df.iloc[:, 1]
        clean_df['y10'] = df['^TNX'] if '^TNX' in df else 4.0
        clean_df['y30'] = df['^TYX'] if '^TYX' in df else 4.5

        logger.info(f"Successfully processed {len(clean_df)} macro trading days.")
        return clean_df
