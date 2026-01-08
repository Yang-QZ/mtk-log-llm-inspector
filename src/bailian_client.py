"""Alibaba Cloud Bailian (Qwen) LLM HTTP API Client.
阿里云百炼（通义千问）大语言模型HTTP API客户端。
"""

import os
import json
from typing import Dict, Any, Optional
import requests


class BailianClient:
    """Client for Alibaba Cloud Bailian LLM API.
    阿里云百炼大模型API客户端。
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60
    ):
        """Initialize the Bailian client.
        初始化百炼客户端。
        
        Args:
            api_key: API key for authentication (reads from BAILIAN_API_KEY env if not provided)
                    用于身份验证的API密钥（如果未提供，则从BAILIAN_API_KEY环境变量读取）
            base_url: Base URL for API (reads from BAILIAN_BASE_URL env if not provided)
                     API的基础URL（如果未提供，则从BAILIAN_BASE_URL环境变量读取）
            model: Model name (reads from BAILIAN_MODEL env if not provided, defaults to qwen-plus)
                  模型名称（如果未提供，则从BAILIAN_MODEL环境变量读取，默认为qwen-plus）
            timeout: Request timeout in seconds (请求超时时间，单位秒)
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
        使用大语言模型分析日志窗口。
        
        Args:
            system_prompt: System prompt from docs/prompt.md
                          系统提示词，来自docs/prompt.md
            log_content: Log content to analyze
                        要分析的日志内容
            temperature: Sampling temperature (lower = more deterministic)
                        采样温度（越低越确定性）
            
        Returns:
            Dict containing the parsed JSON response from LLM
            包含大模型解析后的JSON响应的字典
            
        Raises:
            requests.RequestException: If API request fails (如果API请求失败)
            json.JSONDecodeError: If response is not valid JSON (如果响应不是有效的JSON)
            ValueError: If response doesn't match expected schema (如果响应不符合预期的模式)
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
        # 从响应中提取实际内容
        if "choices" not in result or len(result["choices"]) == 0:
            raise ValueError("No choices in API response")
        
        content = result["choices"][0]["message"]["content"]
        
        # Parse the JSON content (解析JSON内容)
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM response is not valid JSON: {content}") from e
        
        # Validate schema (验证模式)
        required_fields = ["final_state", "confidence", "reason", "evidence", "next_actions"]
        for field in required_fields:
            if field not in parsed:
                raise ValueError(f"Missing required field '{field}' in response: {parsed}")
        
        # Validate final_state (验证final_state字段)
        if parsed["final_state"] not in ["PLAYING", "MUTED", "UNKNOWN"]:
            raise ValueError(f"Invalid final_state: {parsed['final_state']}")
        
        # Validate confidence (验证confidence字段)
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
        获取原始API响应用于调试。
        
        Args:
            system_prompt: System prompt (系统提示词)
            log_content: Log content to analyze (要分析的日志内容)
            temperature: Sampling temperature (采样温度)
            
        Returns:
            Complete API response as dict (完整的API响应字典)
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
