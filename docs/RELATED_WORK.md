# Related Work & Technical Foundations

## Core Inspiration

### llm-council (Karpathy, 2025)
**URL**: https://github.com/karpathy/llm-council  
**Relevance**: Provides the foundational three-stage consensus architecture (independent opinion → anonymous review → final synthesis) that TDH adapts for security analysis.  
**Key Contribution**: Demonstrates practical multi-LLM collaboration with identity anonymization to reduce individual model bias.

## Complementary Approaches

### Multi-Agent AI Security Tools
- **ChatGPT/GPT-4 Code Interpreter**: Single-model code analysis
- **Claude Code**: Specialized code understanding capabilities
- **DeepSeek-Coder**: Open-source code-specialized LLM

### Traditional Security Methodologies
- **Test-Driven Development (TDD)**: Red-green-refactor cycle applied to security
- **Chaos Engineering**: "Break things to prove resilience" philosophy
- **Scientific Method**: Hypothesis → Experiment → Conclusion framework

## How TDH Extends Existing Work

TDH uniquely combines:
1. **llm-council's consensus architecture** with...
2. **Security-specific prompt engineering** and...
3. **TDD's empirical validation requirements** and...
4. **CI/CD automation for remediation**

This creates a novel, evidence-based security hardening methodology rather than just another analysis tool.