"""Google Cloud Secret Manager integration for the Agentic App Platform."""

import os
from functools import lru_cache

# Check if we're running in GCP (PROJECT_ID will be set)
IS_GCP_ENVIRONMENT = bool(os.environ.get("PROJECT_ID"))


def get_secret(secret_name: str) -> str | None:
    """
    Retrieve a secret from Google Cloud Secret Manager.

    Falls back to environment variables if not running in GCP
    or if the secret is not found.

    Args:
        secret_name: The full secret name (e.g., "agentic-app-platform-e2b-api-key")

    Returns:
        The secret value, or None if not found
    """
    if not IS_GCP_ENVIRONMENT:
        # Not in GCP, fall back to environment variable
        # Convert secret name to env var format: agentic-app-platform-e2b-api-key -> E2B_API_KEY
        env_var = _secret_name_to_env_var(secret_name)
        return os.environ.get(env_var)

    try:
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ["PROJECT_ID"]

        secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": secret_path})

        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Warning: Could not fetch secret '{secret_name}' from Secret Manager: {e}")
        # Fall back to environment variable
        env_var = _secret_name_to_env_var(secret_name)
        return os.environ.get(env_var)


def _secret_name_to_env_var(secret_name: str) -> str:
    """
    Convert a GCP secret name to environment variable format.

    Examples:
        agentic-app-platform-e2b-api-key -> E2B_API_KEY
        agentic-app-platform-openai-api-key -> OPENAI_API_KEY
    """
    # Remove the app prefix
    prefix = "agentic-app-platform-"
    if secret_name.startswith(prefix):
        secret_name = secret_name[len(prefix):]

    # Convert to uppercase with underscores
    return secret_name.upper().replace("-", "_")


@lru_cache(maxsize=None)
def get_cached_secret(secret_name: str) -> str | None:
    """
    Get a secret with caching to reduce API calls.

    Use this for secrets that don't change during runtime.
    """
    return get_secret(secret_name)


# Pre-defined secret names for this app
APP_PREFIX = "agentic-app-platform"

class Secrets:
    """Convenience class for accessing app secrets."""

    E2B_API_KEY = f"{APP_PREFIX}-e2b-api-key"
    OPENAI_API_KEY = f"{APP_PREFIX}-openai-api-key"
    ANTHROPIC_API_KEY = f"{APP_PREFIX}-anthropic-api-key"
    GROQ_API_KEY = f"{APP_PREFIX}-groq-api-key"
    TOGETHER_API_KEY = f"{APP_PREFIX}-together-api-key"
    FIREWORKS_API_KEY = f"{APP_PREFIX}-fireworks-api-key"
    XAI_API_KEY = f"{APP_PREFIX}-xai-api-key"
    DEEPSEEK_API_KEY = f"{APP_PREFIX}-deepseek-api-key"


def load_secrets_to_env():
    """
    Load all secrets into environment variables.

    Call this at app startup to make secrets available via os.environ.
    """
    secret_mappings = {
        Secrets.E2B_API_KEY: "E2B_API_KEY",
        Secrets.OPENAI_API_KEY: "OPENAI_API_KEY",
        Secrets.ANTHROPIC_API_KEY: "ANTHROPIC_API_KEY",
        Secrets.GROQ_API_KEY: "GROQ_API_KEY",
        Secrets.TOGETHER_API_KEY: "TOGETHER_API_KEY",
        Secrets.FIREWORKS_API_KEY: "FIREWORKS_API_KEY",
        Secrets.XAI_API_KEY: "XAI_API_KEY",
        Secrets.DEEPSEEK_API_KEY: "DEEPSEEK_API_KEY",
    }

    for secret_name, env_var in secret_mappings.items():
        # Only fetch from Secret Manager if not already set in environment
        if not os.environ.get(env_var):
            value = get_secret(secret_name)
            if value:
                os.environ[env_var] = value
                print(f"Loaded {env_var} from Secret Manager")
