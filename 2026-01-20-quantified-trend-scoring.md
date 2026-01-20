# Quantified Trend Scoring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a quantified scoring layer for trend analysis so the LLM consumes structured scores instead of raw indicator noise.

**Architecture:** Keep the existing data pipeline and indicator calculations, but extend trend signal generation to output score_total, score_breakdown, and score_signals. The LLM prompt will emphasize total score as primary decision input, improving interpretability for swing/mid-term trading.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, Pandas, LangChain (Azure OpenAI).

### Task 1: Add scoring model helpers

**Files:**
- Modify: `app/services/analysis/trend_analysis.py`

**Step 1: Write the failing test**

```python
def test_score_breakdown_structure():
    df = make_minimal_valid_df()
    result = trend_analysis.generate_trend_signals(df, trend_lookback_period=5)
    assert "score_total" in result
    assert "score_breakdown" in result
    assert "score_signals" in result
    assert isinstance(result["score_breakdown"], dict)
    assert isinstance(result["score_signals"], dict)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_trend_analysis.py::test_score_breakdown_structure -v`
Expected: FAIL with missing keys

**Step 3: Write minimal implementation**

```python
def build_score_breakdown(latest, trend_ticks) -> dict:
    # Example initial mapping: expand later
    return {
        "trend": 0,
        "momentum": 0,
        "volume": 0,
        "risk": 0,
    }

def build_score_signals(latest, trend_ticks) -> dict:
    return {
        "ma_alignment": False,
        "macd_bullish": False,
        "adx_strong": False,
        "rsi_healthy": False,
        "volume_support": False,
        "atr_high_risk": False,
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_trend_analysis.py::test_score_breakdown_structure -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_trend_analysis.py app/services/analysis/trend_analysis.py
git commit -m "feat: add trend scoring scaffolding"
```

### Task 2: Implement scoring rules (swing/mid-term tuned)

**Files:**
- Modify: `app/services/analysis/trend_analysis.py`

**Step 1: Write the failing test**

```python
def test_score_total_logic():
    df = make_trending_df()
    result = trend_analysis.generate_trend_signals(df, trend_lookback_period=5)
    assert result["score_total"] >= 4
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_trend_analysis.py::test_score_total_logic -v`
Expected: FAIL (score_total missing or too low)

**Step 3: Write minimal implementation**

```python
def compute_scores(latest, trend_ticks) -> tuple[int, dict, dict]:
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_trend_analysis.py::test_score_total_logic -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_trend_analysis.py app/services/analysis/trend_analysis.py
git commit -m "feat: implement quantified trend scores"
```

### Task 3: Expose scores in pipeline output

**Files:**
- Modify: `app/services/analysis/stock_trend_pipeline.py`

**Step 1: Write the failing test**

```python
def test_pipeline_output_includes_scores():
    signal = stock_trend_pipeline.analyze_stock_trend_signal("2330.TW")
    # In tests, mock data and confirm keys
    assert "score_total" in signal
    assert "score_breakdown" in signal
    assert "score_signals" in signal
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_stock_trend_pipeline.py::test_pipeline_output_includes_scores -v`
Expected: FAIL with missing keys

**Step 3: Write minimal implementation**

```python
signal = generate_trend_signals(enriched_df)
# signal already contains score_total, score_breakdown, score_signals
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_stock_trend_pipeline.py::test_pipeline_output_includes_scores -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_stock_trend_pipeline.py app/services/analysis/stock_trend_pipeline.py
git commit -m "feat: expose scoring in pipeline output"
```

### Task 4: Update prompt to emphasize score_total

**Files:**
- Modify: `app/prompts/stock_analyzer_prompt.md`

**Step 1: Write the failing test**

```python
def test_prompt_mentions_score_total():
    prompt = load_prompt_contents()
    assert "score_total" in prompt
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_prompt.py::test_prompt_mentions_score_total -v`
Expected: FAIL (file content missing)

**Step 3: Write minimal implementation**

```markdown
- Use score_total as the primary decision input.
- Use score_breakdown for brief justification.
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_prompt.py::test_prompt_mentions_score_total -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/prompts/stock_analyzer_prompt.md tests/test_prompt.py
git commit -m "docs: emphasize scoring in LLM prompt"
```
