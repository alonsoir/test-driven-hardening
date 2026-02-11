# AGENTS.md - Test-Driven Hardening (TDH) Engine

## Project Overview

**Test-Driven Hardening (TDH)** is a security remediation framework that applies scientific rigor and test-driven development principles to vulnerability fixing. The project uses distributed LLM consensus for evidence-based security hardening.

**Main Language**: Python 3.11+
**Architecture**: Modular system with Docker-based SAST orchestration

---

## Build/Test/Lint Commands

All commands should be run from the `engine-prototype/` directory:

```bash
# Setup and dependencies
cd engine-prototype
make setup              # Configure project and install dependencies
make setup-deps         # Install Python dependencies in venv
make build-base         # Build base Docker image

# Testing
make test               # Run complete test suite via tdh_unified.py
python -m pytest tests/ -v                    # Run all pytest tests
python -m pytest tests/test_specific.py -v    # Run single test file
python -m pytest tests/test_specific.py::test_function -v  # Run single test
python tdh_unified.py test                    # Run unified system test

# Linting and checks
make check              # Verify dependencies are installed
python -m pylint src/ --rcfile=.pylintrc      # Run pylint checks

# Maintenance
make clean              # Clean temp files, results, and cache
make docker-info        # Show Docker environment info
make list-tools         # List available SAST tools

# Vagrant (VM-based development)
make vagrant-up         # Start/create VM
make vagrant-ssh        # Connect to VM
make vagrant-halt       # Stop VM
make vm-example         # Run example analysis (inside VM)
```

---

## Code Style Guidelines

### Python Conventions

**Imports**: Group in this order: stdlib → third-party → local. Use explicit imports.
```python
import asyncio
import json
import os
from pathlib import Path

import docker
from rich.console import Console

from core.docker_manager import DockerManager
```

**Naming**:
- Classes: `PascalCase` (e.g., `DockerManager`, `SASTOrchestrator`)
- Functions/variables: `snake_case` (e.g., `create_container`, `repo_url`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- Private methods: `_leading_underscore` (e.g., `_print_sast_summary`)

**Type Hints**: Use type hints for function signatures and complex data structures:
```python
from typing import Dict, Any, List, Optional

def process_vulnerabilities(
    results: List[Dict[str, Any]], 
    severity: Optional[str] = None
) -> Dict[str, int]:
```

**Docstrings**: Use triple quotes with clear descriptions:
```python
def analyze_repository(self, repo_url: str) -> SASTResult:
    """Analyze a repository for security vulnerabilities.
    
    Args:
        repo_url: URL of the Git repository to analyze
        
    Returns:
        SASTResult: Object containing all findings
        
    Raises:
        ValueError: If repo_url is invalid
    """
```

**Error Handling**: Use specific exceptions, log errors with context:
```python
try:
    container = self.client.containers.run(...)
except docker.errors.ImageNotFound as e:
    logger.error(f"❌ Docker image not found: {e}")
    raise
except Exception as e:
    logger.error(f"❌ Unexpected error: {e}")
    raise
```

**Logging**: Use module-level loggers with emojis for visual clarity:
```python
logger = logging.getLogger(__name__)
logger.info("✅ Successfully connected")
logger.warning("⚠️  Resource limit approaching")
logger.error("❌ Operation failed")
```

### File Organization

```
engine-prototype/
├── src/
│   ├── core/              # Core engine components
│   │   ├── docker_manager.py
│   │   ├── sast_pipeline.py
│   │   └── sast_orchestrator.py
│   ├── integration/       # Third-party integrations
│   ├── llm_integration/   # LLM council components
│   └── utils/            # Shared utilities
├── tests/                # Test files (pytest)
├── docker/              # Docker configurations
├── config/              # Tool configurations
├── requirements.txt     # Production dependencies
└── requirements-dev.txt # Development dependencies
```

### Async/Await Pattern

The project heavily uses asyncio for Docker operations:
```python
async def analyze_async(self, repo_url: str) -> SASTResult:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, self._sync_analyze, repo_url
    )
```

### Testing Guidelines

- Use pytest with async support (`pytest-asyncio`)
- Mock Docker operations in unit tests
- Test files named `test_*.py`
- Use fixtures for common setups
- Include both positive and negative test cases

### Configuration

- Max line length: 100 characters (see `.pylintrc`)
- Use Pydantic for data validation
- Store configs in `config/` directory (YAML/JSON)
- Environment variables in `.env` file

### Docker Guidelines

- Base image: `tdh-base:latest`
- Always specify resource limits (memory, CPU)
- Use named volumes for persistence
- Clean up containers after use (`auto_remove`)
- Tag containers with `tdh-{llm_name}-{token}` pattern

---

## Key Principles

1. **Evidence-based**: Every vulnerability must have a reproducible PoC
2. **Distributed consensus**: Multiple LLMs provide unbiased technical review
3. **Human-as-President**: Engineers make final decisions with full context
4. **Institutional learning**: Document fixes with evidence and context
