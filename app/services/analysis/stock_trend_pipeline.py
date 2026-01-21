"""
Stock trend analysis pipeline: fetch kbar, calculate indicators, and generate structured signals for LLM or downstream analysis.
All functions are pure, testable, and follow SRP.
"""

from typing import Any

import pandas as pd

from app.internal.analysis.indicators import (
    calculate_adx,
    calculate_atr,
    calculate_bollinger_bands,
    calculate_cci,
    calculate_kdj,
    calculate_macd,
    calculate_moving_averages,
    calculate_obv,
    calculate_rsi,
    calculate_vma,
)
from app.internal.yfinance.stock_data import fetch_kline_data
from app.services.analysis.trend_analysis import generate_trend_signals
from app.utils.logger import log


def fetch_and_prepare_kline(stock_id: str) -> pd.DataFrame:
    """
    Fetch kbar data for a given stock_id and return a DataFrame.
    Returns empty DataFrame if data is unavailable.
    """
    df = fetch_kline_data(stock_id)
    if df is None or df.empty:
        return pd.DataFrame()
    return df


def enrich_with_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate and append all required technical indicators to the DataFrame.
    Returns the enriched DataFrame.
    """
    df = calculate_moving_averages(df)
    df = calculate_macd(df)
    df = calculate_vma(df)
    df = calculate_cci(df)
    df = calculate_rsi(df)
    df = calculate_bollinger_bands(df)
    df = calculate_atr(df)
    df = calculate_kdj(df)
    df = calculate_obv(df)
    df = calculate_adx(df)
    return df


def convert_numpy_types(obj):
    """
    Recursively convert numpy types in a dict/list to native Python types for serialization and readability.
    """
    import numpy as np

    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(v) for v in obj]
    elif isinstance(obj, (np.generic,)):
        return obj.item()
    return obj


def analyze_stock_trend_signal(stock_id: str) -> dict[str, Any]:
    """
    Main pipeline: fetch kbar, enrich with indicators, and generate structured trend signals.
    Returns a signal dict for LLM or downstream use.
    """
    log.debug("[Breakpoint] Fetching kline data: stock_id={}", stock_id)
    df = fetch_and_prepare_kline(stock_id)
    if df.empty:
        log.debug("[Breakpoint] Kline data empty for {}", stock_id)
        return {"signal_status": "invalid", "reason": f"No kbar data for {stock_id}"}
    enriched_df = enrich_with_all_indicators(df)
    log.debug(
        "[Breakpoint] Enriched data rows={} columns={}",
        len(enriched_df),
        len(enriched_df.columns),
    )
    signal = generate_trend_signals(enriched_df)
    log.debug(
        "[Breakpoint] Signal status={} score_total={}",
        signal.get("signal_status"),
        signal.get("score_total"),
    )
    # Ensure the result is a dict at the top level
    if not isinstance(signal, dict):
        return {"signal_status": "invalid", "reason": "Signal is not a dict"}
    return convert_numpy_types(signal)
