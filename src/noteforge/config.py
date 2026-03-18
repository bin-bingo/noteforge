"""Configuration management for kb-tool."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Self

import yaml


@dataclass(frozen=True, slots=True)
class LLMConfig:
    """LLM configuration."""

    provider: Literal["api", "local"] = "api"
    api_provider: str = "openrouter"
    api_model: str = "anthropic/claude-sonnet-4"
    api_key: str = field(
        default_factory=lambda: os.environ.get("OPENROUTER_API_KEY", "")
    )
    timeout: float = 30.0


@dataclass(frozen=True, slots=True)
class OutputConfig:
    """Output configuration."""

    dir: Path = field(default_factory=lambda: Path.home() / ".kb" / "vault")
    mode: Literal["fidelity", "concise", "raw"] = "fidelity"


@dataclass(frozen=True, slots=True)
class Config:
    """Application configuration."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @classmethod
    def load(cls, path: Path | None = None) -> Self:
        """Load configuration from file.

        Args:
            path: Path to config file. Defaults to ~/.kb/config.yaml.

        Returns:
            Config instance with values from file or defaults.
        """
        config_path = path or Path.home() / ".kb" / "config.yaml"

        if not config_path.exists():
            return cls()

        try:
            data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except Exception:
            return cls()

        llm_data = data.get("llm", {})
        output_data = data.get("output", {})

        llm_config = LLMConfig(
            provider=llm_data.get("provider", "api"),
            api_provider=llm_data.get("api_provider", "openrouter"),
            api_model=llm_data.get("api_model", "anthropic/claude-sonnet-4"),
            api_key=llm_data.get("api_key", os.environ.get("OPENROUTER_API_KEY", "")),
            timeout=llm_data.get("timeout", 30.0),
        )

        output_dir = output_data.get("dir")
        output_config = OutputConfig(
            dir=Path(output_dir).expanduser()
            if output_dir
            else Path.home() / ".kb" / "vault",
            mode=output_data.get("mode", "fidelity"),
        )

        return cls(llm=llm_config, output=output_config)


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance.

    Returns:
        Config instance, loading from file on first call.
    """
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def reset_config() -> None:
    """Reset the global config (useful for testing)."""
    global _config
    _config = None
