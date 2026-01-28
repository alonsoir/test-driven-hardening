# 🛡️ TDH Engine - Test Driven Hardening Prototype

> *"Evidencia sobre opinión, tests sobre suposiciones"*  
> Un framework para remediación automatizada de vulnerabilidades basado en el método científico.

## 🎯 ¿Qué es TDH?

**Test Driven Hardening (TDH)** es una metodología que aplica el rigor del método científico y los principios de Test-Driven Development (TDD) al hardening de seguridad. Cada vulnerabilidad debe ser:

1. **Demostrada** con un test de PoC reproducible
2. **Analizada** por un consejo multi-LLM (simulado inicialmente)
3. **Corregida** con el fix que mejor equilibre seguridad y calidad
4. **Validada** por los mismos tests que demostraban la vulnerabilidad

## 🚀 Comenzando

### Instalación Rápida

```bash
# 1. Clonar el repositorio
git clone https://github.com/alonsoir/test-driven-hardening.git
cd test-driven-hardening/engine-prototype

# 2. Instalar dependencias (sistemas Unix/macOS)
./install.sh

# 3. Verificar instalación
python -m tdh_engine --version