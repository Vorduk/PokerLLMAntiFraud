from typing import Dict, List, Optional
from .base_model import BaseModel
from .cloudflare_models import CloudflareModels


class ModelFactory:
    """Creates model instances based on configuration."""

    def __init__(self, config_loader):
        self.config_loader = config_loader
        self._config = config_loader.load()
        self._model_registry: Dict[str, dict] = {}
        self._build_registry()

    def _build_registry(self):
        """Build an internal registry of available models."""
        providers = self._config.get("providers", {})

        for provider_id, provider_data in providers.items():
            # Берём base_url провайдера, если есть
            provider_base_url = provider_data.get("base_url", "")
            for account in provider_data.get("accounts", []):
                account_id = account["account_id"]
                account_name = account["name"]

                api_keys = {}
                for key_data in account.get("api_keys", []):
                    api_keys[key_data["key_id"]] = key_data["api_key"]

                for model in account.get("models", []):
                    model_id = model["model_id"]

                    compatible_keys = model.get("compatible_keys", [])
                    if compatible_keys:
                        key_id = compatible_keys[0]
                        api_key = api_keys.get(key_id)
                    else:
                        api_key = list(api_keys.values())[0] if api_keys else None

                    if api_key:
                        self._model_registry[model_id] = {
                            "provider": provider_id,
                            "model_name": model.get("display_name", model_id),
                            "account_id": account_id,
                            "account_name": account_name,
                            "api_key": api_key,
                            "max_tokens": model.get("max_tokens", 4096),
                            "base_url": provider_base_url
                        }

    def create_model(self, model_id: str) -> Optional[BaseModel]:
        """Create a model instance by its ID."""
        if model_id not in self._model_registry:
            print(f"[WARNING] Model {model_id} not found in configuration")
            return None

        model_info = self._model_registry[model_id]
        provider = model_info["provider"]

        if provider == "cloudflare":
            return CloudflareModels(
                model_id=model_id,
                model_name=model_info["model_name"],
                account_id=model_info["account_id"],
                api_key=model_info["api_key"],
                base_url=model_info["base_url"],
                max_tokens=model_info["max_tokens"]
            )
        else:
            print(f"[WARNING] Provider {provider} not supported yet")
            return None