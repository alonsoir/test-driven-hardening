# src/llms/openrouter_adapter.py
import aiohttp
import json
import os
from typing import Dict, Any, Optional
from .base_llm import BaseLLM


class OpenRouterLLM(BaseLLM):
    """Adaptador para OpenRouter API (soporta múltiples modelos SOTA)."""
    
    def __init__(self, name: str, api_key: str, model: str):
        super().__init__(name, api_key, model)
        self.base_url = "https://openrouter.ai/api/v1"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_availability(self) -> bool:
        """Verifica disponibilidad de OpenRouter."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with self.session.get(
                f"{self.base_url}/auth/key",
                headers=headers,
                timeout=10
            ) as response:
                self.is_available = response.status == 200
                return self.is_available
                
        except Exception as e:
            print(f"⚠️  {self.name} no disponible: {e}")
            self.is_available = False
            return False
        finally:
            if self.session:
                await self.session.close()
                self.session = None
    
    async def generate_fix(
        self,
        context: Dict[str, Any],
        max_tokens: int = 2000
    ) -> Dict[str, str]:
        """
        Genera fix usando OpenRouter API.
        
        Args:
            context: Contexto enriquecido de la vulnerabilidad
            
        Returns:
            Dict con archivos modificados: {file_path: new_content}
        """
        if not self.is_available:
            raise Exception(f"{self.name} no disponible")
        
        # Construir prompt estructurado
        prompt = self._build_prompt(context)
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://tdh.engine",
                "X-Title": "TDH Security Fix Engine",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": self._get_system_prompt(context)
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.1,
                "top_p": 0.9,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.1
            }
            
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter error ({response.status}): {error_text}")
                
                result = await response.json()
                
                if 'choices' not in result or len(result['choices']) == 0:
                    raise Exception(f"OpenRouter response error: {result}")
                
                content = result['choices'][0]['message']['content']
                
                # Parsear respuesta (esperamos código o JSON con fixes)
                return self._parse_llm_response(content, context)
                
        except aiohttp.ClientError as e:
            print(f"❌ Error de conexión con {self.name}: {e}")
            raise Exception(f"Connection error: {e}")
        except Exception as e:
            print(f"❌ Error con {self.name}: {e}")
            raise
        finally:
            if self.session:
                await self.session.close()
                self.session = None
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Construye prompt estructurado para el LLM."""
        vuln = context.get('vulnerability', {})
        code = context.get('code', {})
        
        prompt = f"""# SECURITY VULNERABILITY FIX REQUEST

## VULNERABILITY:
- **ID**: {vuln.get('id', 'Unknown')}
- **Severity**: {vuln.get('severity', 'Unknown')}
- **Description**: {vuln.get('description', 'No description')}
- **File**: {vuln.get('file', 'Unknown')}:{vuln.get('line', 0)}
- **Language**: {code.get('language', 'Unknown')}

## CODE CONTEXT (vulnerable section):
{code.get('vulnerable_section', 'No code provided')}

## FULL FILE (for reference):
{code.get('full_file', 'No file content')}

## RELATED FILES: {', '.join(context.get('related_files', [])[:3])}

## TASK:
Fix ONLY the security vulnerability. Do not change unrelated code.
Maintain functionality and follow existing code style.

## RESPONSE FORMAT:
Return ONLY the fixed code for the vulnerable file(s). 
If multiple files need changes, return a JSON object:
{{
  "fixed_files": {{
    "file1.c": "// fixed content...",
    "file2.h": "// fixed content..."
  }}
}}

If only one file, return just the fixed code.

## IMPORTANT:
1. Fix ONLY the security issue
2. Maintain all existing functionality
3. Follow existing code style exactly
4. Add security comments if appropriate
5. Never introduce new vulnerabilities

READY TO FIX."""
        
        return prompt
    
    def _get_system_prompt(self, context: Dict[str, Any]) -> str:
        """Prompt del sistema para guiar al LLM."""
        return """You are an expert security engineer fixing vulnerabilities.
Your task is to fix security vulnerabilities in code while:
1. Fixing ONLY the security issue
2. Maintaining all existing functionality
3. Following the existing code style exactly
4. Adding security comments if appropriate
5. Never introducing new vulnerabilities

You will be given vulnerable code and must return the fixed version.
Be precise and minimal in your changes. Only return code, no explanations."""

    def _parse_llm_response(self, response: str, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Parsea la respuesta del LLM para extraer código fijo.
        
        Intenta detectar:
        1. JSON con multiple files
        2. Código directo (single file)
        3. Markdown con código
        """
        response = response.strip()
        
        if not response:
            raise Exception("Empty response from LLM")
        
        # Intentar parsear como JSON
        try:
            # Limpiar posibles marcas de código
            clean_response = response
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            
            data = json.loads(clean_response.strip())
            
            if isinstance(data, dict):
                if 'fixed_files' in data and isinstance(data['fixed_files'], dict):
                    return data['fixed_files']
                # Si es un dict pero no tiene 'fixed_files', asumir que es el contenido
                elif len(data) == 1:
                    # Si solo tiene una clave, asumir que es el archivo
                    for key, value in data.items():
                        if isinstance(value, str):
                            return {key: value}
            
        except json.JSONDecodeError:
            pass
        
        # Si no es JSON, asumir que es el código fijo del archivo principal
        main_file = context.get('vulnerability', {}).get('file', 'unknown.c')
        
        # Limpiar markdown si existe
        if '```' in response:
            lines = response.split('\n')
            code_lines = []
            in_code_block = False
            language = None
            
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('```'):
                    if not in_code_block:
                        # Inicio de bloque de código
                        in_code_block = True
                        language = stripped[3:].strip() or None
                    else:
                        # Fin de bloque de código
                        in_code_block = False
                elif in_code_block:
                    code_lines.append(line)
                elif not stripped.startswith('```') and not stripped.startswith('#'):
                    # Líneas fuera de bloques de código (comentarios o texto)
                    if stripped and not stripped.lower().startswith(('note:', 'explanation:', 'here', 'fixed')):
                        code_lines.append(line)
            
            response = '\n'.join(code_lines).strip()
        
        return {main_file: response}
    
    def __repr__(self) -> str:
        return f"OpenRouterLLM(name='{self.name}', model='{self.model}', available={self.is_available})"