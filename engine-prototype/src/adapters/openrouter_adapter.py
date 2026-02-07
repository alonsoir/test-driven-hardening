# src/adapters/openrouter_adapter.py
"""
Adapter para OpenRouter API - Versión simplificada para pruebas
"""

import os
import json
import aiohttp
from typing import Dict, Any, Optional, List


class OpenRouterAdapter:
    """Adapter simplificado para OpenRouter API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def generate_completion(self, model: str, prompt: str, 
                                 temperature: float = 0.1, 
                                 max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Genera una completación usando OpenRouter.
        
        Args:
            model: Nombre del modelo (ej: "anthropic/claude-3.5-sonnet")
            prompt: Prompt para enviar
            temperature: Temperatura para generación
            max_tokens: Máximo de tokens en respuesta
            
        Returns:
            Respuesta del modelo
        """
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY no configurada")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://tdh-engine.github.io",
            "X-Title": "TDH Engine"
        }
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "content": result["choices"][0]["message"]["content"],
                        "model": result["model"],
                        "usage": result.get("usage", {})
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "status": response.status
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """Lista modelos disponibles en OpenRouter."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.get(f"{self.base_url}/models") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                return []
        except:
            # Si falla, devolver lista de modelos conocidos
            return [
                {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet"},
                {"id": "openai/gpt-4-turbo", "name": "GPT-4 Turbo"},
                {"id": "deepseek/deepseek-coder", "name": "DeepSeek Coder"},
                {"id": "google/gemini-pro", "name": "Gemini Pro"},
                {"id": "meta-llama/llama-3.1-70b", "name": "Llama 3.1 70B"},
                {"id": "meta-llama/codellama-70b", "name": "CodeLlama 70B"}
            ]