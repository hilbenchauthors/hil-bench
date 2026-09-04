import os
from functools import wraps

import litellm
from dotenv import load_dotenv

load_dotenv()


def _require_litellm_user(kwargs):
    if "user" not in kwargs:
        user = os.getenv("LITELLM_USER", "").strip()
        if not user:
            raise RuntimeError(
                "LITELLM_USER is required so every LiteLLM call is attributed"
            )
        kwargs["user"] = user


@wraps(litellm.acompletion)
async def litellm_acompletion(*args, **kwargs):
    """
    Wrapper for litellm.acompletion that automatically passes API key and base URL
    from environment variables (LITELLM_API_KEY and LITELLM_BASE_URL).

    All arguments are passed through to litellm.acompletion. If api_key or base_url
    are explicitly provided in kwargs, they will override the environment variables.
    """
    # Get API key and base URL from environment, but allow override via kwargs
    if "api_key" not in kwargs:
        kwargs["api_key"] = os.environ["LITELLM_API_KEY"]
    if "base_url" not in kwargs:
        kwargs["base_url"] = os.environ["LITELLM_BASE_URL"]
    _require_litellm_user(kwargs)

    return await litellm.acompletion(*args, **kwargs)


@wraps(litellm.completion)
def litellm_completion(*args, **kwargs):
    """
    Wrapper for litellm.completion that automatically passes API key and base URL
    from environment variables (LITELLM_API_KEY and LITELLM_BASE_URL).

    All arguments are passed through to litellm.completion. If api_key or base_url
    are explicitly provided in kwargs, they will override the environment variables.
    """
    if "api_key" not in kwargs:
        kwargs["api_key"] = os.environ["LITELLM_API_KEY"]
    if "base_url" not in kwargs:
        kwargs["base_url"] = os.environ["LITELLM_BASE_URL"]
    _require_litellm_user(kwargs)

    return litellm.completion(*args, **kwargs)
