"""
OpenRouter API Client with caching and robust error handling
"""

import os
import json
import time
import hashlib
import requests
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
import backoff
import time as time_module

try:
    from .storage import FileSystemStorage
except ImportError:
    from storage import FileSystemStorage


@dataclass
class OpenRouterResponse:
    """Response from OpenRouter API"""

    id: str
    model: str
    content: str
    usage: Dict[str, int]
    created: int
    latency_ms: float
    raw_response: Dict[str, Any]


class OpenRouterClient:
    """Client for OpenRouter API with caching and retry logic"""

    BASE_URL = "https://openrouter.ai/api/v1"

    # Available models on OpenRouter
    AVAILABLE_MODELS = {
        # Open source models
        "mistral-7b-instruct": "mistralai/mistral-7b-instruct",
        "mixtral-8x7b": "mistralai/mixtral-8x7b-instruct",
        "llama-3-8b": "meta-llama/llama-3-8b-instruct",
        "llama-3-70b": "meta-llama/llama-3-70b-instruct",
        "codellama-70b": "meta-llama/codellama-70b-instruct",
        # OpenAI models
        "gpt-3.5-turbo": "openai/gpt-3.5-turbo",
        "gpt-4": "openai/gpt-4",
        "gpt-4-turbo": "openai/gpt-4-turbo",
        # Anthropic models
        "claude-3-haiku": "anthropic/claude-3-haiku",
        "claude-3-sonnet": "anthropic/claude-3-sonnet",
        "claude-3-opus": "anthropic/claude-3-opus",
        # Google models
        "gemini-pro": "google/gemini-pro",
        "palm-2-chat": "google/palm-2-chat-bison",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_dir: str = "./data/cache",
        cache_ttl_hours: int = 24,
        rate_limit_delay: float = 2.0,
    ):
        """
        Initialize OpenRouter client

        Args:
            api_key: OpenRouter API key (or set OPENROUTER_API_KEY env var)
            cache_dir: Directory for caching responses
            cache_ttl_hours: Cache time-to-live in hours
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY env var or pass api_key parameter"
            )

        self.storage = FileSystemStorage(cache_dir)
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/aether-framework",
                "X-Title": "AETHER Framework",
            }
        )

    def _get_cache_key(self, model: str, messages: List[Dict], **kwargs) -> str:
        """Generate cache key for request"""
        cache_data = {"model": model, "messages": messages, **kwargs}
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()

    def _is_cache_valid(self, cached_data: Dict) -> bool:
        """Check if cached data is still valid"""
        if not cached_data or "timestamp" not in cached_data:
            return False

        cache_time = datetime.fromisoformat(cached_data["timestamp"])
        return datetime.utcnow() - cache_time < self.cache_ttl

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.RequestException, requests.exceptions.Timeout),
        max_tries=5,
        max_time=120,
        on_backoff=lambda details: print(
            f"Backing off {details['wait']:.1f}s after {details['tries']} tries"
        ),
    )
    def _make_request(self, endpoint: str, data: Dict) -> Dict:
        """Make request to OpenRouter API with retry logic and rate limiting"""
        # Rate limiting: ensure minimum delay between requests
        current_time = time_module.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            print(f"Rate limiting: waiting {sleep_time:.1f}s before next request")
            time_module.sleep(sleep_time)

        self.last_request_time = time_module.time()

        try:
            response = self.session.post(
                f"{self.BASE_URL}{endpoint}", json=data, timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 429:
                # Extract retry-after header if available
                retry_after = e.response.headers.get("Retry-After", "60")
                try:
                    wait_time = float(retry_after)
                except ValueError:
                    wait_time = 60
                print(
                    f"Rate limit hit (429). Waiting {wait_time}s as requested by server"
                )
                time_module.sleep(wait_time)
                raise  # Let backoff handle the retry
            raise

    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        use_cache: bool = True,
        **kwargs,
    ) -> OpenRouterResponse:
        """
        Create chat completion using OpenRouter API

        Args:
            model: Model identifier (use AVAILABLE_MODELS keys or full model path)
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response (not implemented)
            use_cache: Whether to use cache
            **kwargs: Additional parameters for the API

        Returns:
            OpenRouterResponse object
        """
        # Resolve model name
        model_path = self.AVAILABLE_MODELS.get(model, model)

        # Check cache first
        cache_key = self._get_cache_key(
            model_path,
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        if use_cache:
            cached = self.storage.read_json(f"completions/{cache_key}.json")
            if cached and self._is_cache_valid(cached):
                print(f"Using cached response for {model}")
                return OpenRouterResponse(**cached["response"])

        # Prepare request
        request_data = {
            "model": model_path,
            "messages": messages,
            "temperature": temperature,
            **kwargs,
        }

        if max_tokens:
            request_data["max_tokens"] = max_tokens

        # Make request
        start_time = time.time()

        try:
            response_data = self._make_request("/chat/completions", request_data)
            latency_ms = (time.time() - start_time) * 1000

            # Parse response
            choice = response_data["choices"][0]
            response = OpenRouterResponse(
                id=response_data["id"],
                model=response_data["model"],
                content=choice["message"]["content"],
                usage=response_data.get("usage", {}),
                created=response_data.get("created", int(time.time())),
                latency_ms=latency_ms,
                raw_response=response_data,
            )

            # Cache response
            if use_cache:
                cache_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "response": asdict(response),
                }
                self.storage.write_json(f"completions/{cache_key}.json", cache_data)

            # Log usage
            self._log_usage(model_path, response.usage, latency_ms)

            return response

        except requests.exceptions.HTTPError as e:
            if e.response:
                try:
                    error_detail = e.response.json()
                except:
                    error_detail = e.response.text
            else:
                error_detail = str(e)
            print(f"OpenRouter API error: {error_detail}")
            raise
        except Exception as e:
            print(f"Unexpected error calling OpenRouter: {e}")
            raise

    def _log_usage(self, model: str, usage: Dict[str, int], latency_ms: float):
        """Log API usage for tracking"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "model": model,
            "usage": usage,
            "latency_ms": latency_ms,
        }

        # Append to daily log file
        log_date = datetime.utcnow().strftime("%Y-%m-%d")
        self.storage.append_json_line(f"usage/{log_date}.jsonl", log_entry)

    def get_models(self) -> List[Dict[str, Any]]:
        """Get available models from OpenRouter"""
        try:
            response = self.session.get(f"{self.BASE_URL}/models")
            response.raise_for_status()
            return response.json()["data"]
        except Exception as e:
            print(f"Error fetching models: {e}")
            return []

    def get_usage_stats(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get usage statistics from logs"""
        stats = {"total_requests": 0, "total_tokens": 0, "by_model": {}, "by_date": {}}

        # Read usage logs
        usage_files = self.storage.list_files("usage", "*.jsonl")

        for file_path in usage_files:
            file_date = file_path.stem

            # Filter by date range if specified
            if start_date and file_date < start_date:
                continue
            if end_date and file_date > end_date:
                continue

            logs = self.storage.read_json_lines(
                file_path.relative_to(self.storage.base_path)
            )
            if not logs:
                continue

            for log in logs:
                stats["total_requests"] += 1

                usage = log.get("usage", {})
                total_tokens = usage.get("total_tokens", 0)
                stats["total_tokens"] += total_tokens

                # By model stats
                model = log.get("model", "unknown")
                if model not in stats["by_model"]:
                    stats["by_model"][model] = {
                        "requests": 0,
                        "tokens": 0,
                        "avg_latency_ms": 0,
                    }

                model_stats = stats["by_model"][model]
                model_stats["requests"] += 1
                model_stats["tokens"] += total_tokens

                # Update average latency
                current_avg = model_stats["avg_latency_ms"]
                new_latency = log.get("latency_ms", 0)
                model_stats["avg_latency_ms"] = (
                    current_avg * (model_stats["requests"] - 1) + new_latency
                ) / model_stats["requests"]

                # By date stats
                if file_date not in stats["by_date"]:
                    stats["by_date"][file_date] = {"requests": 0, "tokens": 0}

                stats["by_date"][file_date]["requests"] += 1
                stats["by_date"][file_date]["tokens"] += total_tokens

        return stats

    def clear_cache(self, older_than_hours: Optional[int] = None):
        """Clear cache entries older than specified hours"""
        cache_files = self.storage.list_files("completions", "*.json")
        cleared = 0

        for file_path in cache_files:
            if older_than_hours:
                cached = self.storage.read_json(
                    file_path.relative_to(self.storage.base_path)
                )
                if cached and "timestamp" in cached:
                    cache_time = datetime.fromisoformat(cached["timestamp"])
                    age_hours = (datetime.utcnow() - cache_time).total_seconds() / 3600

                    if age_hours < older_than_hours:
                        continue

            if self.storage.delete(file_path.relative_to(self.storage.base_path)):
                cleared += 1

        print(f"Cleared {cleared} cache entries")
        return cleared


# Example usage and testing
if __name__ == "__main__":
    # Test client initialization
    client = OpenRouterClient()

    # Test simple completion
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is 2+2?"},
    ]

    try:
        # Test with a fast, cheap model
        response = client.chat_completion(
            model="mistral-7b-instruct", messages=messages, temperature=0, max_tokens=50
        )

        print(f"Response: {response.content}")
        print(f"Tokens used: {response.usage}")
        print(f"Latency: {response.latency_ms:.2f}ms")

        # Test cache hit
        response2 = client.chat_completion(
            model="mistral-7b-instruct", messages=messages, temperature=0, max_tokens=50
        )
        print(f"\nCached response: {response2.content}")

        # Get usage stats
        stats = client.get_usage_stats()
        print(f"\nUsage stats: {json.dumps(stats, indent=2)}")

    except Exception as e:
        print(f"Error testing OpenRouter client: {e}")
