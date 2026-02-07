import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum, auto

from .llm_state_machine import LLMState, LLMStateContext, LLMStateMachine

class LLMStateMachineDocker(LLMStateMachine):
    """
    Máquina de estados extendida con capacidades Docker.
    """
    
    def __init__(self, llm, llm_name: str, worktree_manager, docker_engine, council=None):
        super().__init__(llm, llm_name, worktree_manager, council)
        self.docker_engine = docker_engine
        self.container_info = None
        
    async def execute_workflow(self, vulnerability: Dict[str, Any], 
                               worktree_dir: str, branch_name: str) -> Dict[str, Any]:
        """
        Flujo extendido con Docker.
        """
        self.start_time = datetime.now()
        self.context = LLMStateContext(
            vulnerability=vulnerability,
            worktree_dir=worktree_dir,
            current_file=vulnerability.get('file', 'unknown')
        )
        
        print(f"\n🤖 [{self.llm_name}] Iniciando workflow con Docker...")
        
        try:
            # ESTADO NUEVO: SETUP_DOCKER
            await self._transition_to(LLMState.SETUP_ENVIRONMENT)
            await self._state_setup_docker()
            
            # Estados originales
            await self._transition_to(LLMState.ANALYZING)
            await self._state_analyzing()
            
            await self._transition_to(LLMState.TEST_DESIGNING)
            await self._state_test_designing()
            
            # ESTADO NUEVO: TEST_IMPLEMENTATION
            await self._transition_to(LLMState.TEST_IMPLEMENTATION)
            await self._state_test_implementation()
            
            # ESTADO NUEVO: TEST_EXECUTION_NOFIX
            await self._transition_to(LLMState.TEST_EXECUTION_NOFIX)
            await self._state_test_execution_nofix()
            
            # ESTADO NUEVO: COMMUNICATE_RESULTS
            await self._transition_to(LLMState.COMMUNICATE_RESULTS)
            await self._state_communicate_results()
            
            await self._transition_to(LLMState.FIX_DESIGNING)
            await self._state_fix_designing()
            
            # ESTADO NUEVO: FIX_APPLICATION
            await self._transition_to(LLMState.FIX_APPLICATION)
            await self._state_fix_application()
            
            # ESTADO NUEVO: TEST_EXECUTION_WITHFIX
            await self._transition_to(LLMState.TEST_EXECUTION_WITHFIX)
            await self._state_test_execution_withfix()
            
            await self._transition_to(LLMState.DOCUMENTING)
            await self._state_documenting()
            
            if self.council:
                await self._transition_to(LLMState.COUNCIL_DISCUSSING)
                await self._state_council_discussing(branch_name)
            
            await self._transition_to(LLMState.FINISHED)
            
        except Exception as e:
            await self._transition_to(LLMState.ERROR)
            self.context.errors.append(str(e))
            print(f"❌ [{self.llm_name}] Error: {e}")
        finally:
            # Limpiar Docker
            if self.container_info:
                await self.docker_engine.cleanup(self.llm_name)
        
        self.end_time = datetime.now()
        return self._compile_results(branch_name)
    
    async def _state_setup_docker(self):
        """Configurar entorno Docker."""
        print(f"   🐳 [{self.llm_name}] Creando contenedor Docker...")
        
        self.container_info = await self.docker_engine.create_llm_environment(
            llm_name=self.llm_name,
            worktree_path=self.context.worktree_dir
        )
        
        # Verificar que funcione
        test_cmd = await self.docker_engine.execute_command(
            llm_name=self.llm_name,
            command="echo 'Docker environment ready' && gcc --version | head -1"
        )
        
        if test_cmd.get('success'):
            print(f"   ✅ [{self.llm_name}] Docker configurado: {test_cmd.get('stdout', '').strip()}")
        else:
            raise Exception(f"Fallo configuración Docker: {test_cmd.get('stderr')}")
    
    async def _state_test_implementation(self):
        """Implementar test real en Docker."""
        print(f"   🧪 [{self.llm_name}] Implementando test en Docker...")
        
        # Pedir al LLM que genere código de test
        test_code_prompt = f"""IMPLEMENTACIÓN DE TEST EN C

VULNERABILIDAD: {self.context.vulnerability.get('message')}
ANÁLISIS: {self.context.analysis_result}
DISEÑO DE TEST: {self.context.test_design}

GENERA un programa C que:
1. Incluya el código vulnerable (o lo simule)
2. Demuestre la explotación de la vulnerabilidad
3. Sea compilable con: gcc -o test_vuln test_vuln.c
4. Muestre claramente el problema

El programa debe:
- Compilar sin errores (solo warnings si son inevitables)
- Ejecutarse y mostrar el problema
- Incluir comentarios explicativos

Salida esperada: CÓDIGO C COMPLETO"""
        
        response = await self.llm.generate_fix({
            'vulnerability': self.context.vulnerability,
            'analysis': self.context.analysis_result,
            'test_design': self.context.test_design,
            'custom_prompt': test_code_prompt
        })
        
        test_code = list(response.values())[0]
        self.context.test_implementation = test_code
        
        # Guardar en archivo
        test_files = {
            'test_vuln.c': test_code,
            'Makefile': 'all:\n\tgcc -o test_vuln test_vuln.c\n\nrun:\n\t./test_vuln'
        }
        
        # Escribir archivos en el contenedor
        container = self.docker_engine.containers[self.llm_name]
        for filename, content in test_files.items():
            # Crear directorios si no existen
            dirname = '/workspace/' + os.path.dirname(filename)
            container.exec_run(f"mkdir -p {dirname}")
            
            # Escribir archivo
            escaped_content = json.dumps(content)
            container.exec_run(
                f"echo {escaped_content} > /workspace/{filename}"
            )
        
        # Compilar
        compile_result = await self.docker_engine.execute_command(
            llm_name=self.llm_name,
            command="cd /workspace && gcc -o test_vuln test_vuln.c 2>&1"
        )
        
        self.context.compile_result = compile_result
        
        if compile_result.get('success'):
            print(f"   ✅ [{self.llm_name}] Test compilado exitosamente")
        else:
            print(f"   ⚠️  [{self.llm_name}] Problemas compilando test: {compile_result.get('stderr')}")
    
    async def _state_test_execution_nofix(self):
        """Ejecutar test sin fix para demostrar vulnerabilidad."""
        print(f"   🚨 [{self.llm_name}] Ejecutando test (sin fix)...")
        
        result = await self.docker_engine.execute_command(
            llm_name=self.llm_name,
            command="cd /workspace && ./test_vuln 2>&1",
            timeout=10
        )
        
        self.context.test_execution_nofix = result
        
        # Verificar que el test muestra la vulnerabilidad
        vulnerability_demonstrated = self._check_vulnerability_demo(result)
        
        if vulnerability_demonstrated:
            print(f"   ✅ [{self.llm_name}] Vulnerabilidad demostrada: {result.get('stdout', '')[:100]}...")
        else:
            print(f"   ⚠️  [{self.llm_name}] Test no muestra vulnerabilidad claramente")
    
    def _check_vulnerability_demo(self, result: Dict) -> bool:
        """Verifica si el resultado demuestra la vulnerabilidad."""
        # Esta es una implementación simple. En realidad, deberíamos analizar el resultado.
        # Por ahora, asumimos que si el programa se ejecuta (exit_code 0) y hay salida, es suficiente.
        return result.get('success') and result.get('stdout', '').strip() != ''
    
    async def _state_communicate_results(self):
        """Comunicar resultados preliminares a otros LLMs."""
        if not self.council:
            return
            
        print(f"   💬 [{self.llm_name}] Compartiendo resultados de test...")
        
        message = {
            'llm': self.llm_name,
            'type': 'test_results',
            'vulnerability': self.context.vulnerability.get('rule_id'),
            'test_implemented': bool(self.context.test_implementation),
            'test_compiled': self.context.compile_result.get('success'),
            'vulnerability_shown': bool(self.context.test_execution_nofix and 
                                      self.context.test_execution_nofix.get('success')),
            'insights': self.context.analysis_result.get('analysis', {}).get('why_vulnerable') if self.context.analysis_result else None,
            'test_code_snippet': (self.context.test_implementation[:500] + '...' 
                                if self.context.test_implementation else None)
        }
        
        # Enviar al consejo para difusión
        await self.council.broadcast_message(
            sender=self.llm_name,
            message=message
        )
        
        # Recibir feedback de otros LLMs
        feedback = await self.council.get_messages_for(self.llm_name)
        self.context.peer_feedback = feedback
        
        if feedback:
            print(f"   📨 [{self.llm_name}] Recibió {len(feedback)} mensajes")
    
    async def _state_fix_application(self):
        """Aplicar fix a múltiples archivos si es necesario."""
        print(f"   🔧 [{self.llm_name}] Aplicando fix...")
        
        fix_code = self.context.fix_code
        
        # Parsear fix_code (puede ser string o dict)
        if isinstance(fix_code, dict) and 'fixed_files' in fix_code:
            # Múltiples archivos
            files_to_write = fix_code['fixed_files']
        elif isinstance(fix_code, str):
            # Un solo archivo - el vulnerable
            vulnerable_file = self.context.current_file
            files_to_write = {vulnerable_file: fix_code}
        else:
            # Formato desconocido
            files_to_write = {self.context.current_file: str(fix_code)}
        
        # Aplicar cada fix
        apply_results = []
        for filename, content in files_to_write.items():
            # Crear archivo en Docker
            cmd = f"cat > /workspace/{filename} << 'EOF'\n{content}\nEOF"
            result = await self.docker_engine.execute_command(
                llm_name=self.llm_name,
                command=cmd
            )
            apply_results.append({
                'file': filename,
                'success': result.get('success'),
                'error': result.get('stderr')
            })
            
            if result.get('success'):
                print(f"     ✅ Archivo {filename} actualizado")
            else:
                print(f"     ❌ Error actualizando {filename}: {result.get('error')}")
        
        self.context.fix_application_results = apply_results
    
    async def _state_test_execution_withfix(self):
        """Ejecutar test con fix para verificar corrección."""
        print(f"   ✅ [{self.llm_name}] Verificando fix...")
        
        # Recompilar con el fix
        compile_cmd = "cd /workspace && gcc -o test_vuln_fixed test_vuln.c"
        compile_result = await self.docker_engine.execute_command(
            llm_name=self.llm_name,
            command=compile_cmd
        )
        
        if not compile_result.get('success'):
            print(f"   ❌ [{self.llm_name}] Error compilando con fix: {compile_result.get('stderr')}")
            self.context.fix_verification = {'compiled': False, 'error': compile_result}
            return
        
        # Ejecutar test con fix
        exec_result = await self.docker_engine.execute_command(
            llm_name=self.llm_name,
            command="cd /workspace && ./test_vuln_fixed 2>&1",
            timeout=10
        )
        
        # También ejecutar test original para comparar
        original_result = self.context.test_execution_nofix
        
        self.context.fix_verification = {
            'compiled': True,
            'execution': exec_result,
            'original': original_result,
            'fixed_success': exec_result.get('success'),
            'vulnerability_fixed': self._is_vulnerability_fixed(original_result, exec_result)
        }
        
        if self.context.fix_verification['vulnerability_fixed']:
            print(f"   🎉 [{self.llm_name}] ¡Vulnerabilidad corregida!")
        else:
            print(f"   ⚠️  [{self.llm_name}] Vulnerabilidad puede persistir")
    
    def _is_vulnerability_fixed(self, original_result: Dict, fixed_result: Dict) -> bool:
        """
        Determina si la vulnerabilidad fue corregida.
        Por ahora, una implementación simple: si el programa con fix se ejecuta sin errores
        y la salida es diferente (o no hay indicios de vulnerabilidad), asumimos que está corregida.
        """
        # En una implementación real, haríamos un análisis más profundo.
        # Por ahora, asumimos que si el programa con fix se ejecuta (exit_code 0) y no hay
        # mensajes de error relacionados con la vulnerabilidad, está corregido.
        if fixed_result.get('success') and not fixed_result.get('stderr', ''):
            return True
        return False