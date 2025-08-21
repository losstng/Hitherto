"""Module Communication Protocol for coordinating signals between modules."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Callable
from enum import Enum

from pydantic import BaseModel

from backend.schemas.core.schemas import SignalBase, MessageEnvelope
from .base import ModuleBase, ModuleResult, ModuleRegistry


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class RoutingRule(BaseModel):
    """Defines how messages should be routed between modules."""
    source_module: str
    target_modules: List[str]
    message_types: List[str]
    priority: MessagePriority = MessagePriority.NORMAL
    conditions: Dict[str, Any] = {}  # Additional routing conditions


class MessageRouter:
    """Routes messages between modules based on defined rules."""
    
    def __init__(self):
        self.routing_rules: List[RoutingRule] = []
        self.message_queue: List[MessageEnvelope] = []
        self.message_history: List[MessageEnvelope] = []
        self.max_history_size = 1000
        
    def add_routing_rule(self, rule: RoutingRule) -> None:
        """Add a new routing rule."""
        self.routing_rules.append(rule)
        logging.info(f"Added routing rule: {rule.source_module} -> {rule.target_modules} for {rule.message_types}")
    
    def remove_routing_rule(self, source_module: str, target_modules: List[str], message_types: List[str]) -> bool:
        """Remove a routing rule."""
        for i, rule in enumerate(self.routing_rules):
            if (rule.source_module == source_module and 
                rule.target_modules == target_modules and 
                rule.message_types == message_types):
                del self.routing_rules[i]
                logging.info(f"Removed routing rule: {source_module} -> {target_modules}")
                return True
        return False
    
    def route_message(self, message: MessageEnvelope) -> List[str]:
        """Determine target modules for a message based on routing rules."""
        target_modules = set()
        
        for rule in self.routing_rules:
            # Check if rule applies to this message
            if (rule.source_module == message.origin_module and 
                message.message_type in rule.message_types):
                
                # Check additional conditions if any
                if self._check_conditions(message, rule.conditions):
                    target_modules.update(rule.target_modules)
        
        return list(target_modules)
    
    def _check_conditions(self, message: MessageEnvelope, conditions: Dict[str, Any]) -> bool:
        """Check if message meets additional routing conditions."""
        if not conditions:
            return True
        
        # Example condition checks - can be extended
        if "min_confidence" in conditions:
            confidence = getattr(message, 'confidence', None)
            if confidence is None or confidence < conditions["min_confidence"]:
                return False
        
        if "asset_filter" in conditions:
            asset = getattr(message, 'payload', {}).get('asset')
            if asset not in conditions["asset_filter"]:
                return False
        
        return True
    
    def queue_message(self, message: MessageEnvelope) -> None:
        """Add message to the queue."""
        self.message_queue.append(message)
        self._update_history(message)
    
    def get_messages_for_module(self, module_name: str) -> List[MessageEnvelope]:
        """Get all queued messages for a specific module."""
        relevant_messages = []
        
        for message in self.message_queue:
            target_modules = self.route_message(message)
            if module_name in target_modules:
                relevant_messages.append(message)
        
        return relevant_messages
    
    def clear_queue(self) -> None:
        """Clear the message queue."""
        self.message_queue.clear()
    
    def _update_history(self, message: MessageEnvelope) -> None:
        """Update message history."""
        self.message_history.append(message)
        if len(self.message_history) > self.max_history_size:
            self.message_history = self.message_history[-self.max_history_size:]
    
    def get_message_stats(self) -> Dict[str, Any]:
        """Get statistics about message routing."""
        stats: Dict[str, Any] = {
            "queued_messages": len(self.message_queue),
            "total_rules": len(self.routing_rules),
            "history_size": len(self.message_history),
        }
        
        # Message type distribution
        type_counts: Dict[str, int] = {}
        for msg in self.message_history[-100:]:  # Last 100 messages
            msg_type = msg.message_type
            type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
        
        stats["message_type_distribution"] = type_counts
        return stats


class ModuleCommunicationProtocol:
    """Orchestrates communication between modules using the registry and router."""
    
    def __init__(self):
        self.registry = ModuleRegistry()
        self.router = MessageRouter()
        self.execution_listeners: List[Callable[[str, ModuleResult], None]] = []
        self.cycle_count = 0
        
        # Set up default routing rules
        self._setup_default_routing()
    
    def _setup_default_routing(self) -> None:
        """Set up default routing rules for common signal flows."""
        
        # All signals go to overseer for fusion
        self.router.add_routing_rule(RoutingRule(
            source_module="sentiment",
            target_modules=["overseer"],
            message_types=["SentimentSignal"]
        ))
        
        self.router.add_routing_rule(RoutingRule(
            source_module="technical",
            target_modules=["overseer"],
            message_types=["TechnicalSignal"]
        ))
        
        self.router.add_routing_rule(RoutingRule(
            source_module="fundamental",
            target_modules=["overseer"],
            message_types=["FundamentalSignal"]
        ))
        
        # Trade proposals go to risk management
        self.router.add_routing_rule(RoutingRule(
            source_module="overseer",
            target_modules=["risk_management"],
            message_types=["TradeProposal"],
            priority=MessagePriority.HIGH
        ))
        
        # Risk signals go to execution (if approved) and overseer (for feedback)
        self.router.add_routing_rule(RoutingRule(
            source_module="risk_management",
            target_modules=["execution", "overseer"],
            message_types=["RiskSignal"],
            priority=MessagePriority.HIGH
        ))
        
        # Regime signals can go to all modules for context
        self.router.add_routing_rule(RoutingRule(
            source_module="overseer",
            target_modules=["sentiment", "technical", "fundamental", "risk_management"],
            message_types=["RegimeSignal"],
            priority=MessagePriority.NORMAL
        ))
    
    def register_module(self, module: ModuleBase, config: Optional[Dict[str, Any]] = None) -> bool:
        """Register a module with the communication protocol."""
        
        # Set up module communication through the router
        module.communication.publish = self.router.queue_message
        module.communication.get_messages_for_module = self.router.get_messages_for_module
        
        # Register with the registry
        success = self.registry.register(module, config)
        
        if success:
            logging.info(f"Module {module.name} registered with communication protocol")
        
        return success
    
    def add_execution_listener(self, listener: Callable[[str, ModuleResult], None]) -> None:
        """Add a listener for module execution results."""
        self.execution_listeners.append(listener)
    
    def execute_cycle(self, context: Optional[Dict[str, SignalBase]] = None) -> Dict[str, Any]:
        """Execute a complete communication cycle."""
        self.cycle_count += 1
        cycle_start = datetime.utcnow()
        
        logging.info(f"Starting communication cycle #{self.cycle_count}")
        
        try:
            # Clear previous message queue
            self.router.clear_queue()
            
            # Execute all modules
            module_results = self.registry.execute_all(context)
            
            # Notify listeners of execution results
            for module_name, result in module_results.items():
                for listener in self.execution_listeners:
                    try:
                        listener(module_name, result)
                    except Exception as e:
                        logging.error(f"Execution listener failed: {e}")
            
            # Collect all signals generated during this cycle
            all_signals = []
            for result in module_results.values():
                all_signals.extend(result.signals)
            
            # Get final message routing statistics
            routing_stats = self.router.get_message_stats()
            
            cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
            
            cycle_summary = {
                "cycle_number": self.cycle_count,
                "cycle_duration_seconds": cycle_duration,
                "modules_executed": len(module_results),
                "signals_generated": len(all_signals),
                "module_results": module_results,
                "routing_stats": routing_stats,
                "timestamp": cycle_start.isoformat()
            }
            
            logging.info(f"Completed cycle #{self.cycle_count} in {cycle_duration:.2f}s - "
                        f"{len(all_signals)} signals generated")
            
            return cycle_summary
            
        except Exception as e:
            logging.error(f"Communication cycle #{self.cycle_count} failed: {e}")
            return {
                "cycle_number": self.cycle_count,
                "error": str(e),
                "timestamp": cycle_start.isoformat()
            }
    
    def add_custom_routing_rule(self, rule: RoutingRule) -> None:
        """Add a custom routing rule."""
        self.router.add_routing_rule(rule)
    
    def get_module_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health status of all modules."""
        return self.registry.health_check_all()
    
    def get_communication_stats(self) -> Dict[str, Any]:
        """Get communication protocol statistics."""
        return {
            "cycle_count": self.cycle_count,
            "registered_modules": len(self.registry.list_modules()),
            "routing_rules": len(self.router.routing_rules),
            "execution_listeners": len(self.execution_listeners),
            "router_stats": self.router.get_message_stats()
        }
    
    def shutdown(self) -> None:
        """Shutdown all modules and clean up."""
        logging.info("Shutting down module communication protocol")
        
        # Deactivate all modules
        self.registry.deactivate_all()
        
        # Clean up modules
        for module_name in self.registry.list_modules():
            module = self.registry.get_module(module_name)
            if module:
                try:
                    module.cleanup()
                except Exception as e:
                    logging.error(f"Error cleaning up module {module_name}: {e}")
        
        # Clear message queues
        self.router.clear_queue()
        
        logging.info("Module communication protocol shutdown complete")


def create_default_protocol() -> ModuleCommunicationProtocol:
    """Create a default communication protocol with standard routing."""
    protocol = ModuleCommunicationProtocol()
    
    # Add logging listener
    def log_execution_result(module_name: str, result: ModuleResult) -> None:
        if result.success:
            logging.info(f"Module {module_name}: SUCCESS - {len(result.signals)} signals, "
                        f"{result.execution_time_ms:.1f}ms")
        else:
            logging.warning(f"Module {module_name}: FAILED - {result.errors}")
    
    protocol.add_execution_listener(log_execution_result)
    
    return protocol
