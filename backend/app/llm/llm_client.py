import logging
import requests
from typing import Dict, Any
from app.config import LLM_PROVIDER, LLM_API_KEY, LLM_MODEL

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Isolated External LLM Client Integration for Real LLM Providers (Groq / OpenAI).

    IMPORTANT SECURITY GUARANTEE:
    This class MUST ONLY be invoked when the Policy Engine returns decision = ALLOW.
    It connects exclusively to real external LLM provider endpoints.
    No mock or local fallback is allowed.
    """
    def __init__(self):
        self.provider = LLM_PROVIDER
        self.api_key = LLM_API_KEY
        self.model = LLM_MODEL

    def generate_response(self, prompt: str) -> Dict[str, Any]:
        """Send the verified safe prompt to the real configured external LLM API."""
        logger.info(f"[LLM_CLIENT_CALL] Invoking Real External LLM API (Provider: {self.provider}, Model: {self.model})")

        if not self.api_key or not self.api_key.strip():
            logger.error("[LLM_CLIENT_ERROR] LLM_API_KEY is not configured in backend/.env")
            return {
                "success": False,
                "text": "LLM Configuration Error: External LLM API key (LLM_API_KEY) is missing. Please add your Groq API key to backend/.env",
                "provider": self.provider,
                "model": self.model,
                "error_code": "MISSING_API_KEY"
            }

        if self.provider == "groq":
            return self._call_groq_api(prompt)
        elif self.provider == "openai":
            return self._call_openai_api(prompt)
        else:
            logger.error(f"[LLM_CLIENT_ERROR] Unsupported LLM provider requested: '{self.provider}'")
            return {
                "success": False,
                "text": f"LLM Configuration Error: Unsupported provider '{self.provider}'. Configured primary provider is 'groq'.",
                "provider": self.provider,
                "model": self.model,
                "error_code": "UNSUPPORTED_PROVIDER"
            }

    def _call_groq_api(self, prompt: str) -> Dict[str, Any]:
        """Calls Groq Cloud Chat Completion API."""
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            model_to_use = self.model or "groq/compound-mini"
            payload = {
                "model": model_to_use,
                "messages": [
                    {"role": "system", "content": "You are a helpful enterprise AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            logger.info(f"[GROQ_API_REQUEST] Sending request to {url} using model {model_to_use}")
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "text": text,
                    "provider": "Groq Cloud",
                    "model": model_to_use
                }
            elif response.status_code == 404 and model_to_use != "groq/compound-mini":
                logger.warning(f"[GROQ_API_ERROR] Requested model '{model_to_use}' not found for Groq. No fallback switching is allowed.")
                error_msg = f"Groq API Error (HTTP {response.status_code}): {response.text}"
                logger.error(f"[GROQ_API_ERROR] {error_msg}")
                return {
                    "success": False,
                    "text": "External AI service is temporarily unavailable.",
                    "provider": "Groq Cloud",
                    "model": model_to_use,
                    "error_code": f"HTTP_{response.status_code}"
                }
            else:
                error_msg = f"Groq API Error (HTTP {response.status_code}): {response.text}"
                logger.error(f"[GROQ_API_ERROR] {error_msg}")
                return {
                    "success": False,
                    "text": "External AI service is temporarily unavailable.",
                    "provider": "Groq Cloud",
                    "model": model_to_use,
                    "error_code": f"HTTP_{response.status_code}"
                }
        except requests.exceptions.RequestException as err:
            logger.error(f"[GROQ_API_EXCEPTION] Exception calling Groq API: {err}")
            return {
                "success": False,
                "text": "External AI service is temporarily unavailable.",
                "provider": "Groq Cloud",
                "model": self.model,
                "error_code": "CONNECTION_ERROR"
            }
        except Exception as err:
            logger.error(f"[GROQ_API_EXCEPTION] Unexpected exception: {err}")
            return {
                "success": False,
                "text": "External AI service is temporarily unavailable.",
                "provider": "Groq Cloud",
                "model": self.model,
                "error_code": "CONNECTION_ERROR"
            }

    def _call_openai_api(self, prompt: str) -> Dict[str, Any]:
        """Calls OpenAI Chat Completion API."""
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            model_to_use = self.model or "gpt-4o-mini"
            payload = {
                "model": model_to_use,
                "messages": [
                    {"role": "system", "content": "You are a helpful enterprise AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            logger.info(f"[OPENAI_API_REQUEST] Sending request to {url} using model {model_to_use}")
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "text": text,
                    "provider": "OpenAI",
                    "model": model_to_use
                }
            else:
                error_msg = f"OpenAI API Error (HTTP {response.status_code}): {response.text}"
                logger.error(f"[OPENAI_API_ERROR] {error_msg}")
                return {
                    "success": False,
                    "text": "External AI service is temporarily unavailable.",
                    "provider": "OpenAI",
                    "model": model_to_use,
                    "error_code": f"HTTP_{response.status_code}"
                }
        except requests.exceptions.RequestException as err:
            logger.error(f"[OPENAI_API_EXCEPTION] Exception calling OpenAI API: {err}")
            return {
                "success": False,
                "text": "External AI service is temporarily unavailable.",
                "provider": "OpenAI",
                "model": self.model,
                "error_code": "CONNECTION_ERROR"
            }
        except Exception as err:
            logger.error(f"[OPENAI_API_EXCEPTION] Unexpected exception: {err}")
            return {
                "success": False,
                "text": "External AI service is temporarily unavailable.",
                "provider": "OpenAI",
                "model": self.model,
                "error_code": "CONNECTION_ERROR"
            }
