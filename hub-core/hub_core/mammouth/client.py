"""
MammouthAI API Client — Mistral-based models with rate limit fallback
Supports: mistral-small-3.1, mistral-medium, mistral-large
"""

from typing import Optional, Dict, Any

import requests
from loguru import logger

from hub_core.config import MAMMOUTH_API_KEY


class MammouthAIClient:
    """Lightweight MammouthAI client for Mistral models."""

    BASE_URL = "https://api.mammouth.ai"
    DEFAULT_MODEL = "mistral-small-3.2-24b-instruct"  # Default when Claude falls back

    def __init__(self, api_key: Optional[str] = None, model: str = None):
        """
        Initialize MammouthAI client.

        Args:
            api_key: MammouthAI API key (defaults to MAMMOUTH_API_KEY env var)
            model: Model to use (defaults to mistral-small-3.1)
        """
        self.api_key = api_key or MAMMOUTH_API_KEY
        self.model = model or self.DEFAULT_MODEL

        if not self.api_key:
            raise ValueError(
                "MAMMOUTH_API_KEY not configured in .env or passed as argument"
            )

        logger.info(f"🦣 MammouthAI client initialized: model={self.model}")

    def complete(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system: Optional[str] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Get completion from MammouthAI.

        Args:
            prompt: User message/prompt
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)
            system: System prompt (optional)
            timeout: Request timeout in seconds

        Returns:
            Response dict with 'text' key containing completion
        """

        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        try:
            response = requests.post(
                f"{self.BASE_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
                timeout=timeout,
            )

            if response.status_code == 200:
                data = response.json()
                text = (
                    data.get("choices", [{}])[0].get("message", {}).get("content", "")
                )

                logger.info(f"✅ MammouthAI ({self.model}): {len(text)} chars")

                return {
                    "success": True,
                    "text": text,
                    "model": self.model,
                    "usage": data.get("usage", {}),
                }

            elif response.status_code == 429:
                logger.error("MammouthAI rate limit reached (429)")
                return {
                    "success": False,
                    "error": "MammouthAI rate limit reached",
                    "status": 429,
                }

            else:
                logger.error(
                    f"MammouthAI error {response.status_code}: {response.text}"
                )
                return {
                    "success": False,
                    "error": response.text,
                    "status": response.status_code,
                }

        except requests.Timeout:
            logger.error(f"MammouthAI timeout (>{timeout}s)")
            return {
                "success": False,
                "error": "MammouthAI request timeout",
                "timeout": timeout,
            }

        except Exception as e:
            logger.error(f"MammouthAI error: {e}")
            return {"success": False, "error": str(e)}

    def test_connection(self) -> bool:
        """Test MammouthAI API connectivity."""
        try:
            result = self.complete(
                prompt="Hello, are you working?", max_tokens=10, timeout=5
            )

            if result.get("success"):
                logger.info("✅ MammouthAI connection test PASSED")
                return True
            else:
                logger.error(
                    f"❌ MammouthAI connection test FAILED: {result.get('error')}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ MammouthAI connection test ERROR: {e}")
            return False


def get_mammouth_client() -> Optional[MammouthAIClient]:
    """Factory function to get MammouthAI client (safe if key missing)."""
    try:
        return MammouthAIClient()
    except ValueError as e:
        logger.warning(f"MammouthAI client unavailable: {e}")
        return None
