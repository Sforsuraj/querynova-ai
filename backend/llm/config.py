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
        return cls(
            api_key=os.getenv('OPENROUTER_API_KEY', '').strip(),
            model=os.getenv('OPENROUTER_MODEL', 'openrouter/free').strip() or 'openrouter/free',
            site_url=os.getenv('OPENROUTER_SITE_URL', '').strip(),
            app_name=os.getenv('OPENROUTER_APP_NAME', 'QueryNova').strip() or 'QueryNova',
        )

