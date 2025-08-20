from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from collections import deque

class AgentMemory:
    """Memory management for agents with short and long-term storage"""
    
    def __init__(self, max_short_term: int = 100, max_long_term: int = 1000):
        self.short_term = deque(maxlen=max_short_term)  # Recent events
        self.long_term = deque(maxlen=max_long_term)    # Important events
        self.episodic = {}  # Key episodes/patterns
        self.working = {}    # Current working memory
        
    def store_event(self, event: Dict[str, Any], importance: float = 0.5):
        """Store an event in memory based on importance"""
        timestamped_event = {
            **event,
            "timestamp": datetime.now().isoformat(),
            "importance": importance
        }
        
        self.short_term.append(timestamped_event)
        
        if importance > 0.7:  # Important events go to long-term
            self.long_term.append(timestamped_event)
            
        # Update working memory with latest relevant info
        self._update_working_memory(event)
    
    def _update_working_memory(self, event: Dict):
        """Update working memory with relevant information"""
        if "signal_type" in event:
            self.working[event["signal_type"]] = event
            
    def recall_recent(self, n: int = 10) -> List[Dict]:
        """Recall n most recent events"""
        return list(self.short_term)[-n:]
    
    def recall_similar(self, pattern: Dict, threshold: float = 0.8) -> List[Dict]:
        """Recall events similar to a pattern"""
        similar = []
        for event in self.long_term:
            if self._similarity(event, pattern) > threshold:
                similar.append(event)
        return similar
    
    def _similarity(self, event1: Dict, event2: Dict) -> float:
        """Calculate similarity between two events"""
        # Implement similarity metric
        # Placeholder: check key overlap
        keys1 = set(event1.keys())
        keys2 = set(event2.keys())
        if not keys1 or not keys2:
            return 0.0
        return len(keys1 & keys2) / len(keys1 | keys2)
    
    def consolidate(self):
        """Consolidate short-term memories into patterns"""
        # Identify patterns in short-term memory
        # Store important patterns in episodic memory
        pass
    
    def get_context_for_llm(self) -> Dict[str, Any]:
        """Prepare memory context for LLM"""
        return {
            "working_memory": self.working,
            "recent_events": self.recall_recent(5),
            "important_patterns": list(self.episodic.values())
        }