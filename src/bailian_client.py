"""Alibaba Cloud Bailian (Qwen) LLM HTTP API Client."""

import os
import json
from typing import Dict, Any, Optional
import requests


class BailianClient:
    """Client for Alibaba Cloud Bailian LLM API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60
    ):
        """Initialize the Bailian client.
        
        Args:
            api_key: API key for authentication (reads from BAILIAN_API_KEY env if not provided)
            base_url: Base URL for API (reads from BAILIAN_BASE_URL env if not provided)
            model: Model name (reads from BAILIAN_MODEL env if not provided, defaults to qwen-plus)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.environ.get("BAILIAN_API_KEY")
        if not self.api_key:
            raise ValueError("BAILIAN_API_KEY must be set in environment or provided as parameter")
        
        self.base_url = base_url or os.environ.get(
            "BAILIAN_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.model = model or os.environ.get("BAILIAN_MODEL", "qwen-plus")
        self.timeout = timeout

    def analyze_log_window(
        self,
        system_prompt: str,
        log_content: str,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """Analyze a log window using the LLM.
        
        Args:
            system_prompt: System prompt from docs/prompt.md
            log_content: Log content to analyze
            temperature: Sampling temperature (lower = more deterministic)
            
        Returns:
            Dict containing the parsed JSON response from LLM
            
        Raises:
            requests.RequestException: If API request fails
            json.JSONDecodeError: If response is not valid JSON
            ValueError: If response doesn't match expected schema
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this log window:\n\n{log_content}"}
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }

        url = f"{self.base_url}/chat/completions"
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        result = response.json()
        
        # Extract the actual content from the response
        if "choices" not in result or len(result["choices"]) == 0:
            raise ValueError("No choices in API response")
        
        content = result["choices"][0]["message"]["content"]
        
        # Parse the JSON content
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM response is not valid JSON: {content}") from e
        
        # Validate schema
        required_fields = ["final_state", "confidence", "reason", "evidence", "next_actions"]
        for field in required_fields:
            if field not in parsed:
                raise ValueError(f"Missing required field '{field}' in response: {parsed}")
        
        # Validate final_state
        if parsed["final_state"] not in ["PLAYING", "MUTED", "UNKNOWN"]:
            raise ValueError(f"Invalid final_state: {parsed['final_state']}")
        
        # Validate confidence
        if not isinstance(parsed["confidence"], (int, float)) or not 0 <= parsed["confidence"] <= 1:
            raise ValueError(f"Invalid confidence value: {parsed['confidence']}")
        
        return parsed

    def get_raw_response(
        self,
        system_prompt: str,
        log_content: str,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """Get raw API response for debugging purposes.
        
        Args:
            system_prompt: System prompt
            log_content: Log content to analyze
            temperature: Sampling temperature
            
        Returns:
            Complete API response as dict
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this log window:\n\n{log_content}"}
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"}
        }

        url = f"{self.base_url}/chat/completions"
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        return response.json()
