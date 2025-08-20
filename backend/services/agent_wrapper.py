from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from enum import Enum

class MessageType(Enum):
    SIGNAL = "signal"
    QUERY = "query"
    POLICY = "policy"
    ALERT = "alert"
    STATE_UPDATE = "state"

@dataclass
class AgentMessage:
    """Structured message for inter-agent communication"""
    sender: str
    receiver: str
    message_type: MessageType
    payload: Dict[str, Any]
    timestamp: datetime
    correlation_id: Optional[str] = None
    requires_response: bool = False
    
    def to_json(self) -> str:
        return json.dumps({
            **asdict(self),
            'message_type': self.message_type.value,
            'timestamp': self.timestamp.isoformat()
        })

class AgentWrapper:
    """Base wrapper to make services act as autonomous agents"""
    
    def __init__(self, agent_id: str, service_instance: Any):
        self.agent_id = agent_id
        self.service = service_instance
        self.state = {}
        self.message_queue: List[AgentMessage] = []
        self.context_history = []
        
    def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process incoming message and generate response if needed"""
        # Update internal state based on message
        self.update_state(message)
        
        if message.requires_response:
            response_payload = self.generate_response(message)
            return AgentMessage(
                sender=self.agent_id,
                receiver=message.sender,
                message_type=MessageType.SIGNAL,
                payload=response_payload,
                timestamp=datetime.now(),
                correlation_id=message.correlation_id
            )
        return None
    
    def update_state(self, message: AgentMessage):
        """Update agent's internal state based on received message"""
        self.state[f"{message.sender}_last_signal"] = message.payload
        self.state["last_update"] = message.timestamp
        
    def generate_response(self, message: AgentMessage) -> Dict[str, Any]:
        """Generate response based on service logic"""
        # This would call the actual service method
        # Example: self.service.analyze(message.payload)
        raise NotImplementedError
        
    def prepare_context_for_llm(self) -> Dict[str, Any]:
        """Prepare structured context for LLM consumption"""
        return {
            "agent_id": self.agent_id,
            "current_state": self.state,
            "recent_messages": [msg.to_json() for msg in self.message_queue[-10:]],
            "service_output": self.get_latest_output()
        }
    
    def get_latest_output(self) -> Any:
        """Get the latest output from the wrapped service"""
        # Override in specific implementations
        raise NotImplementedError