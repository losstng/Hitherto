"""Module system for Hitherto signal processing."""

from .base import ModuleBase, ModuleResult, ModuleError, ModuleRegistry, ModuleCommunication
from .overseer import OverseerModule
from .risk_management import RiskManagementModule
from .communication import ModuleCommunicationProtocol, MessageRouter, RoutingRule, create_default_protocol

__all__ = [
    "ModuleBase",
    "ModuleResult", 
    "ModuleError",
    "ModuleRegistry",
    "ModuleCommunication",
    "OverseerModule",
    "RiskManagementModule",
    "ModuleCommunicationProtocol",
    "MessageRouter",
    "RoutingRule",
    "create_default_protocol",
]
