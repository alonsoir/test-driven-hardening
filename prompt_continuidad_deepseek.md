# 📋 PROMPT DE CONTINUIDAD – TDH ENGINE (2026-02-12)

## ✅ LO QUE HEMOS LOGRADO HOY

| Área                          | Estado     | Detalle |
|-------------------------------|------------|---------|
| **Agente SOTA autónomo**      | ✅ COMPLETO | `sota_agent.py` lee `llm_council.yaml`, ejecuta test/fix con iteración, logs con `[STATE:]`. |
| **Configuración LLM Council** | ✅ COMPLETO | `llm_council.yaml` con `state_prompts` completos, sin instrucciones hardcodeadas. |
| **Orquestador multi‑SOTA**    | ✅ COMPLETO | `SASTOrchestrator.orchestrate()`: filtra HIGH/CRITICAL, crea worktrees, lanza contenedores, monitoriza logs, genera PRs. |
| **CLI unificada**            | ✅ COMPLETO | `tdh_unified.py` con comando `sast-orchestrated`, soporte `--council` y `--dry-run`. |
| **Docker base image**        | ✅ ACTUALIZADA | Copia `sota_agent.py`, instala `python-dotenv`. |
| **Makefile**                 | ✅ LIMPIO    | Separado del Dockerfile, targets para VM y host. |
| **Entorno Vagrant**          | ⚠️ PENDIENTE | Requiere verificación completa de aprovisionamiento. |
| **Prueba end‑to‑end real**   | ⚠️ PENDIENTE | No ejecutada aún; solo validación conceptual. |

---

## 🎯 PLAN DE ACCIÓN PARA MAÑANA (2026-02-13)

### 🔹 FASE 0 – VERIFICACIÓN DEL ENTORNO VAGRANT
- [ ] Destruir VM actual: `make vagrant-destroy`
- [ ] Levantar VM limpia: `make vagrant-up`
- [ ] Conectarse: `make vagrant-ssh`
- [ ] Dentro de la VM: `cd /home/vagrant/tdh-engine`
- [ ] Ejecutar setup completo: `make vm-setup`
- [ ] Verificar Docker: `make docker-info`
- [ ] Verificar imagen base: `docker images | grep tdh-base`

### 🔹 FASE 1 – PRUEBA DEL AGENTE EN CONTENEDOR AISLADO
- [ ] Crear un worktree manualmente y montarlo en un contenedor:
  ```bash
  git clone https://github.com/alonsoir/test-zeromq-c-.git /tmp/test-repo
  cd /tmp/test-repo
  git worktree add ../test-worktree -b test-branch
  echo '{"model":"claude-3-5-sonnet","vulnerability":{"id":"CWE-78","file":"src/command.c","line":42,"description":"OS command injection","severity":"CRITICAL"},"repo_path":"/workspace","openrouter_api_key":"'$OPENROUTER_API_KEY'"}' | \
  docker run -i --rm -v /tmp/test-worktree:/workspace:rw tdh-base:latest sota_agent.py
  ```

Verificar que el agente genera test, lo ejecuta, itera si falla, produce fix.
🔹 FASE 2 – PRUEBA DE ORQUESTACIÓN COMPLETA (DRY‑RUN)

Exportar OPENROUTER_API_KEY (desde .env)
Ejecutar: make vm-example
Observar logs: creación de worktrees, lanzamiento de contenedores, estados [STATE:].
Verificar que se genera el reporte JSON en results/.
🔹 FASE 3 – PRUEBA CON PR REAL (OPCIONAL)

Configurar GITHUB_TOKEN en .env
Ejecutar sin --dry-run sobre un fork de prueba.
Confirmar que se crea la Pull Request en GitHub.
🔹 FASE 4 – DOCUMENTACIÓN Y DEMO

Escribir breve guía de uso (README.md actualizado).
Preparar demo para stakeholders: un repo con vulnerabilidad CWE-78, mostrar fix automático.
⚠️ RIESGOS Y SUPUESTOS PARA MAÑANA

Conexión a OpenRouter: La API key debe estar presente y tener fondos/crédito.
Repositorio de prueba: test-zeromq-c debe tener un Makefile funcional y la vulnerabilidad debe ser detectable.
Worktrees: Git 2.5+ necesario (Vagrant VM tiene Git 2.34+ OK).
Permisos en volúmenes: El contenedor escribe como tdh-user (UID 1000). Si el worktree en el host pertenece a otro usuario, puede haber problemas de permisos. En Vagrant se usa vagrant (UID 1000) → compatible.
Tiempo de ejecución: Cada contenedor puede tomar varios minutos (llamadas a LLM). Configurar timeouts generosos.