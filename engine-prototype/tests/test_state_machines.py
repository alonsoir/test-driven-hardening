# tests/test_state_machines.py
"""
Pruebas integradas para las máquinas de estados del TDH Engine.
"""

import asyncio
import json
from pathlib import Path
from src.core.llm_state_machine import LLMStateMachine, LLMState
from src.core.llm_council_enhanced import EnhancedLLMCouncil
from src.core.git_worktree_manager import GitWorktreeManager


async def test_state_machine_workflow():
    """Prueba el workflow completo de una máquina de estados."""
    print("🧪 Probando máquina de estados...")
    
    # Vulnerabilidad de ejemplo
    mock_vulnerability = {
        'rule_id': 'CWE-78',
        'severity': 'CRITICAL',
        'confidence': 'HIGH',
        'message': 'Possible command injection',
        'file': 'src/main.c',
        'line': 42,
        'cwe': 'CWE-78',
        'owasp': 'A1:2017-Injection',
        'more_info': 'https://cwe.mitre.org/data/definitions/78.html',
        'code_snippet': '''
void vulnerable_function(char *user_input) {
    char command[100];
    sprintf(command, "echo %s", user_input);
    system(command);  // VULNERABLE: command injection
}
'''
    }
    
    # Mock LLM para pruebas
    class MockLLM:
        def __init__(self, name):
            self.name = name
            
        async def generate_response(self, prompt, temperature=0.1, max_tokens=2000):
            print(f"🤖 {self.name} recibió prompt ({len(prompt)} chars)")
            
            # Respuesta mock basada en el prompt
            if "ANÁLISIS DE VULNERABILIDAD" in prompt:
                return json.dumps({
                    "analysis": {
                        "what": "Función que ejecuta comandos del sistema con input del usuario",
                        "why_vulnerable": "Command injection via sprintf + system",
                        "exploitation_scenario": "Usuario puede inyectar '; rm -rf /' u otros comandos",
                        "potential_impact": "alto",
                        "impact_justification": "Ejecución arbitraria de comandos como el usuario del proceso",
                        "possible_solutions": [
                            "Usar execve con argumentos separados",
                            "Validar y sanitizar input del usuario",
                            "Usar funciones seguras como snprintf"
                        ]
                    },
                    "confidence": "alta",
                    "notes": "Vulnerabilidad clásica de command injection"
                }, ensure_ascii=False)
            
            elif "DISEÑO DE TEST CONCEPTUAL" in prompt:
                return json.dumps({
                    "test_design": {
                        "test_concept": "Test de command injection via user input",
                        "test_type": "security",
                        "prerequisites": ["compilador C", "entorno Unix"],
                        "steps_to_reproduce": [
                            "Compilar código vulnerable",
                            "Ejecutar con input: 'test; ls -la'",
                            "Verificar que se ejecuta 'ls -la'"
                        ],
                        "expected_behavior_without_fix": "Se ejecuta 'ls -la' mostrando directorio",
                        "expected_behavior_with_fix": "Error o input sanitizado",
                        "verification_method": "Capturar salida de sistema",
                        "success_criteria": "No ejecución de comandos arbitrarios",
                        "tools_needed": ["gcc", "valgrind", "strace"],
                        "estimated_time": "5"
                    },
                    "notes": "Test simple de proof-of-concept"
                }, ensure_ascii=False)
            
            elif "DISEÑO DE FIX" in prompt:
                return '''
void safe_function(char *user_input) {
    // Validar input - solo caracteres alfanuméricos
    for (int i = 0; user_input[i]; i++) {
        if (!isalnum(user_input[i])) {
            fprintf(stderr, "Invalid input\n");
            return;
        }
    }
    
    char command[100];
    snprintf(command, sizeof(command), "echo %s", user_input);
    system(command);  // Aún vulnerable pero input validado
    
    // Mejor alternativa: evitar system completamente
    // execl("/bin/echo", "echo", user_input, NULL);
}
'''
            
            elif "DOCUMENTACIÓN COMPLETA" in prompt:
                return json.dumps({
                    "documentation": {
                        "summary": "Fix para command injection en función vulnerable",
                        "vulnerability_details": {
                            "cwe": "CWE-78",
                            "type": "Command Injection",
                            "root_cause": "Concatenación no validada + system()",
                            "attack_vector": "Input del usuario"
                        },
                        "fix_explanation": {
                            "approach": "Validación de input + uso de snprintf",
                            "changes_made": ["Añadida validación alfanumérica", "Usado snprintf en lugar de sprintf"],
                            "security_improvements": "Previene ejecución de comandos arbitrarios"
                        },
                        "validation_instructions": {
                            "test_steps": ["Probar con input alfanumérico", "Probar con input malicioso '; rm -rf'"],
                            "expected_results": "Input válido funciona, input malicioso rechazado",
                            "verification_method": "Pruebas manuales y automatizadas"
                        },
                        "considerations": {
                            "performance_impact": "bajo",
                            "backward_compatibility": "compatible",
                            "maintenance_notes": "Considerar usar execl() para mayor seguridad"
                        },
                        "references": [
                            {"title": "CWE-78", "url": "https://cwe.mitre.org/data/definitions/78.html"},
                            {"title": "OWASP Command Injection", "url": "https://owasp.org/www-community/attacks/Command_Injection"}
                        ]
                    },
                    "metadata": {
                        "llm_name": "MockLLM",
                        "timestamp": "2024-02-06T12:00:00",
                        "vulnerability_id": "CWE-78"
                    }
                }, ensure_ascii=False)
            
            return '{"error": "Prompt no reconocido"}'
    
    # Mock Worktree Manager
    class MockWorktreeManager:
        async def prepare_llm_context(self, issue_id, sast_issue, include_related=True):
            return {
                'code': {
                    'vulnerable_section': sast_issue.get('code_snippet', '// No code'),
                    'related_code': '// Contexto adicional mockeado'
                }
            }
    
    # Crear y ejecutar máquina de estados
    mock_llm = MockLLM("TestLLM")
    mock_worktree = MockWorktreeManager()
    
    state_machine = LLMStateMachine(
        llm=mock_llm,
        llm_name="TestLLM",
        worktree_manager=mock_worktree,
        council=None
    )
    
    results = await state_machine.execute_workflow(
        vulnerability=mock_vulnerability,
        worktree_dir="/tmp/test_worktree",
        branch_name="test-branch"
    )
    
    print("\n✅ Máquina de estados completada!")
    print(f"📊 Estado final: {results['state']}")
    print(f"📦 Artefactos generados:")
    print(f"   🔍 Análisis: {'Sí' if results['artifacts']['analysis'] else 'No'}")
    print(f"   🧪 Test: {'Sí' if results['artifacts']['test_design'] else 'No'}")
    print(f"   🔧 Fix: {'Sí' if results['artifacts']['fix_code'] else 'No'}")
    print(f"   📝 Documentación: {'Sí' if results['artifacts']['documentation'] else 'No'}")
    
    return results


async def test_enhanced_council():
    """Prueba el consejo mejorado con máquinas de estados."""
    print("\n🏛️  Probando consejo mejorado...")
    
    # Este test requiere configuración real de OpenRouter
    # Para pruebas, mostramos la estructura
    
    council = EnhancedLLMCouncil()
    
    # Mostrar estado
    status = council.get_council_status()
    print(f"📋 Estado del consejo: {status}")
    
    print("✅ Prueba de estructura completada")
    print("💡 Nota: Para pruebas reales, configura OPENROUTER_API_KEY")


if __name__ == "__main__":
    print("="*70)
    print("🧪 TDH Engine - Pruebas de Máquinas de Estados")
    print("="*70)
    
    # Ejecutar pruebas
    asyncio.run(test_state_machine_workflow())
    
    print("\n" + "="*70)
    print("🎉 Pruebas completadas")
    print("="*70)