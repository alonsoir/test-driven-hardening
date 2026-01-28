"""
Scoring Engine for TDH
Implements the beauty criteria and scoring system for proposed fixes.
"""

import ast
import re
from typing import Dict, Any, List, Optional
import radon.complexity as radon_cc
from radon.visitors import ComplexityVisitor
import lizard


class FixScorer:
    """Scores proposed fixes based on multiple criteria."""
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize the scorer with weights for each criterion.
        
        Args:
            weights: Dictionary with weights for each criterion.
                     Default: complexity=0.25, dependencies=0.20, 
                     loc_delta=0.15, test_coverage=0.25, beauty=0.15
        """
        self.weights = weights or {
            'complexity': 0.25,
            'dependencies': 0.20,
            'loc_delta': 0.15,
            'test_coverage': 0.25,
            'beauty': 0.15
        }
        
        # Validate weights sum to 1.0
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total}")
    
    def score(self, fix_code: str, original_code: str, 
              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Score a proposed fix against multiple criteria.
        
        Args:
            fix_code: The proposed fix code
            original_code: The original vulnerable code
            context: Additional context (language, etc.)
            
        Returns:
            Dictionary with scores and breakdown
        """
        language = (context or {}).get('language', 'python')
        
        # Calculate individual scores
        complexity_score = self._score_complexity(fix_code, language)
        dependencies_score = self._score_dependencies(fix_code, original_code, language)
        loc_delta_score = self._score_loc_delta(fix_code, original_code)
        test_coverage_score = self._score_test_coverage(fix_code, language)
        beauty_score = self._score_beauty(fix_code, language)
        
        # Calculate weighted total
        scores = {
            'complexity': complexity_score,
            'dependencies': dependencies_score,
            'loc_delta': loc_delta_score,
            'test_coverage': test_coverage_score,
            'beauty': beauty_score
        }
        
        total_score = sum(
            scores[criterion] * self.weights[criterion]
            for criterion in self.weights
        )
        
        return {
            'total': total_score,
            'breakdown': scores,
            'weights': self.weights,
            'passed': total_score >= 70.0  # Acceptance threshold
        }
    
    def _score_complexity(self, code: str, language: str) -> float:
        """
        Score based on code complexity (cyclomatic complexity).
        
        Returns:
            Score from 0-100, where 100 is least complex
        """
        if language == 'python':
            try:
                # Use radon for Python
                visitor = ComplexityVisitor.from_code(code)
                complexities = [block.complexity for block in visitor.blocks]
                avg_complexity = sum(complexities) / len(complexities) if complexities else 1
            except:
                # Fallback: count control flow statements
                control_flow_keywords = ['if', 'elif', 'else', 'for', 'while', 
                                       'try', 'except', 'finally', 'with']
                lines = code.split('\n')
                keyword_count = sum(1 for line in lines 
                                  if any(kw in line for kw in control_flow_keywords))
                avg_complexity = keyword_count / max(1, len(lines) / 10)
        else:
            # For other languages, use lizard
            try:
                analysis = lizard.analyze_file.analyze_source_code("temp", code)
                avg_complexity = analysis.average_cyclomatic_complexity
            except:
                avg_complexity = 5  # Default fallback
        
        # Map complexity to score
        if avg_complexity <= 5:
            return 100.0
        elif avg_complexity <= 10:
            return 80.0
        elif avg_complexity <= 15:
            return 60.0
        elif avg_complexity <= 20:
            return 40.0
        else:
            return 20.0
    
    def _score_dependencies(self, fix_code: str, original_code: str, 
                           language: str) -> float:
        """
        Score based on new dependencies introduced.
        
        Returns:
            Score from 0-100, where 100 is no new heavy dependencies
        """
        # Count imports/includes in original code
        if language == 'python':
            original_imports = self._extract_python_imports(original_code)
            fix_imports = self._extract_python_imports(fix_code)
        elif language in ['c', 'cpp']:
            original_imports = self._extract_c_includes(original_code)
            fix_imports = self._extract_c_includes(fix_code)
        else:
            # For other languages, use simple line matching
            original_imports = self._extract_imports_generic(original_code)
            fix_imports = self._extract_imports_generic(fix_code)
        
        # Find new imports
        new_imports = fix_imports - original_imports
        
        # Heavy libraries to penalize
        heavy_libs = {
            'python': ['tensorflow', 'torch', 'pandas', 'numpy', 'scipy'],
            'c': ['windows.h', 'mach/mach.h', 'complex.h'],
            'cpp': ['boost', 'qt', 'wx', 'opencv2']
        }
        
        # Check for heavy libraries
        heavy_count = 0
        for imp in new_imports:
            for heavy in heavy_libs.get(language, []):
                if heavy in imp.lower():
                    heavy_count += 1
        
        # Calculate score
        if len(new_imports) == 0:
            return 100.0
        elif len(new_imports) <= 2 and heavy_count == 0:
            return 80.0
        elif len(new_imports) <= 5 and heavy_count == 0:
            return 60.0
        elif len(new_imports) <= 10:
            return 40.0
        else:
            return 20.0
    
    def _score_loc_delta(self, fix_code: str, original_code: str) -> float:
        """
        Score based on lines of code delta (smaller change is better).
        
        Returns:
            Score from 0-100, where 100 is minimal change
        """
        fix_lines = len(fix_code.splitlines())
        original_lines = len(original_code.splitlines())
        
        delta = abs(fix_lines - original_lines)
        
        if delta <= 5:
            return 100.0
        elif delta <= 10:
            return 80.0
        elif delta <= 20:
            return 60.0
        elif delta <= 50:
            return 40.0
        else:
            return 20.0
    
    def _score_test_coverage(self, code: str, language: str) -> float:
        """
        Score based on presence of tests in the fix.
        
        Returns:
            Score from 0-100, where 100 includes comprehensive tests
        """
        # Look for test indicators
        test_indicators = {
            'python': ['assert ', 'unittest', 'pytest', 'def test_'],
            'c': ['assert(', 'TEST(', 'CHECK(', 'CU_ASSERT'],
            'cpp': ['assert(', 'TEST(', 'BOOST_TEST', 'CHECK('],
            'java': ['assert ', '@Test', 'JUnit', 'Assert.']
        }
        
        indicators = test_indicators.get(language, test_indicators['python'])
        
        # Count test indicators
        count = 0
        for line in code.split('\n'):
            if any(indicator in line for indicator in indicators):
                count += 1
        
        # Score based on test density
        lines = len(code.splitlines())
        if lines == 0:
            return 0.0
        
        test_density = count / lines
        
        if test_density >= 0.1:  # 10% or more test lines
            return 100.0
        elif test_density >= 0.05:
            return 80.0
        elif test_density >= 0.02:
            return 60.0
        elif test_density >= 0.01:
            return 40.0
        else:
            return 20.0
    
    def _score_beauty(self, code: str, language: str) -> float:
        """
        Score based on code beauty (readability, simplicity, elegance).
        
        Returns:
            Score from 0-100, where 100 is most beautiful
        """
        # Initialize beauty score
        beauty = 100.0
        
        # Penalize long lines
        lines = code.split('\n')
        for line in lines:
            if len(line) > 100:  # Very long line
                beauty -= 5
            elif len(line) > 80:  # Long line
                beauty -= 2
        
        # Penalize high nesting depth
        nesting_depth = self._calculate_nesting_depth(code, language)
        if nesting_depth > 4:
            beauty -= 20
        elif nesting_depth > 3:
            beauty -= 10
        elif nesting_depth > 2:
            beauty -= 5
        
        # Penalize magic numbers
        magic_numbers = re.findall(r'\b\d+\b', code)
        if len(magic_numbers) > 5:
            beauty -= 10
        elif len(magic_numbers) > 3:
            beauty -= 5
        
        # Reward descriptive variable names
        if language == 'python':
            # Extract variable names (simple heuristic)
            var_pattern = r'\b([a-z_][a-z0-9_]*)\s*='
            variables = re.findall(var_pattern, code)
            descriptive = sum(1 for v in variables if len(v) > 2 and '_' in v)
            if variables:
                beauty += (descriptive / len(variables)) * 10
        
        # Ensure score is within bounds
        return max(0.0, min(100.0, beauty))
    
    def _calculate_nesting_depth(self, code: str, language: str) -> int:
        """Calculate maximum nesting depth in code."""
        # Simple heuristic: count braces/brackets/indentation
        if language == 'python':
            # Count indentation
            max_depth = 0
            current_depth = 0
            for line in code.split('\n'):
                stripped = line.lstrip()
                if stripped.startswith('if ') or stripped.startswith('for ') or \
                   stripped.startswith('while ') or stripped.startswith('def ') or \
                   stripped.startswith('class ') or stripped.startswith('with '):
                    current_depth += 1
                elif stripped and not stripped.startswith(' ') and not stripped.startswith('\t'):
                    # Reset on dedent
                    current_depth = 0
                max_depth = max(max_depth, current_depth)
            return max_depth
        else:
            # Count braces
            depth = 0
            max_depth = 0
            for char in code:
                if char in '{[(':
                    depth += 1
                    max_depth = max(max_depth, depth)
                elif char in '}])':
                    depth -= 1
            return max_depth
    
    def _extract_python_imports(self, code: str) -> set:
        """Extract Python imports from code."""
        imports = set()
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module)
        except:
            # Fallback: regex
            import re
            patterns = [
                r'^\s*import\s+([a-zA-Z0-9_\.]+)',
                r'^\s*from\s+([a-zA-Z0-9_\.]+)\s+import'
            ]
            for pattern in patterns:
                matches = re.findall(pattern, code, re.MULTILINE)
                imports.update(matches)
        
        return imports
    
    def _extract_c_includes(self, code: str) -> set:
        """Extract C/C++ includes from code."""
        includes = set()
        import re
        
        # Match #include statements
        pattern = r'^\s*#include\s+[<"]([^>"]+)[>"]'
        matches = re.findall(pattern, code, re.MULTILINE)
        includes.update(matches)
        
        return includes
    
    def _extract_imports_generic(self, code: str) -> set:
        """Extract imports/includes generically."""
        imports = set()
        
        # Common patterns
        patterns = [
            r'^\s*import\s+([^;\s]+)',  # Java, JavaScript, etc.
            r'^\s*#include\s+[<"]([^>"]+)[>"]',  # C/C++
            r'^\s*require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',  # Node.js
            r'^\s*using\s+([^;\s]+);',  # C#
            r'^\s*extern\s+crate\s+([^;\s]+);',  # Rust
        ]
        
        import re
        for pattern in patterns:
            matches = re.findall(pattern, code, re.MULTILINE)
            imports.update(matches)
        
        return imports


# Example usage
if __name__ == '__main__':
    scorer = FixScorer()
    
    original_code = """
def bad_function(x):
    if x > 0:
        if x < 10:
            if x % 2 == 0:
                return True
    return False
"""
    
    fix_code = """
def good_function(x):
    return 0 < x < 10 and x % 2 == 0
"""
    
    result = scorer.score(fix_code, original_code, {'language': 'python'})
    print(f"Total score: {result['total']:.1f}")
    print("Breakdown:")
    for criterion, score in result['breakdown'].items():
        print(f"  {criterion}: {score:.1f}")