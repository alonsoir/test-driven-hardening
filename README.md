# Test Driven Hardening (TDH)

> A scientific methodology for evidence-based security hardening through distributed LLM consensus.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Paper Status](https://img.shields.io/badge/Paper-Pre--print-orange)](papers/theoretical-framework.md)

## 📖 Overview

**Test Driven Hardening (TDH)** is a security remediation framework that applies scientific rigor and test-driven development principles to vulnerability fixing. Each security fix must be:

1. **Empirically validated** through a failing proof-of-concept test
2. **Peer-reviewed** by a distributed council of LLMs
3. **Verified** by the same test after remediation
4. **Documented** in a self-contained, evidence-based artifact

## 🔗 Technical Foundation

TDH builds upon the consensus architecture demonstrated in **[Karpathy's llm-council](https://github.com/karpathy/llm-council)** project, extending it with:
- **Security-specialized prompts** for vulnerability analysis
- **Evidence-driven consensus** focused on exploitability validation
- **Integration with CI/CD pipelines** for automated remediation
- **Hardening Journal** for institutional learning
## 🧠 Core Philosophy

- **Evidence Over Opinion**: Every vulnerability must have a reproducible PoC
- **Distributed Consensus**: Multiple LLMs provide unbiased technical review
- **Human-as-President**: Engineers make final decisions with full context
- **Institutional Learning**: Every fix becomes documented, searchable knowledge

## 📚 Papers

- **[Theoretical Framework](papers/theoretical-framework.md)** - Core TDH methodology and architecture
- **[ML Defender Case Study](papers/ml-defender-case-study.md)** - Empirical validation in production

## 🏗️ Architecture Components

| Component | Purpose | Status |
|-----------|---------|--------|
| **LLM Council** | Distributed consensus through multiple AI models | Designed |
| **Hardening Journal** | Institutional memory via vector database | Designed |
| **TDH Agent** | Automated PR generation with evidence | Designed |
| **Telemetry System** | Continuous improvement through metrics | Designed |

## 🔬 Origin & Validation

TDH was conceived and empirically validated during the development of the **ML Defender** aka aegisIDS intrusion detection system, specifically through the resolution of ISSUE-003 (thread-local FlowManager bug). The methodology demonstrated:

- ✅ **4× performance improvement** (3.69μs → 0.93μs)
- ✅ **100% feature recovery** (11/142 → 142/142 features)
- ✅ **Unanimous LLM consensus** (5/5 models agreement)
- ✅ **Scientific validation** (ThreadSanitizer, benchmarks, PoC tests)

## 🚀 Getting Started

### For Researchers
1. Read the [theoretical framework](papers/theoretical-framework.md)
2. Review the [case study](papers/ml-defender-case-study.md) for empirical validation
3. Check [CONTRIBUTING.md](docs/CONTRIBUTING.md) for collaboration guidelines

### For Practitioners
TDH is designed for gradual adoption:
1. Start by requiring PoC tests for critical vulnerabilities
2. Introduce multi-reviewer processes (human or AI)
3. Document fixes with evidence and context
4. Consider implementing a Hardening Journal for institutional learning

### **TDH Engine – Multi-SOTA Hardening Flow**

```mermaid
flowchart TD
    A[Inicio: Vulnerabilidad detectada / análisis inicial] --> B[Engine asigna vulnerabilidad a SOTA 1]
    B --> C[SOTA recibe prompt inicial y crea PoC test]
    C --> D[PoC test compilado y ejecutado → demuestra vulnerabilidad (ROJO/VERDE)]
    D --> E[Engine recibe PoC y lo comparte con otras SOTAs]
    E --> F[Otras SOTAs verifican el PoC, validación reproducible]
    F --> G[SOTAs generan fix individual según su estrategia]
    G --> H[Engine coordina logs, estado de cada SOTA y posibles interdependencias]
    H --> I[Engine aplica fix en worktree y genera commit]
    I --> J[Pull Request automática con: fix, test, logs y análisis de SOTA]
    J --> K[Revisión humana final y decisión de merge]
    K --> L[Actualización del Hardening Journal / aprendizaje institucional]
```

### **Leyenda / Conceptos clave**

* **PoC test (Prueba de concepto)**:

  * Compilable y ejecutable en lenguaje base (C/C++ actualmente).
  * **ROJO** → vulnerabilidad corregida; **VERDE** → vulnerabilidad presente.

* **SOTA (State-of-the-Art AI model)**:

  * Genera fixes, tests y documentación.
  * Se comunica con engine mediante archivos de log o `chat-incoming`.
  * Interacción multi-SOTA gestionada por engine.

* **Engine**:

  * Coordina worktrees, contenedores, estado de cada SOTA y comunicación.
  * Propaga PoC y fixes entre SOTAs.
  * Automatiza commits y creación de PRs, pero no toma decisiones de análisis.

* **Human-in-the-loop**:

  * Revisión final de PR.
  * Decide qué fixes se aceptan, basándose en evidencia reproducible.

## 📊 Status

**Current**: Pre-print research framework  
**Goal**: Production-ready implementation  
**Validation**: Empirical evidence from ML Defender ISSUE-003  

## 📄 License

This research framework is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Concept developed through collaboration with DeepSeek AI
- Empirically validated in the ML Defender pipeline
- Inspired by scientific methodology and test-driven development