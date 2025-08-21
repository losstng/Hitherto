"""Base module framework for Hitherto signal processing."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field

from backend.schemas.core.schemas import SignalBase, MessageEnvelope


class ModuleStatus(str, Enum):
    """Module operational status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class ModuleResult(BaseModel):
    """Standardized result from module execution."""
    success: bool
    signals: List[SignalBase] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: Optional[float] = None


class ModuleError(Exception):
    """Base exception for module errors."""
    
    def __init__(self, message: str, module_name: str, error_code: Optional[str] = None):
        self.message = message
        self.module_name = module_name
        self.error_code = error_code
        super().__init__(f"[{module_name}] {message}")


class ModuleCommunication:
    """Handles inter-module communication protocol."""
    
    def __init__(self):
        self._message_queue: List[MessageEnvelope] = []
        self._subscribers: Dict[str, List[str]] = {}  # message_type -> list of module names
    
    def publish(self, message: MessageEnvelope) -> None:
        """Publish a message to all subscribers."""
        self._message_queue.append(message)
    
    def subscribe(self, module_name: str, message_types: List[str]) -> None:
        """Subscribe a module to specific message types."""
        for msg_type in message_types:
            if msg_type not in self._subscribers:
                self._subscribers[msg_type] = []
            if module_name not in self._subscribers[msg_type]:
                self._subscribers[msg_type].append(module_name)
    
    def get_messages_for_module(self, module_name: str) -> List[MessageEnvelope]:
        """Get all messages relevant to a specific module."""
        relevant_messages = []
        for message in self._message_queue:
            if message.message_type in self._subscribers:
                if module_name in self._subscribers[message.message_type]:
                    relevant_messages.append(message)
        return relevant_messages
    
    def clear_queue(self) -> None:
        """Clear the message queue."""
        self._message_queue.clear()


class ModuleBase(ABC):
    """Abstract base class for all Hitherto modules."""
    
    def __init__(
        self, 
        name: str, 
        version: str = "1.0.0",
        communication: Optional[ModuleCommunication] = None
    ):
        self.name = name
        self.version = version
        self.status = ModuleStatus.INACTIVE
        self.communication = communication or ModuleCommunication()
        self.config: Dict[str, Any] = {}
        self.last_execution: Optional[datetime] = None
        self.execution_count = 0
        
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the module with configuration."""
        pass
    
    @abstractmethod
    def process(self, context: Dict[str, SignalBase]) -> ModuleResult:
        """Process signals and generate module output."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources when module is shut down."""
        pass
    
    def get_subscribed_message_types(self) -> List[str]:
        """Return list of message types this module subscribes to."""
        return []
    
    def health_check(self) -> Dict[str, Any]:
        """Return module health status."""
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status.value,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "execution_count": self.execution_count,
        }
    
    def activate(self) -> None:
        """Activate the module."""
        if self.status == ModuleStatus.INACTIVE:
            self.status = ModuleStatus.ACTIVE
    
    def deactivate(self) -> None:
        """Deactivate the module."""
        self.status = ModuleStatus.INACTIVE
    
    def set_error_status(self, error_msg: str) -> None:
        """Set module to error status."""
        self.status = ModuleStatus.ERROR
        # Could log error here
    
    def execute(self, context: Dict[str, SignalBase]) -> ModuleResult:
        """Execute the module with error handling and timing."""
        if self.status != ModuleStatus.ACTIVE:
            return ModuleResult(
                success=False,
                errors=[f"Module {self.name} is not active (status: {self.status.value})"]
            )
        
        start_time = datetime.utcnow()
        try:
            result = self.process(context)
            result.execution_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.last_execution = datetime.utcnow()
            self.execution_count += 1
            
            # Publish any signals generated
            for signal in result.signals:
                self.communication.publish(signal)
            
            return result
            
        except Exception as e:
            self.set_error_status(str(e))
            return ModuleResult(
                success=False,
                errors=[f"Module {self.name} execution failed: {str(e)}"],
                execution_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
            )


class ModuleRegistry:
    """Registry to manage all modules in the system."""
    
    def __init__(self):
        self._modules: Dict[str, ModuleBase] = {}
        self._execution_order: List[str] = []
        self.communication = ModuleCommunication()
    
    def register(self, module: ModuleBase, config: Optional[Dict[str, Any]] = None) -> bool:
        """Register a module in the system."""
        if module.name in self._modules:
            raise ValueError(f"Module {module.name} already registered")
        
        # Set up communication
        module.communication = self.communication
        
        # Initialize module
        init_config = config or {}
        if not module.initialize(init_config):
            return False
        
        # Subscribe to message types
        subscribed_types = module.get_subscribed_message_types()
        if subscribed_types:
            self.communication.subscribe(module.name, subscribed_types)
        
        self._modules[module.name] = module
        self._execution_order.append(module.name)
        
        return True
    
    def unregister(self, module_name: str) -> bool:
        """Unregister a module from the system."""
        if module_name not in self._modules:
            return False
        
        module = self._modules[module_name]
        module.cleanup()
        
        del self._modules[module_name]
        if module_name in self._execution_order:
            self._execution_order.remove(module_name)
        
        return True
    
    def get_module(self, name: str) -> Optional[ModuleBase]:
        """Get a module by name."""
        return self._modules.get(name)
    
    def list_modules(self) -> List[str]:
        """List all registered module names."""
        return list(self._modules.keys())
    
    def activate_all(self) -> None:
        """Activate all modules."""
        for module in self._modules.values():
            module.activate()
    
    def deactivate_all(self) -> None:
        """Deactivate all modules."""
        for module in self._modules.values():
            module.deactivate()
    
    def execute_all(self, context: Optional[Dict[str, SignalBase]] = None) -> Dict[str, ModuleResult]:
        """Execute all active modules in order."""
        context = context or {}
        results = {}
        
        # Clear previous message queue
        self.communication.clear_queue()
        
        for module_name in self._execution_order:
            module = self._modules[module_name]
            
            # Get messages for this module
            relevant_messages = self.communication.get_messages_for_module(module_name)
            
            # Execute module
            result = module.execute(context)
            results[module_name] = result
            
            # Update context with any signals generated
            for signal in result.signals:
                context[f"{module_name}_{signal.message_type}"] = signal
        
        return results
    
    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Get health status of all modules."""
        return {name: module.health_check() for name, module in self._modules.items()}
