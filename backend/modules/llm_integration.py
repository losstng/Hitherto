"""Enhanced LLM integration for the modules architecture."""

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

from pydantic import BaseModel, Field

from backend.schemas.core.schemas import (
    SignalBase, TradeAction, TradeProposal, RegimeSignal
)

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    LOCAL = "local"
    ANTHROPIC = "anthropic"
    MOCK = "mock"


class LLMConfig(BaseModel):
    """Configuration for LLM providers."""
    provider: LLMProvider = LLMProvider.OPENAI
    model: str = "gpt-3.5-turbo"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 1024
    temperature: float = 0.7
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0


class LLMResponse(BaseModel):
    """Standardized LLM response."""
    content: str
    usage_tokens: Optional[int] = None
    model: str
    provider: str
    response_time_ms: float
    success: bool = True
    error_message: Optional[str] = None


class PromptTemplate(BaseModel):
    """Template for LLM prompts."""
    name: str
    template: str
    required_variables: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    examples: List[Dict[str, Any]] = Field(default_factory=list)


class LLMProvider_Base(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None
        self._initialize()
    
    @abstractmethod
    def _initialize(self) -> None:
        """Initialize the LLM client."""
        pass
    
    @abstractmethod
    def _make_request(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """Make a request to the LLM."""
        pass
    
    @property
    def available(self) -> bool:
        """Check if the provider is available."""
        return self._client is not None
    
    def complete(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """Complete a chat conversation with retry logic."""
        
        for attempt in range(self.config.retry_attempts):
            try:
                start_time = time.perf_counter()
                response = self._make_request(messages)
                response.response_time_ms = (time.perf_counter() - start_time) * 1000
                return response
                
            except Exception as e:
                logger.warning(f"LLM request attempt {attempt + 1} failed: {e}")
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                else:
                    return LLMResponse(
                        content="",
                        model=self.config.model,
                        provider=self.config.provider.value,
                        response_time_ms=0,
                        success=False,
                        error_message=str(e)
                    )


class OpenAIProvider(LLMProvider_Base):
    """OpenAI LLM provider."""
    
    def _initialize(self) -> None:
        """Initialize OpenAI client."""
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OpenAI API key not found")
            return
        
        try:
            import openai
            self._client = openai.OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized")
        except ImportError:
            logger.error("OpenAI package not installed")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def _make_request(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """Make request to OpenAI API."""
        if not self._client:
            raise Exception("OpenAI client not initialized")
        
        response = self._client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            timeout=self.config.timeout
        )
        
        return LLMResponse(
            content=response.choices[0].message.content,
            usage_tokens=response.usage.total_tokens if response.usage else None,
            model=response.model,
            provider=self.config.provider.value,
            response_time_ms=0  # Will be set by caller
        )


class LocalProvider(LLMProvider_Base):
    """Local LLM provider (LM Studio, etc.)."""
    
    def _initialize(self) -> None:
        """Initialize local LLM client."""
        try:
            import requests
            self._client = requests
            self.base_url = self.config.base_url or "http://127.0.0.1:1234/v1"
            logger.info(f"Local LLM client initialized with base_url: {self.base_url}")
        except ImportError:
            logger.error("Requests package not installed")
        except Exception as e:
            logger.error(f"Failed to initialize local LLM client: {e}")
    
    def _make_request(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """Make request to local LLM API."""
        if not self._client:
            raise Exception("Local LLM client not initialized")
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "stream": False
        }
        
        response = self._client.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            timeout=self.config.timeout
        )
        response.raise_for_status()
        
        data = response.json()
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        return LLMResponse(
            content=content,
            usage_tokens=data.get("usage", {}).get("total_tokens"),
            model=self.config.model,
            provider=self.config.provider.value,
            response_time_ms=0  # Will be set by caller
        )


class MockProvider(LLMProvider_Base):
    """Mock LLM provider for testing."""
    
    def _initialize(self) -> None:
        """Initialize mock client."""
        self._client = True
        logger.info("Mock LLM client initialized")
    
    def _make_request(self, messages: List[Dict[str, str]]) -> LLMResponse:
        """Generate mock response."""
        time.sleep(0.1)  # Simulate network delay
        
        # Generate simple mock response based on last message
        last_message = messages[-1].get("content", "") if messages else ""
        
        if "trade" in last_message.lower() or "action" in last_message.lower():
            mock_content = json.dumps({
                "actions": [
                    {
                        "asset": "MOCK_ASSET",
                        "action": "BUY",
                        "size": 100,
                        "rationale": "Mock trading decision based on signals"
                    }
                ]
            })
        else:
            mock_content = "Mock LLM response for: " + last_message[:50] + "..."
        
        return LLMResponse(
            content=mock_content,
            usage_tokens=50,
            model=self.config.model,
            provider=self.config.provider.value,
            response_time_ms=0  # Will be set by caller
        )


class PromptManager:
    """Manages prompt templates and formatting."""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self) -> None:
        """Load default prompt templates."""
        
        # Trade decision template
        self.add_template(PromptTemplate(
            name="trade_decision",
            template="""You are an AI trading strategist for the Hitherto trading system.

Current Context:
- Market Regime: {regime}
- Playbook Weights: {playbook_weights}
- Available Signals: {signals}

Your task is to analyze the signals and generate trade actions based on the current regime and playbook configuration.

Output Format:
Return a JSON object with an "actions" list. Each action must include:
- asset: string (asset symbol)
- action: "BUY" or "SELL"
- size: number (position size)
- rationale: string (brief explanation)

Constraints:
- Only trade assets mentioned in the signals
- Consider signal confidence and regime appropriateness
- Limit to maximum 5 actions per cycle
- Ensure rationale explains the decision logic

Context Data: {context_json}""",
            required_variables=["regime", "playbook_weights", "signals", "context_json"],
            description="Generate trade actions from market signals"
        ))
        
        # Proposal summary template
        self.add_template(PromptTemplate(
            name="proposal_summary",
            template="""Summarize the following trade proposal in 1-2 clear sentences:

Proposal Data: {proposal_json}

Focus on:
- Number and type of actions
- Key assets involved
- Overall strategy (buy/sell bias)
- Any notable risk considerations

Keep it concise and informative for human reviewers.""",
            required_variables=["proposal_json"],
            description="Create human-readable proposal summaries"
        ))
        
        # Risk analysis template
        self.add_template(PromptTemplate(
            name="risk_analysis",
            template="""You are a risk management expert analyzing a trade proposal.

Proposal: {proposal_json}
Risk Metrics: {risk_metrics}
Market Context: {market_context}

Provide a brief risk assessment covering:
1. Key risk factors identified
2. Risk level (LOW/MEDIUM/HIGH)
3. Recommended actions (APPROVE/DOWNGRADE/REJECT)
4. Brief rationale

Format as JSON:
{{
    "risk_level": "LOW|MEDIUM|HIGH",
    "recommendation": "APPROVE|DOWNGRADE|REJECT",
    "key_risks": ["risk1", "risk2", ...],
    "rationale": "Brief explanation"
}}""",
            required_variables=["proposal_json", "risk_metrics", "market_context"],
            description="Analyze risk for trade proposals"
        ))
        
        # Regime classification template
        self.add_template(PromptTemplate(
            name="regime_classification",
            template="""You are a market regime analyst. Analyze the current market conditions and classify the regime.

Market Data: {market_data}
Recent Signals: {recent_signals}
Historical Context: {historical_context}

Available Regimes: BULL, BEAR, SIDEWAYS, HIGH_VOL, LOW_VOL, CRISIS, RECOVERY

Consider:
- Volatility patterns
- Market momentum
- Risk sentiment
- Economic indicators

Output JSON format:
{{
    "regime": "REGIME_NAME",
    "confidence": 0.0-1.0,
    "rationale": "Brief explanation",
    "key_indicators": ["indicator1", "indicator2", ...]
}}""",
            required_variables=["market_data", "recent_signals", "historical_context"],
            description="Classify market regime using LLM analysis"
        ))
    
    def add_template(self, template: PromptTemplate) -> None:
        """Add a prompt template."""
        self.templates[template.name] = template
        logger.debug(f"Added prompt template: {template.name}")
    
    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a prompt template by name."""
        return self.templates.get(name)
    
    def format_prompt(self, template_name: str, **kwargs) -> str:
        """Format a prompt template with variables."""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Check required variables
        missing_vars = set(template.required_variables) - set(kwargs.keys())
        if missing_vars:
            raise ValueError(f"Missing required variables: {missing_vars}")
        
        return template.template.format(**kwargs)


class EnhancedLLMReasoner:
    """Enhanced LLM reasoning for modules architecture."""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.provider = self._create_provider()
        self.prompt_manager = PromptManager()
        self.request_count = 0
        self.total_tokens = 0
    
    def _create_provider(self) -> LLMProvider_Base:
        """Create the appropriate LLM provider."""
        if self.config.provider == LLMProvider.OPENAI:
            return OpenAIProvider(self.config)
        elif self.config.provider == LLMProvider.LOCAL:
            return LocalProvider(self.config)
        elif self.config.provider == LLMProvider.MOCK:
            return MockProvider(self.config)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    @property
    def available(self) -> bool:
        """Check if LLM is available."""
        return self.provider.available
    
    def decide_trades(
        self,
        regime: str,
        signals: List[SignalBase],
        playbook_weights: Dict[str, float]
    ) -> Tuple[List[TradeAction], List[str]]:
        """Generate trade decisions using LLM reasoning."""
        
        if not self.available:
            logger.warning("LLM not available, returning empty actions")
            return [], []
        
        try:
            # Prepare context
            context = {
                "regime": regime,
                "playbook_weights": playbook_weights,
                "signals": [s.model_dump() for s in signals],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Format prompt
            prompt = self.prompt_manager.format_prompt(
                "trade_decision",
                regime=regime,
                playbook_weights=json.dumps(playbook_weights),
                signals=json.dumps([s.model_dump() for s in signals], indent=2),
                context_json=json.dumps(context, indent=2)
            )
            
            # Make LLM request
            messages = [{"role": "user", "content": prompt}]
            response = self.provider.complete(messages)
            
            self._update_stats(response)
            
            if not response.success:
                logger.error(f"LLM request failed: {response.error_message}")
                return [], []
            
            # Parse response
            try:
                data = json.loads(response.content)
                actions = []
                rationales = []
                
                for action_data in data.get("actions", []):
                    if all(key in action_data for key in ["asset", "action", "size"]):
                        actions.append(TradeAction(
                            asset=action_data["asset"],
                            action=action_data["action"],
                            size=action_data["size"]
                        ))
                        rationales.append(action_data.get("rationale", "No rationale provided"))
                
                logger.info(f"LLM generated {len(actions)} trade actions")
                return actions, rationales
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.debug(f"Raw response: {response.content}")
                return [], []
                
        except Exception as e:
            logger.error(f"Trade decision generation failed: {e}")
            return [], []
    
    def summarize_proposal(self, proposal: TradeProposal) -> str:
        """Generate human-readable proposal summary."""
        
        if not self.available:
            # Fallback summary
            actions = proposal.payload.actions
            if not actions:
                return "No actions proposed"
            
            parts = [f"{a.action} {a.size} {a.asset}" for a in actions]
            return f"Proposed actions: {'; '.join(parts)}"
        
        try:
            prompt = self.prompt_manager.format_prompt(
                "proposal_summary",
                proposal_json=json.dumps(proposal.payload.model_dump(), indent=2)
            )
            
            messages = [{"role": "user", "content": prompt}]
            response = self.provider.complete(messages)
            
            self._update_stats(response)
            
            if response.success:
                return response.content.strip()
            else:
                logger.error(f"Summary generation failed: {response.error_message}")
                return "Summary generation failed"
                
        except Exception as e:
            logger.error(f"Proposal summarization failed: {e}")
            return "Summary unavailable"
    
    def analyze_risk(
        self,
        proposal_data: Dict[str, Any],
        risk_metrics: Dict[str, float],
        market_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze risk using LLM reasoning."""
        
        if not self.available:
            return {
                "risk_level": "MEDIUM",
                "recommendation": "APPROVE",
                "key_risks": ["LLM unavailable"],
                "rationale": "Risk analysis unavailable - LLM not accessible"
            }
        
        try:
            prompt = self.prompt_manager.format_prompt(
                "risk_analysis",
                proposal_json=json.dumps(proposal_data, indent=2),
                risk_metrics=json.dumps(risk_metrics, indent=2),
                market_context=json.dumps(market_context, indent=2)
            )
            
            messages = [{"role": "user", "content": prompt}]
            response = self.provider.complete(messages)
            
            self._update_stats(response)
            
            if response.success:
                try:
                    return json.loads(response.content)
                except json.JSONDecodeError:
                    return {
                        "risk_level": "MEDIUM",
                        "recommendation": "APPROVE",
                        "key_risks": ["Parse error"],
                        "rationale": response.content[:200] + "..."
                    }
            else:
                return {
                    "risk_level": "HIGH",
                    "recommendation": "REJECT",
                    "key_risks": ["Analysis failed"],
                    "rationale": f"Risk analysis failed: {response.error_message}"
                }
                
        except Exception as e:
            logger.error(f"Risk analysis failed: {e}")
            return {
                "risk_level": "HIGH",
                "recommendation": "REJECT",
                "key_risks": ["System error"],
                "rationale": f"Risk analysis error: {str(e)}"
            }
    
    def classify_regime(
        self,
        market_data: Dict[str, Any],
        recent_signals: List[Dict[str, Any]],
        historical_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Classify market regime using LLM."""
        
        if not self.available:
            return {
                "regime": "BULL",
                "confidence": 0.5,
                "rationale": "Default regime - LLM unavailable",
                "key_indicators": ["fallback"]
            }
        
        try:
            prompt = self.prompt_manager.format_prompt(
                "regime_classification",
                market_data=json.dumps(market_data, indent=2),
                recent_signals=json.dumps(recent_signals, indent=2),
                historical_context=json.dumps(historical_context, indent=2)
            )
            
            messages = [{"role": "user", "content": prompt}]
            response = self.provider.complete(messages)
            
            self._update_stats(response)
            
            if response.success:
                try:
                    result = json.loads(response.content)
                    # Validate result
                    valid_regimes = ["BULL", "BEAR", "SIDEWAYS", "HIGH_VOL", "LOW_VOL", "CRISIS", "RECOVERY"]
                    if result.get("regime") not in valid_regimes:
                        result["regime"] = "BULL"
                    if not isinstance(result.get("confidence"), (int, float)) or not 0 <= result.get("confidence") <= 1:
                        result["confidence"] = 0.5
                    
                    return result
                except json.JSONDecodeError:
                    return {
                        "regime": "BULL",
                        "confidence": 0.5,
                        "rationale": "Parse error in regime classification",
                        "key_indicators": ["parse_error"]
                    }
            else:
                return {
                    "regime": "BULL",
                    "confidence": 0.3,
                    "rationale": f"Classification failed: {response.error_message}",
                    "key_indicators": ["error"]
                }
                
        except Exception as e:
            logger.error(f"Regime classification failed: {e}")
            return {
                "regime": "BULL",
                "confidence": 0.3,
                "rationale": f"Classification error: {str(e)}",
                "key_indicators": ["system_error"]
            }
    
    def _update_stats(self, response: LLMResponse) -> None:
        """Update usage statistics."""
        self.request_count += 1
        if response.usage_tokens:
            self.total_tokens += response.usage_tokens
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "provider": self.config.provider.value,
            "model": self.config.model,
            "available": self.available,
            "request_count": self.request_count,
            "total_tokens": self.total_tokens,
            "avg_tokens_per_request": self.total_tokens / max(1, self.request_count)
        }


def create_default_reasoner() -> EnhancedLLMReasoner:
    """Create a default LLM reasoner with standard configuration."""
    
    # Try to determine best available provider
    if os.getenv("OPENAI_API_KEY"):
        config = LLMConfig(provider=LLMProvider.OPENAI)
    elif os.getenv("LOCAL_LLM_BASE_URL"):
        config = LLMConfig(
            provider=LLMProvider.LOCAL,
            base_url=os.getenv("LOCAL_LLM_BASE_URL"),
            model=os.getenv("LOCAL_LLM_MODEL", "local-model")
        )
    else:
        config = LLMConfig(provider=LLMProvider.MOCK)
        logger.warning("No LLM configuration found, using mock provider")
    
    return EnhancedLLMReasoner(config)
