"""
Interface for LLM Council providers.
Defines the abstract base class that all council providers must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class FixProposal:
    """A fix proposed by a council member."""
    id: str
    author: str  # Name of the LLM/model
    role: str    # Role of this model (architect, security, etc.)
    code: str    # The fix code
    explanation: str  # Explanation of the fix
    tests: Optional[str] = None  # Test code to validate the fix
    confidence: float = 0.0  # Confidence score from 0-1
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class VulnerabilityAnalysis:
    """Analysis of a vulnerability by a council member."""
    vulnerability_id: str
    council_member: str
    root_cause: str
    exploitability: str  # HIGH, MEDIUM, LOW
    proposed_fixes: List[FixProposal]
    poc_code: Optional[str] = None  # Proof of concept code
    recommendations: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LLMProvider(ABC):
    """
    Abstract base class for all LLM providers in the council.
    Each provider can be a real LLM API, a mock, or a local model.
    """
    
    @abstractmethod
    def __init__(self, name: str, role: str, config: Dict[str, Any]):
        """
        Initialize the provider.
        
        Args:
            name: Name of the provider (e.g., "claude", "deepseek")
            role: Role in the council (e.g., "architect", "security")
            config: Provider-specific configuration
        """
        self.name = name
        self.role = role
        self.config = config
    
    @abstractmethod
    async def analyze_vulnerability(self, 
                                   vulnerability_data: Dict[str, Any],
                                   code_context: str) -> VulnerabilityAnalysis:
        """
        Analyze a vulnerability and propose fixes.
        
        Args:
            vulnerability_data: Information about the vulnerability
            code_context: The vulnerable code and surrounding context
            
        Returns:
            VulnerabilityAnalysis with proposed fixes
        """
        pass
    
    @abstractmethod
    async def review_fix(self,
                        fix_proposal: FixProposal,
                        original_code: str,
                        vulnerability_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Review a fix proposed by another council member.
        
        Args:
            fix_proposal: The fix to review
            original_code: The original vulnerable code
            vulnerability_data: Information about the vulnerability
            
        Returns:
            Review with score and comments
        """
        pass
    
    @abstractmethod
    async def generate_poc(self,
                          vulnerability_data: Dict[str, Any],
                          code_context: str) -> str:
        """
        Generate a proof-of-concept exploit for the vulnerability.
        
        Args:
            vulnerability_data: Information about the vulnerability
            code_context: The vulnerable code
            
        Returns:
            POC code as a string
        """
        pass
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get the capabilities of this provider.
        
        Returns:
            Dictionary describing provider capabilities
        """
        return {
            'name': self.name,
            'role': self.role,
            'can_analyze': True,
            'can_review': True,
            'can_generate_poc': True,
            'config': self.config
        }