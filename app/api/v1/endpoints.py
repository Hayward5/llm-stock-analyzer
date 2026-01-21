# FastAPI API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.internal.llm.chain import (
    build_stock_analysis_chain_with_retry,
    get_analysis_prompt_template,
    get_llm_client,
)
from app.utils.logger import log

router = APIRouter()


class StockAnalysisRequest(BaseModel):
    stock_id: str


class StockAnalysisResponse(BaseModel):
    stock_id: str
    suggestion: str
    reason: str


@router.post("/stock/llm-report", response_model=StockAnalysisResponse)
async def get_stock_llm_report(request: StockAnalysisRequest):
    """
    Generate a stock analysis report using LLM based on technical indicators.
    Returns a clear, actionable trading suggestion and rationale.
    """
    log.debug("[Breakpoint] /stock/llm-report request: stock_id={}", request.stock_id)
    llm_client = get_llm_client()
    prompt_template = get_analysis_prompt_template()
    chain = build_stock_analysis_chain_with_retry(llm_client, prompt_template)
    try:
        llm_result = await chain.ainvoke(request.stock_id)
        log.debug("[Breakpoint] LLM result keys: {}", list(llm_result.keys()))
        # Ensure the response is in the expected JSON format
        return StockAnalysisResponse(
            stock_id=llm_result.get("stock_id", request.stock_id),
            suggestion=llm_result.get("suggestion", ""),
            reason=llm_result.get("reason", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM analysis failed: {str(e)}")
