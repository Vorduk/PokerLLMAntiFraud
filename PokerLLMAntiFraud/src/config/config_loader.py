from pathlib import Path
from dotenv import load_dotenv
import re
import os
import yaml
from typing import Any, Optional

class ConfigLoader:
    """ Loads providers.yaml and substitutes ${VARIABLES} from the .env file

    Use:
        config_loader = ConfigLoader() or ConfigLoader(providers_filename, env_filename)
        providers = config_loader.load()
        providers is Python Dictionary
    """

    def __init__(self, providers_filename: str = "providers.yaml", env_filename: str = ".env"):
        """ Searches for files in the config/ folder two levels up src/config/config_loader.py -> ../../config/

        Args:
            providers_filename: name of YAML file with models providers
            env_filename: name of .env with api keys etc...
        """

        # Folder with this script: src/config/
        current_dir = Path(__file__).parent

        # src/config/ -> src/ -> project root
        project_root = current_dir.parent.parent

        # Folder with configs
        self.config_dir = project_root / "config"

        # File paths
        self.providers_path = self.config_dir / providers_filename
        self.env_path = self.config_dir / env_filename

        # cache
        self._config = None

        self._load_env()


    def _load_env(self):
        """ Loads the .env file, the variables go to os.environ

        """

        if self.env_path.exists():
            load_dotenv(self.env_path)
            print(f"[INFO]: Loaded .env from {self.env_path}")
        else:
            print(f"[WARNING]: .env not found {self.env_path}")

    def _resolve_env_var(self, value: str) -> str:
        """ Substitutes the value from the environment variable

        "${CLOUDFLARE_KEY_1}" -> "sk-real-key"
        """

        # Check for non string values from yaml
        if not isinstance(value, str):
            return value

        # ${VARIABLE_NAME}
        pattern = r'\$\{([^}]+)\}'

        def replace_match(match):
            var_name = match.group(1) #remove brackets
            env_value = os.environ.get(var_name)

            if env_value is not None:
                return env_value # Env var found, returns it
            else:
                print(f"[WARNING]: Environment variable {var_name} not found")
                return match.group(0)  # Return match as is

        return re.sub(pattern, replace_match, value)

    def _resolve_all_env_vars(self, data: Any) -> Any:
        """ Recursively traverses the structure and substitutes variables

        Works for: string: "${VAR}" -> value; lists, dicts.
        """
        if isinstance(data, str):
            return self._resolve_env_var(data)
        elif isinstance(data, list):
            return [self._resolve_all_env_vars(item) for item in data]
        elif isinstance(data, dict):
            return {key: self._resolve_all_env_vars(value) for key, value in data.items()}
        else:
            return data # return values as is.

    def load(self)-> dict:
        """ Loads and processes providers.yaml

        Returns:
            dict: {
                'cloudflare': {
                    'name': 'Cloudflare AI',
                    'base_url': 'https://api.cloudflare.com/client/v4',
                    'accounts': [
                        {
                            'account_id': 'реальный-id',
                            'api_keys': [
                                {
                                    'key_id': 'key-1',
                                    'api_key': 'sk-реальный-ключ',
                                    ...
                                }
                            ],
                            'models': [...]
                        }
                    ]
                }
            }
        """
        # Check if cache exist
        if self._config is not None:
            return self._config

        # Check if file exist
        if not self.providers_path.exists():
            raise FileNotFoundError(
                f"[WARNING]: Providers config file not found {self.providers_path}\n"
            )

        # Read YAML
        with open(self.providers_path, 'r', encoding='utf-8') as f:
            raw_data = yaml.safe_load(f)

        # Substitute env vars
        resolved_data = self._resolve_all_env_vars(raw_data)

        print(f"[INFO]: Loaded configuration from {self.providers_path}")

        # Update cache
        self._config = resolved_data

        return resolved_data

    def get_provider(self, provider_id: str) -> Optional[dict]:
        """ Get particular provider by ID

        Args:
            provider_id: for example 'cloudflare'

        Returns:
            dict with settings or None
        """
        data = self.load()
        return data.get('providers', {}).get(provider_id)

    def get_provider_names(self) -> list:
        """Get list of all available provider IDs

        Returns:
            list: ['cloudflare', 'openai', ...]
        """
        data = self.load()
        return list(data.get('providers', {}).keys())

    def reload(self) -> dict:
        """Force reload configuration (clears cache)

        """
        self._config = None
        return self.load()
