"""
Configuration management for the agent, using Pydantic models and YAML loading.
"""

import os
from functools import lru_cache

import yaml
from typing import Optional

from pydantic import BaseModel, StrictFloat, StrictInt, StrictStr
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    host: StrictStr
    name: StrictStr
    description: StrictStr
    version: StrictStr
    port: StrictInt
    log_level: StrictStr


class LLMConfig(BaseModel):
    stock_analyzer_prompt_path: StrictStr
    temperature: StrictFloat
    max_tokens: StrictInt
    retry: StrictInt
    provider: StrictStr


class ShioajiConfig(BaseModel):
    api_key: str
    api_secret: str


class BedrockConfig(BaseModel):
    region: StrictStr
    model_id: StrictStr


class OpenCodeConfig(BaseModel):
    command: StrictStr
    model: StrictStr
    variant: Optional[StrictStr] = None
    attach_url: Optional[StrictStr] = None
    format: StrictStr = "default"
    timeout_seconds: StrictInt = 120


class Config(BaseSettings):
    app: AppConfig
    llm: LLMConfig
    shioaji: ShioajiConfig
    bedrock: BedrockConfig
    opencode: Optional[OpenCodeConfig] = None


@lru_cache()
def get_config() -> Config:
    config_path = os.getenv("CONFIG_PATH", "app/configs/config.yaml")

    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    return Config(**raw_config)
