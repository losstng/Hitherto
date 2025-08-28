"""
LLM Provider Interface for Hitherto

This module provides the core LLM reasoning engine interface as described in Simple.md.
Focuses on supplying structured context to LLMs for decision-making across all modules.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json


@dataclass
class LLMMessage:
    """Structured message for LLM communication"""
    role: str  # "system", "user", "assistant"
    content: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMContext:
    """Structured context container for LLM reasoning"""
    module_name: str
    context_data: Dict[str, Any]
    instructions: str
    priority: str = "normal"  # "low", "normal", "high", "critical"


class LLMProvider(ABC):
    """Abstract base class for LLM provider implementations"""
    
    def __init__(self, model_name: str, api_key: Optional[str] = None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    async def send_prompt(
        self, 
        messages: List[LLMMessage], 
        context: Optional[LLMContext] = None,
        **kwargs
    ) -> str:
        """
        Send structured context and prompt to the LLM provider
        
        Args:
            messages: List of structured messages for the conversation
            context: Optional structured context for the reasoning task
            **kwargs: Provider-specific parameters
            
        Returns:
            LLM response as string
        """
        pass
    
    @abstractmethod
    def format_context(self, context: LLMContext) -> str:
        """Format structured context for the specific provider"""
        pass


class HithertoLLM:
    """
    Main LLM interface for the Hitherto framework
    
    Manages provider connections and routes structured context to appropriate LLMs
    for reasoning across all modules as per the framework design.
    """
    
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self.default_provider: Optional[str] = None
    
    def register_provider(self, name: str, provider: LLMProvider, set_as_default: bool = False):
        """Register an LLM provider"""
        self.providers[name] = provider
        if set_as_default or not self.default_provider:
            self.default_provider = name
    
    async def reason(
        self, 
        prompt: str, 
        context: Optional[LLMContext] = None, 
        provider_name: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Core reasoning method - sends context and prompt to LLM for decision-making
        
        Args:
            prompt: The reasoning prompt/question
            context: Structured context for the LLM to reason about
            provider_name: Specific provider to use (defaults to configured default)
            **kwargs: Additional parameters for the provider
            
        Returns:
            LLM reasoning response
        """
        provider_name = provider_name or self.default_provider
        
        if not provider_name or provider_name not in self.providers:
            raise ValueError(f"No valid provider specified. Available: {list(self.providers.keys())}")
        
        provider = self.providers[provider_name]
        
        # Build messages with context if provided
        messages = []
        
        if context:
            system_message = LLMMessage(
                role="system",
                content=f"Module: {context.module_name}\nInstructions: {context.instructions}",
                metadata={"module": context.module_name, "priority": context.priority}
            )
            messages.append(system_message)
            
            # Add structured context as a user message
            context_content = provider.format_context(context)
            context_message = LLMMessage(
                role="user", 
                content=f"Context:\n{context_content}",
                metadata={"type": "context"}
            )
            messages.append(context_message)
        
        # Add the main prompt
        prompt_message = LLMMessage(role="user", content=prompt)
        messages.append(prompt_message)
        
        return await provider.send_prompt(messages, context, **kwargs)
    
    def get_provider(self, name: Optional[str] = None) -> LLMProvider:
        """Get a specific provider or the default"""
        provider_name = name or self.default_provider
        if not provider_name or provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")
        return self.providers[provider_name]


# Global instance for the framework
hitherto_llm = HithertoLLM()


def create_context(
    module_name: str, 
    data: Dict[str, Any], 
    instructions: str, 
    priority: str = "normal"
) -> LLMContext:
    """Convenience function to create structured context for LLM reasoning"""
    return LLMContext(
        module_name=module_name,
        context_data=data,
        instructions=instructions,
        priority=priority
    )


def create_message(role: str, content: str, **metadata) -> LLMMessage:
    """Convenience function to create LLM messages"""
    return LLMMessage(role=role, content=content, metadata=metadata)
