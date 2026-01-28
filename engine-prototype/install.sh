#!/bin/bash
# TDH Engine - Installation Script
# Compatible con Python 3.9-3.14

set -e  # Exit on error

echo "🧪 TDH Engine - Test Driven Hardening Prototype"
echo "=============================================="

# Check Python version
echo "🔍 Checking Python version..."
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
required_major="3"
required_minor="9"

# Extraer major y minor
major=$(echo $python_version | cut -d. -f1)
minor=$(echo $python_version | cut -d. -f2)

# Comparar versiones
if [ $major -gt $required_major ] || ([ $major -eq $required_major ] && [ $minor -ge $required_minor ]); then
    echo "✅ Python $python_version detected (>= $required_major.$required_minor required)"
else
    echo "❌ Python $required_major.$required_minor or higher required. Found: $python_version"
    exit 1
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "📁 Virtual environment already exists"
fi

# Activate virtual environment
echo "🚀 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies with potential compatibility fixes
echo "📦 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    # Intentar instalar normalmente primero
    if ! pip install -r requirements.txt; then
        echo "⚠️  Standard installation failed, trying with relaxed constraints..."
        # Instalar sin binarios precompilados (puede ser más lento pero más compatible)
        pip install -r requirements.txt --no-binary :all: || \
        echo "⚠️  Some packages may have compatibility issues with Python 3.14"
    fi
else
    echo "❌ requirements.txt not found"
    exit 1
fi

# Verificar instalación de dependencias críticas
echo "🔍 Verifying critical dependencies..."
for package in "gitpython" "semgrep" "bandit" "radon" "requests" "pyyaml"; do
    if python -c "import $package" 2>/dev/null; then
        echo "✅ $package installed"
    else
        echo "⚠️  $package not installed properly"
    fi
done

# Install system dependencies (if needed)
echo "🔧 Checking for system dependencies..."

# Check for git
if command -v git &> /dev/null; then
    echo "✅ Git is installed"
else
    echo "⚠️  Git is not installed."
    echo "   Please install git manually: https://git-scm.com/"
fi

# Check for cppcheck (for C/C++ analysis)
if command -v cppcheck &> /dev/null; then
    echo "✅ cppcheck is installed"
else
    echo "📝 cppcheck not found. C/C++ analysis will be limited."
    echo "   To install:"
    echo "   - Ubuntu/Debian: sudo apt-get install cppcheck"
    echo "   - macOS: brew install cppcheck"
    echo "   - Windows: Download from http://cppcheck.sourceforge.net/"
fi

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p knowledge_base/{CWE-120,CWE-89,CWE-416,CWE-79,CWE-22}
mkdir -p config/prompts
mkdir -p logs
mkdir -p tests

# Download example vulnerabilities
echo "📥 Downloading example vulnerabilities..."
if [ ! -f "knowledge_base/CWE-120/example1.c" ]; then
    cat > knowledge_base/CWE-120/example1.c << 'EOF'
// CWE-120: Buffer Overflow
#include <string.h>
#include <stdio.h>

void vulnerable_function(char *input) {
    char buffer[64];
    strcpy(buffer, input);  // No bounds checking
    printf("%s\n", buffer);
}

int main(int argc, char *argv[]) {
    if (argc > 1) {
        vulnerable_function(argv[1]);
    }
    return 0;
}
EOF
    echo "✅ Created buffer overflow example"
fi

# Create configuration file
echo "⚙️ Creating configuration file..."
mkdir -p config
cat > config/tdh_config.yaml << 'EOF'
# TDH Engine Configuration
engine:
  name: "tdh-engine"
  version: "0.1.0"
  mode: "community"
  python_version: "3.14"

scoring:
  weights:
    complexity: 0.25
    dependencies: 0.20
    loc_delta: 0.15
    test_coverage: 0.25
    beauty: 0.15
  acceptance_threshold: 70

sast:
  tools:
    - semgrep
    - bandit
    - cppcheck
  severity_filter: ["CRITICAL", "HIGH"]

council:
  providers:
    - name: "mock"
      type: "mock"
      role: "architect"
    - name: "deepseek_local"
      type: "local"
      role: "security_analyst"
  max_proposals_per_vuln: 3

workspace:
  temp_dir: "/tmp/tdh_workspaces"
  max_workspaces: 10
  cleanup_after_hours: 24

logging:
  level: "INFO"
  file: "logs/tdh_engine.log"
  max_size_mb: 10
EOF
echo "✅ Created configuration file"

# Create prompt templates
echo "📝 Creating prompt templates..."
mkdir -p config/prompts
cat > config/prompts/claude_architect.yaml << 'EOF'
role: "Software Architect & Test Designer"
objective: "Analyze security vulnerabilities from architectural perspective"
instructions: |
  Focus on:
  1. System-wide implications
  2. Test design that proves exploitability
  3. Architectural patterns for the fix
  4. Long-term maintainability
EOF

cat > config/prompts/deepseek_performance.yaml << 'EOF'
role: "Performance Optimization Specialist"
objective: "Ensure fixes don't degrade performance"
instructions: |
  Focus on:
  1. Time/space complexity
  2. Memory usage implications
  3. Cache locality and CPU efficiency
  4. Benchmarking approach
EOF

cat > config/prompts/gpt4_security.yaml << 'EOF'
role: "Security Expert"
objective: "Analyze security implications"
instructions: |
  Focus on:
  1. Security impact assessment
  2. Exploit vectors and attack surface
  3. Defense in depth considerations
  4. Compliance and security standards
EOF

# Make main script executable
if [ -f "tdh_engine.py" ]; then
    chmod +x tdh_engine.py
    echo "✅ Made tdh_engine.py executable"
fi

# Run basic tests
echo "🧪 Running basic tests..."
if python -c "import sys; print('✅ Python', sys.version)" 2>/dev/null; then
    echo "✅ Python test passed"
    
    # Test imports básicos
    test_imports="import git; import requests; import yaml"
    if python -c "$test_imports" 2>/dev/null; then
        echo "✅ Basic imports work"
    else
        echo "⚠️  Some imports failed"
    fi
else
    echo "⚠️  Python test failed"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Quick start:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run demo: python tdh_engine.py demo --example buffer_overflow"
echo "3. Analyze a repo: python tdh_engine.py analyze /path/to/repo"
echo ""
echo "Need help? Check README.md or run: python tdh_engine.py --help"