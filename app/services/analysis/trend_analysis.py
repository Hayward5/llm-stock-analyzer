"""
Trend analysis service for stock market data.
Provides pure, stateless functions for technical trend detection and signal generation.
"""

from typing import Any, Dict, List

import pandas as pd

from app.utils.logger import log

REQUIRED_COLUMNS = [
    "macd",
    "signal_line",
    "5ma",
    "10ma",
    "20ma",
    "open",
    "high",
    "low",
    "close",
    "vma_short",
    "vma_long",
    "cci",
    "volume",
    "rsi",
    "bollinger_upper",
    "bollinger_lower",
    "atr",
]


def compute_scores(
    latest: pd.Series, trend_ticks: pd.DataFrame
) -> tuple[int, Dict[str, int], Dict[str, bool]]:
    trend = 0
    momentum = 0
    volume = 0
    risk = 0

    ma_alignment = latest["5ma"] > latest["10ma"] > latest["20ma"]
    macd_bullish = (latest["macd"] - latest["signal_line"]) > 0
    adx_strong = latest.get("adx", 0) > 20

    if ma_alignment:
        trend += 2
    if macd_bullish:
        trend += 2
    if adx_strong:
        trend += 1

    rsi = float(latest["rsi"])
    rsi_healthy = 40 <= rsi <= 70
    if rsi_healthy:
        momentum += 1

    vma_short = trend_ticks["vma_short"].mean()
    vma_long = trend_ticks["vma_long"].mean()
    volume_support = vma_short > vma_long
    if volume_support:
        volume += 1

    atr = float(latest["atr"])
    close = float(latest["close"])
    atr_ratio = atr / close if close else 0
    atr_high_risk = atr_ratio > 0.05
    if atr_high_risk:
        risk -= 1

    score_total = trend + momentum + volume + risk
    score_breakdown = {
        "trend": trend,
        "momentum": momentum,
        "volume": volume,
        "risk": risk,
    }
    score_signals = {
        "ma_alignment": ma_alignment,
        "macd_bullish": macd_bullish,
        "adx_strong": adx_strong,
        "rsi_healthy": rsi_healthy,
        "volume_support": volume_support,
        "atr_high_risk": atr_high_risk,
    }
    return score_total, score_breakdown, score_signals


def validate_required_columns(df: pd.DataFrame, required: List[str]) -> bool:
    missing = [col for col in required if col not in df.columns]
    if missing:
        log.error(f"[Error] Missing columns: {missing}")
        return False
    return True


def macd_bullish_signal(latest: pd.Series, prev: pd.Series) -> bool:
    macd_diff = latest["macd"] - latest["signal_line"]
    short_ma = latest["5ma"]
    middle_ma = latest["10ma"]
    long_ma = latest["20ma"]
    ma_slope = (latest["5ma"] - prev["10ma"]) / prev["5ma"] if prev["5ma"] != 0 else 0
    return macd_diff > 0.01 and short_ma > middle_ma > long_ma and ma_slope > 0


def recent_high_signal(trend_ticks: pd.DataFrame) -> bool:
    latest_close = trend_ticks["close"].iloc[-1]
    rolling_high_3 = trend_ticks["close"].iloc[-3:-1].max()
    return latest_close > rolling_high_3


def sustained_highs_count(
    trend_ticks: pd.DataFrame, breakout_window: int, sustained_days: int
) -> int:
    sustained_highs = 0
    for i in range(1, sustained_days + 1):
        rolling_high_prev_series = (
            trend_ticks["close"].iloc[: -(i + 1)].rolling(window=breakout_window).max()
        )
        if (
            isinstance(rolling_high_prev_series, pd.Series)
            and not rolling_high_prev_series.empty
        ):
            rolling_high_prev = rolling_high_prev_series.iloc[-1]
        else:
            rolling_high_prev = float("-inf")
        if trend_ticks["close"].iloc[-i] > rolling_high_prev:
            sustained_highs += 1
        else:
            break
    return sustained_highs


def trend_momentum_signal(latest: pd.Series, trend_ticks: pd.DataFrame) -> bool:
    avg_vma_short = trend_ticks["vma_short"].mean()
    avg_vma_long = trend_ticks["vma_long"].mean()
    cci_latest = latest["cci"]
    return cci_latest > 100 and avg_vma_short > avg_vma_long


def volume_spike_signal(latest: pd.Series, trend_ticks: pd.DataFrame) -> bool:
    volume_today = latest["volume"]
    volume_20ma = trend_ticks["volume"].rolling(window=20).mean().iloc[-1]
    return volume_today > 2 * volume_20ma


