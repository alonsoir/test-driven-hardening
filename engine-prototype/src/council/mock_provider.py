"""Mock council provider"""

class MockCouncil:
    def __init__(self, config=None):
        self.config = config or {}
    
    def propose_fixes(self, vulnerability):
        return [{
            "description": "Mock fix for demonstration",
            "confidence": 0.8
        }]
