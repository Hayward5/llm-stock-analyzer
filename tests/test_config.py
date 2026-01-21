from unittest.mock import mock_open, patch

import yaml

from app.configs import config


def test_get_config_loads_yaml(monkeypatch):
    # Prepare a minimal valid config dict
    config_dict = {
        "app": {
            "host": "127.0.0.1",
            "name": "TestApp",
            "description": "desc",
            "version": "0.1",
            "port": 8000,
            "log_level": "INFO",
        },
        "llm": {
            "stock_analyzer_prompt_path": "./prompt.md",
            "temperature": 0.5,
            "max_tokens": 100,
            "retry": 2,
            "provider": "bedrock",
        },
        "shioaji": {"api_key": "key", "api_secret": "secret"},
        "bedrock": {
            "region": "us-east-1",
            "model_id": "amazon.nova-pro-v1:0",
        },
        "opencode": {
            "command": "opencode",
            "model": "google/antigravity-claude-sonnet-4-5",
            "variant": "max",
            "attach_url": "http://localhost:4096",
            "format": "default",
            "timeout_seconds": 120,
        },
    }
    yaml_str = yaml.dump(config_dict)
    # Patch open to return this YAML
    with patch("builtins.open", mock_open(read_data=yaml_str)):
        # Patch os.getenv to force config path
        monkeypatch.setenv("CONFIG_PATH", "dummy.yaml")
        cfg = config.get_config()
        assert cfg.app.name == "TestApp"
        assert cfg.llm.temperature == 0.5
        assert cfg.shioaji.api_key == "key"
    assert cfg.bedrock.region == "us-east-1"