def momentum_kbar_signal(df: pd.DataFrame, index: int) -> bool:
    vol_threshold = 2
    if index == 0:
        return False
    current_bar = df.iloc[index]
    previous_bar = df.iloc[index - 1]
    if current_bar["volume"] <= previous_bar["volume"] * vol_threshold:
        return False
    body_size = abs(current_bar["close"] - current_bar["open"])
    total_length = current_bar["high"] - current_bar["low"]
    if total_length == 0:
        return False
    shadow_ratio = (
        current_bar["high"]
        - max(current_bar["close"], current_bar["open"])
        + min(current_bar["close"], current_bar["open"])
        - current_bar["low"]
    ) / total_length
    if shadow_ratio > 0.2:
        return False
    recent_high = df.iloc[max(0, index - 3) : index]["high"].max()
    recent_low = df.iloc[max(0, index - 3) : index]["low"].min()
    return current_bar["close"] > recent_high or current_bar["close"] < recent_low


def rsi_overbought_signal(rsi: float) -> bool:
    return rsi > 70


def rsi_oversold_signal(rsi: float) -> bool:
    return rsi < 30


def bollinger_breakout_signal(latest_close: float, upper: float, lower: float) -> str:
    if latest_close > upper:
        return "breakout_upper"
    elif latest_close < lower:
        return "breakout_lower"
    return "none"


def generate_trend_signals(
    df: pd.DataFrame,
    trend_lookback_period: int = 60,
    breakout_window: int = 10,
    sustained_breakout_days: int = 3,
) -> Dict[str, Any]:
    """
    Generate a structured signal dict for LLM or downstream analysis based on technical indicators.
    Returns dict with all indicator results and values.
    """
    if not validate_required_columns(df, REQUIRED_COLUMNS):
        return {"signal_status": "invalid", "reason": "缺少必要欄位"}

    trend_ticks = df.iloc[-trend_lookback_period:]
    latest = trend_ticks.iloc[-1]
    prev = trend_ticks.iloc[-2]
    signal = {}

    # MACD
    signal["macd_bullish"] = macd_bullish_signal(latest, prev)
    signal["macd"] = float(latest["macd"])
    signal["signal_line"] = float(latest["signal_line"])

    # 近期創新高
    signal["recent_high"] = recent_high_signal(trend_ticks)

    # 連續突破
    sustained_highs = sustained_highs_count(
        trend_ticks, breakout_window, sustained_breakout_days
    )
    signal["sustained_highs"] = sustained_highs
    signal["sustained_highs_enough"] = sustained_highs >= sustained_breakout_days

    # 趨勢動能
    signal["trend_momentum"] = trend_momentum_signal(latest, trend_ticks)
    signal["cci"] = float(latest["cci"])
    signal["vma_short"] = float(latest["vma_short"])
    signal["vma_long"] = float(latest["vma_long"])

    # 成交量活躍度
    signal["volume_spike"] = volume_spike_signal(latest, trend_ticks)
    signal["volume"] = float(latest["volume"])

    # 動量Kbar
    signal["momentum_kbar"] = momentum_kbar_signal(df, len(df) - 1)

    # RSI
    rsi = float(latest["rsi"])
    signal["rsi"] = rsi
    signal["rsi_overbought"] = rsi_overbought_signal(rsi)
    signal["rsi_oversold"] = rsi_oversold_signal(rsi)

    # Bollinger Bands
    upper = float(latest["bollinger_upper"])
    lower = float(latest["bollinger_lower"])
    close = float(latest["close"])
    signal["bollinger_upper"] = upper
    signal["bollinger_lower"] = lower
    signal["bollinger_breakout"] = bollinger_breakout_signal(close, upper, lower)

    # ATR
    signal["atr"] = float(latest["atr"])

    score_total, score_breakdown, score_signals = compute_scores(latest, trend_ticks)
    signal["score_total"] = score_total
    signal["score_breakdown"] = score_breakdown
    signal["score_signals"] = score_signals

    # 綜合 summary (可給 LLM)
    signal["trend_categories"] = [
        k
        for k, v in {
            "macd_bullish": signal["macd_bullish"],
            "recent_high": signal["recent_high"],
            "sustained_highs_enough": signal["sustained_highs_enough"],
            "trend_momentum": signal["trend_momentum"],
            "volume_spike": signal["volume_spike"],
            "momentum_kbar": signal["momentum_kbar"],
            "rsi_overbought": signal["rsi_overbought"],
            "rsi_oversold": signal["rsi_oversold"],
            "bollinger_breakout": signal["bollinger_breakout"] != "none",
        }.items()
        if v
    ]
    signal["signal_status"] = "ok"
    return signal
