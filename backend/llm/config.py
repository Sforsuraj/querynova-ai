import os
from dataclasses import dataclass

@dataclass(frozen=True)
class OpenRouterConfig:
    api_key: str
    model: str
    site_url: str
    app_name: str

    @classmethod
    def from_environment(cls):
        return cls(os.getenv('OPENROUTER_API_KEY', ''), os.getenv('OPENROUTER_MODEL', 'openrouter/free'), os.getenv('OPENROUTER_SITE_URL', ''), os.getenv('OPENROUTER_APP_NAME', 'QueryNova AI'))
