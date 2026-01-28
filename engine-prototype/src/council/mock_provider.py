"""
Mock LLM Provider for testing and development
"""

from .interface import LLMProvider, VulnerabilityAnalysis, FixProposal


class MockProvider(LLMProvider):
    """Mock provider that returns predefined responses"""
    
    def __init__(self, name: str = "mock", role: str = "architect", 
                 config: Dict[str, Any] = None):
        super().__init__(name, role, config or {})
        self.response_index = 0
    
    async def analyze_vulnerability(self, vulnerability_data: Dict[str, Any], 
                                   code_context: str) -> VulnerabilityAnalysis:
        """Return mock analysis"""
        return VulnerabilityAnalysis(
            vulnerability_id=vulnerability_data.get('id', 'mock_vuln'),
            council_member=self.name,
            root_cause="Mock root cause for testing",
            exploitability="HIGH",
            proposed_fixes=[
                FixProposal(
                    id="mock_fix_1",
                    author=self.name,
                    role=self.role,
                    code="// Mock fix code\nprintf('Fixed!');",
                    explanation="This is a mock fix for testing purposes",
                    confidence=0.8
                )
            ],
            poc_code="// Mock POC\nvoid exploit() { printf('Mock exploit'); }",
            recommendations="This is a mock analysis"
        )
    
    async def review_fix(self, fix_proposal: FixProposal, original_code: str,
                        vulnerability_data: Dict[str, Any]) -> Dict[str, Any]:
        """Return mock review"""
        return {
            'reviewer': self.name,
            'score': 75.0 + (self.response_index * 5),
            'comments': 'Mock review comment',
            'suggestions': ['Suggestion 1', 'Suggestion 2'],
            'approved': True
        }
    
    async def generate_poc(self, vulnerability_data: Dict[str, Any],
                          code_context: str) -> str:
        """Return mock POC"""
        return f"// Mock POC for {vulnerability_data.get('id', 'unknown')}\n// TODO: Implement real POC"