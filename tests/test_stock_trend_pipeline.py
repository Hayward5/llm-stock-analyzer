import pandas as pd

from app.services.analysis import stock_trend_pipeline
from app.services.analysis.stock_trend_pipeline import enrich_with_all_indicators


def test_enrich_with_all_indicators_adds_columns():
    # Minimal DataFrame with required columns for all indicators
    df = pd.DataFrame(
        {
            "open": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "high": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "low": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "close": [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5],
            "volume": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
        }
    )
    result = enrich_with_all_indicators(df.copy())
    expected_columns = [
        "5ma",
        "10ma",
        "20ma",
        "macd",
        "signal_line",
        "vma_short",
        "vma_long",
        "cci",
        "rsi",
        "bollinger_upper",
        "bollinger_lower",
        "atr",
        "kdj_k",
        "kdj_d",
        "kdj_j",
        "obv",
        "adx",
    ]
    for col in expected_columns:
        assert col in result.columns, f"Missing column: {col}"
    # Ensure original DataFrame is not modified in place
    for col in expected_columns:
        assert col not in df.columns


def test_pipeline_output_includes_scores(monkeypatch):
    df = pd.DataFrame(
        {
            "open": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "high": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "low": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "close": [1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5],
            "volume": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
        }
    )

    def fake_fetch_kline_data(stock_id: str):
        return df.copy()

    monkeypatch.setattr(stock_trend_pipeline, "fetch_kline_data", fake_fetch_kline_data)

    signal = stock_trend_pipeline.analyze_stock_trend_signal("2330.TW")
    assert "score_total" in signal
    assert "score_breakdown" in signal
    assert "score_signals" in signal
