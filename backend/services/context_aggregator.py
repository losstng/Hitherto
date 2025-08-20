from typing import Dict, List, Any, Optional
from datetime import datetime
import json

class ContextAggregator:
    """Aggregates context from all agents for LLM consumption"""
    
    def __init__(self):
        self.agents: Dict[str, AgentWrapper] = {}
        self.global_context = {}
        self.regime_state = "unknown"
        
    def register_agent(self, agent: AgentWrapper):
        """Register an agent with the aggregator"""
        self.agents[agent.agent_id] = agent
        
    def collect_all_contexts(self) -> Dict[str, Any]:
        """Collect and structure context from all agents"""
        timestamp = datetime.now()
        
        # Collect individual agent contexts
        agent_contexts = {}
        for agent_id, agent in self.agents.items():
            try:
                agent_contexts[agent_id] = agent.prepare_context_for_llm()
            except Exception as e:
                agent_contexts[agent_id] = {"error": str(e)}
        
        # Build the master context
        master_context = {
            "timestamp": timestamp.isoformat(),
            "regime": self.regime_state,
            "agents": agent_contexts,
            "fusion": self._fuse_signals(agent_contexts),
            "risk_status": self._get_risk_status(),
            "action_proposals": self._generate_proposals(agent_contexts)
        }
        
        return master_context
    
    def _fuse_signals(self, contexts: Dict[str, Any]) -> Dict[str, Any]:
        """Fuse signals from multiple agents into unified view"""
        # Extract and combine signals
        signals = {}
        for agent_id, context in contexts.items():
            if "service_output" in context:
                signals[agent_id] = context["service_output"]
        
        # Apply fusion logic (weighted average, voting, etc.)
        return {
            "consensus_direction": self._calculate_consensus(signals),
            "confidence": self._calculate_confidence(signals),
            "conflicts": self._identify_conflicts(signals)
        }
    
    def _calculate_consensus(self, signals: Dict) -> str:
        """Calculate consensus from multiple signals"""
        # Implement voting or weighted averaging
        # This is a placeholder
        return "bullish"
    
    def _calculate_confidence(self, signals: Dict) -> float:
        """Calculate overall confidence level"""
        # Implement confidence scoring
        return 0.75
    
    def _identify_conflicts(self, signals: Dict) -> List[str]:
        """Identify conflicting signals between agents"""
        conflicts = []
        # Compare signals and identify disagreements
        return conflicts
    
    def _get_risk_status(self) -> Dict[str, Any]:
        """Get current risk status from risk agent"""
        if "risk" in self.agents:
            return self.agents["risk"].state.get("current_limits", {})
        return {}
    
    def _generate_proposals(self, contexts: Dict) -> List[Dict]:
        """Generate action proposals based on all contexts"""
        proposals = []
        # Synthesize contexts into actionable proposals
        return proposals
    
    def prepare_llm_prompt(self) -> str:
        """Prepare the full prompt for LLM with all context"""
        context = self.collect_all_contexts()
        
        prompt = f"""
## Current Market Intelligence Context

**Timestamp**: {context['timestamp']}
**Market Regime**: {context['regime']}

### Agent Signals:
{json.dumps(context['agents'], indent=2)}

### Signal Fusion:
- Consensus Direction: {context['fusion']['consensus_direction']}
- Confidence Level: {context['fusion']['confidence']}
- Conflicts: {context['fusion'].get('conflicts', [])}

### Risk Status:
{json.dumps(context['risk_status'], indent=2)}

### Action Proposals:
{json.dumps(context['action_proposals'], indent=2)}

Based on this comprehensive context, provide investment recommendations.
"""
        return prompt