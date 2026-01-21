import pandas as pd

from app.services.analysis import trend_analysis


def make_minimal_valid_df():
    return pd.DataFrame(
        {
            "macd": [0.1] * 6,
            "signal_line": [0.05] * 6,
            "5ma": [1] * 6,
            "10ma": [1] * 6,
            "20ma": [1] * 6,
            "open": [1] * 6,
            "high": [2] * 6,
            "low": [1] * 6,
            "close": [1.5] * 6,
            "vma_short": [100] * 6,
            "vma_long": [90] * 6,
            "cci": [120] * 6,
            "volume": [1000] * 6,
            "rsi": [50] * 6,
            "bollinger_upper": [11] * 6,
            "bollinger_lower": [0] * 6,
            "atr": [0.5] * 6,
        }
    )


def make_trending_df():
    return pd.DataFrame(
        {
            "macd": [0.2] * 6,
            "signal_line": [0.05] * 6,
            "5ma": [3] * 6,
            "10ma": [2] * 6,
            "20ma": [1] * 6,
            "open": [1] * 6,
            "high": [12] * 6,
            "low": [1] * 6,
            "close": [10] * 6,
            "vma_short": [200] * 6,
            "vma_long": [100] * 6,
            "cci": [120] * 6,
            "volume": [1000] * 6,
            "rsi": [55] * 6,
            "bollinger_upper": [12] * 6,
            "bollinger_lower": [0] * 6,
            "atr": [0.2] * 6,
            "adx": [25] * 6,
        }
    )


def test_generate_trend_signals_valid():
    # DataFrame with all required columns and enough rows
    df = pd.DataFrame(
        {
            "macd": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            "signal_line": [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5],
            "5ma": [1] * 10,
            "10ma": [1] * 10,
            "20ma": [1] * 10,
            "open": [1] * 10,
            "high": [2] * 10,
            "low": [1] * 10,
            "close": [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5],
            "vma_short": [100] * 10,
            "vma_long": [90] * 10,
            "cci": [120] * 10,
            "volume": [1000] * 10,
            "rsi": [50] * 10,
            "bollinger_upper": [11] * 10,
            "bollinger_lower": [0] * 10,
            "atr": [0.5] * 10,
        }
    )
    result = trend_analysis.generate_trend_signals(df, trend_lookback_period=5)
    assert result["signal_status"] == "ok"
    assert "macd_bullish" in result
    assert "trend_categories" in result
    assert isinstance(result["trend_categories"], list)


def test_generate_trend_signals_missing_columns():
    # DataFrame missing required columns
    df = pd.DataFrame({"macd": [0.1, 0.2]})
    result = trend_analysis.generate_trend_signals(df)
    assert result["signal_status"] == "invalid"
    assert "reason" in result


def test_score_breakdown_structure():
    df = make_minimal_valid_df()
    result = trend_analysis.generate_trend_signals(df, trend_lookback_period=5)
    assert "score_total" in result
    assert "score_breakdown" in result
    assert "score_signals" in result
    assert isinstance(result["score_breakdown"], dict)
    assert isinstance(result["score_signals"], dict)


def test_score_total_logic():
    df = make_trending_df()
    result = trend_analysis.generate_trend_signals(df, trend_lookback_period=5)
    assert result["score_total"] >= 4
