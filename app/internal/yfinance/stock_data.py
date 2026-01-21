"""
YFinance data retrieval service for stock OHLCV and info.
All functions are pure and suitable for dependency injection.
"""

import os
from typing import Dict, Optional

import pandas as pd

import yfinance as yf
from app.utils.logger import log


def _build_session():
    insecure = os.getenv("INSECURE_TLS", "").lower() in {"1", "true", "yes"}
    insecure = insecure or os.getenv("YFINANCE_INSECURE_TLS", "").lower() in {
        "1",
        "true",
        "yes",
    }
    if insecure:
        try:
            from curl_cffi import requests as curl_requests

            session = curl_requests.Session()
            session.verify = False
            log.warning("YFinance TLS verification disabled (curl_cffi)")
            return session
        except ImportError:
            import requests

            session = requests.Session()
            session.verify = False
            log.warning("YFinance TLS verification disabled (requests)")
            return session
    return None


def fetch_kline_data(yf_code: str) -> pd.DataFrame:
    """
    Fetch K-line (OHLCV) data from yfinance and return as a DataFrame.
    Args:
        yf_code (str): yfinance ticker code (e.g., '2330.TW').
    Returns:
        pd.DataFrame: DataFrame with columns [open, high, low, close, volume].
    """
    try:
        session = _build_session()
        data = yf.download(
            tickers=yf_code,
            period="3mo",
            interval="1d",
            auto_adjust=True,
            session=session,
        )
        if data is None or data.empty:
            log.warning(f"No data returned for ({yf_code})")
            return pd.DataFrame()
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        column_mapping = {
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
        expected_columns = list(column_mapping.keys())
        missing_columns = [col for col in expected_columns if col not in data.columns]
        if missing_columns:
            log.warning(
                f"Missing expected columns {missing_columns} in data for {yf_code}"
            )
            return pd.DataFrame()
        data = data.rename(columns=column_mapping)
        data.index.name = "timestamp"
        data = data[["open", "high", "low", "close", "volume"]]
        # If data is a Series, convert to DataFrame
        if isinstance(data, pd.Series):
            data = data.to_frame().T
        data["volume"] = data["volume"] // 1000
        data["open"] = data["open"] // 1
        data["high"] = data["high"] // 1
        data["low"] = data["low"] // 1
        data["close"] = data["close"] // 1
        return data
    except Exception as e:
        log.error(f"Error fetching data for ({yf_code}): {e}")
        return pd.DataFrame()


def fetch_stock_info(yf_code: str) -> Dict[str, str]:
    """
    Fetch sector and industry info for a stock from yfinance.
    Args:
        yf_code (str): Stock ticker code.
    Returns:
        dict: {"sector": str, "industry": str}
    """
    try:
        session = _build_session()
        stock = yf.Ticker(yf_code, session=session)
        info = stock.info
        sector = info.get("sector", "未知行業")
        industry = info.get("industry", "未知產業")
        return {"sector": sector, "industry": industry}
    except Exception as e:
        log.error(f"Failed to get basic info for {yf_code}: {e}")
        return {"sector": "未知行業", "industry": "未知產業"}
