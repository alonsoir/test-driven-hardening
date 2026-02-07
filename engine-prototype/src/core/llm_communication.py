from datetime import datetime
from typing import Dict, List, Optional

class LLMCommunicationHub:
    """
    Centro de comunicación para que los LLMs compartan información.
    """
    
    def __init__(self):
        self.messages: Dict[str, List[Dict]] = {}  # llm -> [messages]
        self.broadcast_history: List[Dict] = []
        
    async def send_message(self, sender: str, recipient: str, message: Dict):
        """Envía mensaje directo a otro LLM."""
        if recipient not in self.messages:
            self.messages[recipient] = []
        
        message_with_meta = {
            'sender': sender,
            'recipient': recipient,
            'timestamp': datetime.now(),
            'message': message
        }
        
        self.messages[recipient].append(message_with_meta)
        
        # También mantener histórico
        self.broadcast_history.append(message_with_meta)
        
        print(f"   📨 {sender} → {recipient}: {message.get('type', 'message')}")
    
    async def broadcast(self, sender: str, message: Dict, exclude_sender: bool = True):
        """Envía mensaje a todos los LLMs."""
        recipients = [llm for llm in self.messages.keys() 
                     if not (exclude_sender and llm == sender)]
        
        for recipient in recipients:
            await self.send_message(sender, recipient, message)
    
    async def get_messages(self, llm_name: str, clear: bool = False) -> List[Dict]:
        """Obtiene mensajes para un LLM."""
        messages = self.messages.get(llm_name, [])
        
        if clear:
            self.messages[llm_name] = []
        
        return messages
    
    def get_status(self) -> Dict:
        """Estado del hub de comunicación."""
        return {
            'active_llms': list(self.messages.keys()),
            'total_messages': len(self.broadcast_history),
            'unread_by_llm': {llm: len(msgs) for llm, msgs in self.messages.items()}
        }