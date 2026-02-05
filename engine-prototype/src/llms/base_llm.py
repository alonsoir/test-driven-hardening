# src/llms/base_llm.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseLLM(ABC):
    """Interfaz base minimalista para todos los LLMs SOTA."""
    
    def __init__(self, name: str, api_key: str, model: str):
        self.name = name
        self.api_key = api_key
        self.model = model
        self.is_available = True
    
    @abstractmethod
    async def generate_fix(
        self,
        context: Dict[str, Any],
        max_tokens: int = 2000
    ) -> Dict[str, str]:
        """
        Genera un fix para la vulnerabilidad basado en el contexto.
        
        Returns:
            Dict con archivos modificados: {file_path: new_content}
        """
        pass
    
    @abstractmethod
    async def check_availability(self) -> bool:
        """Verifica si el LLM está disponible."""
        pass
    
    def __str__(self) -> str:
        return f"{self.name} ({self.model})"